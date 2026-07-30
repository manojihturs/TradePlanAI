"""Tests for application.replay_runner."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from application.replay_configuration import ReplayConfiguration
from application.replay_runner import ReplayRunner
from application.replay_session import ReplayStatus
from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.weekly_future_stage import WeeklyFutureStage
from core.events import MarketOpenEvent
from core.exceptions import UnresolvedBusinessRuleError, ValidationError
from data.historical_dataset import HistoricalDataset
from event_recorder.event_recorder import EventRecorder
from events.event_bus import EventBus
from models.market_snapshot import MarketSnapshot
from reference_builder.reference_builder import ReferenceBuilder
from reference_builder.reference_validator import StrikeCandleInput
from replay.replay_engine import ReplayEngine
from strike_selector.strike_selector import StrikeSelector
from weekly_future.weekly_future_calculator import WeeklyFutureCalculator


def _ts(second: int = 0) -> datetime:
    return datetime(2026, 7, 30, 9, 20, second, tzinfo=UTC)


def _candle(second: int) -> MarketSnapshot:
    return MarketSnapshot(timestamp=_ts(second), underlying_price=Decimal(24000))


def _dataset(*seconds: int) -> HistoricalDataset:
    snapshots = tuple(_candle(s) for s in seconds)
    return HistoricalDataset(
        symbol="NIFTY",
        timeframe="1m",
        date_range_start=snapshots[0].timestamp.date(),
        date_range_end=snapshots[-1].timestamp.date(),
        snapshots=snapshots,
    )


def _config() -> ReplayConfiguration:
    return ReplayConfiguration(start_date=date(2026, 7, 1), end_date=date(2026, 7, 31))


class _AlwaysReadyStage:
    def __init__(self, name: str = "stage") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        return StageOutcome(context=context)


class _UnresolvedStage:
    @property
    def name(self) -> str:
        return "unresolved_stage"

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        raise UnresolvedBusinessRuleError("Weekly Future formula is MISSING INFORMATION.")


def _orchestrator(bus: EventBus | None = None, unresolved: bool = False) -> BusinessOrchestrator:
    execution = ExecutionContext(mode=ExecutionMode.REPLAY, clock=lambda: _ts(0), event_bus=bus)
    orchestrator = BusinessOrchestrator(execution)
    orchestrator.register(_UnresolvedStage() if unresolved else _AlwaysReadyStage())
    return orchestrator


class TestSuccessfulReplay:
    def test_runs_every_candle_and_reports_success(self) -> None:
        bus = EventBus()
        recorder = EventRecorder(bus)
        replay_engine = ReplayEngine(bus=bus, clock=lambda: _ts(0), id_factory=uuid.uuid4)
        runner = ReplayRunner(
            replay_engine=replay_engine,
            orchestrator=_orchestrator(bus=bus),
            event_recorder=recorder,
            clock=lambda: _ts(0),
        )

        result = runner.run(_dataset(1, 2, 3), _config())

        assert result.session.status is ReplayStatus.COMPLETED
        assert result.session.dataset_id == "NIFTY@1m"
        assert result.session.statistics is not None
        assert result.session.statistics.candles_processed == 3
        assert result.succeeded_count == 3
        assert result.failed_count == 0
        # MarketOpenEvent + MarketCloseEvent recorded via the shared bus
        assert result.session.statistics.events_recorded == 2
        assert any(isinstance(event, MarketOpenEvent) for event in result.events)


class TestGracefulUnresolved:
    def test_unresolved_business_rule_does_not_abort_replay(self) -> None:
        bus = EventBus()
        replay_engine = ReplayEngine(bus=bus)
        runner = ReplayRunner(
            replay_engine=replay_engine,
            orchestrator=_orchestrator(bus=bus, unresolved=True),
        )

        result = runner.run(_dataset(1, 2), _config())

        assert result.session.status is ReplayStatus.COMPLETED
        assert result.succeeded_count == 0
        assert result.failed_count == 2
        assert all(r.error is None for r in result.business_results)


class TestNoEventRecorder:
    def test_events_empty_when_no_recorder_injected(self) -> None:
        bus = EventBus()
        replay_engine = ReplayEngine(bus=bus)
        runner = ReplayRunner(replay_engine=replay_engine, orchestrator=_orchestrator(bus=bus))

        result = runner.run(_dataset(1), _config())

        assert result.events == ()
        assert result.session.statistics is not None
        assert result.session.statistics.events_recorded == 0


class TestDefaultDependencies:
    def test_default_clock_and_id_factory_produce_valid_result(self) -> None:
        replay_engine = ReplayEngine()
        runner = ReplayRunner(replay_engine=replay_engine, orchestrator=_orchestrator())

        result = runner.run(_dataset(1), _config())

        assert result.session.session_id != uuid.UUID(int=0)
        assert result.session.started_at.tzinfo is not None


def _candle_ohlc(price: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_ts(0),
        underlying_price=Decimal(24000),
        open=Decimal(price),
        high=Decimal(price),
        low=Decimal(price),
        close=Decimal(price),
    )


def _reference_inputs(count: int = 13) -> tuple[StrikeCandleInput, ...]:
    return tuple(
        StrikeCandleInput(
            strike=Decimal(24000 + i * 50),
            ce_candle=_candle_ohlc("150"),
            pe_candle=_candle_ohlc("120"),
        )
        for i in range(count)
    )


class _CapturingStage:
    """Records the reference_data it observed on every candle it ran on."""

    def __init__(self) -> None:
        self.observed_reference_data: list[tuple[object, ...]] = []

    @property
    def name(self) -> str:
        return "capturing_stage"

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        self.observed_reference_data.append(context.reference_data)
        return StageOutcome(context=context)


class TestReferenceBuilderIntegration:
    def test_reference_level_reaches_every_candle_context(self) -> None:
        bus = EventBus()
        replay_engine = ReplayEngine(bus=bus)
        stage = _CapturingStage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY, clock=lambda: _ts(0), event_bus=bus)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(stage)
        runner = ReplayRunner(
            replay_engine=replay_engine,
            orchestrator=orchestrator,
            reference_builder=ReferenceBuilder(),
        )

        result = runner.run(_dataset(1, 2, 3), _config(), reference_inputs=_reference_inputs())

        assert result.session.status is ReplayStatus.COMPLETED
        assert len(stage.observed_reference_data) == 3
        for observed in stage.observed_reference_data:
            assert len(observed) == 13

    def test_multiple_trading_days_all_receive_the_same_ladder(self) -> None:
        bus = EventBus()
        replay_engine = ReplayEngine(bus=bus)
        stage = _CapturingStage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY, clock=lambda: _ts(0), event_bus=bus)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(stage)
        runner = ReplayRunner(
            replay_engine=replay_engine,
            orchestrator=orchestrator,
            reference_builder=ReferenceBuilder(),
        )

        runner.run(_dataset(1, 2, 3, 4, 5), _config(), reference_inputs=_reference_inputs())

        assert len(stage.observed_reference_data) == 5
        first, *rest = stage.observed_reference_data
        assert all(observed == first for observed in rest)

    def test_no_reference_builder_injected_leaves_reference_data_empty(self) -> None:
        bus = EventBus()
        replay_engine = ReplayEngine(bus=bus)
        stage = _CapturingStage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY, clock=lambda: _ts(0), event_bus=bus)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(stage)
        runner = ReplayRunner(replay_engine=replay_engine, orchestrator=orchestrator)

        runner.run(_dataset(1), _config(), reference_inputs=_reference_inputs())

        assert stage.observed_reference_data == [()]

    def test_empty_reference_inputs_leaves_reference_data_empty(self) -> None:
        bus = EventBus()
        replay_engine = ReplayEngine(bus=bus)
        stage = _CapturingStage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY, clock=lambda: _ts(0), event_bus=bus)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(stage)
        runner = ReplayRunner(
            replay_engine=replay_engine,
            orchestrator=orchestrator,
            reference_builder=ReferenceBuilder(),
        )

        runner.run(_dataset(1), _config())

        assert stage.observed_reference_data == [()]

    def test_reference_builder_failure_propagates(self) -> None:
        bus = EventBus()
        replay_engine = ReplayEngine(bus=bus)
        runner = ReplayRunner(
            replay_engine=replay_engine,
            orchestrator=_orchestrator(bus=bus),
            reference_builder=ReferenceBuilder(),
        )

        with pytest.raises(ValidationError, match="Expected exactly 13 strikes"):
            runner.run(_dataset(1), _config(), reference_inputs=_reference_inputs(count=5))

    def test_existing_behaviour_unchanged_without_reference_inputs(self) -> None:
        bus = EventBus()
        recorder = EventRecorder(bus)
        replay_engine = ReplayEngine(bus=bus, clock=lambda: _ts(0), id_factory=uuid.uuid4)
        runner = ReplayRunner(
            replay_engine=replay_engine,
            orchestrator=_orchestrator(bus=bus),
            event_recorder=recorder,
            clock=lambda: _ts(0),
        )

        result = runner.run(_dataset(1, 2, 3), _config())

        assert result.session.status is ReplayStatus.COMPLETED
        assert result.succeeded_count == 3
        assert result.failed_count == 0


def _tc1_candle(price: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_ts(0),
        underlying_price=Decimal(24000),
        open=Decimal(price),
        high=Decimal(price),
        low=Decimal(price),
        close=Decimal(price),
    )


class TestWeeklyFutureStageEndToEndRegression:
    """Real ReferenceBuilder -> real WeeklyFutureCalculator ->
    real StrikeSelector, through one full ReplayRunner run, verified
    against TC-1 (2026-07-29) in WEEKLY_FUTURE_TEST_CASES.md."""

    def test_replay_produces_tc1_weekly_future_and_strikes(self) -> None:
        anchor_strike = Decimal(24200)
        inputs = (
            StrikeCandleInput(
                strike=anchor_strike,
                ce_candle=MarketSnapshot(
                    timestamp=_ts(0),
                    underlying_price=Decimal(24000),
                    open=Decimal("143.45"),
                    high=Decimal("143.45"),
                    low=Decimal(116),
                    close=Decimal(130),
                ),
                pe_candle=MarketSnapshot(
                    timestamp=_ts(0),
                    underlying_price=Decimal(24000),
                    open=Decimal("165.8"),
                    high=Decimal("165.8"),
                    low=Decimal(128),
                    close=Decimal(140),
                ),
            ),
            *(
                StrikeCandleInput(
                    strike=Decimal(strike),
                    ce_candle=_tc1_candle("150"),
                    pe_candle=_tc1_candle("120"),
                )
                for strike in range(24000, 24650, 50)
                if strike != int(anchor_strike)
            ),
        )[:13]

        bus = EventBus()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY, clock=lambda: _ts(0), event_bus=bus)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(
            WeeklyFutureStage(
                anchor_strike=anchor_strike,
                weekly_future_calculator=WeeklyFutureCalculator(),
                strike_selector=StrikeSelector(),
            )
        )
        replay_engine = ReplayEngine(bus=bus)
        runner = ReplayRunner(
            replay_engine=replay_engine,
            orchestrator=orchestrator,
            reference_builder=ReferenceBuilder(),
        )

        result = runner.run(_dataset(1), _config(), reference_inputs=inputs)

        assert result.succeeded_count == 1
        final_context = result.business_results[0].context
        assert final_context.weekly_future is not None
        assert final_context.weekly_future.high == Decimal("24215.45")
        assert final_context.weekly_future.low == Decimal("24150.2")
        assert final_context.selected_strike is not None
        assert final_context.selected_strike.top_strike == Decimal(24200)
        assert final_context.selected_strike.bottom_strike == Decimal(24150)

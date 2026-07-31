"""Tests for business.stages.winner_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from business.business_errors import StageExecutionError
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.winner_stage import WinnerStage
from core.enums import TradeDirection
from core.exceptions import AmbiguousWinnerError, ValidationError
from events.event_bus import EventBus
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from models.strike_chain_snapshot import StrikeChainSnapshot
from winner_engine.winner_engine import WinnerEngine

_ANCHOR_STRIKE = Decimal(24000)
_TIMESTAMP = datetime(2026, 7, 30, 9, 25, 0, tzinfo=UTC)


def _anchor_level() -> ReferenceLevel:
    return ReferenceLevel(
        strike=_ANCHOR_STRIKE,
        ce_high=Decimal(100),
        ce_low=Decimal(90),
        pe_high=Decimal(100),
        pe_low=Decimal(90),
    )


def _reference_data(include_anchor: bool = True) -> tuple[ReferenceLevel, ...]:
    other = ReferenceLevel(
        strike=Decimal(24050),
        ce_high=Decimal(100),
        ce_low=Decimal(90),
        pe_high=Decimal(100),
        pe_low=Decimal(90),
    )
    return (_anchor_level(), other) if include_anchor else (other,)


def _snapshot(low: str, high: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_TIMESTAMP,
        underlying_price=Decimal(high),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _chain_snapshot(
    include_anchor: bool = True,
    ce_range: tuple[str, str] = ("70", "80"),
    pe_range: tuple[str, str] = ("70", "80"),
) -> tuple[StrikeChainSnapshot, ...]:
    anchor_pair = StrikeChainSnapshot(
        strike=_ANCHOR_STRIKE, ce=_snapshot(*ce_range), pe=_snapshot(*pe_range)
    )
    other_pair = StrikeChainSnapshot(
        strike=Decimal(24050), ce=_snapshot("70", "80"), pe=_snapshot("70", "80")
    )
    return (anchor_pair, other_pair) if include_anchor else (other_pair,)


def _context(
    reference_data: tuple[ReferenceLevel, ...] = (),
    chain_snapshot: tuple[StrikeChainSnapshot, ...] = (),
) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(),
        candle_timestamp=_TIMESTAMP,
        reference_data=reference_data,
        chain_snapshot=chain_snapshot,
    )


def _stage(winner_engine: WinnerEngine | None = None) -> WinnerStage:
    engine = winner_engine if winner_engine is not None else WinnerEngine(bus=EventBus())
    return WinnerStage(anchor_strike=_ANCHOR_STRIKE, winner_engine=engine)


class TestIsReady:
    def test_ready_when_reference_data_and_chain_snapshot_present(self) -> None:
        stage = _stage()

        assert stage.is_ready(_context(_reference_data(), _chain_snapshot())) is True

    def test_not_ready_when_reference_data_empty(self) -> None:
        stage = _stage()

        assert stage.is_ready(_context((), _chain_snapshot())) is False

    def test_not_ready_when_chain_snapshot_empty(self) -> None:
        stage = _stage()

        assert stage.is_ready(_context(_reference_data(), ())) is False


class TestRun:
    def test_no_touch_yields_no_winner(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        outcome = stage.run(_context(_reference_data(), _chain_snapshot()), execution)

        assert outcome.context.winner is None

    def test_ce_touch_yields_winner(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        snapshot = _chain_snapshot(ce_range=("95", "105"))

        outcome = stage.run(_context(_reference_data(), snapshot), execution)

        assert outcome.context.winner is not None
        assert outcome.context.winner.winning_side == TradeDirection.CE
        assert outcome.context.winner.winning_strike == _ANCHOR_STRIKE

    def test_pe_touch_yields_winner(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        snapshot = _chain_snapshot(pe_range=("95", "105"))

        outcome = stage.run(_context(_reference_data(), snapshot), execution)

        assert outcome.context.winner is not None
        assert outcome.context.winner.winning_side == TradeDirection.PE

    def test_both_touch_raises_ambiguous_winner(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        snapshot = _chain_snapshot(ce_range=("95", "105"), pe_range=("95", "105"))

        with pytest.raises(AmbiguousWinnerError):
            stage.run(_context(_reference_data(), snapshot), execution)

    def test_missing_anchor_in_reference_data_raises(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        with pytest.raises(ValidationError, match="No ReferenceLevel found for anchor strike"):
            stage.run(_context(_reference_data(include_anchor=False), _chain_snapshot()), execution)

    def test_missing_anchor_in_chain_snapshot_raises(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        with pytest.raises(ValidationError, match="No StrikeChainSnapshot found for anchor"):
            stage.run(_context(_reference_data(), _chain_snapshot(include_anchor=False)), execution)

    def test_does_not_double_publish_winner_event(self) -> None:
        # WinnerEngine.evaluate() already publishes internally - the
        # stage must not also return it via StageOutcome.events, or
        # EntryEngine would fire twice per Winner.
        bus = EventBus()
        received = []
        from core.events import WinnerDetectedEvent

        bus.subscribe(WinnerDetectedEvent, received.append)
        stage = _stage(WinnerEngine(bus=bus))
        execution = ExecutionContext(mode=ExecutionMode.REPLAY, event_bus=bus)
        snapshot = _chain_snapshot(ce_range=("95", "105"))

        outcome = stage.run(_context(_reference_data(), snapshot), execution)
        for event in outcome.events:
            bus.publish(event)

        assert len(received) == 1


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())

        result = orchestrator.run(_context(_reference_data(), _chain_snapshot()))

        assert result.success is True
        assert result.completed_stages == ("winner",)

    def test_stage_fault_is_absorbed_into_business_result_not_raised(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())

        result = orchestrator.run(
            _context(_reference_data(include_anchor=False), _chain_snapshot())
        )

        assert result.success is False
        assert isinstance(result.error, StageExecutionError)

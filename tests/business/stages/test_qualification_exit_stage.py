"""Tests for business.stages.qualification_exit_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from business.business_pipeline import BusinessPipeline
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.qualification_exit_stage import QualificationExitStage
from core.enums import AnchorRole, ExitReason, TradeDirection
from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.qualification_signal import QualificationSignal
from models.qualified_position import QualifiedPosition
from models.strike import StrikeSelection
from models.strike_chain_snapshot import StrikeChainSnapshot
from qualification_engine.qualification_exit_engine import QualificationExitEngine
from qualification_engine.qualification_position_manager import QualificationPositionManager
from qualification_engine.qualification_trailing_stop import (
    NeverTriggersQualificationTrailingStop,
)

_TOP = Decimal(24250)
_BOTTOM = Decimal(24200)
_TIMESTAMP = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)


def _snapshot(low: str, high: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_TIMESTAMP,
        underlying_price=Decimal(24140),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _no_touch() -> MarketSnapshot:
    return _snapshot("9998", "9999")


def _touching(level_value: str) -> MarketSnapshot:
    value = Decimal(level_value)
    return _snapshot(str(value - 1), str(value + 1))


def _selected_strike() -> StrikeSelection:
    return StrikeSelection(
        session_id=uuid.uuid4(), top_strike=_TOP, bottom_strike=_BOTTOM, selected_at=_TIMESTAMP
    )


def _chain_snapshot(
    top_ce: MarketSnapshot | None = None,
    top_pe: MarketSnapshot | None = None,
    include_top: bool = True,
) -> tuple[StrikeChainSnapshot, ...]:
    top_ce = top_ce if top_ce is not None else _no_touch()
    top_pe = top_pe if top_pe is not None else _no_touch()
    pairs = []
    if include_top:
        pairs.append(StrikeChainSnapshot(strike=_TOP, ce=top_ce, pe=top_pe))
    return tuple(pairs)


def _context(
    chain_snapshot: tuple[StrikeChainSnapshot, ...] = (),
    selected_strike: StrikeSelection | None = None,
    qualified_position_top: QualifiedPosition | None = None,
) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(),
        candle_timestamp=_TIMESTAMP,
        chain_snapshot=chain_snapshot,
        selected_strike=selected_strike,
        qualified_position_top=qualified_position_top,
    )


def _build_stage_with_open_position(
    anchor_role: AnchorRole = AnchorRole.TOP,
) -> tuple[QualificationExitStage, QualificationPositionManager, QualifiedPosition]:
    position_manager = QualificationPositionManager()
    exit_engine = QualificationExitEngine(
        position_manager=position_manager, trailing_stop=NeverTriggersQualificationTrailingStop()
    )
    position = position_manager.open(
        QualificationSignal(
            signal_id=uuid.uuid4(),
            anchor_role=anchor_role,
            side=TradeDirection.CE,
            entry_strike=_TOP,
            entry_level=Decimal("120.1"),
            target_level=Decimal("145.2"),
            stop_loss_level=Decimal("98.3"),
            competitor_exit_level=Decimal("121.5"),
            qualified_at=_TIMESTAMP,
        )
    )
    assert position is not None
    stage = QualificationExitStage(
        anchor_role=anchor_role, exit_engine=exit_engine, position_manager=position_manager
    )
    return stage, position_manager, position


class TestIsReady:
    def test_always_ready(self) -> None:
        position_manager = QualificationPositionManager()
        exit_engine = QualificationExitEngine(
            position_manager=position_manager,
            trailing_stop=NeverTriggersQualificationTrailingStop(),
        )
        stage = QualificationExitStage(
            anchor_role=AnchorRole.TOP, exit_engine=exit_engine, position_manager=position_manager
        )

        assert stage.is_ready(_context()) is True


class TestRunNoActivePosition:
    def test_no_op_when_no_trade_active(self) -> None:
        position_manager = QualificationPositionManager()
        exit_engine = QualificationExitEngine(
            position_manager=position_manager,
            trailing_stop=NeverTriggersQualificationTrailingStop(),
        )
        stage = QualificationExitStage(
            anchor_role=AnchorRole.TOP, exit_engine=exit_engine, position_manager=position_manager
        )
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context()

        outcome = stage.run(context, execution)

        assert outcome.context is context
        assert outcome.context.qualification_exited_position_top is None


class TestRunWithActivePosition:
    def test_finds_anchor_when_not_first_in_chain_snapshot(self) -> None:
        stage, _position_manager, _pos = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        chain_snapshot = (
            StrikeChainSnapshot(strike=_BOTTOM, ce=_no_touch(), pe=_no_touch()),
            StrikeChainSnapshot(strike=_TOP, ce=_touching("145.2"), pe=_no_touch()),
        )
        context = _context(chain_snapshot, _selected_strike())

        outcome = stage.run(context, execution)

        assert outcome.context.qualification_exited_position_top is not None
        assert (
            outcome.context.qualification_exited_position_top.exit_reason == ExitReason.TARGET_HIT
        )

    def test_neither_touches_position_stays_open(self) -> None:
        stage, position_manager, _pos = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(_chain_snapshot(), _selected_strike())

        outcome = stage.run(context, execution)

        assert outcome.context.qualification_exited_position_top is None
        assert position_manager.is_trade_active() is True

    def test_target_touch_closes_via_target_hit(self) -> None:
        stage, position_manager, _pos = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(_chain_snapshot(top_ce=_touching("145.2")), _selected_strike())

        outcome = stage.run(context, execution)

        assert outcome.context.qualification_exited_position_top is not None
        assert (
            outcome.context.qualification_exited_position_top.exit_reason == ExitReason.TARGET_HIT
        )
        assert position_manager.is_trade_active() is False

    def test_competitor_touch_closes_via_competitor_hit(self) -> None:
        stage, _, _pos = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(_chain_snapshot(top_pe=_touching("121.5")), _selected_strike())

        outcome = stage.run(context, execution)

        assert outcome.context.qualification_exited_position_top is not None
        assert (
            outcome.context.qualification_exited_position_top.exit_reason
            == ExitReason.COMPETITOR_HIT
        )

    def test_missing_selected_strike_raises(self) -> None:
        stage, _, _pos = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(_chain_snapshot(), None)

        with pytest.raises(ValidationError, match="requires PipelineContext.selected_strike"):
            stage.run(context, execution)

    def test_missing_anchor_in_chain_snapshot_raises(self) -> None:
        stage, _, _pos = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(_chain_snapshot(include_top=False), _selected_strike())

        with pytest.raises(ValidationError, match="No StrikeChainSnapshot found for anchor strike"):
            stage.run(context, execution)

    def test_skips_exit_check_for_position_opened_this_same_candle(self) -> None:
        # Touching data for both Target and Competitor is present, but
        # since context.qualified_position_top matches the active
        # position, this candle is the one that just opened it - exit
        # monitoring must not fire yet (see qualification_exit_stage's
        # own docstring for why).
        stage, position_manager, position = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(
            _chain_snapshot(top_ce=_touching("145.2"), top_pe=_touching("121.5")),
            _selected_strike(),
            qualified_position_top=position,
        )

        outcome = stage.run(context, execution)

        assert outcome.context is context
        assert outcome.context.qualification_exited_position_top is None
        assert position_manager.is_trade_active() is True

    def test_bottom_anchor_writes_to_bottom_field(self) -> None:
        stage, _position_manager, _pos = _build_stage_with_open_position(AnchorRole.BOTTOM)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        chain_snapshot = (
            StrikeChainSnapshot(strike=_BOTTOM, ce=_touching("145.2"), pe=_no_touch()),
        )
        context = _context(chain_snapshot, _selected_strike())

        outcome = stage.run(context, execution)

        assert outcome.context.qualification_exited_position_bottom is not None
        assert outcome.context.qualification_exited_position_top is None


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        stage, _, _pos = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(stage)
        context = _context(_chain_snapshot(top_ce=_touching("145.2")), _selected_strike())

        result = orchestrator.run(context)

        assert result.success is True
        assert result.completed_stages == ("qualification_exit_top",)
        assert result.context.qualification_exited_position_top is not None

    def test_pipeline_stages_property_includes_the_stage(self) -> None:
        stage, _, _pos = _build_stage_with_open_position()
        pipeline = BusinessPipeline((stage,))

        assert pipeline.stages == (stage,)

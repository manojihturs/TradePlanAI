"""Tests for business.stages.exit_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from backtest.null_engines import NeverTriggersStopLoss, NeverTriggersTrailingStop
from business.business_pipeline import BusinessPipeline
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.exit_stage import ExitStage
from core.enums import ExitReason, TradeDirection
from core.exceptions import ValidationError
from exit_engine.exit_engine import ExitEngine
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from models.strike_chain_snapshot import StrikeChainSnapshot
from position_manager.position_manager import PositionManager
from trade_manager.trade_manager import TradeManager

_ENTRY_STRIKE = Decimal(24000)
_TARGET_STRIKE = Decimal(24050)
_COMPETITOR_STRIKE = Decimal(23950)
_TIMESTAMP = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)


def _level(strike: Decimal) -> ReferenceLevel:
    return ReferenceLevel(
        strike=strike,
        ce_high=Decimal(110),
        ce_low=Decimal(90),
        pe_high=Decimal(110),
        pe_low=Decimal(90),
    )


_LADDER = (_level(_ENTRY_STRIKE), _level(_TARGET_STRIKE), _level(_COMPETITOR_STRIKE))


def _snapshot(low: str, high: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_TIMESTAMP,
        underlying_price=Decimal(high),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _no_touch() -> MarketSnapshot:
    return _snapshot("200", "210")


def _touching(level_value: str) -> MarketSnapshot:
    value = Decimal(level_value)
    return _snapshot(str(value - 5), str(value + 5))


def _chain_snapshot(
    target_ce: MarketSnapshot | None = None, competitor_pe: MarketSnapshot | None = None
) -> tuple[StrikeChainSnapshot, ...]:
    target_ce = target_ce if target_ce is not None else _no_touch()
    competitor_pe = competitor_pe if competitor_pe is not None else _no_touch()
    return (
        StrikeChainSnapshot(strike=_TARGET_STRIKE, ce=target_ce, pe=_no_touch()),
        StrikeChainSnapshot(strike=_COMPETITOR_STRIKE, ce=_no_touch(), pe=competitor_pe),
    )


def _context(chain_snapshot: tuple[StrikeChainSnapshot, ...] = ()) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(), candle_timestamp=_TIMESTAMP, chain_snapshot=chain_snapshot
    )


def _build_stage_with_open_position() -> tuple[ExitStage, PositionManager]:
    trade_manager = TradeManager()
    position_manager = PositionManager(trade_manager)
    exit_engine = ExitEngine(
        position_manager=position_manager,
        reference_levels=_LADDER,
        stop_loss_engine=NeverTriggersStopLoss(),
        trailing_stop_engine=NeverTriggersTrailingStop(),
    )
    position_manager.open_position(
        trade_id=uuid.uuid4(),
        entry_strike=_ENTRY_STRIKE,
        entry_side=TradeDirection.CE,
        opened_at=_TIMESTAMP,
        reference_levels=_LADDER,
    )
    stage = ExitStage(exit_engine=exit_engine, position_manager=position_manager)
    return stage, position_manager


class TestIsReady:
    def test_always_ready(self) -> None:
        trade_manager = TradeManager()
        position_manager = PositionManager(trade_manager)
        exit_engine = ExitEngine(
            position_manager=position_manager,
            reference_levels=_LADDER,
            stop_loss_engine=NeverTriggersStopLoss(),
            trailing_stop_engine=NeverTriggersTrailingStop(),
        )
        stage = ExitStage(exit_engine=exit_engine, position_manager=position_manager)

        assert stage.is_ready(_context()) is True


class TestRunNoActivePosition:
    def test_no_op_when_no_trade_active(self) -> None:
        trade_manager = TradeManager()
        position_manager = PositionManager(trade_manager)
        exit_engine = ExitEngine(
            position_manager=position_manager,
            reference_levels=_LADDER,
            stop_loss_engine=NeverTriggersStopLoss(),
            trailing_stop_engine=NeverTriggersTrailingStop(),
        )
        stage = ExitStage(exit_engine=exit_engine, position_manager=position_manager)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context()

        outcome = stage.run(context, execution)

        assert outcome.context is context
        assert outcome.context.exited_position is None


class TestRunWithActivePosition:
    def test_neither_touches_position_stays_open(self) -> None:
        stage, position_manager = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        outcome = stage.run(_context(_chain_snapshot()), execution)

        assert outcome.context.exited_position is None
        assert position_manager.is_active() is True

    def test_target_touch_closes_via_target_hit(self) -> None:
        stage, position_manager = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        chain_snapshot = _chain_snapshot(target_ce=_touching("110"))

        outcome = stage.run(_context(chain_snapshot), execution)

        assert outcome.context.exited_position is not None
        assert outcome.context.exited_position.exit_reason == ExitReason.TARGET_HIT
        assert position_manager.is_active() is False

    def test_competitor_touch_closes_via_competitor_hit(self) -> None:
        stage, _ = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        chain_snapshot = _chain_snapshot(competitor_pe=_touching("110"))

        outcome = stage.run(_context(chain_snapshot), execution)

        assert outcome.context.exited_position is not None
        assert outcome.context.exited_position.exit_reason == ExitReason.COMPETITOR_HIT

    def test_missing_target_strike_raises(self) -> None:
        stage, _ = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        chain_snapshot = (
            StrikeChainSnapshot(strike=_COMPETITOR_STRIKE, ce=_no_touch(), pe=_no_touch()),
        )

        with pytest.raises(ValidationError, match="No StrikeChainSnapshot found for strike"):
            stage.run(_context(chain_snapshot), execution)

    def test_missing_competitor_strike_raises(self) -> None:
        stage, _ = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        chain_snapshot = (
            StrikeChainSnapshot(strike=_TARGET_STRIKE, ce=_no_touch(), pe=_no_touch()),
        )

        with pytest.raises(ValidationError, match="No StrikeChainSnapshot found for strike"):
            stage.run(_context(chain_snapshot), execution)


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        stage, _ = _build_stage_with_open_position()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(stage)

        result = orchestrator.run(_context(_chain_snapshot(target_ce=_touching("110"))))

        assert result.success is True
        assert result.completed_stages == ("exit",)
        assert result.context.exited_position is not None

    def test_pipeline_stages_property_includes_the_stage(self) -> None:
        stage, _ = _build_stage_with_open_position()
        pipeline = BusinessPipeline((stage,))

        assert pipeline.stages == (stage,)

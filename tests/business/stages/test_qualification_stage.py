"""Tests for business.stages.qualification_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from business.business_errors import StageExecutionError
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.qualification_stage import QualificationStage
from core.enums import AnchorRole, TradeDirection, TrendDirection
from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from models.strike import StrikeSelection
from models.strike_chain_snapshot import StrikeChainSnapshot
from qualification_engine.qualification_engine import QualificationEngine
from qualification_engine.qualification_position_manager import QualificationPositionManager

_TOP = Decimal(24250)
_BOTTOM = Decimal(24200)
_TIMESTAMP = datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)

# Real, confirmed 30-July-2026 values (subset needed for Top/Bottom).
_LEVELS = {
    Decimal(24200): (Decimal("150.0"), Decimal("110.3"), Decimal("131.6"), Decimal("98.3")),
    Decimal(24250): (Decimal("121.5"), Decimal("87.0"), Decimal("159.0"), Decimal("120.1")),
    Decimal(24300): (Decimal("103.2"), Decimal("67.05"), Decimal("189.0"), Decimal("145.2")),
}


def _reference_data() -> tuple[ReferenceLevel, ...]:
    return tuple(
        ReferenceLevel(strike=strike, ce_high=ch, ce_low=cl, pe_high=ph, pe_low=pl)
        for strike, (ch, cl, ph, pl) in _LEVELS.items()
    )


def _candle(value: Decimal) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_TIMESTAMP,
        underlying_price=Decimal(24140),
        open=value - Decimal("0.05"),
        high=value + Decimal("0.05"),
        low=value - Decimal("0.05"),
        close=value,
    )


def _no_touch() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_TIMESTAMP,
        underlying_price=Decimal(24140),
        open=Decimal(9999),
        high=Decimal("9999.1"),
        low=Decimal("9998.9"),
        close=Decimal(9999),
    )


def _chain_snapshot(
    top_ce: MarketSnapshot, top_pe: MarketSnapshot, include_top: bool = True
) -> tuple[StrikeChainSnapshot, ...]:
    pairs = []
    if include_top:
        pairs.append(StrikeChainSnapshot(strike=_TOP, ce=top_ce, pe=top_pe))
    pairs.append(StrikeChainSnapshot(strike=_BOTTOM, ce=_no_touch(), pe=_no_touch()))
    return tuple(pairs)


def _selected_strike() -> StrikeSelection:
    return StrikeSelection(
        session_id=uuid.uuid4(), top_strike=_TOP, bottom_strike=_BOTTOM, selected_at=_TIMESTAMP
    )


def _context(
    reference_data: tuple[ReferenceLevel, ...] = (),
    chain_snapshot: tuple[StrikeChainSnapshot, ...] = (),
    selected_strike: StrikeSelection | None = None,
    trend: TrendDirection | None = None,
) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(),
        candle_timestamp=_TIMESTAMP,
        reference_data=reference_data,
        chain_snapshot=chain_snapshot,
        selected_strike=selected_strike,
        trend=trend,
    )


def _stage(anchor_role: AnchorRole = AnchorRole.TOP) -> QualificationStage:
    return QualificationStage(
        anchor_role=anchor_role,
        qualification_engine=QualificationEngine(),
        position_manager=QualificationPositionManager(),
    )


class TestIsReady:
    def test_ready_when_everything_present(self) -> None:
        stage = _stage()
        context = _context(
            _reference_data(),
            _chain_snapshot(_no_touch(), _no_touch()),
            _selected_strike(),
            TrendDirection.BULLISH,
        )

        assert stage.is_ready(context) is True

    def test_not_ready_when_reference_data_empty(self) -> None:
        stage = _stage()
        context = _context(
            (),
            _chain_snapshot(_no_touch(), _no_touch()),
            _selected_strike(),
            TrendDirection.BULLISH,
        )

        assert stage.is_ready(context) is False

    def test_not_ready_when_chain_snapshot_empty(self) -> None:
        stage = _stage()
        context = _context(_reference_data(), (), _selected_strike(), TrendDirection.BULLISH)

        assert stage.is_ready(context) is False

    def test_not_ready_when_selected_strike_missing(self) -> None:
        stage = _stage()
        context = _context(
            _reference_data(),
            _chain_snapshot(_no_touch(), _no_touch()),
            None,
            TrendDirection.BULLISH,
        )

        assert stage.is_ready(context) is False

    def test_not_ready_when_trend_missing(self) -> None:
        stage = _stage()
        context = _context(
            _reference_data(), _chain_snapshot(_no_touch(), _no_touch()), _selected_strike(), None
        )

        assert stage.is_ready(context) is False


class TestRun:
    def test_no_qualification_yields_no_position(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(
            _reference_data(),
            _chain_snapshot(_no_touch(), _no_touch()),
            _selected_strike(),
            TrendDirection.BULLISH,
        )

        outcome = stage.run(context, execution)

        assert outcome.context.qualified_position_top is None

    def test_top_ce_qualification_opens_position(self) -> None:
        stage = _stage(AnchorRole.TOP)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(
            _reference_data(),
            _chain_snapshot(_candle(Decimal("120.1")), _candle(Decimal("121.5"))),
            _selected_strike(),
            TrendDirection.BULLISH,
        )

        outcome = stage.run(context, execution)

        assert outcome.context.qualified_position_top is not None
        assert outcome.context.qualified_position_top.side is TradeDirection.CE
        assert outcome.context.qualified_position_top.anchor_role is AnchorRole.TOP
        assert outcome.context.qualified_position_top.target_level == Decimal("145.2")

    def test_bottom_qualification_writes_to_bottom_field(self) -> None:
        stage = _stage(AnchorRole.BOTTOM)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        below_bottom = Decimal(24150)
        reference_data = _reference_data() + (
            ReferenceLevel(
                strike=below_bottom,
                ce_high=Decimal("170.0"),
                ce_low=Decimal("130.0"),
                pe_high=Decimal("113.6"),
                pe_low=Decimal("80.3"),
            ),
        )
        context = _context(
            reference_data,
            (
                StrikeChainSnapshot(strike=_TOP, ce=_no_touch(), pe=_no_touch()),
                StrikeChainSnapshot(
                    strike=_BOTTOM, ce=_candle(Decimal("131.6")), pe=_candle(Decimal("110.3"))
                ),
            ),
            _selected_strike(),
            TrendDirection.BEARISH,
        )

        outcome = stage.run(context, execution)

        assert outcome.context.qualified_position_bottom is not None
        assert outcome.context.qualified_position_bottom.anchor_role is AnchorRole.BOTTOM
        assert outcome.context.qualified_position_top is None

    def test_missing_top_in_chain_snapshot_raises(self) -> None:
        stage = _stage(AnchorRole.TOP)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(
            _reference_data(),
            _chain_snapshot(_no_touch(), _no_touch(), include_top=False),
            _selected_strike(),
            TrendDirection.BULLISH,
        )

        with pytest.raises(ValidationError, match="No StrikeChainSnapshot found for anchor strike"):
            stage.run(context, execution)

    def test_second_qualification_while_active_does_not_open_new_position(self) -> None:
        manager = QualificationPositionManager()
        stage = QualificationStage(AnchorRole.TOP, QualificationEngine(), manager)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(
            _reference_data(),
            _chain_snapshot(_candle(Decimal("120.1")), _candle(Decimal("121.5"))),
            _selected_strike(),
            TrendDirection.BULLISH,
        )
        first = stage.run(context, execution)
        assert first.context.qualified_position_top is not None

        second = stage.run(context, execution)

        assert second.context.qualified_position_top is None


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())
        context = _context(
            _reference_data(),
            _chain_snapshot(_no_touch(), _no_touch()),
            _selected_strike(),
            TrendDirection.BULLISH,
        )

        result = orchestrator.run(context)

        assert result.success is True
        assert result.completed_stages == ("qualification_top",)

    def test_stage_fault_is_absorbed_into_business_result_not_raised(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())
        context = _context(
            _reference_data(),
            _chain_snapshot(_no_touch(), _no_touch(), include_top=False),
            _selected_strike(),
            TrendDirection.BULLISH,
        )

        result = orchestrator.run(context)

        assert result.success is False
        assert isinstance(result.error, StageExecutionError)

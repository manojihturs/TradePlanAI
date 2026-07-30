"""Tests for business.stages.orb_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from business.business_errors import StageExecutionError
from business.business_pipeline import BusinessPipeline
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.orb_stage import ORBStage
from core.enums import OptionType, ORBStatus
from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from orb_engine.orb_engine import ORBEngine

_ANCHOR_STRIKE = Decimal(24200)
_TIMESTAMP = datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC)


def _anchor_level() -> ReferenceLevel:
    return ReferenceLevel(
        strike=_ANCHOR_STRIKE,
        ce_high=Decimal("143.45"),
        ce_low=Decimal(116),
        pe_high=Decimal("165.8"),
        pe_low=Decimal(128),
    )


def _other_level(strike: int) -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(strike),
        ce_high=Decimal(150),
        ce_low=Decimal(100),
        pe_high=Decimal(150),
        pe_low=Decimal(100),
    )


def _reference_data(include_anchor: bool = True) -> tuple[ReferenceLevel, ...]:
    others = tuple(
        _other_level(24000 + i * 50) for i in range(12) if 24000 + i * 50 != _ANCHOR_STRIKE
    )
    if include_anchor:
        return (_anchor_level(), *others[:12])
    return others[:13]


def _candle(minute_offset: int, high: str, low: str) -> MarketSnapshot:
    timestamp = _TIMESTAMP + timedelta(minutes=minute_offset)
    return MarketSnapshot(
        timestamp=timestamp,
        underlying_price=Decimal(high),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _context(
    reference_data: tuple[ReferenceLevel, ...] = (),
    candles: tuple[MarketSnapshot, ...] = (),
) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(),
        candle_timestamp=_TIMESTAMP,
        reference_data=reference_data,
        candles=candles,
    )


def _stage() -> ORBStage:
    return ORBStage(anchor_strike=_ANCHOR_STRIKE, side=OptionType.CALL, orb_engine=ORBEngine())


class TestIsReady:
    def test_ready_when_reference_data_present(self) -> None:
        stage = _stage()

        assert stage.is_ready(_context(_reference_data())) is True

    def test_not_ready_when_reference_data_empty(self) -> None:
        stage = _stage()

        assert stage.is_ready(_context(())) is False

    def test_ready_even_when_candles_empty(self) -> None:
        stage = _stage()

        assert stage.is_ready(_context(_reference_data(), candles=())) is True


class TestRun:
    def test_calculates_orb_result(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        candles = (_candle(5, "130", "120"),)

        outcome = stage.run(_context(_reference_data(), candles), execution)

        assert outcome.context.orb_result is not None
        assert outcome.context.orb_result.opening_high == Decimal("143.45")
        assert outcome.context.orb_result.opening_low == Decimal(116)
        assert outcome.context.orb_result.status == ORBStatus.NONE

    def test_no_candles_yields_none_status(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        outcome = stage.run(_context(_reference_data(), ()), execution)

        assert outcome.context.orb_result is not None
        assert outcome.context.orb_result.status == ORBStatus.NONE

    def test_breakout_candle_is_classified(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        candles = (_candle(5, "150", "140"),)  # crosses opening_high=143.45

        outcome = stage.run(_context(_reference_data(), candles), execution)

        assert outcome.context.orb_result is not None
        assert outcome.context.orb_result.status == ORBStatus.BREAKOUT

    def test_missing_anchor_strike_raises(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        with pytest.raises(ValidationError, match="No ReferenceLevel found for anchor strike"):
            stage.run(_context(_reference_data(include_anchor=False)), execution)

    def test_stage_performs_no_calculation_itself(self) -> None:
        # A stage with an engine that returns a fixed sentinel result
        # proves the stage only delegates - it never recomputes.
        class _SentinelEngine:
            def calculate(self, session_id, level, side, candles, calculated_at):  # type: ignore[no-untyped-def]
                from models.orb_result import ORBResult

                return ORBResult(
                    orb_result_id=uuid.uuid4(),
                    session_id=session_id,
                    strike=level.strike,
                    side=side,
                    opening_high=Decimal(999),
                    opening_low=Decimal(1),
                    range=Decimal(998),
                    status=ORBStatus.BREAKOUT,
                    calculated_at=calculated_at,
                )

        stage = ORBStage(
            anchor_strike=_ANCHOR_STRIKE,
            side=OptionType.CALL,
            orb_engine=_SentinelEngine(),  # type: ignore[arg-type]
        )
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        outcome = stage.run(_context(_reference_data()), execution)

        assert outcome.context.orb_result is not None
        assert outcome.context.orb_result.opening_high == Decimal(999)


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())

        result = orchestrator.run(_context(_reference_data()))

        assert result.success is True
        assert result.context.orb_result is not None
        assert result.completed_stages == ("orb",)

    def test_stage_fault_is_absorbed_into_business_result_not_raised(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())

        result = orchestrator.run(_context(_reference_data(include_anchor=False)))

        assert result.success is False
        assert isinstance(result.error, StageExecutionError)
        assert "ValidationError" in str(result.error)

    def test_pipeline_stages_property_includes_the_stage(self) -> None:
        stage = _stage()
        pipeline = BusinessPipeline((stage,))

        assert pipeline.stages == (stage,)

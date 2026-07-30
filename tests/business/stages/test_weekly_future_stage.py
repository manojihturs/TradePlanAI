"""Tests for business.stages.weekly_future_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from business.business_errors import StageExecutionError
from business.business_pipeline import BusinessPipeline
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.weekly_future_stage import WeeklyFutureStage
from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel
from strike_selector.strike_selector import StrikeSelector
from weekly_future.weekly_future_calculator import WeeklyFutureCalculator

# TC-1, 2026-07-29, verified in WEEKLY_FUTURE_CALCULATION_EXAMPLES.md
_ANCHOR_STRIKE = Decimal(24200)
_EXPECTED_HIGH = Decimal("24215.45")
_EXPECTED_LOW = Decimal("24150.2")
_EXPECTED_TOP = Decimal(24200)
_EXPECTED_BOTTOM = Decimal(24150)


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


def _context(reference_data: tuple[ReferenceLevel, ...] = ()) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(),
        candle_timestamp=datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC),
        reference_data=reference_data,
    )


def _stage() -> WeeklyFutureStage:
    return WeeklyFutureStage(
        anchor_strike=_ANCHOR_STRIKE,
        weekly_future_calculator=WeeklyFutureCalculator(),
        strike_selector=StrikeSelector(),
    )


class TestIsReady:
    def test_ready_when_reference_data_present(self) -> None:
        stage = _stage()

        assert stage.is_ready(_context(_reference_data())) is True

    def test_not_ready_when_reference_data_empty(self) -> None:
        stage = _stage()

        assert stage.is_ready(_context(())) is False


class TestRun:
    def test_calculates_weekly_future_and_selects_strikes(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        outcome = stage.run(_context(_reference_data()), execution)

        assert outcome.context.weekly_future is not None
        assert outcome.context.weekly_future.high == _EXPECTED_HIGH
        assert outcome.context.weekly_future.low == _EXPECTED_LOW
        assert outcome.context.selected_strike is not None
        assert outcome.context.selected_strike.top_strike == _EXPECTED_TOP
        assert outcome.context.selected_strike.bottom_strike == _EXPECTED_BOTTOM

    def test_missing_anchor_strike_raises(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        with pytest.raises(ValidationError, match="No ReferenceLevel found for anchor strike"):
            stage.run(_context(_reference_data(include_anchor=False)), execution)

    def test_stage_performs_no_calculation_itself(self) -> None:
        # A stage with a calculator/selector that return fixed sentinel
        # values proves the stage only delegates - it never recomputes.
        class _SentinelCalculator:
            def calculate(self, session_id, level, calculated_at):  # type: ignore[no-untyped-def]
                from models.weekly_future import WeeklyFuture

                return WeeklyFuture(
                    weekly_future_id=uuid.uuid4(),
                    session_id=session_id,
                    high=Decimal(100),
                    low=Decimal(50),
                    calculated_at=calculated_at,
                )

        stage = WeeklyFutureStage(
            anchor_strike=_ANCHOR_STRIKE,
            weekly_future_calculator=_SentinelCalculator(),  # type: ignore[arg-type]
            strike_selector=StrikeSelector(),
        )
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)

        outcome = stage.run(_context(_reference_data()), execution)

        assert outcome.context.weekly_future is not None
        assert outcome.context.weekly_future.high == Decimal(100)


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())

        result = orchestrator.run(_context(_reference_data()))

        assert result.success is True
        assert result.context.weekly_future is not None
        assert result.context.weekly_future.high == _EXPECTED_HIGH
        assert result.completed_stages == ("weekly_future",)

    def test_stage_fault_is_absorbed_into_business_result_not_raised(self) -> None:
        # Per business_pipeline.py's own documented design, a stage
        # fault is caught and recorded on BusinessResult.error - it
        # is never re-raised out of BusinessPipeline/BusinessOrchestrator.
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

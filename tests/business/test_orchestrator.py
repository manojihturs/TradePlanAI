"""Tests for business.orchestrator."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError


def _ts() -> datetime:
    return datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


def _context() -> PipelineContext:
    return PipelineContext(session_id=uuid.uuid4(), candle_timestamp=_ts())


class _Stage:
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        return StageOutcome(context=context.with_diagnostic(f"{self._name} ran"))


class TestConstruction:
    def test_none_execution_raises(self) -> None:
        with pytest.raises(ValidationError, match="execution must not be None"):
            BusinessOrchestrator(None)  # type: ignore[arg-type]


class TestRegister:
    def test_none_stage_raises(self) -> None:
        orchestrator = BusinessOrchestrator(ExecutionContext(mode=ExecutionMode.LIVE))

        with pytest.raises(ValidationError, match="register\\(stage\\) must not be None"):
            orchestrator.register(None)  # type: ignore[arg-type]

    def test_registration_order_is_execution_order(self) -> None:
        orchestrator = BusinessOrchestrator(ExecutionContext(mode=ExecutionMode.LIVE))
        orchestrator.register(_Stage("weekly_future"))
        orchestrator.register(_Stage("strike_selection"))

        pipeline = orchestrator.build_pipeline()

        assert [stage.name for stage in pipeline.stages] == ["weekly_future", "strike_selection"]


class TestRun:
    def test_run_executes_registered_stages(self) -> None:
        orchestrator = BusinessOrchestrator(ExecutionContext(mode=ExecutionMode.LIVE))
        orchestrator.register(_Stage("weekly_future"))

        result = orchestrator.run(_context())

        assert result.success is True
        assert result.completed_stages == ("weekly_future",)

    def test_run_can_be_called_repeatedly(self) -> None:
        orchestrator = BusinessOrchestrator(ExecutionContext(mode=ExecutionMode.LIVE))
        orchestrator.register(_Stage("weekly_future"))

        first = orchestrator.run(_context())
        second = orchestrator.run(_context())

        assert first.success is True
        assert second.success is True

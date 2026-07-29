"""Tests for business.business_result."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from business.business_errors import StageExecutionError
from business.business_result import BusinessResult
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError


def _context() -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(),
        candle_timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
    )


class TestConstruction:
    def test_defaults(self) -> None:
        result = BusinessResult(success=True, context=_context())

        assert result.completed_stages == ()
        assert result.skipped_stages == ()
        assert result.warnings == ()
        assert result.execution_time == timedelta()
        assert result.diagnostics == ()
        assert result.error is None

    def test_failure_with_error(self) -> None:
        error = StageExecutionError("weekly_future raised UnresolvedBusinessRuleError")

        result = BusinessResult(success=False, context=_context(), error=error)

        assert result.success is False
        assert result.error is error


class TestValidation:
    def test_none_context_raises(self) -> None:
        with pytest.raises(ValidationError, match="context must not be None"):
            BusinessResult(success=True, context=None)  # type: ignore[arg-type]

    def test_none_execution_time_raises(self) -> None:
        with pytest.raises(ValidationError, match="execution_time must not be None"):
            BusinessResult(success=True, context=_context(), execution_time=None)  # type: ignore[arg-type]

    def test_negative_execution_time_raises(self) -> None:
        with pytest.raises(ValidationError, match="must not be negative"):
            BusinessResult(success=True, context=_context(), execution_time=timedelta(seconds=-1))

    def test_success_with_error_raises(self) -> None:
        with pytest.raises(ValidationError, match="error must be None when success is True"):
            BusinessResult(success=True, context=_context(), error=StageExecutionError("boom"))

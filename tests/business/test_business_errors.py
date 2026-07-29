"""Tests for business.business_errors."""

from __future__ import annotations

import pytest

from business.business_errors import (
    BusinessOrchestrationError,
    StageExecutionError,
    StagePrerequisiteError,
)
from core.exceptions import StrategyEngineError


@pytest.mark.parametrize("exception_type", [StagePrerequisiteError, StageExecutionError])
def test_every_subclass_is_a_business_orchestration_error(
    exception_type: type[Exception],
) -> None:
    assert issubclass(exception_type, BusinessOrchestrationError)


def test_business_orchestration_error_is_a_strategy_engine_error() -> None:
    assert issubclass(BusinessOrchestrationError, StrategyEngineError)


def test_can_raise_and_catch_base_class() -> None:
    with pytest.raises(BusinessOrchestrationError):
        raise StageExecutionError("boom")

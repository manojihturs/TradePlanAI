"""Tests for core.exceptions."""

from __future__ import annotations

import pytest

from core.exceptions import (
    AmbiguousWinnerError,
    EventBusError,
    ReplayError,
    StateMachineError,
    StrategyEngineError,
    TradeManagerError,
    UnresolvedBusinessRuleError,
    ValidationError,
)


@pytest.mark.parametrize(
    "exception_type",
    [
        ValidationError,
        EventBusError,
        TradeManagerError,
        StateMachineError,
        ReplayError,
        UnresolvedBusinessRuleError,
        AmbiguousWinnerError,
    ],
)
def test_every_subclass_is_a_strategy_engine_error(exception_type: type[Exception]) -> None:
    assert issubclass(exception_type, StrategyEngineError)


def test_can_raise_and_catch_base_class() -> None:
    with pytest.raises(StrategyEngineError):
        raise ValidationError("boom")


def test_unresolved_business_rule_error_message() -> None:
    with pytest.raises(UnresolvedBusinessRuleError, match="Weekly Future formula"):
        raise UnresolvedBusinessRuleError("Weekly Future formula is MISSING INFORMATION.")

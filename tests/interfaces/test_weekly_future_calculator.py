"""Conformance tests for interfaces.weekly_future_calculator.

These tests verify only the Protocol *shape* and the documented
"raise until resolved" stub convention - they do not, and must not,
implement the Weekly Future formula itself (Specification Section 20
item 1, Critical, still MISSING INFORMATION).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.exceptions import UnresolvedBusinessRuleError
from interfaces.weekly_future_calculator import WeeklyFutureCalculator
from models.market_snapshot import MarketSnapshot


class _StubWeeklyFutureCalculator:
    """A stub satisfying the Protocol shape; always raises, per the
    documented convention for unresolved business rules."""

    def calculate(self, first_five_minute_candle: MarketSnapshot) -> object:
        raise UnresolvedBusinessRuleError(
            "Weekly Future formula is MISSING INFORMATION (Specification Section 20 item 1)."
        )


def _candle() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
        underlying_price=Decimal(24000),
        open=Decimal(23990),
        high=Decimal(24010),
        low=Decimal(23980),
        close=Decimal(24000),
    )


def test_stub_satisfies_protocol() -> None:
    assert isinstance(_StubWeeklyFutureCalculator(), WeeklyFutureCalculator)


def test_object_without_calculate_does_not_satisfy_protocol() -> None:
    class NotACalculator:
        pass

    assert not isinstance(NotACalculator(), WeeklyFutureCalculator)


def test_stub_raises_unresolved_business_rule_error() -> None:
    calculator: WeeklyFutureCalculator = _StubWeeklyFutureCalculator()
    with pytest.raises(UnresolvedBusinessRuleError, match="MISSING INFORMATION"):
        calculator.calculate(_candle())

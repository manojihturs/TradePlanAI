"""Conformance tests for interfaces.weekly_future_calculator.

Verifies only the Protocol *shape* - the real implementation and its
own tests live in ``src/weekly_future/`` (formula RESOLVED 2026-07-30,
see ``WEEKLY_FUTURE_FORMULA_SPECIFICATION.md`` v1.0).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.exceptions import UnresolvedBusinessRuleError
from interfaces.weekly_future_calculator import WeeklyFutureCalculator
from models.reference_level import ReferenceLevel
from models.weekly_future import WeeklyFuture


class _StubWeeklyFutureCalculator:
    """A stub satisfying the Protocol shape, for structural
    conformance testing only."""

    def calculate(
        self, session_id: uuid.UUID, level: ReferenceLevel, calculated_at: datetime
    ) -> WeeklyFuture:
        raise UnresolvedBusinessRuleError(
            "stub - see src/weekly_future/ for the real implementation."
        )


def _level() -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(24200),
        ce_high=Decimal("143.45"),
        ce_low=Decimal(116),
        pe_high=Decimal("165.8"),
        pe_low=Decimal(128),
    )


def test_stub_satisfies_protocol() -> None:
    assert isinstance(_StubWeeklyFutureCalculator(), WeeklyFutureCalculator)


def test_object_without_calculate_does_not_satisfy_protocol() -> None:
    class NotACalculator:
        pass

    assert not isinstance(NotACalculator(), WeeklyFutureCalculator)


def test_stub_raises() -> None:
    calculator: WeeklyFutureCalculator = _StubWeeklyFutureCalculator()
    with pytest.raises(UnresolvedBusinessRuleError):
        calculator.calculate(uuid.uuid4(), _level(), datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC))

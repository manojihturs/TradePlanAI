"""Conformance tests for interfaces.strike_selector.

Verifies only the Protocol shape and stub convention - the ATM
selection rule itself (Specification Section 20 item 2, Critical)
remains MISSING INFORMATION and is not implemented here.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from core.exceptions import UnresolvedBusinessRuleError
from interfaces.strike_selector import StrikeSelector
from models.weekly_future import WeeklyFuture


class _StubStrikeSelector:
    def select(
        self, session_id: uuid.UUID, weekly_future: WeeklyFuture, selected_at: datetime
    ) -> object:
        raise UnresolvedBusinessRuleError(
            "ATM strike selection rule is MISSING INFORMATION (Specification Section 20 item 2)."
        )


def _weekly_future() -> WeeklyFuture:
    from decimal import Decimal

    return WeeklyFuture(
        weekly_future_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        high=Decimal(24500),
        low=Decimal(24000),
        calculated_at=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
    )


def test_stub_satisfies_protocol() -> None:
    assert isinstance(_StubStrikeSelector(), StrikeSelector)


def test_object_without_select_does_not_satisfy_protocol() -> None:
    class NotASelector:
        pass

    assert not isinstance(NotASelector(), StrikeSelector)


def test_stub_raises_unresolved_business_rule_error() -> None:
    selector: StrikeSelector = _StubStrikeSelector()
    with pytest.raises(UnresolvedBusinessRuleError, match="MISSING INFORMATION"):
        selector.select(uuid.uuid4(), _weekly_future(), datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC))

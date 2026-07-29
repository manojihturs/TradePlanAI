"""Tests for models.weekly_future."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.weekly_future import WeeklyFuture


def test_valid_construction() -> None:
    wf = WeeklyFuture(
        weekly_future_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        high=Decimal(24500),
        low=Decimal(24000),
        calculated_at=datetime(2026, 7, 30, 9, 20, 0),  # noqa: DTZ001
    )
    assert wf.high == Decimal(24500)


def test_low_may_exceed_high_no_invariant_enforced() -> None:
    # Deliberately not validated - see module docstring: a prior,
    # different evidence source found exactly this case in its own
    # Weekly Future worked example.
    wf = WeeklyFuture(
        weekly_future_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        high=Decimal(100),
        low=Decimal(200),
        calculated_at=datetime(2026, 7, 30, 9, 20, 0),  # noqa: DTZ001
    )
    assert wf.low > wf.high


def test_none_weekly_future_id_raises() -> None:
    with pytest.raises(ValidationError, match="weekly_future_id must not be None"):
        WeeklyFuture(
            weekly_future_id=None,  # type: ignore[arg-type]
            session_id=uuid.uuid4(),
            high=Decimal(1),
            low=Decimal(1),
            calculated_at=datetime(2026, 7, 30, 9, 20, 0),  # noqa: DTZ001
        )


def test_none_session_id_raises() -> None:
    with pytest.raises(ValidationError, match="session_id must not be None"):
        WeeklyFuture(
            weekly_future_id=uuid.uuid4(),
            session_id=None,  # type: ignore[arg-type]
            high=Decimal(1),
            low=Decimal(1),
            calculated_at=datetime(2026, 7, 30, 9, 20, 0),  # noqa: DTZ001
        )


def test_none_calculated_at_raises() -> None:
    with pytest.raises(ValidationError, match="calculated_at must not be None"):
        WeeklyFuture(
            weekly_future_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            high=Decimal(1),
            low=Decimal(1),
            calculated_at=None,  # type: ignore[arg-type]
        )

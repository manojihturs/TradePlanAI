"""Tests for models.strike."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.strike import StrikeSelection


def _make(**overrides: object) -> StrikeSelection:
    fields: dict[str, object] = {
        "session_id": uuid.uuid4(),
        "top_strike": Decimal(24100),
        "bottom_strike": Decimal(23900),
        "selected_at": datetime(2026, 7, 30, 9, 20, 0),  # noqa: DTZ001
    }
    fields.update(overrides)
    return StrikeSelection(**fields)  # type: ignore[arg-type]


def test_valid_construction() -> None:
    selection = _make()
    assert selection.top_strike == Decimal(24100)


def test_top_and_bottom_may_be_equal_no_invariant_enforced() -> None:
    selection = _make(top_strike=Decimal(24000), bottom_strike=Decimal(24000))
    assert selection.top_strike == selection.bottom_strike


def test_none_session_id_raises() -> None:
    with pytest.raises(ValidationError, match="session_id must not be None"):
        _make(session_id=None)


def test_non_positive_top_strike_raises() -> None:
    with pytest.raises(ValidationError, match="top_strike must be greater than 0"):
        _make(top_strike=Decimal(0))


def test_non_positive_bottom_strike_raises() -> None:
    with pytest.raises(ValidationError, match="bottom_strike must be greater than 0"):
        _make(bottom_strike=Decimal(0))


def test_none_selected_at_raises() -> None:
    with pytest.raises(ValidationError, match="selected_at must not be None"):
        _make(selected_at=None)

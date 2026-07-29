"""Tests for models.trade_signal."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from core.enums import TradeDirection
from core.exceptions import ValidationError
from models.trade_signal import TradeSignal


def _make(**overrides: object) -> TradeSignal:
    fields: dict[str, object] = {
        "signal_id": uuid.uuid4(),
        "winner_event_id": uuid.uuid4(),
        "side": TradeDirection.CE,
        "strike": Decimal(24100),
        "raised_at": datetime(2026, 7, 30, 9, 30, 0),  # noqa: DTZ001
    }
    fields.update(overrides)
    return TradeSignal(**fields)  # type: ignore[arg-type]


def test_valid_construction_defaults_not_accepted() -> None:
    signal = _make()
    assert signal.accepted is False


def test_accepted_can_be_set() -> None:
    signal = _make(accepted=True)
    assert signal.accepted is True


def test_none_signal_id_raises() -> None:
    with pytest.raises(ValidationError, match="signal_id must not be None"):
        _make(signal_id=None)


def test_none_winner_event_id_raises() -> None:
    with pytest.raises(ValidationError, match="winner_event_id must not be None"):
        _make(winner_event_id=None)


def test_non_positive_strike_raises() -> None:
    with pytest.raises(ValidationError, match="strike must be greater than 0"):
        _make(strike=Decimal(0))


def test_none_raised_at_raises() -> None:
    with pytest.raises(ValidationError, match="raised_at must not be None"):
        _make(raised_at=None)

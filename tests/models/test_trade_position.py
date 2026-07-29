"""Tests for models.trade_position."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from core.enums import ExitReason, TradeDirection, TradeState
from core.exceptions import ValidationError
from models.trade_position import TradePosition


def _make(**overrides: object) -> TradePosition:
    fields: dict[str, object] = {
        "trade_id": uuid.uuid4(),
        "entry_strike": Decimal(24100),
        "entry_side": TradeDirection.CE,
        "target_level": Decimal(24150),
        "support_level": Decimal(24050),
        "competitor_monitor_strike": Decimal(24050),
        "opened_at": datetime(2026, 7, 30, 9, 30, 0),  # noqa: DTZ001
    }
    fields.update(overrides)
    return TradePosition(**fields)  # type: ignore[arg-type]


def test_valid_active_construction() -> None:
    position = _make()
    assert position.is_active() is True
    assert position.status == TradeState.TRADE_ACTIVE


def test_none_trade_id_raises() -> None:
    with pytest.raises(ValidationError, match="trade_id must not be None"):
        _make(trade_id=None)


def test_non_positive_entry_strike_raises() -> None:
    with pytest.raises(ValidationError, match="entry_strike must be greater than 0"):
        _make(entry_strike=Decimal(0))


def test_none_opened_at_raises() -> None:
    with pytest.raises(ValidationError, match="opened_at must not be None"):
        _make(opened_at=None)


def test_invalid_status_raises() -> None:
    with pytest.raises(ValidationError, match="status must be TRADE_ACTIVE or TRADE_CLOSED"):
        _make(status=TradeState.IDLE)


def test_active_with_exit_reason_raises() -> None:
    with pytest.raises(ValidationError, match="active TradePosition must not have an exit_reason"):
        _make(status=TradeState.TRADE_ACTIVE, exit_reason=ExitReason.TARGET_HIT)


def test_active_with_closed_at_raises() -> None:
    with pytest.raises(ValidationError, match="active TradePosition must not have a closed_at"):
        _make(
            status=TradeState.TRADE_ACTIVE,
            closed_at=datetime(2026, 7, 30, 9, 40, 0),  # noqa: DTZ001
        )


def test_closed_without_exit_reason_raises() -> None:
    with pytest.raises(ValidationError, match="closed TradePosition must have an exit_reason"):
        _make(
            status=TradeState.TRADE_CLOSED,
            closed_at=datetime(2026, 7, 30, 9, 40, 0),  # noqa: DTZ001
        )


def test_closed_without_closed_at_raises() -> None:
    with pytest.raises(ValidationError, match="closed TradePosition must have a closed_at"):
        _make(status=TradeState.TRADE_CLOSED, exit_reason=ExitReason.TARGET_HIT)


class TestClose:
    def test_close_returns_new_closed_instance(self) -> None:
        position = _make()
        closed_at = datetime(2026, 7, 30, 9, 45, 0)  # noqa: DTZ001
        closed = position.close(ExitReason.TARGET_HIT, closed_at)

        assert position.is_active() is True  # original untouched
        assert closed.is_active() is False
        assert closed.exit_reason == ExitReason.TARGET_HIT
        assert closed.closed_at == closed_at
        assert closed.trade_id == position.trade_id

    def test_close_already_closed_raises(self) -> None:
        position = _make()
        closed = position.close(
            ExitReason.TARGET_HIT, datetime(2026, 7, 30, 9, 45, 0)  # noqa: DTZ001
        )
        with pytest.raises(ValidationError, match="is already closed"):
            closed.close(ExitReason.STOP_LOSS, datetime(2026, 7, 30, 9, 50, 0))  # noqa: DTZ001

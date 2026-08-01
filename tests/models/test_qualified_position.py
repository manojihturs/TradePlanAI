"""Tests for models.qualified_position."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import AnchorRole, ExitReason, TradeDirection, TradeState
from core.exceptions import ValidationError
from models.qualified_position import QualifiedPosition


def _make(**overrides: object) -> QualifiedPosition:
    fields: dict[str, object] = {
        "position_id": uuid.uuid4(),
        "anchor_role": AnchorRole.TOP,
        "side": TradeDirection.CE,
        "entry_strike": Decimal(24250),
        "entry_level": Decimal("120.1"),
        "target_level": Decimal("145.2"),
        "stop_loss_level": Decimal("98.3"),
        "competitor_exit_level": Decimal("121.5"),
        "opened_at": datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
    }
    fields.update(overrides)
    return QualifiedPosition(**fields)  # type: ignore[arg-type]


def test_valid_active_construction() -> None:
    position = _make()
    assert position.is_active() is True
    assert position.status == TradeState.TRADE_ACTIVE


def test_none_position_id_raises() -> None:
    with pytest.raises(ValidationError, match="position_id must not be None"):
        _make(position_id=None)


def test_non_positive_entry_strike_raises() -> None:
    with pytest.raises(ValidationError, match="entry_strike must be greater than 0"):
        _make(entry_strike=Decimal(0))


@pytest.mark.parametrize(
    "field", ["entry_level", "target_level", "stop_loss_level", "competitor_exit_level"]
)
def test_non_positive_price_field_raises(field: str) -> None:
    with pytest.raises(ValidationError, match=f"{field} must be greater than 0"):
        _make(**{field: Decimal(0)})


def test_none_opened_at_raises() -> None:
    with pytest.raises(ValidationError, match="opened_at must not be None"):
        _make(opened_at=None)


def test_invalid_status_raises() -> None:
    with pytest.raises(ValidationError, match="status must be TRADE_ACTIVE or TRADE_CLOSED"):
        _make(status=TradeState.IDLE)


def test_active_with_exit_reason_raises() -> None:
    with pytest.raises(
        ValidationError, match="active QualifiedPosition must not have an exit_reason"
    ):
        _make(status=TradeState.TRADE_ACTIVE, exit_reason=ExitReason.TARGET_HIT)


def test_active_with_closed_at_raises() -> None:
    with pytest.raises(ValidationError, match="active QualifiedPosition must not have a closed_at"):
        _make(status=TradeState.TRADE_ACTIVE, closed_at=datetime(2026, 7, 30, 9, 40, 0, tzinfo=UTC))


def test_closed_without_exit_reason_raises() -> None:
    with pytest.raises(ValidationError, match="closed QualifiedPosition must have an exit_reason"):
        _make(status=TradeState.TRADE_CLOSED, closed_at=datetime(2026, 7, 30, 9, 40, 0, tzinfo=UTC))


def test_closed_without_closed_at_raises() -> None:
    with pytest.raises(ValidationError, match="closed QualifiedPosition must have a closed_at"):
        _make(status=TradeState.TRADE_CLOSED, exit_reason=ExitReason.TARGET_HIT)


class TestClose:
    def test_close_returns_new_closed_instance(self) -> None:
        position = _make()
        closed_at = datetime(2026, 7, 30, 9, 45, 0, tzinfo=UTC)
        closed = position.close(ExitReason.TARGET_HIT, closed_at)

        assert position.is_active() is True  # original untouched
        assert closed.is_active() is False
        assert closed.exit_reason == ExitReason.TARGET_HIT
        assert closed.closed_at == closed_at
        assert closed.position_id == position.position_id

    def test_close_already_closed_raises(self) -> None:
        position = _make()
        closed = position.close(ExitReason.TARGET_HIT, datetime(2026, 7, 30, 9, 45, 0, tzinfo=UTC))
        with pytest.raises(ValidationError, match="is already closed"):
            closed.close(ExitReason.STOP_LOSS, datetime(2026, 7, 30, 9, 50, 0, tzinfo=UTC))

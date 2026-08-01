"""Tests for models.qualification_signal."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import AnchorRole, TradeDirection
from core.exceptions import ValidationError
from models.qualification_signal import QualificationSignal


def _make(**overrides: object) -> QualificationSignal:
    fields: dict[str, object] = {
        "signal_id": uuid.uuid4(),
        "anchor_role": AnchorRole.TOP,
        "side": TradeDirection.CE,
        "entry_strike": Decimal(24250),
        "entry_level": Decimal("120.1"),
        "target_level": Decimal("145.2"),
        "stop_loss_level": Decimal("98.3"),
        "competitor_exit_level": Decimal("121.5"),
        "qualified_at": datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
    }
    fields.update(overrides)
    return QualificationSignal(**fields)  # type: ignore[arg-type]


def test_valid_construction() -> None:
    signal = _make()
    assert signal.anchor_role is AnchorRole.TOP
    assert signal.side is TradeDirection.CE
    assert signal.entry_strike == Decimal(24250)


def test_none_signal_id_raises() -> None:
    with pytest.raises(ValidationError, match="signal_id must not be None"):
        _make(signal_id=None)


def test_non_positive_entry_strike_raises() -> None:
    with pytest.raises(ValidationError, match="entry_strike must be greater than 0"):
        _make(entry_strike=Decimal(0))


@pytest.mark.parametrize(
    "field", ["entry_level", "target_level", "stop_loss_level", "competitor_exit_level"]
)
def test_non_positive_price_field_raises(field: str) -> None:
    with pytest.raises(ValidationError, match=f"{field} must be greater than 0"):
        _make(**{field: Decimal(0)})


def test_none_qualified_at_raises() -> None:
    with pytest.raises(ValidationError, match="qualified_at must not be None"):
        _make(qualified_at=None)

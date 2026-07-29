"""Tests for models.reference_level."""

from __future__ import annotations

from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel


def _make(**overrides: object) -> ReferenceLevel:
    fields: dict[str, object] = {
        "strike": Decimal(24100),
        "ce_high": Decimal(110),
        "ce_low": Decimal(90),
        "pe_high": Decimal(105),
        "pe_low": Decimal(85),
    }
    fields.update(overrides)
    return ReferenceLevel(**fields)  # type: ignore[arg-type]


def test_valid_construction() -> None:
    level = _make()
    assert level.strike == Decimal(24100)


def test_non_positive_strike_raises() -> None:
    with pytest.raises(ValidationError, match="strike must be greater than 0"):
        _make(strike=Decimal(0))


def test_ce_high_below_low_raises() -> None:
    with pytest.raises(ValidationError, match="ce_high .* is less than ce_low"):
        _make(ce_high=Decimal(80), ce_low=Decimal(90))


def test_pe_high_below_low_raises() -> None:
    with pytest.raises(ValidationError, match="pe_high .* is less than pe_low"):
        _make(pe_high=Decimal(80), pe_low=Decimal(90))

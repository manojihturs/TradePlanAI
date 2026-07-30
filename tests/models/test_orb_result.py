"""Tests for models.orb_result."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import OptionType, ORBStatus
from core.exceptions import ValidationError
from models.orb_result import ORBResult

_TIMESTAMP = datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


def _result(**overrides: object) -> ORBResult:
    defaults: dict[str, object] = {
        "orb_result_id": uuid.uuid4(),
        "session_id": uuid.uuid4(),
        "strike": Decimal(24200),
        "side": OptionType.CALL,
        "opening_high": Decimal("143.45"),
        "opening_low": Decimal(116),
        "range": Decimal("143.45") - Decimal(116),
        "status": ORBStatus.NONE,
        "calculated_at": _TIMESTAMP,
    }
    defaults.update(overrides)
    return ORBResult(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_valid_construction(self) -> None:
        result = _result()

        assert result.status == ORBStatus.NONE
        assert result.range == Decimal("27.45")

    def test_none_orb_result_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="orb_result_id must not be None"):
            _result(orb_result_id=None)

    def test_none_session_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="session_id must not be None"):
            _result(session_id=None)

    def test_non_positive_strike_raises(self) -> None:
        with pytest.raises(ValidationError, match="strike must be greater than 0"):
            _result(strike=Decimal(0))

    def test_opening_high_below_opening_low_raises(self) -> None:
        with pytest.raises(ValidationError, match="opening_high .* is less than opening_low"):
            _result(opening_high=Decimal(100), opening_low=Decimal(200), range=Decimal(-100))

    def test_mismatched_range_raises(self) -> None:
        with pytest.raises(ValidationError, match="range must equal opening_high - opening_low"):
            _result(range=Decimal(999))

    def test_none_calculated_at_raises(self) -> None:
        with pytest.raises(ValidationError, match="calculated_at must not be None"):
            _result(calculated_at=None)

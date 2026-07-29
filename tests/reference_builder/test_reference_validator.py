"""Tests for reference_builder.reference_validator."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from reference_builder.reference_validator import (
    EXPECTED_LADDER_SIZE,
    ReferenceValidator,
    StrikeCandleInput,
)


def _candle(low: str = "90", high: str = "110") -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
        underlying_price=Decimal(24000),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _tick() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC), underlying_price=Decimal(24000)
    )


def _valid_inputs(count: int = EXPECTED_LADDER_SIZE) -> tuple[StrikeCandleInput, ...]:
    base = 23700
    return tuple(
        StrikeCandleInput(strike=Decimal(base + i * 50), ce_candle=_candle(), pe_candle=_candle())
        for i in range(count)
    )


@pytest.fixture
def validator() -> ReferenceValidator:
    return ReferenceValidator()


class TestValidateInputs:
    def test_valid_13_strike_ladder_passes(self, validator: ReferenceValidator) -> None:
        validator.validate_inputs(_valid_inputs())  # must not raise

    def test_wrong_count_raises(self, validator: ReferenceValidator) -> None:
        with pytest.raises(ValidationError, match="Expected exactly 13 strikes"):
            validator.validate_inputs(_valid_inputs(count=10))

    def test_duplicate_strikes_raise(self, validator: ReferenceValidator) -> None:
        inputs = list(_valid_inputs())
        inputs[1] = StrikeCandleInput(
            strike=inputs[0].strike, ce_candle=_candle(), pe_candle=_candle()
        )
        with pytest.raises(ValidationError, match="duplicate strikes"):
            validator.validate_inputs(tuple(inputs))

    def test_non_candle_ce_raises(self, validator: ReferenceValidator) -> None:
        inputs = list(_valid_inputs())
        inputs[0] = StrikeCandleInput(
            strike=inputs[0].strike, ce_candle=_tick(), pe_candle=_candle()
        )
        with pytest.raises(ValidationError, match="CE candle .* is not candle-mode"):
            validator.validate_inputs(tuple(inputs))

    def test_non_candle_pe_raises(self, validator: ReferenceValidator) -> None:
        inputs = list(_valid_inputs())
        inputs[0] = StrikeCandleInput(
            strike=inputs[0].strike, ce_candle=_candle(), pe_candle=_tick()
        )
        with pytest.raises(ValidationError, match="PE candle .* is not candle-mode"):
            validator.validate_inputs(tuple(inputs))

    def test_non_standard_spacing_is_not_rejected(self, validator: ReferenceValidator) -> None:
        # Deliberately irregular spacing - spacing is MISSING INFORMATION
        # and must never be assumed/enforced.
        strikes = [
            23700,
            23760,
            23800,
            23900,
            23950,
            24000,
            24050,
            24100,
            24200,
            24300,
            24310,
            24400,
            24500,
        ]
        inputs = tuple(
            StrikeCandleInput(strike=Decimal(s), ce_candle=_candle(), pe_candle=_candle())
            for s in strikes
        )
        validator.validate_inputs(inputs)  # must not raise


class TestValidateLevels:
    def _level(self, strike: int) -> ReferenceLevel:
        return ReferenceLevel(
            strike=Decimal(strike),
            ce_high=Decimal(110),
            ce_low=Decimal(90),
            pe_high=Decimal(105),
            pe_low=Decimal(85),
        )

    def test_valid_13_level_ladder_passes(self, validator: ReferenceValidator) -> None:
        levels = tuple(self._level(23700 + i * 50) for i in range(EXPECTED_LADDER_SIZE))
        validator.validate_levels(levels)  # must not raise

    def test_wrong_count_raises(self, validator: ReferenceValidator) -> None:
        levels = tuple(self._level(23700 + i * 50) for i in range(5))
        with pytest.raises(ValidationError, match="Expected exactly 13 levels"):
            validator.validate_levels(levels)

    def test_duplicate_strikes_raise(self, validator: ReferenceValidator) -> None:
        levels = tuple(self._level(23700) for _ in range(EXPECTED_LADDER_SIZE))
        with pytest.raises(ValidationError, match="duplicate strikes"):
            validator.validate_levels(levels)

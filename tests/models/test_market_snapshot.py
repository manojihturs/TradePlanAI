"""Tests for models.market_snapshot."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot


@pytest.fixture
def timestamp() -> datetime:
    return datetime(2026, 7, 30, 9, 16, 0)  # noqa: DTZ001


class TestTickMode:
    def test_valid_tick(self, timestamp: datetime) -> None:
        snapshot = MarketSnapshot(timestamp=timestamp, underlying_price=Decimal(24000))
        assert snapshot.is_candle() is False

    def test_non_positive_price_raises(self, timestamp: datetime) -> None:
        with pytest.raises(ValidationError, match="underlying_price must be greater than 0"):
            MarketSnapshot(timestamp=timestamp, underlying_price=Decimal(0))


class TestCandleMode:
    def test_valid_candle(self, timestamp: datetime) -> None:
        snapshot = MarketSnapshot(
            timestamp=timestamp,
            underlying_price=Decimal(24000),
            open=Decimal(100),
            high=Decimal(110),
            low=Decimal(95),
            close=Decimal(105),
            volume=1000,
        )
        assert snapshot.is_candle() is True

    def test_partial_ohlc_raises(self, timestamp: datetime) -> None:
        with pytest.raises(ValidationError, match="all present .* or all absent"):
            MarketSnapshot(timestamp=timestamp, underlying_price=Decimal(24000), open=Decimal(100))

    def test_high_below_low_raises(self, timestamp: datetime) -> None:
        with pytest.raises(ValidationError, match="high .* is less than low"):
            MarketSnapshot(
                timestamp=timestamp,
                underlying_price=Decimal(24000),
                open=Decimal(100),
                high=Decimal(90),
                low=Decimal(95),
                close=Decimal(92),
            )

    def test_open_outside_range_raises(self, timestamp: datetime) -> None:
        with pytest.raises(ValidationError, match="open .* is outside"):
            MarketSnapshot(
                timestamp=timestamp,
                underlying_price=Decimal(24000),
                open=Decimal(200),
                high=Decimal(110),
                low=Decimal(95),
                close=Decimal(105),
            )

    def test_close_outside_range_raises(self, timestamp: datetime) -> None:
        with pytest.raises(ValidationError, match="close .* is outside"):
            MarketSnapshot(
                timestamp=timestamp,
                underlying_price=Decimal(24000),
                open=Decimal(100),
                high=Decimal(110),
                low=Decimal(95),
                close=Decimal(1),
            )

    def test_negative_volume_raises(self, timestamp: datetime) -> None:
        with pytest.raises(ValidationError, match="volume must not be negative"):
            MarketSnapshot(
                timestamp=timestamp,
                underlying_price=Decimal(24000),
                open=Decimal(100),
                high=Decimal(110),
                low=Decimal(95),
                close=Decimal(105),
                volume=-1,
            )

    def test_none_timestamp_raises(self) -> None:
        with pytest.raises(ValidationError, match="timestamp must not be None"):
            MarketSnapshot(timestamp=None, underlying_price=Decimal(1))  # type: ignore[arg-type]

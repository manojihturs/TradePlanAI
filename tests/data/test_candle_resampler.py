"""Tests for data.candle_resampler."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from data.candle_resampler import resample_candles
from models.market_snapshot import MarketSnapshot

_SESSION_START = time(9, 15)


def _candle(
    minute_offset: int, open_: str, high: str, low: str, close: str, volume: int = 10
) -> MarketSnapshot:
    timestamp = datetime(2026, 7, 30, 9, 15, tzinfo=UTC) + timedelta(minutes=minute_offset)
    return MarketSnapshot(
        timestamp=timestamp,
        underlying_price=Decimal(close),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=volume,
    )


class TestEmptyAndInvalidInput:
    def test_empty_input_returns_empty(self) -> None:
        assert resample_candles((), 5, _SESSION_START) == ()

    def test_non_positive_bucket_minutes_raises(self) -> None:
        with pytest.raises(ValidationError, match="bucket_minutes must be positive"):
            resample_candles((_candle(0, "100", "101", "99", "100"),), 0, _SESSION_START)

    def test_tick_mode_candle_raises(self) -> None:
        tick = MarketSnapshot(
            timestamp=datetime(2026, 7, 30, 9, 15, tzinfo=UTC), underlying_price=Decimal(100)
        )
        with pytest.raises(ValidationError, match="candle-mode"):
            resample_candles((tick,), 5, _SESSION_START)


class TestAggregation:
    def test_single_bucket_aggregates_ohlcv_correctly(self) -> None:
        candles = (
            _candle(0, "100", "101", "99", "100.5", volume=10),
            _candle(1, "100.5", "103", "100", "102", volume=20),
            _candle(2, "102", "102.5", "101", "101.5", volume=5),
        )

        resampled = resample_candles(candles, 5, _SESSION_START)

        assert len(resampled) == 1
        bucket = resampled[0]
        assert bucket.timestamp == datetime(2026, 7, 30, 9, 15, tzinfo=UTC)
        assert bucket.open == Decimal(100)
        assert bucket.high == Decimal(103)
        assert bucket.low == Decimal(99)
        assert bucket.close == Decimal("101.5")
        assert bucket.volume == 35

    def test_multiple_buckets_sorted_chronologically(self) -> None:
        candles = (
            _candle(0, "100", "101", "99", "100"),
            _candle(4, "100", "101", "99", "100"),
            _candle(5, "105", "106", "104", "105"),
            _candle(9, "105", "107", "103", "106"),
        )

        resampled = resample_candles(candles, 5, _SESSION_START)

        assert len(resampled) == 2
        assert resampled[0].timestamp == datetime(2026, 7, 30, 9, 15, tzinfo=UTC)
        assert resampled[1].timestamp == datetime(2026, 7, 30, 9, 20, tzinfo=UTC)
        assert resampled[0].close == Decimal(100)
        assert resampled[1].close == Decimal(106)

    def test_candle_before_session_start_is_skipped(self) -> None:
        before_open = MarketSnapshot(
            timestamp=datetime(2026, 7, 30, 9, 0, tzinfo=UTC),
            underlying_price=Decimal(100),
            open=Decimal(100),
            high=Decimal(101),
            low=Decimal(99),
            close=Decimal(100),
            volume=10,
        )
        candles = (before_open, _candle(0, "100", "101", "99", "100"))

        resampled = resample_candles(candles, 5, _SESSION_START)

        assert len(resampled) == 1
        assert resampled[0].timestamp == datetime(2026, 7, 30, 9, 15, tzinfo=UTC)

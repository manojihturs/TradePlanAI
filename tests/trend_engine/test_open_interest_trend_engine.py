"""Tests for trend_engine.open_interest_trend_engine."""

from __future__ import annotations

from decimal import Decimal

from core.enums import TrendDirection
from trend_engine.open_interest_trend_engine import OpenInterestTrendEngine


class TestOpenInterestTrendEngine:
    def test_price_up_oi_up_is_bullish(self) -> None:
        engine = OpenInterestTrendEngine()

        result = engine.evaluate(
            session_open_price=Decimal(24000),
            current_price=Decimal(24050),
            session_open_call_oi=1000,
            session_open_put_oi=1000,
            current_call_oi=1000,
            current_put_oi=1200,
        )

        assert result is TrendDirection.BULLISH

    def test_price_down_oi_up_is_bearish(self) -> None:
        engine = OpenInterestTrendEngine()

        result = engine.evaluate(
            session_open_price=Decimal(24000),
            current_price=Decimal(23950),
            session_open_call_oi=1000,
            session_open_put_oi=1000,
            current_call_oi=1000,
            current_put_oi=1200,
        )

        assert result is TrendDirection.BEARISH

    def test_price_up_oi_down_is_no_signal(self) -> None:
        engine = OpenInterestTrendEngine()

        result = engine.evaluate(
            session_open_price=Decimal(24000),
            current_price=Decimal(24050),
            session_open_call_oi=1000,
            session_open_put_oi=1000,
            current_call_oi=1200,
            current_put_oi=1000,
        )

        assert result is None

    def test_price_down_oi_down_is_no_signal(self) -> None:
        engine = OpenInterestTrendEngine()

        result = engine.evaluate(
            session_open_price=Decimal(24000),
            current_price=Decimal(23950),
            session_open_call_oi=1000,
            session_open_put_oi=1000,
            current_call_oi=1200,
            current_put_oi=1000,
        )

        assert result is None

    def test_price_unchanged_is_no_signal(self) -> None:
        engine = OpenInterestTrendEngine()

        result = engine.evaluate(
            session_open_price=Decimal(24000),
            current_price=Decimal(24000),
            session_open_call_oi=1000,
            session_open_put_oi=1000,
            current_call_oi=1000,
            current_put_oi=1200,
        )

        assert result is None

    def test_oi_tie_is_no_signal(self) -> None:
        engine = OpenInterestTrendEngine()

        result = engine.evaluate(
            session_open_price=Decimal(24000),
            current_price=Decimal(24050),
            session_open_call_oi=1000,
            session_open_put_oi=1000,
            current_call_oi=1200,
            current_put_oi=1200,
        )

        assert result is None

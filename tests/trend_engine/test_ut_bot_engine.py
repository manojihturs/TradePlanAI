"""Tests for trend_engine.ut_bot_engine.

Hand-computed scenarios use ``atr_period=1`` so the running ATR always
equals the current bar's own True Range - this keeps every expected
value independently verifiable by hand, exercising every branch of
the formula (see ``ut_bot_engine.py``'s own docstring for the
formula).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from trend_engine.ut_bot_engine import UTBotEngine, UTBotSignal

_START = datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)


def _candle(index: int, high: str, low: str, close: str) -> MarketSnapshot:
    timestamp = _START + timedelta(minutes=5 * index)
    return MarketSnapshot(
        timestamp=timestamp,
        underlying_price=Decimal(close),
        open=Decimal(close),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
    )


class TestValidation:
    def test_non_positive_atr_period_raises(self) -> None:
        with pytest.raises(ValidationError, match="atr_period must be greater than 0"):
            UTBotEngine(atr_period=0)

    def test_non_candle_snapshot_raises(self) -> None:
        engine = UTBotEngine()
        tick = MarketSnapshot(timestamp=_START, underlying_price=Decimal(100))

        with pytest.raises(ValidationError, match="requires candle-mode snapshots"):
            engine.update(tick)


class TestFirstCandle:
    def test_first_candle_emits_no_signal_and_seeds_stop(self) -> None:
        engine = UTBotEngine(key_value=Decimal(1), atr_period=1)

        # TR1 = high - low = 20; ATR = 20; nLoss = 20; stop = close - nLoss = 100 - 20 = 80.
        signal = engine.update(_candle(0, "110", "90", "100"))

        assert signal is None
        assert engine.current_trailing_stop == Decimal(80)


class TestBuySellFlips:
    def test_full_sequence_seed_then_sell_then_buy(self) -> None:
        engine = UTBotEngine(key_value=Decimal(1), atr_period=1)

        # Candle 1 (seed): TR=10, ATR=10, nLoss=10, stop = 95 - 10 = 85.
        first = engine.update(_candle(0, "100", "90", "95"))

        # Candle 2 (crash down): TR = max(80-70, |80-95|, |70-95|) = 25.
        # src(75) < prev_stop(85) but prev_src(95) is NOT < prev_stop(85)
        # -> falls to the "else" branch: stop = src + nLoss = 75 + 25 = 100.
        # prev_src(95) >= prev_stop(85) and src(75) < stop(100) -> SELL.
        second = engine.update(_candle(1, "80", "70", "75"))

        assert first is None
        assert second is UTBotSignal.SELL
        assert engine.current_trailing_stop == Decimal(100)

        # Candle 3 (rally back): TR = max(115-105, |115-75|, |105-75|) = 40.
        # src(110) > prev_stop(100) but prev_src(75) is NOT > prev_stop(100)
        # -> falls to "elif src > prev_stop": stop = src - nLoss = 110 - 40 = 70.
        # prev_src(75) <= prev_stop(100) and src(110) > stop(70) -> BUY.
        third = engine.update(_candle(2, "115", "105", "110"))

        assert third is UTBotSignal.BUY
        assert engine.current_trailing_stop == Decimal(70)

    def test_uptrend_continuation_takes_the_max_branch_no_signal(self) -> None:
        engine = UTBotEngine(key_value=Decimal(1), atr_period=1)

        # Candle 1 (seed): TR=20, ATR=20, nLoss=20, stop = 100 - 20 = 80.
        engine.update(_candle(0, "110", "90", "100"))

        # Candle 2 (continues up): TR = max(105-95, |105-100|, |95-100|) = 10.
        # src(102) > prev_stop(80) and prev_src(100) > prev_stop(80)
        # -> "max" branch: stop = max(80, 102 - 10) = max(80, 92) = 92.
        # No crossover (src stays above stop both bars) -> no signal.
        signal = engine.update(_candle(1, "105", "95", "102"))

        assert signal is None
        assert engine.current_trailing_stop == Decimal(92)

    def test_downtrend_continuation_takes_the_min_branch_no_signal(self) -> None:
        engine = UTBotEngine(key_value=Decimal(1), atr_period=1)

        # Candle 1 (seed): TR=10, ATR=10, nLoss=10, stop = 95 - 10 = 85.
        engine.update(_candle(0, "100", "90", "95"))

        # Candle 2 (crash, else branch): TR=25, stop = 75 + 25 = 100 (SELL).
        engine.update(_candle(1, "80", "70", "75"))

        # Candle 3 (continues down): TR = max(65-55, |65-75|, |55-75|) = 20.
        # src(60) < prev_stop(100) and prev_src(75) < prev_stop(100)
        # -> "min" branch: stop = min(100, 60 + 20) = min(100, 80) = 80.
        # No crossover (src stays below stop both bars) -> no signal.
        signal = engine.update(_candle(2, "65", "55", "60"))

        assert signal is None
        assert engine.current_trailing_stop == Decimal(80)


class TestATRWarmup:
    def test_partial_atr_seed_before_period_is_filled(self) -> None:
        engine = UTBotEngine(key_value=Decimal(1), atr_period=3)

        # TR1 = 10 -> ATR = 10 (average of the one value seen so far).
        engine.update(_candle(0, "100", "90", "95"))
        # TR2 = max(105-97, |105-95|, |97-95|) = 10 -> ATR = avg(10, 10) = 10.
        signal = engine.update(_candle(1, "105", "97", "100"))

        assert signal is None

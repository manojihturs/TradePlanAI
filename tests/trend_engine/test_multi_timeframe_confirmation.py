"""Tests for trend_engine.multi_timeframe_confirmation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from core.enums import TrendDirection
from models.market_snapshot import MarketSnapshot
from trend_engine.multi_timeframe_confirmation import MultiTimeframeUTBotConfirmation
from trend_engine.ut_bot_engine import UTBotSignal

_START = datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)


def _five_minute_candles(count: int) -> tuple[MarketSnapshot, ...]:
    candles = []
    for i in range(count):
        ts = _START + timedelta(minutes=5 * i)
        price = Decimal(100 + i)
        candles.append(
            MarketSnapshot(
                timestamp=ts,
                underlying_price=price,
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
            )
        )
    return tuple(candles)


class _FakeUTBotEngine:
    """Records every candle fed to it; ``current_position`` is set
    directly by the test rather than computed."""

    def __init__(self) -> None:
        self.fed: list[MarketSnapshot] = []
        self.current_position: UTBotSignal | None = None

    def update(self, candle: MarketSnapshot) -> UTBotSignal | None:
        self.fed.append(candle)
        return None


class TestBucketFeeding:
    def test_feeds_exactly_one_complete_bucket_per_timeframe(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        # Exactly 3 five-minute candles = one complete 15m bucket, but
        # not enough for a complete 30m (needs 6) or 1h (needs 12) bucket.
        confirmation.update(_five_minute_candles(3))

        assert len(fake_15m.fed) == 1
        assert len(fake_30m.fed) == 0
        assert len(fake_1h.fed) == 0

    def test_partial_bucket_is_never_fed(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        # 5 candles = one complete 15m bucket (3) plus 2 leftover
        # candles that must NOT be fed as a partial bucket.
        confirmation.update(_five_minute_candles(5))

        assert len(fake_15m.fed) == 1

    def test_does_not_re_feed_already_completed_buckets(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        confirmation.update(_five_minute_candles(6))  # 2 complete 15m buckets
        confirmation.update(_five_minute_candles(6))  # same data again - no new buckets

        assert len(fake_15m.fed) == 2

    def test_feeds_a_second_newly_completed_bucket_only(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        confirmation.update(_five_minute_candles(3))  # bucket 1 completes
        confirmation.update(_five_minute_candles(6))  # bucket 2 completes

        assert len(fake_15m.fed) == 2

    def test_all_three_timeframes_fed_once_enough_data_exists(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        confirmation.update(_five_minute_candles(12))  # exactly one 1h bucket

        assert len(fake_15m.fed) == 4
        assert len(fake_30m.fed) == 2
        assert len(fake_1h.fed) == 1


class TestConfirmation:
    def test_no_confirmation_when_any_timeframe_has_no_position_yet(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        fake_15m.current_position = UTBotSignal.BUY
        fake_30m.current_position = UTBotSignal.BUY
        fake_1h.current_position = None
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        result = confirmation.update(_five_minute_candles(3))

        assert result is None

    def test_no_confirmation_when_timeframes_disagree(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        fake_15m.current_position = UTBotSignal.BUY
        fake_30m.current_position = UTBotSignal.SELL
        fake_1h.current_position = UTBotSignal.BUY
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        result = confirmation.update(_five_minute_candles(3))

        assert result is None

    def test_confirmed_bullish_when_all_three_agree_buy(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        fake_15m.current_position = UTBotSignal.BUY
        fake_30m.current_position = UTBotSignal.BUY
        fake_1h.current_position = UTBotSignal.BUY
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        result = confirmation.update(_five_minute_candles(3))

        assert result is TrendDirection.BULLISH

    def test_confirmed_bearish_when_all_three_agree_sell(self) -> None:
        fake_15m, fake_30m, fake_1h = _FakeUTBotEngine(), _FakeUTBotEngine(), _FakeUTBotEngine()
        fake_15m.current_position = UTBotSignal.SELL
        fake_30m.current_position = UTBotSignal.SELL
        fake_1h.current_position = UTBotSignal.SELL
        confirmation = MultiTimeframeUTBotConfirmation(
            engine_15m=fake_15m, engine_30m=fake_30m, engine_1h=fake_1h
        )

        result = confirmation.update(_five_minute_candles(3))

        assert result is TrendDirection.BEARISH


class TestDefaultEngines:
    def test_defaults_construct_real_ut_bot_engines(self) -> None:
        confirmation = MultiTimeframeUTBotConfirmation()

        # No flip possible yet with only 3 candles (partial data for
        # every timeframe) - just proves the default wiring doesn't
        # blow up and behaves like "no confirmation yet".
        result = confirmation.update(_five_minute_candles(3))

        assert result is None

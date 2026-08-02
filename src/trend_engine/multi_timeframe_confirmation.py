"""MultiTimeframeUTBotConfirmation: confirms a trend across 15m/30m/1h
UT Bot readings before treating it as trustworthy.

Traceability
------------
Product Owner (2026-08-02, chat): "try higher timeframe 15mins,
30mins and one hour then confirm the trend." Standard multi-timeframe
confirmation technique - a trend on a lower timeframe is only acted
on once higher timeframes agree, reducing false signals from noise on
the fast timeframe. Confirmation rule and 5-minute signal's role both
explicitly confirmed by the Product Owner (chat, same exchange):
**all three of 15m/30m/1h must agree** (strictest of the three
options offered), and the **5-minute UT Bot signal still triggers
entries** - the higher timeframes only gate/confirm it, they don't
replace it (see ``business.stages.multi_timeframe_confirmation_stage.MultiTimeframeConfirmationStage``,
which applies that gate to ``PipelineContext.trend``).

Runs three independent :class:`~trend_engine.ut_bot_engine.UTBotEngine`
instances (same confirmed formula, just fed coarser candles), each
updated only once its own bucket of 5-minute candles is fully closed
- never on a still-forming, partial bucket, which would let the
indicator "repaint" mid-bar. Reuses
``data.candle_resampler.resample_candles`` unchanged, the same
aggregation this project already uses for building 5-minute candles
from 1-minute Upstox data.
"""

from __future__ import annotations

from datetime import time
from decimal import Decimal

from core.enums import TrendDirection
from data.candle_resampler import resample_candles
from models.market_snapshot import MarketSnapshot
from trend_engine.ut_bot_engine import UTBotEngine, UTBotSignal

_SIGNAL_TO_TREND = {
    UTBotSignal.BUY: TrendDirection.BULLISH,
    UTBotSignal.SELL: TrendDirection.BEARISH,
}

_TIMEFRAME_MINUTES = (15, 30, 60)
_SOURCE_BUCKET_MINUTES = 5


class MultiTimeframeUTBotConfirmation:
    """Feeds 15m/30m/1h buckets (aggregated from 5-minute candles) to
    three independent ``UTBotEngine`` instances, and reports the
    confirmed trend only when all three currently agree.

    Each of the three timeframe engines can be constructor-injected
    directly (matching this codebase's own "constructor-injected
    dependencies only" convention, e.g.
    ``qualification_engine.qualification_exit_engine.QualificationExitEngine``) -
    primarily so tests can substitute a lightweight test double
    instead of needing hours of real candle data to exercise a real
    ``UTBotEngine``'s ATR warm-up. When not supplied, a real
    ``UTBotEngine`` is built from ``key_value``/``atr_period``, applied
    uniformly to whichever timeframe(s) were not injected. Stateful
    across calls by design - construct a fresh instance per trading
    session.
    """

    def __init__(
        self,
        engine_15m: UTBotEngine | None = None,
        engine_30m: UTBotEngine | None = None,
        engine_1h: UTBotEngine | None = None,
        key_value: Decimal = Decimal(1),
        atr_period: int = 10,
        market_open: time = time(9, 15),
    ) -> None:
        self._market_open = market_open
        self._engines: dict[int, UTBotEngine] = {
            15: (
                engine_15m
                if engine_15m is not None
                else UTBotEngine(key_value=key_value, atr_period=atr_period)
            ),
            30: (
                engine_30m
                if engine_30m is not None
                else UTBotEngine(key_value=key_value, atr_period=atr_period)
            ),
            60: (
                engine_1h
                if engine_1h is not None
                else UTBotEngine(key_value=key_value, atr_period=atr_period)
            ),
        }
        self._fed_bucket_count = {minutes: 0 for minutes in _TIMEFRAME_MINUTES}

    def update(self, five_minute_candles: tuple[MarketSnapshot, ...]) -> TrendDirection | None:
        """Feed any newly-completed higher-timeframe buckets implied
        by ``five_minute_candles`` (the full session-so-far series, in
        order), and return the confirmed trend if 15m, 30m, and 1h
        all currently agree, else ``None``.

        Raises:
            core.exceptions.ValidationError: if
                ``resample_candles`` rejects the input (non-candle-mode
                snapshots) - see that function's own docstring.
        """
        for minutes in _TIMEFRAME_MINUTES:
            self._feed_new_buckets(five_minute_candles, minutes)

        positions = tuple(self._engines[minutes].current_position for minutes in _TIMEFRAME_MINUTES)
        if any(position is None for position in positions):
            return None
        if positions[0] is positions[1] is positions[2]:
            assert positions[0] is not None
            return _SIGNAL_TO_TREND[positions[0]]
        return None

    def _feed_new_buckets(
        self, five_minute_candles: tuple[MarketSnapshot, ...], bucket_minutes: int
    ) -> None:
        # bucket_minutes only ever comes from the fixed _TIMEFRAME_MINUTES
        # tuple (15, 30, 60), all positive multiples of _SOURCE_BUCKET_MINUTES
        # by construction - no runtime guard needed for a value this
        # module itself controls.
        candles_per_bucket = bucket_minutes // _SOURCE_BUCKET_MINUTES
        complete_count = len(five_minute_candles) // candles_per_bucket
        already_fed = self._fed_bucket_count[bucket_minutes]
        if complete_count <= already_fed:
            return

        buckets = resample_candles(
            five_minute_candles[: complete_count * candles_per_bucket],
            bucket_minutes,
            self._market_open,
        )
        for bucket in buckets[already_fed:complete_count]:
            self._engines[bucket_minutes].update(bucket)
        self._fed_bucket_count[bucket_minutes] = complete_count

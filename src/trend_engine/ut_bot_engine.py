"""UTBotEngine: replication of the public "UT Bot Alerts" TradingView
indicator (ATR trailing-stop flip), for backtest comparison against
``trend_engine.open_interest_trend_engine.OpenInterestTrendEngine``.

Traceability
------------
Product Owner asked (2026-08-02, chat) to backtest both trend
approaches and decide between them, rather than picking one now. This
is a **publicly documented, third-party technical indicator formula**
(Pine Script, widely published as "UT Bot Alerts" by community author
"yo_adriiiiaan") - implementing it is replicating known, objective
math, not inventing a trading rule the way a fresh entry/exit
threshold would be. No Product Owner evidence is needed for the
formula itself; it is reproduced here as faithfully as possible from
the public source.

Formula (Key Value ``a``, ATR Period ``c``, ``src`` = close):

    xATR = ATR(c)                      # Wilder/RMA smoothing, matching Pine's ta.atr
    nLoss = a * xATR
    xATRTrailingStop[t] =
        max(xATRTrailingStop[t-1], src[t] - nLoss)
            if src[t] > xATRTrailingStop[t-1] and src[t-1] > xATRTrailingStop[t-1]
        min(xATRTrailingStop[t-1], src[t] + nLoss)
            if src[t] < xATRTrailingStop[t-1] and src[t-1] < xATRTrailingStop[t-1]
        src[t] - nLoss   if src[t] > xATRTrailingStop[t-1]
        src[t] + nLoss   otherwise

    BUY  fires the bar src crosses above xATRTrailingStop
    SELL fires the bar src crosses below xATRTrailingStop

**UNTESTED AGAINST A REAL TRADINGVIEW CHART.** This module's own unit
tests verify the formula is internally self-consistent against
hand-computed values, matching this project's existing precedent for
third-party API/formula integrations (e.g.
``run_upstox_backtest.py``'s own "UNTESTED AGAINST THE REAL UPSTOX
API" caveat). Before trusting a comparison run's results, visually
check its Buy/Sell flips for one session against the same indicator
plotted on an actual TradingView chart with the same Key Value/ATR
Period inputs.

Needs the underlying INDEX's own OHLC candle series (not option
premiums) - a different data source than
``backtest.upstox_dataset_builder``, which only fetches per-strike
CE/PE option candles. Fetching that series is a separate, not-yet-
built plumbing task.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot

_DEFAULT_KEY_VALUE = Decimal(1)
_DEFAULT_ATR_PERIOD = 10


class UTBotSignal(Enum):
    """A Buy/Sell flip fired on this candle, or neither."""

    BUY = "BUY"
    SELL = "SELL"


class UTBotEngine:
    """Streaming, one-candle-at-a-time replication of UT Bot Alerts.

    Stateful by construction (running ATR, trailing stop level, prior
    close/position) - construct a fresh instance per session, feed
    candles via :meth:`update` in chronological order.
    """

    def __init__(
        self,
        key_value: Decimal = _DEFAULT_KEY_VALUE,
        atr_period: int = _DEFAULT_ATR_PERIOD,
    ) -> None:
        if atr_period <= 0:
            raise ValidationError("UTBotEngine.atr_period must be greater than 0.")
        self._key_value = key_value
        self._atr_period = atr_period
        self._true_ranges: list[Decimal] = []
        self._atr: Decimal | None = None
        self._prev_close: Decimal | None = None
        self._prev_stop: Decimal | None = None
        self._prev_src: Decimal | None = None
        self._position: UTBotSignal | None = None

    @property
    def current_trailing_stop(self) -> Decimal | None:
        """The most recently computed trailing stop level, or
        ``None`` before the first candle has been fed."""
        return self._prev_stop

    @property
    def current_position(self) -> UTBotSignal | None:
        """The last Buy/Sell flip that fired, persisting across
        candles until the opposite flip fires - mirrors the Pine
        Script indicator's own ``pos`` variable, which carries
        forward rather than resetting to neutral between flips.
        ``None`` until the first flip ever fires."""
        return self._position

    def update(self, candle: MarketSnapshot) -> UTBotSignal | None:
        """Feed one candle (in chronological order) and return the
        Buy/Sell signal it fires, if any.

        Raises:
            core.exceptions.ValidationError: if ``candle`` is not
                candle-mode (OHLC).
        """
        if not candle.is_candle():
            raise ValidationError("UTBotEngine requires candle-mode snapshots (OHLC).")
        assert candle.high is not None and candle.low is not None and candle.close is not None
        src = candle.close

        true_range = self._true_range(candle.high, candle.low)
        self._atr = self._update_atr(true_range)

        if self._prev_stop is None:
            # First candle - no prior trailing stop to compare against
            # yet; seed it (src - nLoss, the "src > prior stop" branch
            # with prior stop treated as 0/na) without emitting a
            # signal.
            n_loss = self._key_value * self._atr
            stop = src - n_loss
            self._prev_stop = stop
            self._prev_src = src
            self._prev_close = src
            return None

        n_loss = self._key_value * self._atr
        prev_stop = self._prev_stop
        prev_src = self._prev_src
        assert prev_src is not None

        if src > prev_stop and prev_src > prev_stop:
            stop = max(prev_stop, src - n_loss)
        elif src < prev_stop and prev_src < prev_stop:
            stop = min(prev_stop, src + n_loss)
        elif src > prev_stop:
            stop = src - n_loss
        else:
            stop = src + n_loss

        signal: UTBotSignal | None = None
        if prev_src <= prev_stop and src > stop:
            signal = UTBotSignal.BUY
        elif prev_src >= prev_stop and src < stop:
            signal = UTBotSignal.SELL

        if signal is not None:
            self._position = signal
        self._prev_stop = stop
        self._prev_src = src
        self._prev_close = src
        return signal

    def _true_range(self, high: Decimal, low: Decimal) -> Decimal:
        if self._prev_close is None:
            return high - low
        return max(
            high - low,
            abs(high - self._prev_close),
            abs(low - self._prev_close),
        )

    def _update_atr(self, true_range: Decimal) -> Decimal:
        if self._atr is None:
            self._true_ranges.append(true_range)
            if len(self._true_ranges) < self._atr_period:
                # Not enough bars yet for a full Wilder seed - approximate
                # with the simple average of what's available so far
                # (Pine's ta.atr also produces a partial/na-influenced
                # value before the period is filled; this is the closest
                # sane behaviour without inventing a different formula).
                return sum(self._true_ranges, Decimal(0)) / len(self._true_ranges)
            return sum(self._true_ranges, Decimal(0)) / self._atr_period
        return (self._atr * (self._atr_period - 1) + true_range) / self._atr_period

"""fetch_underlying_index_candles: the underlying index's own OHLC
candle series (not option premiums) for one session.

Traceability
------------
``backtest.upstox_dataset_builder`` only fetches per-strike CE/PE
option candles - ``trend_engine.ut_bot_engine.UTBotEngine`` needs the
underlying index's own price series for its ATR calculation, a
different Upstox instrument entirely. Reuses the same already-working
``UpstoxCandleSource`` -> ``HistoricalDataProvider`` ->
``resample_candles`` pipeline unchanged, just pointed at the index
instrument key instead of an option contract - no new fetch/parse
logic, matching this project's own precedent of reusing proven
pieces rather than duplicating them.

``NIFTY_50_INSTRUMENT_KEY`` is a fixed, publicly documented Upstox
instrument key (Upstox API reference, "Market Quote" examples) - an
engineering/API-integration fact, not something requiring instrument-
master resolution the way option contracts do (their strike/expiry
combinations change every week; the index itself does not).

UNTESTED AGAINST THE REAL UPSTOX API - same caveat as
``backtest.upstox_dataset_builder`` and ``run_upstox_backtest.py``.
"""

from __future__ import annotations

from datetime import date, time

from data.candle_resampler import resample_candles
from data.historical_data_provider import HistoricalDataProvider
from data.upstox_candle_source import UpstoxCandleSource
from data.upstox_rest_client import RestClient
from models.market_snapshot import MarketSnapshot

NIFTY_50_INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"

_DEFAULT_MARKET_OPEN = time(9, 15)
_DEFAULT_CANDLE_MINUTES = 5


def fetch_underlying_index_candles(
    rest_client: RestClient,
    access_token: str,
    session_date: date,
    instrument_key: str = NIFTY_50_INSTRUMENT_KEY,
    market_open: time = _DEFAULT_MARKET_OPEN,
    candle_minutes: int = _DEFAULT_CANDLE_MINUTES,
) -> tuple[MarketSnapshot, ...]:
    """Fetch and resample one session's underlying index candles.

    Raises:
        core.exceptions.HistoricalDataError: if the fetch/parse fails
            or produces no candles for ``session_date``.
    """
    source = UpstoxCandleSource(
        rest_client=rest_client,
        access_token=access_token,
        instrument_key=instrument_key,
        interval_minutes=1,
        day_from=session_date,
        day_to=session_date,
    )
    dataset = HistoricalDataProvider().load(source, symbol=instrument_key, timeframe="1m")
    return resample_candles(dataset.snapshots, candle_minutes, market_open)

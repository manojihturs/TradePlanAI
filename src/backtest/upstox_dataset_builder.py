"""build_upstox_fixture: assemble a real BacktestFixture from Upstox historical data.

Traceability
------------
Produces exactly the same ``backtest.fixture.BacktestFixture`` shape
``backtest.synthetic_data.build_synthetic_fixture`` does - so
``backtest.runner.BacktestRunner`` runs unchanged against real data.
This module only assembles/aligns data; it computes no trading rule
and invents no threshold - see ``docs/BUSINESS_LOGIC_FLOW.md`` for the
confirmed pipeline this feeds.

UNTESTED AGAINST THE REAL UPSTOX API. Every piece here is unit-tested
with a fake ``RestClient`` (no real network, no real token), but this
module's assumptions about response shape and interval support have
not been verified against a live Upstox account. Before relying on a
run's results, validate a single small fetch manually first (see
``tools/upstox_rest_client.py``'s own docstring).
"""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal

from backtest.fixture import BacktestFixture
from core.exceptions import HistoricalDataError
from data.candle_resampler import resample_candles
from data.historical_data_provider import HistoricalDataProvider
from data.option_chain_dataset import OptionChainCandle, OptionChainDataset
from data.upstox_candle_source import UpstoxCandleSource
from data.upstox_instrument_resolver import UpstoxInstrumentResolver
from data.upstox_rest_client import RestClient
from models.market_snapshot import MarketSnapshot
from models.strike_chain_snapshot import StrikeChainSnapshot
from reference_builder.reference_validator import StrikeCandleInput

_STRIKE_STEP = Decimal(50)
_LADDER_HALF_WIDTH = 6  # 6 ITM + ATM + 6 OTM = 13 strikes, matching ReferenceBuilder.
_DEFAULT_MARKET_OPEN = time(9, 15)
_DEFAULT_CANDLE_MINUTES = 5


def _strikes_around(anchor_strike: Decimal) -> tuple[Decimal, ...]:
    return tuple(
        anchor_strike + (Decimal(i) * _STRIKE_STEP)
        for i in range(-_LADDER_HALF_WIDTH, _LADDER_HALF_WIDTH + 1)
    )


def build_upstox_fixture(
    rest_client: RestClient,
    access_token: str,
    underlying_symbol: str,
    expiry: date,
    anchor_strike: Decimal,
    session_date: date,
    market_open: time = _DEFAULT_MARKET_OPEN,
    candle_minutes: int = _DEFAULT_CANDLE_MINUTES,
) -> BacktestFixture:
    """Fetch and assemble one session's real option-chain data into a
    :class:`~backtest.fixture.BacktestFixture`.

    Raises:
        core.exceptions.HistoricalDataError: if any instrument cannot
            be resolved/fetched, or the strikes' candle timestamps do
            not sufficiently align (see module docstring - this is
            real-world data, gaps are possible).
    """
    strikes = _strikes_around(anchor_strike)
    resolver = UpstoxInstrumentResolver(rest_client)
    instrument_keys = resolver.resolve_option_chain(underlying_symbol, expiry, strikes)

    provider = HistoricalDataProvider()
    ce_by_strike: dict[Decimal, tuple[MarketSnapshot, ...]] = {}
    pe_by_strike: dict[Decimal, tuple[MarketSnapshot, ...]] = {}
    for strike in strikes:
        for side, store in (("CE", ce_by_strike), ("PE", pe_by_strike)):
            instrument_key = instrument_keys[(strike, side)]
            source = UpstoxCandleSource(
                rest_client=rest_client,
                access_token=access_token,
                instrument_key=instrument_key,
                interval_minutes=1,
                day_from=session_date,
                day_to=session_date,
            )
            raw_dataset = provider.load(source, symbol=instrument_key, timeframe="1m")
            store[strike] = resample_candles(raw_dataset.snapshots, candle_minutes, market_open)

    for strike in strikes:
        if not ce_by_strike[strike] or not pe_by_strike[strike]:
            raise HistoricalDataError(
                f"No candles resampled for strike {strike} on {session_date} - "
                "cannot build the first-candle reference input."
            )

    reference_inputs = tuple(
        StrikeCandleInput(
            strike=strike, ce_candle=ce_by_strike[strike][0], pe_candle=pe_by_strike[strike][0]
        )
        for strike in strikes
    )

    common_timestamps = {candle.timestamp for candle in ce_by_strike[anchor_strike][1:]}
    for strike in strikes:
        ce_timestamps = {candle.timestamp for candle in ce_by_strike[strike][1:]}
        pe_timestamps = {candle.timestamp for candle in pe_by_strike[strike][1:]}
        common_timestamps &= ce_timestamps & pe_timestamps

    if not common_timestamps:
        raise HistoricalDataError(
            f"No candle timestamp is present across all {len(strikes)} strikes' CE and PE "
            f"series for {session_date} - cannot build an aligned option-chain dataset."
        )

    ce_index = {
        strike: {candle.timestamp: candle for candle in ce_by_strike[strike]} for strike in strikes
    }
    pe_index = {
        strike: {candle.timestamp: candle for candle in pe_by_strike[strike]} for strike in strikes
    }

    candles = tuple(
        OptionChainCandle(
            timestamp=timestamp,
            strikes=tuple(
                StrikeChainSnapshot(
                    strike=strike, ce=ce_index[strike][timestamp], pe=pe_index[strike][timestamp]
                )
                for strike in strikes
            ),
        )
        for timestamp in sorted(common_timestamps)
    )

    return BacktestFixture(
        session_date=session_date,
        anchor_strike=anchor_strike,
        reference_inputs=reference_inputs,
        dataset=OptionChainDataset(session_date=session_date, candles=candles),
    )

"""Ad hoc comparison: OpenInterestTrendEngine vs UTBotEngine over the
past week's real Upstox data.

NOT part of src/ - a throwaway analysis script, same status as
run_upstox_backtest.py's own "glue script" category, just narrower in
purpose (compare two trend methods candle-by-candle, not run the full
qualification pipeline). Requires UPSTOX_ACCESS_TOKEN in the
environment (never pasted here).
"""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from upstox_rest_client import RequestsRestClient, access_token_from_env  # noqa: E402

from backtest.upstox_index_fetcher import fetch_underlying_index_candles  # noqa: E402
from data.historical_data_provider import HistoricalDataProvider  # noqa: E402
from data.upstox_candle_source import UpstoxCandleSource  # noqa: E402
from data.candle_resampler import resample_candles  # noqa: E402
from core.enums import TrendDirection  # noqa: E402
from core.exceptions import HistoricalDataError  # noqa: E402
from trend_engine.open_interest_trend_engine import OpenInterestTrendEngine  # noqa: E402
from trend_engine.ut_bot_engine import UTBotEngine, UTBotSignal  # noqa: E402

UNDERLYING_SYMBOL = "NIFTY"
ANCHOR_STRIKE = Decimal(24250)  # confirmed Top Strike, reused from run_upstox_backtest.py
SESSION_DATES = [date(2026, 7, 27), date(2026, 7, 28), date(2026, 7, 29), date(2026, 7, 30), date(2026, 7, 31)]


def _fetch_anchor_option_candles(rest_client, access_token, session_date):
    from backtest.upstox_dataset_builder import _strikes_around
    from data.upstox_instrument_resolver import UpstoxInstrumentResolver

    resolver = UpstoxInstrumentResolver(rest_client)
    strikes = _strikes_around(ANCHOR_STRIKE)
    keys = resolver.resolve_option_chain(UNDERLYING_SYMBOL, date(2026, 8, 4), strikes)

    def _side(side):
        source = UpstoxCandleSource(
            rest_client=rest_client,
            access_token=access_token,
            instrument_key=keys[(ANCHOR_STRIKE, side)],
            interval_minutes=1,
            day_from=session_date,
            day_to=session_date,
        )
        dataset = HistoricalDataProvider().load(
            source, symbol=keys[(ANCHOR_STRIKE, side)], timeframe="1m"
        )
        return resample_candles(dataset.snapshots, 5, __import__("datetime").time(9, 15))

    return _side("CE"), _side("PE")


def main() -> None:
    access_token = access_token_from_env()
    rest_client = RequestsRestClient()

    for session_date in SESSION_DATES:
        print(f"\n=== {session_date} ===")
        try:
            index_candles = fetch_underlying_index_candles(rest_client, access_token, session_date)
            ce_candles, pe_candles = _fetch_anchor_option_candles(
                rest_client, access_token, session_date
            )
        except HistoricalDataError as exc:
            print(f"  SKIPPED (data error): {exc}")
            continue

        oi_engine = OpenInterestTrendEngine()
        ut_engine = UTBotEngine()
        session_open_price = None
        session_open_call_oi = None
        session_open_put_oi = None

        rows = []
        n = min(len(index_candles), len(ce_candles), len(pe_candles))
        for i in range(n):
            index_candle = index_candles[i]
            ce_candle = ce_candles[i]
            pe_candle = pe_candles[i]

            if ce_candle.open_interest is None or pe_candle.open_interest is None:
                oi_trend = "NO_OI_DATA"
            else:
                if session_open_price is None:
                    session_open_price = index_candle.close
                    session_open_call_oi = ce_candle.open_interest
                    session_open_put_oi = pe_candle.open_interest
                result = oi_engine.evaluate(
                    session_open_price=session_open_price,
                    current_price=index_candle.close,
                    session_open_call_oi=session_open_call_oi,
                    session_open_put_oi=session_open_put_oi,
                    current_call_oi=ce_candle.open_interest,
                    current_put_oi=pe_candle.open_interest,
                )
                oi_trend = result.value if result else "NONE"

            ut_signal = ut_engine.update(index_candle)
            ut_label = ut_signal.value if ut_signal else "-"

            rows.append(
                (
                    index_candle.timestamp.strftime("%H:%M"),
                    str(index_candle.close),
                    oi_trend,
                    ut_label,
                    str(ut_engine.current_trailing_stop),
                )
            )

        print(f"  {'Time':6} {'Price':>10} {'OI-Trend':10} {'UTBot':6} {'UT-Stop':>10}")
        for row in rows:
            print(f"  {row[0]:6} {row[1]:>10} {row[2]:10} {row[3]:6} {row[4]:>10}")


if __name__ == "__main__":
    main()

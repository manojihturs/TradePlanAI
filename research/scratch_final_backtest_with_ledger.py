"""Final pre-launch verification: full confirmed pipeline against real
Upstox historical data (27-31 July 2026), now also running every
closed position through CapitalLedger for real rupee P&L - the same
CapitalLedger/pipeline wiring run_live_paper_trading.py uses.

NOT part of src/ - same throwaway-analysis status as other
research/scratch_*.py scripts.
"""

from __future__ import annotations

import sys
from dataclasses import replace
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

from backtest.runner import BacktestRunner  # noqa: E402
from backtest.upstox_dataset_builder import build_upstox_fixture  # noqa: E402
from backtest.upstox_index_fetcher import fetch_underlying_index_candles  # noqa: E402
from capital_ledger.capital_ledger import CapitalLedger  # noqa: E402
from core.enums import TrendDirection  # noqa: E402
from core.exceptions import HistoricalDataError  # noqa: E402
from data.option_chain_dataset import OptionChainDataset  # noqa: E402

UNDERLYING_SYMBOL = "NIFTY"
EXPIRY = date(2026, 8, 4)
ANCHOR_STRIKE = Decimal(24250)
SESSION_DATES = [
    date(2026, 7, 27),
    date(2026, 7, 28),
    date(2026, 7, 29),
    date(2026, 7, 30),
    date(2026, 7, 31),
]


def main() -> None:
    access_token = access_token_from_env()
    rest_client = RequestsRestClient()
    ledger = CapitalLedger(starting_capital=Decimal(50000))

    print(f"Starting capital: Rs.{ledger.starting_capital}\n")

    for session_date in SESSION_DATES:
        try:
            fixture = build_upstox_fixture(
                rest_client=rest_client,
                access_token=access_token,
                underlying_symbol=UNDERLYING_SYMBOL,
                expiry=EXPIRY,
                anchor_strike=ANCHOR_STRIKE,
                session_date=session_date,
            )
            index_candles = fetch_underlying_index_candles(rest_client, access_token, session_date)
        except HistoricalDataError as exc:
            print(f"{session_date}: SKIPPED ({exc})")
            continue

        index_by_ts = {c.timestamp: c for c in index_candles}
        common = tuple(c for c in fixture.dataset.candles if c.timestamp in index_by_ts)
        if not common:
            print(f"{session_date}: SKIPPED (no common timestamps)")
            continue
        aligned_index = tuple(index_by_ts[c.timestamp] for c in common)
        fixture = replace(
            fixture,
            dataset=OptionChainDataset(session_date=fixture.dataset.session_date, candles=common),
        )

        result = BacktestRunner().run(
            fixture, TrendDirection.BULLISH, underlying_index_candles=aligned_index
        )

        session_start_balance = ledger.balance
        for position in result.qualification_positions:
            ledger.record_position(position)
        session_pnl = ledger.balance - session_start_balance

        print(
            f"{session_date}: {len([p for p in result.qualification_positions if p.exit_price is not None])} "
            f"recorded trades, session P&L Rs.{session_pnl}, running balance Rs.{ledger.balance}"
        )

    print(f"\nFinal: {ledger.trade_count} trades, realized P&L Rs.{ledger.realized_pnl}, "
          f"balance Rs.{ledger.balance} (started Rs.{ledger.starting_capital})")


if __name__ == "__main__":
    main()

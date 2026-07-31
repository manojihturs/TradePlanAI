"""Glue script: runs the confirmed src/ pipeline (docs/BUSINESS_LOGIC_FLOW.md)
against real Upstox historical option-chain data for one session.

Traceability
------------
NOT part of the src/ package - only the composition root wiring
together tools/upstox_rest_client.py (real HTTP), backtest.upstox_dataset_builder
(fetch + assemble), and backtest.runner.BacktestRunner (the confirmed
pipeline itself, already used by backtest.synthetic_data for the
not-real-data proof-of-plumbing run).

UNTESTED AGAINST THE REAL UPSTOX API. Every piece this wires together
is unit-tested with a fake transport, but nobody has run this exact
script against a live Upstox account yet. Before trusting a full run:

1. Set the UPSTOX_ACCESS_TOKEN environment variable yourself (never
   paste the token into this file, a command-line argument, or a
   chat/AI session - command-line args are visible in shell history
   and process listings).
2. Run this once with a short, recent SESSION_DATE and watch for
   errors - a resolution failure (missing contracts) or an alignment
   failure (no common candle timestamps) will raise a clear
   core.exceptions.HistoricalDataError explaining what went wrong.
3. Only then trust the trade-level output.

Scope: Qualification, Stop Loss, and Trailing Stop remain blocked
pending Product Owner evidence (see research/incoming/*_intake_*.md).
This backtest can only ever close a trade via the Target or Competitor
leg - see backtest.null_engines for why. No P&L is computed or
displayed - see backtest.report's own docstring for why.
"""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TOOLS = Path(__file__).resolve().parent / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from upstox_rest_client import RequestsRestClient, access_token_from_env

from backtest.report import summarize_backtest
from backtest.runner import BacktestRunner
from backtest.upstox_dataset_builder import build_upstox_fixture

# Edit these for the session you want to backtest.
UNDERLYING_SYMBOL = "NIFTY"
EXPIRY = date(2026, 8, 4)  # NIFTY weeklies expire on Tuesdays - verified against real Upstox data
ANCHOR_STRIKE = Decimal(24250)  # confirmed Top Strike for SESSION_DATE via the real formula
SESSION_DATE = date(2026, 7, 30)


def main() -> None:
    access_token = access_token_from_env()
    rest_client = RequestsRestClient()

    print(f"Fetching {UNDERLYING_SYMBOL} option-chain data for {SESSION_DATE}...")
    fixture = build_upstox_fixture(
        rest_client=rest_client,
        access_token=access_token,
        underlying_symbol=UNDERLYING_SYMBOL,
        expiry=EXPIRY,
        anchor_strike=ANCHOR_STRIKE,
        session_date=SESSION_DATE,
    )
    print(f"Fetched {len(fixture.dataset.candles)} candles across 13 strikes.")

    print("Running the confirmed pipeline (Weekly Future -> ... -> Exit)...")
    result = BacktestRunner().run(fixture)

    summary = summarize_backtest(result.trade_history.get_all(), len(result.business_results))
    print()
    print(f"Candles processed: {summary.candles_processed}")
    print(f"Trades completed:  {summary.total_trades}")
    for reason, count in summary.exit_reason_counts.items():
        print(f"  {reason.value}: {count}")
    if summary.average_duration is not None:
        print(f"Average trade duration: {summary.average_duration}")

    failed = [r for r in result.business_results if not r.success]
    if failed:
        print(
            f"\n{len(failed)} candle(s) did not complete successfully - see BusinessResult.error."
        )

    print("\nNo P&L is shown - see backtest.report's own docstring for why.")


if __name__ == "__main__":
    main()

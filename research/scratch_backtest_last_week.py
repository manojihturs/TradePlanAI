"""Ad hoc: full-week backtest (27-31 July 2026) using the confirmed
pipeline with real UT Bot + 15m/30m/1h multi-timeframe-confirmed
trend, against real Upstox data.

NOT part of src/ - same throwaway-analysis status as
run_upstox_backtest.py / scratch_compare_trend_methods.py.
"""

from __future__ import annotations

import sys
from datetime import date, time
from decimal import Decimal
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from upstox_rest_client import RequestsRestClient, access_token_from_env  # noqa: E402

from backtest.fixture import BacktestFixture  # noqa: E402
from backtest.runner import BacktestRunner  # noqa: E402
from backtest.upstox_dataset_builder import build_upstox_fixture  # noqa: E402
from backtest.upstox_index_fetcher import fetch_underlying_index_candles  # noqa: E402
from core.enums import TrendDirection  # noqa: E402
from core.exceptions import HistoricalDataError  # noqa: E402
from data.option_chain_dataset import OptionChainDataset  # noqa: E402
from dataclasses import replace  # noqa: E402

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

    grand_total_trades = 0
    grand_total_captured = Decimal(0)

    for session_date in SESSION_DATES:
        print(f"\n{'=' * 90}\n{session_date} (weekday={session_date.strftime('%A')})\n{'=' * 90}")
        try:
            fixture: BacktestFixture = build_upstox_fixture(
                rest_client=rest_client,
                access_token=access_token,
                underlying_symbol=UNDERLYING_SYMBOL,
                expiry=EXPIRY,
                anchor_strike=ANCHOR_STRIKE,
                session_date=session_date,
            )
            index_candles = fetch_underlying_index_candles(rest_client, access_token, session_date)
        except HistoricalDataError as exc:
            print(f"  SKIPPED (data error): {exc}")
            continue

        index_by_ts = {c.timestamp: c for c in index_candles}
        common_option_candles = tuple(
            c for c in fixture.dataset.candles if c.timestamp in index_by_ts
        )
        aligned_index_candles = tuple(index_by_ts[c.timestamp] for c in common_option_candles)
        if not common_option_candles:
            print("  SKIPPED (no common timestamps between option and index data)")
            continue
        fixture = replace(
            fixture,
            dataset=OptionChainDataset(
                session_date=fixture.dataset.session_date, candles=common_option_candles
            ),
        )
        index_candles = aligned_index_candles
        print(f"  Aligned candles: {len(common_option_candles)}")

        result = BacktestRunner().run(
            fixture, TrendDirection.BULLISH, underlying_index_candles=index_candles
        )

        positions = result.qualification_positions
        print(f"  Qualification trades: {len(positions)}")
        if not positions:
            print("  (no trend confirmation reached this session - no trades)")
            continue

        print(
            f"  {'Anchor':7} {'Side':4} {'Strike':>8} {'Entry':>7} {'Exit':>7} "
            f"{'Open':>6} {'Close':>6} {'Reason':14} {'Captured':>9}"
        )
        session_captured = Decimal(0)
        for p in positions:
            entry = p.entry_level
            # Both CE and PE positions are long the premium bought at
            # entry (never short) - Target/SL/Competitor are always
            # numerically above/below entry respectively regardless of
            # side (see QualificationEngine's own confirmed column
            # formulas), so captured = exit - entry uniformly, no
            # side-based sign flip.
            captured = (p.exit_price - entry) if p.exit_price is not None else Decimal(0)
            session_captured += captured
            print(
                f"  {p.anchor_role.value:7} {p.side.value:4} {p.entry_strike!s:>8} "
                f"{entry!s:>7} {(p.exit_price if p.exit_price is not None else '-')!s:>7} "
                f"{p.opened_at.strftime('%H:%M'):>6} "
                f"{(p.closed_at.strftime('%H:%M') if p.closed_at else '-'):>6} "
                f"{(p.exit_reason.value if p.exit_reason else '-'):14} {captured!s:>9}"
            )
        print(f"  Session net captured (premium points, before costs): {session_captured}")
        grand_total_trades += len(positions)
        grand_total_captured += session_captured

    print(f"\n{'=' * 90}")
    print(f"WEEK TOTAL: {grand_total_trades} trades, {grand_total_captured} premium points captured")
    print("(Uses each position's real exit_price now, incl. Trailing Stop; no brokerage/tax cost model exists.)")


if __name__ == "__main__":
    main()

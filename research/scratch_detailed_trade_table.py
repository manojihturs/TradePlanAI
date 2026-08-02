"""Ad hoc: full trade-by-trade detail table (27-31 July 2026), the
exact columns requested: Entry time, Price, Target, SL, TSL, CE/PE,
Entry Premium, Competitor Strike, Competitor Price, Exit time, Exit
price, Captured points, Total, Entry reason, Exit Reason.

NOT part of src/ - same throwaway-analysis status as the other
research/scratch_*.py scripts.
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
_ACTIVATION_POINTS = Decimal(3)

_COLS = (
    "Date", "Entry time", "Price", "Target", "SL", "TSL", "CE/PE",
    "Entry Premium", "Comp Strike", "Comp Price", "Exit time",
    "Exit price", "Captured", "Total", "Entry reason", "Exit Reason",
)


def main() -> None:
    access_token = access_token_from_env()
    rest_client = RequestsRestClient()

    rows: list[list[str]] = []
    running_total = Decimal(0)

    for session_date in SESSION_DATES:
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
        except HistoricalDataError:
            continue

        index_by_ts = {c.timestamp: c for c in index_candles}
        common = tuple(c for c in fixture.dataset.candles if c.timestamp in index_by_ts)
        if not common:
            continue
        aligned_index = tuple(index_by_ts[c.timestamp] for c in common)
        fixture = replace(
            fixture,
            dataset=OptionChainDataset(session_date=fixture.dataset.session_date, candles=common),
        )
        underlying_by_ts = {c.timestamp: c.close for c in aligned_index}

        result = BacktestRunner().run(
            fixture, TrendDirection.BULLISH, underlying_index_candles=aligned_index
        )

        for p in result.qualification_positions:
            captured = (p.exit_price - p.entry_level) if p.exit_price is not None else Decimal(0)
            running_total += captured
            tsl_level = p.entry_level + _ACTIVATION_POINTS
            entry_price = underlying_by_ts.get(p.opened_at, None)
            rows.append(
                [
                    session_date.isoformat(),
                    p.opened_at.strftime("%H:%M"),
                    str(entry_price) if entry_price is not None else "-",
                    str(p.target_level),
                    str(p.stop_loss_level),
                    str(tsl_level),
                    p.side.value,
                    str(p.entry_level),
                    "N/A",  # Competitor Strike - not tracked, see script header
                    str(p.competitor_exit_level),
                    p.closed_at.strftime("%H:%M") if p.closed_at else "-",
                    str(p.exit_price) if p.exit_price is not None else "-",
                    str(captured),
                    str(running_total),
                    f"{p.anchor_role.value} dual-crossover",
                    p.exit_reason.value if p.exit_reason else "-",
                ]
            )

    widths = [max(len(_COLS[i]), *(len(r[i]) for r in rows)) for i in range(len(_COLS))]
    header = " | ".join(c.ljust(w) for c, w in zip(_COLS, widths, strict=True))
    print(header)
    print("-" * len(header))
    for r in rows:
        print(" | ".join(v.ljust(w) for v, w in zip(r, widths, strict=True)))
    print(f"\nTotal trades: {len(rows)}  |  Week net captured: {running_total} pts (before costs)")


if __name__ == "__main__":
    main()

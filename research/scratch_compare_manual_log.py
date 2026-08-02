"""Ad hoc: compare the Product Owner's manually-traded log (29/30/31
July 2026) against the simulated pipeline, running BULLISH and
BEARISH separately per session (bypassing UT Bot) so the trend
disagreement found earlier is isolated out - this checks the entry/
target/SL/competitor mechanics on their own.

NOT part of src/ - same throwaway-analysis status as other
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

from backtest.runner import BacktestRunner  # noqa: E402
from backtest.upstox_dataset_builder import build_upstox_fixture  # noqa: E402
from core.enums import TrendDirection  # noqa: E402
from core.exceptions import HistoricalDataError  # noqa: E402

UNDERLYING_SYMBOL = "NIFTY"
EXPIRY = date(2026, 8, 4)
ANCHOR_STRIKE = Decimal(24250)

# (date, manual_entry_time, anchor_label, side, entry, target, sl, comp) from the PO's log.
MANUAL_TRADES = [
    (date(2026, 7, 29), "11:05", "24200-TOP", "CE", "152.05", "179.7", "128", "117.62"),
    (date(2026, 7, 29), "09:20", "24150-BOTTOM", "CE", "165.8", "189.6", "137.3", "116"),
    (date(2026, 7, 29), "13:05", "24150-BOTTOM", "CE", "189.6", "221.35", "165.8", "92.5"),
    (date(2026, 7, 30), "09:20", "24250-TOP", "CE", "120.1", "145.2", "98.3", "121.5"),
    (date(2026, 7, 30), "10:40", "24250-TOP", "CE", "98.3", "120.1", "80", "121.5"),
    (date(2026, 7, 30), "13:10", "24250-TOP", "PE", "103.2", "121.5", "74.75", "120.1"),
    (date(2026, 7, 30), "14:45", "24250-TOP", "CE", "120.1", "145.2", "98.3", "103.2"),
    (date(2026, 7, 30), "10:40", "24150-BOTTOM", "CE", "159", "189", "131.6", "87"),
    (date(2026, 7, 30), "13:10", "24150-BOTTOM", "PE", "67.05", "87", "50.5", "189"),
    (date(2026, 7, 31), "09:30", "24400-TOP", "PE", "145", "180", "86.85", "64.75"),
    (date(2026, 7, 31), "09:30", "24300-BOTTOM", "PE", "92.75", "121", "71.15", "123"),
    (date(2026, 7, 31), "10:40", "24300-BOTTOM", "CE", "123", "139.95", "98.7", "71.15"),
]


def main() -> None:
    access_token = access_token_from_env()
    rest_client = RequestsRestClient()

    for session_date, entry_time, anchor_label, side, entry, target, sl, comp in MANUAL_TRADES:
        try:
            fixture = build_upstox_fixture(
                rest_client=rest_client,
                access_token=access_token,
                underlying_symbol=UNDERLYING_SYMBOL,
                expiry=EXPIRY,
                anchor_strike=ANCHOR_STRIKE,
                session_date=session_date,
            )
        except HistoricalDataError as exc:
            print(f"{session_date} SKIP: {exc}")
            continue

        trend = TrendDirection.BULLISH if side == "CE" else TrendDirection.BEARISH
        result = BacktestRunner().run(fixture, trend)

        matches = [
            p
            for p in result.qualification_positions
            if p.side.value == side and p.entry_level == Decimal(entry)
        ]

        print(f"\n{session_date} {entry_time} {anchor_label} {side} entry={entry} target={target} sl={sl} comp={comp}")
        print(f"  Manual log expects this exact entry_level={entry} to qualify under {trend.value}.")
        if not matches:
            print(f"  SIMULATED: NO MATCH - no {side} position opened at entry_level={entry} this session.")
        else:
            for p in matches:
                print(
                    f"  SIMULATED: entry_strike={p.entry_strike} opened={p.opened_at.strftime('%H:%M')} "
                    f"target={p.target_level} sl={p.stop_loss_level} comp={p.competitor_exit_level} "
                    f"closed={p.closed_at.strftime('%H:%M') if p.closed_at else '-'} "
                    f"exit_price={p.exit_price} reason={p.exit_reason.value if p.exit_reason else '-'}"
                )


if __name__ == "__main__":
    main()

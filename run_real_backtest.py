"""Glue script: runs the strategy/ package (Modules 1-7) against real
historical data for one session, fetched via the existing orb_common
Upstox helpers. This script is NOT part of the strategy/ package - it
is only the network-fetching adapter, since the package itself is
required to have no network dependency of its own.
"""

import sys
from datetime import date, datetime

sys.path.insert(0, r"C:\Code\Trade\TradePlan")

import orb_common as oc
from strategy.level_capture import capture_levels
from strategy.premium_mapping import build_premium_mapping
from strategy.entry_signal import Candle as StrategyCandle
from strategy.replay_engine import run_replay, format_summary
from strategy.paper_trading import PaperTradingEngine

SESSION_DATE = date(2026, 7, 22)
STRIKE_GAP = 50
NUM_STRIKES = 6


def main() -> None:
    row = oc.db().execute(
        "SELECT expiry FROM orb_summary WHERE session_date=?", (SESSION_DATE.isoformat(),)
    ).fetchone()
    if not row:
        raise SystemExit(f"No capture found for {SESSION_DATE} in orb_levels.db")
    expiry = date.fromisoformat(row[0])

    spot_open = oc.get_spot_open_915(SESSION_DATE)
    print(f"Spot open (09:15): {spot_open}")

    # fetch_first_candle: works for ANY strike, not just the ones already
    # captured in orb_levels.db - resolves the contract live via the
    # instrument master and fetches its first 5-min candle. Needed both
    # for Module 1's initial +/-6 capture AND for Module 8's on-demand
    # ladder expansion beyond that range.
    def fetch_first_candle(strike: int, side: str):
        chain = oc.resolve_option_chain(expiry, strike, gap=STRIKE_GAP, n=0)
        instrument_key = chain[(strike, side)]
        candles_1m = oc.fetch_historical_candles(instrument_key, 1, SESSION_DATE, SESSION_DATE)
        first = oc.first_5min_candle(oc.resample(candles_1m, oc.CANDLE_MINUTES), SESSION_DATE)
        if first is None:
            raise RuntimeError(f"no first-5min candle available for strike {strike} {side}")
        return (first.open, first.high, first.low, first.close)

    capture = capture_levels(
        session_date=SESSION_DATE, spot_open=spot_open, strike_gap=STRIKE_GAP,
        num_strikes=NUM_STRIKES, fetch_first_candle=fetch_first_candle,
    )
    print(f"ATM={capture.atm}  Top={capture.top_strike:.2f}  Bottom={capture.bottom_strike:.2f}")

    # 3. Module 2: Premium Mapping.
    mapping = build_premium_mapping(capture, strike_gap=STRIKE_GAP)
    print(f"Top anchor (rounded): {mapping.top_strike_rounded}  "
          f"Bottom anchor (rounded): {mapping.bottom_strike_rounded}")

    # 4. Fetch the FULL day's 5-min candle series for every captured
    #    strike's CE and PE - the real market data the replay walks
    #    through one candle at a time.
    strikes = sorted(capture.levels.keys())
    ce_series = {}
    pe_series = {}
    for strike in strikes:
        chain = oc.resolve_option_chain(expiry, strike, gap=STRIKE_GAP, n=0)
        ce_key = chain[(strike, "CE")]
        pe_key = chain[(strike, "PE")]

        ce_candles = oc.resample(oc.fetch_historical_candles(ce_key, 1, SESSION_DATE, SESSION_DATE),
                                  oc.CANDLE_MINUTES)
        pe_candles = oc.resample(oc.fetch_historical_candles(pe_key, 1, SESSION_DATE, SESSION_DATE),
                                  oc.CANDLE_MINUTES)
        ce_series[strike] = {c.ts: StrategyCandle(c.open, c.high, c.low, c.close) for c in ce_candles}
        pe_series[strike] = {c.ts: StrategyCandle(c.open, c.high, c.low, c.close) for c in pe_candles}
        print(f"  fetched strike {strike}: {len(ce_series[strike])} CE candles, "
              f"{len(pe_series[strike])} PE candles")

    # 5. Module 7: Replay Engine - runs Modules 3-6 one candle at a time.
    #    Module 8 (ladder expansion) is enabled by passing capture/
    #    strike_gap/fetch_first_candle - an edge-strike entry needing a
    #    rung beyond the initial +/-6 range fetches it live rather than
    #    the trade being skipped.
    result = run_replay(
        mapping, ce_series, pe_series,
        capture=capture, strike_gap=STRIKE_GAP, fetch_first_candle=fetch_first_candle,
    )
    print()
    print(format_summary(result))

    # 6. Export to Excel. run_replay() already used Module 6 internally to
    #    build each Trade; this script only needs openpyxl directly to
    #    write the ALREADY-BUILT trades out (not re-run Module 6's public
    #    API, which takes a ClosedTrade+ExitLevels pair, not a Trade).
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Paper Trades"
    ws.append(["Date", "Time", "Side", "Entry", "Exit", "Reason", "Target", "Stop Loss", "PnL"])
    for t in result.trades:
        ws.append([t.trade_date.isoformat(), t.trade_time.isoformat(), t.side.value,
                   t.entry, t.exit, t.reason, t.target, t.stop_loss, t.pnl])
    out_path = "real_backtest_20260722.xlsx"
    wb.save(out_path)
    print(f"\nExported to {out_path}")


if __name__ == "__main__":
    main()

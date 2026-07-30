"""Glue script: connects strategy/live_paper_trading.py (Module 11) to the
REAL live Upstox feed for today's session. NOT part of the strategy/
package - only the network adapter, per every other module's no-network-
dependency design. Paper trading only - no real orders are ever placed
(this script never calls any order-placement endpoint).
"""

import logging
import sys
import time as systime
from datetime import date, datetime, time as dtime

sys.path.insert(0, r"C:\Code\Trade\TradePlan")

import orb_common as oc
from strategy.entry_signal import Candle as StrategyCandle
from strategy.level_capture import capture_levels
from strategy.premium_mapping import build_premium_mapping
from strategy.live_paper_trading import (
    CapitalTracker,
    LivePaperTradingEngine,
    export_end_of_day_excel,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                     handlers=[logging.StreamHandler(),
                               logging.FileHandler("live_paper_trading.log")])
logger = logging.getLogger("live_paper_trading")

STRIKE_GAP = 50
NUM_STRIKES = 6
CAPTURE_TIME = dtime(9, 20)
SQUARE_OFF = dtime(15, 25)   # last tradeable candle close, matches existing SQUARE_OFF convention
POLL_SECONDS = 20


def wait_until(target_time: dtime) -> None:
    while True:
        now = datetime.now(oc.IST).time()
        if now >= target_time:
            return
        systime.sleep(5)


def main() -> None:
    session_date = date.today()
    logger.info("Market Open: waiting for session %s", session_date)

    wait_until(dtime(9, 15))
    logger.info("Market Open confirmed for %s", session_date)

    wait_until(CAPTURE_TIME)
    logger.info("Opening range window closed (09:20) - beginning capture")

    row = oc.db().execute(
        "SELECT expiry FROM orb_summary WHERE session_date=?", (session_date.isoformat(),)
    ).fetchone()
    if row:
        expiry = date.fromisoformat(row[0])
    else:
        # No pre-existing capture row for today yet - resolve nearest weekly
        # expiry via the instrument master itself (orb_common.get_nearest_expiry),
        # the same correct logic orb_auto.py's live path already uses. The
        # earlier "assume Thursday" guess was wrong (it picked a date with no
        # 23650 strike listed) - this reads real expiry dates from the master
        # instead of assuming a weekday.
        expiry = oc.get_nearest_expiry(session_date)
    logger.info("Using expiry %s", expiry)

    def fetch_first_candle(strike: int, side: str):
        chain = oc.resolve_option_chain(expiry, strike, gap=STRIKE_GAP, n=0)
        instrument_key = chain[(strike, side)]
        candles_1m = oc.fetch_intraday_candles(instrument_key, 1)
        first = oc.first_5min_candle(oc.resample(candles_1m, oc.CANDLE_MINUTES), session_date)
        if first is None:
            raise RuntimeError(f"no first-5min candle yet for strike {strike} {side}")
        return (first.open, first.high, first.low, first.close)

    spot_open = oc.get_spot_open_915(session_date)
    capture = capture_levels(session_date=session_date, spot_open=spot_open, strike_gap=STRIKE_GAP,
                              num_strikes=NUM_STRIKES, fetch_first_candle=fetch_first_candle)
    mapping = build_premium_mapping(capture, strike_gap=STRIKE_GAP)
    logger.info("Top/Bottom Calculated: ATM=%d Top=%.2f (anchor %d) Bottom=%.2f (anchor %d)",
                capture.atm, capture.top_strike, mapping.top_strike_rounded,
                capture.bottom_strike, mapping.bottom_strike_rounded)

    capital = CapitalTracker(initial_capital=50_000.0)
    engine = LivePaperTradingEngine(
        session_date=session_date, capture=capture, mapping=mapping,
        strike_gap=STRIKE_GAP, fetch_first_candle=fetch_first_candle, capital=capital,
    )

    strikes = sorted(capture.levels.keys())
    instrument_keys = {}
    for strike in strikes:
        chain = oc.resolve_option_chain(expiry, strike, gap=STRIKE_GAP, n=0)
        instrument_keys[strike] = {"CE": chain[(strike, "CE")], "PE": chain[(strike, "PE")]}

    processed_ts = set()

    logger.info("Beginning live monitoring loop (poll every %ds, until %s)", POLL_SECONDS, SQUARE_OFF)
    while True:
        now = datetime.now(oc.IST)
        if now.time() >= SQUARE_OFF:
            logger.info("Square-off time reached - stopping live monitoring")
            break

        try:
            ce_by_strike = {}
            pe_by_strike = {}
            for strike in strikes:
                ce_1m = oc.fetch_intraday_candles(instrument_keys[strike]["CE"], 1)
                pe_1m = oc.fetch_intraday_candles(instrument_keys[strike]["PE"], 1)
                ce_5m = oc.resample(ce_1m, oc.CANDLE_MINUTES)
                pe_5m = oc.resample(pe_1m, oc.CANDLE_MINUTES)
                ce_by_strike[strike] = {c.ts: StrategyCandle(c.open, c.high, c.low, c.close) for c in ce_5m}
                pe_by_strike[strike] = {c.ts: StrategyCandle(c.open, c.high, c.low, c.close) for c in pe_5m}

            all_new_ts = sorted({
                ts for s in ce_by_strike.values() for ts in s if ts not in processed_ts
            } | {
                ts for s in pe_by_strike.values() for ts in s if ts not in processed_ts
            })

            for ts in all_new_ts:
                if ts.time() < CAPTURE_TIME:
                    continue   # never trade on the 09:15 opening-range candle itself
                ce_candles = {k: v[ts] for k, v in ce_by_strike.items() if ts in v}
                pe_candles = {k: v[ts] for k, v in pe_by_strike.items() if ts in v}
                engine.on_candle_close(ts, ce_candles, pe_candles)
                processed_ts.add(ts)

            try:
                spot_price = oc.get_spot_ltp()
            except Exception:
                spot_price = None
            snap = engine.dashboard_snapshot(now, spot_price)
            logger.info(
                "DASHBOARD time=%s spot=%s top=%d bottom=%d open_trade=%s avail_capital=%.2f "
                "running_pnl=%.2f trades=%d win%%=%.1f open_positions=%d",
                snap.current_time.strftime("%H:%M:%S"), snap.spot_price, snap.top_strike, snap.bottom_strike,
                (f"{snap.current_open_trade.side.value}@{snap.current_open_trade.strike}"
                 if snap.current_open_trade else "none"),
                snap.available_capital, snap.running_pnl, snap.todays_trades, snap.win_pct,
                snap.open_positions,
            )
        except Exception as exc:
            logger.error("Poll iteration failed (continuing): %s", exc)

        systime.sleep(POLL_SECONDS)

    logger.info(engine.end_of_day_summary())
    out_path = export_end_of_day_excel(engine, f"live_paper_trading_{session_date.isoformat()}.xlsx")
    logger.info("End-of-day report exported to %s", out_path)


if __name__ == "__main__":
    main()

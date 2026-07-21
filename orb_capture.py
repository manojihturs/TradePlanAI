# orb_capture.py - run at 09:21 IST (or any time after, or for a past date).
# Captures the 09:15 5-min candle for ATM +/- NUM_STRIKES CE & PE,
# computes SP High/Low via put-call parity, stores everything in SQLite.
#
# Usage:
#   python orb_capture.py --expiry 2026-07-28                # today, live
#   python orb_capture.py --expiry 2026-07-28 --date 2026-07-21 --atm 24200
#     (--atm required for past dates since we can't know 09:15 spot then;
#      or give --spot to auto-round)

import argparse
from datetime import date, datetime, timedelta
from orb_common import (IST, STRIKE_GAP, NUM_STRIKES, nearest_strike,
                        resolve_option_chain, get_spot_ltp,
                        fetch_intraday_candles, fetch_historical_candles,
                        first_5min_candle, db, alert)

def capture(session_date, expiry, atm):
    chain = resolve_option_chain(expiry, atm)
    is_today = (session_date == datetime.now(IST).date())
    conn = db()
    levels = {}

    for (strike, side), ikey in sorted(chain.items()):
        if is_today:
            candles = fetch_intraday_candles(ikey, 5)
        else:
            candles = fetch_historical_candles(ikey, 5, session_date, session_date)
        c = first_5min_candle(candles, session_date)
        if c is None:
            alert("WARN no 09:15 candle for %d%s (%s)" % (strike, side, ikey))
            continue
        levels[(strike, side)] = c
        conn.execute("""INSERT OR REPLACE INTO orb_levels VALUES (?,?,?,?,?,?,?,?,?)""",
                     (session_date.isoformat(), strike, side, ikey,
                      c.open, c.high, c.low, c.close, c.volume))

    atm_ce = levels.get((atm, "CE"))
    atm_pe = levels.get((atm, "PE"))
    if not atm_ce or not atm_pe:
        raise RuntimeError("ATM CE/PE first candle missing - cannot compute SP zone.")

    # Put-call parity on the first candle (your Excel, automated):
    fut_high = atm + atm_ce.high - atm_pe.low
    fut_low  = atm + atm_ce.low  - atm_pe.high
    sp_high  = nearest_strike(fut_high)
    sp_low   = nearest_strike(fut_low)

    conn.execute("""INSERT OR REPLACE INTO orb_summary VALUES (?,?,?,?,?,?,?,?)""",
                 (session_date.isoformat(), atm, expiry.isoformat(),
                  fut_high, fut_low, sp_high, sp_low,
                  datetime.now(IST).isoformat()))
    conn.commit()

    alert("ORB captured %s | ATM %d | FutRange %.2f-%.2f | SP zone %d-%d | %d contracts"
          % (session_date, atm, fut_low, fut_high, sp_low, sp_high, len(levels)))
    return sp_low, sp_high, fut_low, fut_high

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--expiry", required=True, help="YYYY-MM-DD")
    p.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    p.add_argument("--atm", type=int, default=None)
    p.add_argument("--spot", type=float, default=None)
    a = p.parse_args()

    session = date.fromisoformat(a.date) if a.date else datetime.now(IST).date()
    expiry  = date.fromisoformat(a.expiry)

    if a.atm:
        atm = a.atm
    elif a.spot:
        atm = nearest_strike(a.spot)
    elif session == datetime.now(IST).date():
        atm = nearest_strike(get_spot_ltp())
    else:
        raise SystemExit("Past date: provide --atm or --spot.")

    capture(session, expiry, atm)

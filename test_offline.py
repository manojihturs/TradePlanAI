# test_offline.py - exercises orb_signal's parity math and state machine
# with synthetic candles, with no network / Upstox token required.
# Run: python test_offline.py

import os, tempfile
from datetime import datetime, date

# Point the DB at a throwaway file before importing orb_common.
os.environ.setdefault("UPSTOX_ACCESS_TOKEN", "dummy-not-used-offline")

import orb_common
orb_common.DB_PATH = os.path.join(tempfile.gettempdir(), "orb_test.db")
if os.path.exists(orb_common.DB_PATH):
    os.remove(orb_common.DB_PATH)

from orb_common import IST, Candle, db, nearest_strike
from orb_signal import DayState, on_candle_close, ladder_lines

SESSION = date(2026, 7, 21)
ATM = 24200

def ts(h, m):
    return datetime(2026, 7, 21, h, m, tzinfo=IST)

def seed_levels(conn):
    # ATM CE/PE first-candle levels matching the Jul 21 Excel example from the chat.
    rows = [
        (ATM, "CE", "NSE_FO|ATMCE", 90, 114.6, 47.1, 100, 1000),
        (ATM, "PE", "NSE_FO|ATMPE", 50, 69,   29.15, 60, 1000),
        (ATM - 50, "CE", "NSE_FO|ITM1CE", 130, 160, 90, 140, 1000),
        (ATM + 50, "PE", "NSE_FO|OTM1PE", 30, 45, 15, 35, 1000),
    ]
    for strike, side, ikey, o, h, l, c, v in rows:
        conn.execute("INSERT OR REPLACE INTO orb_levels VALUES (?,?,?,?,?,?,?,?,?)",
                     (SESSION.isoformat(), strike, side, ikey, o, h, l, c, v))
    fut_high = ATM + 114.6 - 29.15   # 24285.45
    fut_low  = ATM + 47.1 - 69       # 24178.10
    conn.execute("INSERT OR REPLACE INTO orb_summary VALUES (?,?,?,?,?,?,?,?)",
                 (SESSION.isoformat(), ATM, "2026-07-28", fut_high, fut_low,
                  nearest_strike(fut_high), nearest_strike(fut_low),
                  datetime.now(IST).isoformat()))
    conn.commit()

def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print("[%s] %s" % (status, label))
    assert cond, label

def main():
    conn = db()
    seed_levels(conn)

    row = conn.execute("SELECT sp_high, sp_low FROM orb_summary WHERE session_date=?",
                       (SESSION.isoformat(),)).fetchone()
    sp_high, sp_low = row
    check("SP zone computed as 24200-24300", (sp_low, sp_high) == (24200, 24300))

    levels = {}
    for strike, side, ikey, fh, flo in conn.execute(
            "SELECT strike, side, instrument_key, first_high, first_low "
            "FROM orb_levels WHERE session_date=?", (SESSION.isoformat(),)):
        levels[(strike, side)] = {"key": ikey, "high": fh, "low": flo}

    lines = ladder_lines(levels, ATM, "CE")
    check("ladder_lines returns ITM1 CE high for CE side", lines == [160])

    # --- NEUTRAL: implied spot inside zone -> no trade
    st = DayState()
    ce_flat = Candle(ts(10, 0), 100, 100, 95, 100, 10)
    pe_flat = Candle(ts(10, 0), 60, 60, 55, 60, 10)
    on_candle_close(ts(10, 0), ce_flat, pe_flat, ATM, sp_high, sp_low, levels, st, conn, SESSION)
    check("NEUTRAL state takes no trade", st.position is None and st.signals == 0)

    # --- CE_WINS: implied spot > sp_high, CE close > its 9:15 high (114.6), PE close < its low (29.15)
    ce_break = Candle(ts(10, 30), 100, 130, 100, 120, 10)   # close 120 > 114.6
    pe_break = Candle(ts(10, 30), 25, 25, 20, 22, 10)       # close 22 < 29.15
    # implied spot = 24200 + 120 - 22 = 24298 -> > sp_high(24300)? not quite; bump CE
    ce_break = Candle(ts(10, 30), 100, 140, 100, 130, 10)   # close 130
    on_candle_close(ts(10, 30), ce_break, pe_break, ATM, sp_high, sp_low, levels, st, conn, SESSION)
    implied = ATM + 130 - 22
    check("implied spot breaks SP high (%.1f > %d)" % (implied, sp_high), implied > sp_high)
    check("CE_WINS entry taken", st.position is not None and st.position["side"] == "CE")
    check("entry price recorded at candle close (130)", st.position and st.position["entry"] == 130)

    # --- line cross: next CE close reaches the ITM1 CE ladder line (160)
    ce_line = Candle(ts(10, 33), 130, 165, 128, 162, 10)
    pe_line = Candle(ts(10, 33), 20, 20, 15, 17, 10)
    on_candle_close(ts(10, 33), ce_line, pe_line, ATM, sp_high, sp_low, levels, st, conn, SESSION)
    check("line crossed increments counter", st.position and st.position["crossed"] == 1)

    # --- exit: implied spot falls back inside SP zone
    ce_back = Candle(ts(11, 0), 130, 130, 100, 105, 10)
    pe_back = Candle(ts(11, 0), 40, 60, 40, 55, 10)  # implied spot = 24200+105-55=24250 -> inside zone
    on_candle_close(ts(11, 0), ce_back, pe_back, ATM, sp_high, sp_low, levels, st, conn, SESSION)
    check("position closed on zone re-entry", st.position is None)

    trades = conn.execute("SELECT side, entry_price, exit_price, exit_reason, lines_crossed "
                          "FROM orb_trades WHERE session_date=?", (SESSION.isoformat(),)).fetchall()
    check("one trade logged", len(trades) == 1)
    print("Trade row:", trades[0])

    print("\nAll offline logic checks passed.")

if __name__ == "__main__":
    main()

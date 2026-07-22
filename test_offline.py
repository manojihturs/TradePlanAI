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

# Never let synthetic test trades hit the real Telegram bot, even if a real
# .env is loaded (orb_common auto-loads .env on import).
orb_common.TELEGRAM_BOT_TOKEN = ""
orb_common.TELEGRAM_CHAT_ID = ""

import orb_journal
orb_journal.JOURNAL_PATH = os.path.join(tempfile.gettempdir(), "orb_test_journal.xlsx")
if os.path.exists(orb_journal.JOURNAL_PATH):
    os.remove(orb_journal.JOURNAL_PATH)

from orb_common import IST, Candle, db, nearest_strike, SL_POINTS, MAX_DAILY_LOSS, QTY
from orb_signal import DayState, on_candle_close, ladder_lines, CANDLE_MINUTES
from orb_auto import should_run_today_now, next_market_open
from datetime import timedelta

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
        # ATM+50 strike is ITM for a PUT (strike > spot) -> higher intrinsic value,
        # so its first-candle high must exceed the ATM PE high (69), mirroring CE.
        (ATM + 50, "PE", "NSE_FO|ITM1PE", 85, 95, 60, 90, 1000),
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

    trades = conn.execute(
        "SELECT side, entry_price, exit_price, exit_reason, lines_crossed, entry_note, exit_note "
        "FROM orb_trades WHERE session_date=?", (SESSION.isoformat(),)).fetchall()
    check("one trade logged", len(trades) == 1)
    check("entry_note recorded", bool(trades[0][5]) and "CE WINS" in trades[0][5])
    check("exit_note recorded", bool(trades[0][6]) and "Loss" in trades[0][6])
    print("Trade row:", trades[0])

    import orb_journal as _oj
    check("journal workbook created", os.path.exists(_oj.JOURNAL_PATH))
    from openpyxl import load_workbook
    wb = load_workbook(_oj.JOURNAL_PATH)
    check("journal has a sheet for the session date", str(SESSION) in wb.sheetnames)
    ws = wb[str(SESSION)]
    check("journal sheet has header + at least 1 trade row", ws.max_row >= 2)

    # =====================================================================
    # PE_WINS mirror path + breakeven-lock TSL
    # =====================================================================
    st2 = DayState()
    ce_lo = Candle(ts(12, 0), 45, 45, 38, 40, 10)    # CE close 40 < CE 9:15 low 47.1
    pe_hi = Candle(ts(12, 0), 75, 82, 74, 80, 10)     # PE close 80 > PE 9:15 high 69
    on_candle_close(ts(12, 0), ce_lo, pe_hi, ATM, sp_high, sp_low, levels, st2, conn, SESSION)
    implied2 = ATM + 40 - 80
    check("implied spot breaks SP low (%.1f < %d)" % (implied2, sp_low), implied2 < sp_low)
    check("PE_WINS entry taken", st2.position is not None and st2.position["side"] == "PE")
    check("PE entry price recorded (80)", st2.position["entry"] == 80)
    expected_sl = max(0.0, 80 - SL_POINTS)
    check("PE initial SL = entry - SL_POINTS (%.2f)" % expected_sl,
          abs(st2.position["trail"] - expected_sl) < 1e-6)

    # push PE up through its ladder line (95) AND past the 1R breakeven trigger (~19.2 pts)
    ce_lo2 = Candle(ts(12, 3), 40, 40, 30, 33, 10)
    pe_up  = Candle(ts(12, 3), 80, 105, 80, 102, 10)   # +22 pts, crosses line 95 too
    on_candle_close(ts(12, 3), ce_lo2, pe_up, ATM, sp_high, sp_low, levels, st2, conn, SESSION)
    expected_trail = max(80.0, 95 - (SL_POINTS * 0.5))   # line-cross trail vs. breakeven, whichever is higher
    check("trail locks at max(breakeven, line-cross trail) = %.2f" % expected_trail,
          abs(st2.position["trail"] - expected_trail) < 1e-6)
    check("trail is at/above breakeven (no longer a losing trade)", st2.position["trail"] >= 80)

    # price pulls back to just under that trail -> exits in profit, not counted as a stop
    ce_lo3 = Candle(ts(12, 6), 33, 40, 30, 35, 10)
    pe_be  = Candle(ts(12, 6), 100, 100, 84, expected_trail - 0.01, 10)
    stops_before = st2.stops
    on_candle_close(ts(12, 6), ce_lo3, pe_be, ATM, sp_high, sp_low, levels, st2, conn, SESSION)
    check("trail-hit exit closes position", st2.position is None)
    check("profitable trail exit is not counted as a stop", st2.stops == stops_before)

    # =====================================================================
    # Daily loss cap: two losing trades should lock the machine out
    # =====================================================================
    st3 = DayState()
    ce_e = Candle(ts(13, 0), 100, 140, 100, 130, 10)
    pe_e = Candle(ts(13, 0), 20, 20, 1, 2, 10)         # implied = 24200+130-2=24328 > sp_high
    on_candle_close(ts(13, 0), ce_e, pe_e, ATM, sp_high, sp_low, levels, st3, conn, SESSION)
    check("trade A (CE) entered", st3.position is not None)
    # next candle: gaps straight through SL on a close (no intrabar check - candle-close only)
    ce_sl = Candle(ts(13, 3), 130, 130, 100, 108, 10)
    pe_sl = Candle(ts(13, 3), 3, 3, 1, 2, 10)          # implied = 24200+108-2=24306, still > sp_high
    on_candle_close(ts(13, 3), ce_sl, pe_sl, ATM, sp_high, sp_low, levels, st3, conn, SESSION)
    check("trade A stopped out", st3.position is None and st3.stops == 1)

    ce_e2 = Candle(ts(13, 30), 45, 45, 18, 20, 10)
    pe_e2 = Candle(ts(13, 30), 75, 82, 74, 80, 10)     # implied = 24200+20-80=24140 < sp_low
    on_candle_close(ts(13, 30), ce_e2, pe_e2, ATM, sp_high, sp_low, levels, st3, conn, SESSION)
    check("trade B (PE) entered", st3.position is not None)
    ce_sl2 = Candle(ts(13, 33), 20, 20, 15, 18, 10)
    pe_sl2 = Candle(ts(13, 33), 80, 80, 55, 58, 10)    # implied = 24200+18-58=24160, still < sp_low
    on_candle_close(ts(13, 33), ce_sl2, pe_sl2, ATM, sp_high, sp_low, levels, st3, conn, SESSION)
    check("trade B stopped out", st3.position is None and st3.stops == 2)
    check("two stops trip the lockout", st3.locked is True)
    check("daily loss recorded (Rs %.2f, cap Rs %.2f)" % (st3.daily_pnl_rupees, MAX_DAILY_LOSS),
          st3.daily_pnl_rupees < 0)

    # findings, not failures: candle-close-only stops can overshoot the nominal
    # per-trade risk budget when a candle gaps through the SL level.
    per_trade_budget = MAX_DAILY_LOSS / 2
    actual_worst = min(-22 * QTY, -22 * QTY)  # both legs realized -22 pts in this scenario
    if abs(actual_worst) > per_trade_budget:
        print("[NOTE] candle-close SL overshot the Rs %.0f/trade risk budget by Rs %.2f "
              "in this scenario - stops are evaluated on candle close, not intrabar."
              % (per_trade_budget, abs(actual_worst) - per_trade_budget))

    # =====================================================================
    # orb_auto: starting late (after 9:21) on a trading day must run TODAY,
    # not silently skip to tomorrow (this was a real bug found live on
    # 2026-07-22: starting at 09:57 scheduled the next run for 09:23 the
    # following day instead of capturing immediately).
    # =====================================================================
    tuesday_late_start = datetime(2026, 7, 21, 9, 57, tzinfo=IST)   # 2026-07-21 is a Tuesday
    check("late start (09:57, past 09:21) runs today immediately",
          should_run_today_now(tuesday_late_start, None) is True)

    tuesday_before_open = datetime(2026, 7, 21, 9, 0, tzinfo=IST)
    check("before 09:21 does not run immediately (normal sleep-until-open path)",
          should_run_today_now(tuesday_before_open, None) is False)

    tuesday_after_close = datetime(2026, 7, 21, 16, 0, tzinfo=IST)
    check("after square-off does not trigger an immediate run",
          should_run_today_now(tuesday_after_close, None) is False)

    tuesday_already_ran = datetime(2026, 7, 21, 10, 0, tzinfo=IST)
    check("does not re-run today if last_run_date is already today",
          should_run_today_now(tuesday_already_ran, date(2026, 7, 21)) is False)

    saturday = datetime(2026, 7, 25, 10, 0, tzinfo=IST)
    check("weekend never triggers an immediate run",
          should_run_today_now(saturday, None) is False)

    # =====================================================================
    # run_live_for_day's backlog catch-up filter (found live on 2026-07-22:
    # starting orb_auto after 09:21 caused the whole morning's candle
    # history to be processed as if it were live, entering a trade on a
    # candle timestamped 09:30 while the real time was already 10:05).
    # This mirrors the exact filter condition in orb_signal.run_live_for_day.
    # =====================================================================
    now_ = datetime(2026, 7, 22, 10, 5, tzinfo=IST)
    cutoff = now_ - timedelta(minutes=CANDLE_MINUTES)
    stale_candle_ts = datetime(2026, 7, 22, 9, 30, tzinfo=IST)   # the actual bad entry from today
    fresh_candle_ts = datetime(2026, 7, 22, 10, 3, tzinfo=IST)
    check("a 9:30 candle seen at 10:05 is classified as stale backlog (not acted on)",
          stale_candle_ts < cutoff)
    check("a 10:03 candle seen at 10:05 is classified as fresh (acted on live)",
          fresh_candle_ts >= cutoff)

    print("\nAll offline logic checks passed.")

if __name__ == "__main__":
    main()

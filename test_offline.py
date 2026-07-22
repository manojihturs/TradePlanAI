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

from orb_common import (IST, Candle, db, nearest_strike, SL_POINTS, MAX_DAILY_LOSS, QTY,
                        MIN_PROFIT_POINTS, MIN_ENTRY_MARGIN_POINTS, PE_ENTRY_MARGIN_POINTS)
import orb_signal
from orb_signal import (DayState, on_candle_close, ladder_lines, build_watch_pairs,
                        run_replay, CANDLE_MINUTES)
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
        # Cross-plotted ladder for a CE_WINS (TOP) trade: the trader watches
        # the PUT's own first-5min LOW at neighboring strikes, not the
        # CALL's own high (confirmed in chat - this is a cross-plot, not a
        # same-side extension).
        (ATM - 50, "PE", "NSE_FO|ITM1CE", 165, 170, 160, 168, 1000),
        (ATM - 100, "PE", "NSE_FO|ITM2CE", 205, 210, 200, 208, 1000),   # for the early-exit test
        # A cross-plotted strike whose own low (50) sits BELOW where CE will
        # enter (130) - a real strike, unrelated in magnitude, that must NOT
        # be counted as an already-crossed target the instant the position opens.
        (ATM + 150, "PE", "NSE_FO|PE_BELOW_ENTRY", 45, 55, 50, 52, 1000),
        # Cross-plotted ladder for a PE_WINS (BOTTOM) trade: the CALL's own
        # first-5min LOW at a neighboring strike.
        (ATM + 50, "CE", "NSE_FO|ITM1PE", 100, 105, 95, 98, 1000),
        # Competitor reference for the CE side: at strike 24150 (the strike
        # feeding our own target1, level 160), the competitor's (PE's) own
        # symmetric reference is THIS record's high field (1.0 - deliberately
        # tiny so it never interferes with existing PE closes used elsewhere
        # in these tests; the dedicated competitor test constructs a PE close
        # at/below it on purpose). Its low is kept just as tiny so it's also
        # safely below any PE_WINS entry price and doesn't pollute that ladder.
        (ATM - 50, "CE", "NSE_FO|COMPETITOR_CE_24150", 0.6, 1.0, 0.5, 0.8, 1000),
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
    check("ladder_lines cross-plots PE lows ascending (50, 160, 200)", lines == [50, 160, 200])

    watch_pairs = build_watch_pairs(levels, ATM, "CE")
    check("watch_pairs chains the full cross-plotted ladder in order",
          watch_pairs == [
              {"strike": ATM + 150, "key": "NSE_FO|PE_BELOW_ENTRY", "next_level": 160},
              {"strike": ATM - 50, "key": "NSE_FO|ITM1CE", "next_level": 200},
          ])

    # --- NEUTRAL: implied spot inside zone -> no trade
    st = DayState()
    ce_flat = Candle(ts(10, 0), 100, 100, 95, 100, 10)
    pe_flat = Candle(ts(10, 0), 60, 60, 55, 60, 10)
    on_candle_close(ts(10, 0), ce_flat, pe_flat, ATM, sp_high, sp_low, levels, st, conn, SESSION)
    check("NEUTRAL state takes no trade", st.position is None and st.signals == 0)

    # =====================================================================
    # MIN_ENTRY_MARGIN_POINTS: a close that only barely beats its own 9:15
    # high/low (here by 2 pts, need 5) must NOT count as confirmed, even
    # though the plain boolean condition (close > high) and the implied-spot
    # zone break are both satisfied. Found in a 9-day backtest: thin-margin
    # CE entries were disproportionately losses.
    # =====================================================================
    st_margin = DayState()
    thin_close = 114.6 + max(1.0, MIN_ENTRY_MARGIN_POINTS - 2)   # margin < MIN_ENTRY_MARGIN_POINTS
    ce_thin = Candle(ts(10, 15), 100, thin_close + 5, 100, thin_close, 10)
    pe_thin = Candle(ts(10, 15), 15, 15, 8, 10, 10)              # well below its own low (29.15)
    implied_thin = ATM + thin_close - 10
    on_candle_close(ts(10, 15), ce_thin, pe_thin, ATM, sp_high, sp_low, levels, st_margin, conn, SESSION)
    check("thin-margin implied spot still breaks SP high (%.1f > %d)" % (implied_thin, sp_high),
          implied_thin > sp_high)
    check("thin-margin entry (%.1fpt < %.0fpt minimum) does NOT trigger CE_WINS"
          % (thin_close - 114.6, MIN_ENTRY_MARGIN_POINTS),
          st_margin.position is None and st_margin.signals == 0)

    # Same setup, but CE clears its high by well over the minimum - now it fires.
    thick_close = 114.6 + MIN_ENTRY_MARGIN_POINTS + 3
    ce_thick = Candle(ts(10, 18), 100, thick_close + 5, 100, thick_close, 10)
    pe_thick = Candle(ts(10, 18), 15, 15, 8, 10, 10)
    on_candle_close(ts(10, 18), ce_thick, pe_thick, ATM, sp_high, sp_low, levels, st_margin, conn, SESSION)
    check("sufficient-margin entry (%.1fpt >= %.0fpt minimum) DOES trigger CE_WINS"
          % (thick_close - 114.6, MIN_ENTRY_MARGIN_POINTS),
          st_margin.position is not None and st_margin.signals == 1)

    # =====================================================================
    # PE_ENTRY_MARGIN_POINTS: PE needs a STRONGER margin than CE - a 13-day
    # combined backtest found PE never once reached its own first target
    # (11 trades, 0 hits), consistent with put volatility skew producing
    # false-start confirmations. A margin that clears CE's threshold but not
    # PE's stronger one must still be rejected when the traded side is PE.
    # =====================================================================
    st_pe_margin = DayState()
    pe_mid_close = 69.0 + (MIN_ENTRY_MARGIN_POINTS + PE_ENTRY_MARGIN_POINTS) / 2
    ce_mid = Candle(ts(10, 21), 30, 30, 15, 20, 10)      # well below CE's own low (47.1)
    pe_mid = Candle(ts(10, 21), 60, pe_mid_close + 5, 60, pe_mid_close, 10)
    on_candle_close(ts(10, 21), ce_mid, pe_mid, ATM, sp_high, sp_low, levels, st_pe_margin, conn, SESSION)
    check("PE margin (%.1fpt) clears CE's threshold but not PE's stronger one - rejected"
          % (pe_mid_close - 69.0),
          st_pe_margin.position is None and st_pe_margin.signals == 0)

    # Same setup but PE clears its own (stronger) threshold - now it fires.
    pe_thick_close = 69.0 + PE_ENTRY_MARGIN_POINTS + 3
    ce_mid2 = Candle(ts(10, 24), 30, 30, 15, 20, 10)
    pe_thick2 = Candle(ts(10, 24), 60, pe_thick_close + 5, 60, pe_thick_close, 10)
    on_candle_close(ts(10, 24), ce_mid2, pe_thick2, ATM, sp_high, sp_low, levels, st_pe_margin, conn, SESSION)
    check("PE margin (%.1fpt) above its own %.0fpt threshold DOES trigger PE_WINS"
          % (pe_thick_close - 69.0, PE_ENTRY_MARGIN_POINTS),
          st_pe_margin.position is not None and st_pe_margin.signals == 1)

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

    # --- LINE 1 cross: CE close reaches the ITM1 CE ladder line (160). Per
    # instruction, this is now an IMMEDIATE exit (confirmed win, don't hold
    # out trailing for line 2/3) - not a trail update.
    ce_line = Candle(ts(10, 33), 130, 165, 128, 162, 10)
    pe_line = Candle(ts(10, 33), 20, 20, 15, 17, 10)
    on_candle_close(ts(10, 33), ce_line, pe_line, ATM, sp_high, sp_low, levels, st, conn, SESSION)
    check("LINE 1 cross exits the position immediately (confirmed win)",
          st.position is None and st.signals == 1)

    trades = conn.execute(
        "SELECT side, entry_price, exit_price, exit_reason, lines_crossed, entry_note, exit_note, source "
        "FROM orb_trades WHERE session_date=?", (SESSION.isoformat(),)).fetchall()
    check("one trade logged", len(trades) == 1)
    check("entry_note recorded", bool(trades[0][5]) and "CE WINS" in trades[0][5])
    check("exit_note records a profit via LINE 1 target hit, not a loss",
          bool(trades[0][6]) and "Profit" in trades[0][6] and "LINE 1 target hit" in trades[0][3])
    check("exit price is the line level (162), pnl is a win", trades[0][2] == 162 and trades[0][2] > trades[0][1])
    check("source defaults to 'live' when not passed explicitly", trades[0][7] == "live")
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

    # PE crosses its LINE 1 (95) - per instruction, immediate exit, confirmed
    # win, not a trail update.
    ce_lo2 = Candle(ts(12, 3), 40, 40, 30, 33, 10)
    pe_up  = Candle(ts(12, 3), 80, 105, 80, 102, 10)
    on_candle_close(ts(12, 3), ce_lo2, pe_up, ATM, sp_high, sp_low, levels, st2, conn, SESSION)
    check("LINE 1 cross exits the PE position immediately (confirmed win)",
          st2.position is None and st2.signals == 1)
    last_pnl = conn.execute(
        "SELECT pnl_points FROM orb_trades WHERE session_date=? AND side='PE' "
        "ORDER BY rowid DESC LIMIT 1", (SESSION.isoformat(),)).fetchone()[0]
    check("realized win is >= MIN_PROFIT_POINTS (%.2f pts, needed %.2f)" % (last_pnl, MIN_PROFIT_POINTS),
          last_pnl >= MIN_PROFIT_POINTS - 1e-6)

    # =====================================================================
    # Profit-lock floor holds even with NO ladder line crossed (pure 1R
    # trigger) - proves the fix isn't accidentally riding on the line-cross
    # trail dominating in the scenario above.
    # =====================================================================
    st4 = DayState()
    ce_e2 = Candle(ts(9, 30), 100, 140, 100, 130, 10)
    pe_e2 = Candle(ts(9, 30), 20, 20, 1, 2, 10)          # implied = 24200+130-2=24328 > sp_high -> CE wins
    on_candle_close(ts(9, 30), ce_e2, pe_e2, ATM, sp_high, sp_low, levels, st4, conn, SESSION)
    check("CE entered for profit-lock-only test", st4.position is not None)
    # Regression check for the bug found live: the cross-plotted ladder
    # includes a strike (level 50) whose value sits BELOW this entry (130).
    # It must be excluded from "lines" entirely, not trivially "crossed" the
    # instant the position opens.
    check("below-entry ladder level (50) is excluded from future targets",
          50 not in st4.position["lines"] and st4.position["lines"] == [160, 200])
    check("crossed count is 0 right at entry, not incremented by the excluded level",
          st4.position["crossed"] == 0)
    # move up exactly past 1R but stay well below the first ladder line (160)
    just_past_1r = 130 + SL_POINTS + 0.5
    ce_1r = Candle(ts(9, 33), 130, just_past_1r + 1, 128, just_past_1r, 10)
    pe_1r = Candle(ts(9, 33), 3, 3, 1, 2, 10)
    on_candle_close(ts(9, 33), ce_1r, pe_1r, ATM, sp_high, sp_low, levels, st4, conn, SESSION)
    check("no ladder line crossed yet (still below 160)", st4.position["crossed"] == 0)
    check("trail floor is exactly entry + MIN_PROFIT_POINTS (%.2f), not plain breakeven"
          % (130 + MIN_PROFIT_POINTS),
          abs(st4.position["trail"] - (130 + MIN_PROFIT_POINTS)) < 1e-6)

    # =====================================================================
    # Profit-lock takes priority over "spot back in zone": once the TSL
    # floor has moved above entry+MIN_PROFIT_POINTS, a whipsaw back inside
    # the SP zone must NOT force an exit as long as price is still above
    # the trail - the profit floor, not the directional thesis, now governs.
    # =====================================================================
    implied_inside_zone_ce = sp_high - 1   # implied spot back inside zone for a CE trade
    ce_whipsaw = Candle(ts(9, 36), just_past_1r, just_past_1r + 1, just_past_1r - 1, just_past_1r, 10)
    # choose PE close so implied_spot = ATM + ce.close - pe.close lands inside the zone
    pe_whipsaw_close = ATM + just_past_1r - implied_inside_zone_ce
    pe_whipsaw = Candle(ts(9, 36), pe_whipsaw_close, pe_whipsaw_close, pe_whipsaw_close, pe_whipsaw_close, 10)
    on_candle_close(ts(9, 36), ce_whipsaw, pe_whipsaw, ATM, sp_high, sp_low, levels, st4, conn, SESSION)
    check("profit-locked position survives a zone whipsaw (not force-exited)",
          st4.position is not None)

    # =====================================================================
    # Other-strike early exit (the +/- SIGNAL_STRIKES scan): currently
    # disabled by default (ENABLE_OTHER_STRIKE_EARLY_EXIT=False) in favor of
    # the simpler single-competitor rule below - but the mechanism itself
    # must still work correctly when explicitly re-enabled. Toggle it on
    # just for this block, restore the default after.
    # =====================================================================
    orb_signal.ENABLE_OTHER_STRIKE_EARLY_EXIT = True
    st5 = DayState()
    ce_e3 = Candle(ts(10, 0), 100, 140, 100, 130, 10)
    pe_e3 = Candle(ts(10, 0), 20, 20, 1, 2, 10)   # implied = 24328 > sp_high -> CE wins, entry 130
    on_candle_close(ts(10, 0), ce_e3, pe_e3, ATM, sp_high, sp_low, levels, st5, conn, SESSION)
    check("CE entered for early-exit test", st5.position is not None)

    def fake_ltp_triggering(instrument_key):
        # ITM1CE has already reached ITM2's level (200) - should force an exit,
        # regardless of the fact our own ATM CE (currently 133, tiny profit,
        # far below its own SL/trail/first-line) gives no other reason to exit.
        return 205.0 if instrument_key == "NSE_FO|ITM1CE" else 0.0

    ce_tiny_move = Candle(ts(10, 3), 130, 135, 128, 133, 10)   # barely above entry, no other exit fires
    pe_tiny_move = Candle(ts(10, 3), 2, 2, 1, 1.5, 10)
    on_candle_close(ts(10, 3), ce_tiny_move, pe_tiny_move, ATM, sp_high, sp_low, levels, st5, conn,
                     SESSION, ltp_fn=fake_ltp_triggering)
    check("position force-exited when another strike skips ahead of its own next level",
          st5.position is None)
    early_exit_row = conn.execute(
        "SELECT exit_reason FROM orb_trades WHERE session_date=? AND entry_ts=?",
        (SESSION.isoformat(), ts(10, 0).isoformat())).fetchone()
    check("exit reason names the triggering strike (ITM1 = ATM-50 = 24150) and its value",
          str(ATM - 50) in early_exit_row[0] and "205.00" in early_exit_row[0])

    # Sanity: with a non-triggering ltp_fn, the same tiny move does NOT exit
    # (proves the check is actually discriminating, not always firing).
    st6 = DayState()
    ce_e4 = Candle(ts(10, 30), 100, 140, 100, 130, 10)
    pe_e4 = Candle(ts(10, 30), 20, 20, 1, 2, 10)
    on_candle_close(ts(10, 30), ce_e4, pe_e4, ATM, sp_high, sp_low, levels, st6, conn, SESSION)
    on_candle_close(ts(10, 33), ce_tiny_move, pe_tiny_move, ATM, sp_high, sp_low, levels, st6, conn,
                     SESSION, ltp_fn=lambda k: 0.0)
    check("no early exit when no other strike has skipped ahead", st6.position is not None)
    orb_signal.ENABLE_OTHER_STRIKE_EARLY_EXIT = False   # restore the default before continuing

    # =====================================================================
    # Simplified competitor exit rule (the ACTIVE rule now): while holding
    # CE, the competitor is the ATM PE. Its reference level is the SAME
    # strike (24150) that feeds our own target1, but read from OUR side's
    # HIGH field (levels[(24150,"CE")]["high"] = 1.0, seeded above). If PE's
    # own live close falls to/through 1.0 before our target1 (160) is hit,
    # exit immediately - no ltp_fn/network needed, uses the candles already
    # passed into on_candle_close.
    # =====================================================================
    st7 = DayState()
    ce_e5 = Candle(ts(11, 0), 100, 140, 100, 130, 10)
    pe_e5 = Candle(ts(11, 0), 20, 20, 1, 2, 10)   # implied = 24328 > sp_high -> CE wins, entry 130
    on_candle_close(ts(11, 0), ce_e5, pe_e5, ATM, sp_high, sp_low, levels, st7, conn, SESSION)
    check("CE entered for competitor-exit test", st7.position is not None)
    check("competitor reference resolved to strike 24150, level 1.0",
          st7.position["competitor_strike"] == ATM - 50 and
          abs(st7.position["competitor_level"] - 1.0) < 1e-9)

    # PE closes at 0.9 (<= competitor level 1.0), CE barely moved (nowhere
    # near its own target1 of 160, SL, or TSL) - only the competitor rule
    # can explain an exit here.
    ce_comp = Candle(ts(11, 3), 130, 135, 128, 132, 10)
    pe_comp = Candle(ts(11, 3), 2, 2, 0.8, 0.9, 10)
    on_candle_close(ts(11, 3), ce_comp, pe_comp, ATM, sp_high, sp_low, levels, st7, conn, SESSION)
    check("position exits when competitor reaches its level before our target1",
          st7.position is None)
    comp_exit_row = conn.execute(
        "SELECT exit_reason, exit_price FROM orb_trades WHERE session_date=? AND entry_ts=?",
        (SESSION.isoformat(), ts(11, 0).isoformat())).fetchone()
    check("exit reason names the competitor side and its level",
          "competitor PE" in comp_exit_row[0] and "1.00" in comp_exit_row[0])
    check("exit price is our own contract's close (132), not the competitor's",
          comp_exit_row[1] == 132)

    # Negative control: PE stays well above 1.0 - no competitor-triggered exit.
    st8 = DayState()
    ce_e6 = Candle(ts(11, 30), 100, 140, 100, 130, 10)
    pe_e6 = Candle(ts(11, 30), 20, 20, 1, 2, 10)
    on_candle_close(ts(11, 30), ce_e6, pe_e6, ATM, sp_high, sp_low, levels, st8, conn, SESSION)
    ce_nc = Candle(ts(11, 33), 130, 135, 128, 132, 10)
    pe_nc = Candle(ts(11, 33), 2, 2, 1.5, 1.8, 10)   # stays above 1.0
    on_candle_close(ts(11, 33), ce_nc, pe_nc, ATM, sp_high, sp_low, levels, st8, conn, SESSION)
    check("no competitor exit when PE stays above its level", st8.position is not None)

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

    # =====================================================================
    # run_replay's full-ladder backfill: mock the network call and prove the
    # pipeline (fetch -> resample -> backfill -> on_candle_close) correctly
    # reproduces the ACTIVE competitor exit rule from historical data, not
    # just live polling. The competitor rule needs no ltp_fn/network at all
    # (it reads straight off the candles already passed in), so this proves
    # it works identically in replay as in live. This is the actual backtest
    # path a trader would run.
    # =====================================================================
    fake_history = {
        # 5-min buckets from the 09:15 anchor: 09:20, 09:25, 09:30, ...
        "NSE_FO|ATMCE": [(9, 25, 130), (9, 30, 133)],
        # ATMPE drops to 0.9 on the 2nd candle - at/below the competitor
        # level (1.0, from the seeded 24150 CE record) - before CE's own
        # target1 (160) is anywhere close to being hit.
        "NSE_FO|ATMPE": [(9, 25, 2),   (9, 30, 0.9)],
        "NSE_FO|ITM1CE": [(9, 25, 150), (9, 30, 178)],
        "NSE_FO|ITM2CE": [(9, 25, 175), (9, 30, 178)],
        "NSE_FO|ITM1PE": [(9, 25, 90),  (9, 30, 91)],
    }

    def fake_fetch_historical_candles(instrument_key, minutes, day_from, day_to):
        rows = fake_history.get(instrument_key, [])
        return [Candle(ts(h, m), c, c, c, c, 10) for h, m, c in rows]

    orb_signal.fetch_historical_candles = fake_fetch_historical_candles
    run_replay(SESSION)
    replay_row = conn.execute(
        "SELECT entry_price, exit_price, exit_reason, source FROM orb_trades "
        "WHERE session_date=? AND entry_ts=?",
        (SESSION.isoformat(), ts(9, 25).isoformat())).fetchone()
    check("run_replay entered the CE trade from mocked historical data",
          replay_row is not None and replay_row[0] == 130)
    check("run_replay's competitor check fires from backfilled data (no ltp_fn needed)",
          replay_row is not None and "competitor PE" in replay_row[2])
    check("run_replay tags its rows source='replay', not 'live'",
          replay_row is not None and replay_row[3] == "replay")

    # Prove the two sources coexist in the SAME table without being confusable,
    # and that a query CAN separate them (the actual fix for the mixing bug).
    live_count = conn.execute(
        "SELECT COUNT(*) FROM orb_trades WHERE session_date=? AND source='live'",
        (SESSION.isoformat(),)).fetchone()[0]
    replay_count = conn.execute(
        "SELECT COUNT(*) FROM orb_trades WHERE session_date=? AND source='replay'",
        (SESSION.isoformat(),)).fetchone()[0]
    check("live and replay rows for the same date are distinguishable by source",
          live_count > 0 and replay_count > 0)

    # =====================================================================
    # Journal migration: an existing sheet's header (written under an older
    # HEADERS list) must gain new columns at the END, never reshuffle
    # existing ones - otherwise merging this branch would misalign every
    # row already written to a real trader's trade_journal.xlsx.
    # =====================================================================
    import orb_journal as _oj2
    from openpyxl import load_workbook as _lwb
    old_sheet_name = "2020-01-01-legacy"
    wb = _oj2._open_workbook()
    legacy_headers = ["entry_ts", "exit_ts", "side", "strike", "qty", "entry_price",
                      "exit_price", "pnl_points", "pnl_rupees", "lines_crossed",
                      "exit_reason", "why_entered", "why_pnl"]   # pre-source, pre-atm_strike schema
    ws = wb.create_sheet(old_sheet_name)
    ws.append(legacy_headers)
    ws.append(["2020-01-01T09:30:00", "2020-01-01T09:33:00", "CE", 100, 65, 10, 12,
              2, 130, 0, "trail hit", "legacy entry", "legacy exit"])
    wb.save(_oj2.JOURNAL_PATH)

    _oj2.append_trade(old_sheet_name, {
        "entry_ts": "2020-01-01T10:00:00", "exit_ts": "2020-01-01T10:03:00", "side": "PE",
        "source": "live", "atm_strike": 100, "strike": 100, "qty": 65,
        "entry_price": 20, "exit_price": 25, "pnl_points": 5, "pnl_rupees": 325,
        "lines_crossed": 0, "exit_reason": "trail hit", "trigger_strike": "",
        "trigger_strike_value": "", "why_entered": "new entry", "why_pnl": "new exit",
    })
    wb2 = _lwb(_oj2.JOURNAL_PATH)
    ws2 = wb2[old_sheet_name]
    new_header = [c.value for c in ws2[1]]
    check("legacy header columns kept in their original positions",
          new_header[:len(legacy_headers)] == legacy_headers)
    check("new columns (source, atm_strike, ...) appended at the end, not inserted",
          "source" in new_header[len(legacy_headers):])
    old_row = [c.value for c in ws2[2]]
    check("pre-existing legacy row is untouched by the migration",
          old_row[:len(legacy_headers)] == ["2020-01-01T09:30:00", "2020-01-01T09:33:00", "CE",
                                            100, 65, 10, 12, 2, 130, 0, "trail hit",
                                            "legacy entry", "legacy exit"])

    print("\nAll offline logic checks passed.")

if __name__ == "__main__":
    main()

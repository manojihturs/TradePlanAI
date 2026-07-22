# orb_signal.py - CE-wins / PE-wins state machine with triple confirmation.
#
#   NEUTRAL  : implied spot inside SP zone -> NO TRADE (the anti-sentiment rule)
#   CE_WINS  : implied spot close > SP High  AND ATM CE close > its 09:15 high
#                                            AND ATM PE close < its 09:15 low
#   PE_WINS  : the mirror.
#
# Entry  = close of the confirmation candle, on the winning ATM contract.
# Stop   = implied spot closes back inside the SP zone.
# Trail  = ladder lines of the winning side (each line ~ 1 strike of spot move).
# Limits = MAX_SIGNALS_PER_DAY, MAX_STOPS_PER_DAY, LAST_ENTRY, SQUARE_OFF.
#
# Usage:
#   python orb_signal.py --replay 2026-07-21     (after capturing that date)
#   python orb_signal.py --live                  (after today's 09:21 capture)

import argparse, time as systime
from datetime import date, datetime
from orb_common import (IST, CANDLE_MINUTES, SIGNAL_STRIKES, STRIKE_GAP,
                        LAST_ENTRY, SQUARE_OFF, MAX_SIGNALS_PER_DAY,
                        MAX_STOPS_PER_DAY, QTY, MAX_DAILY_LOSS, SL_POINTS,
                        TSL_TRIGGER_R, TSL_STEP_POINTS, APP_NAME, SERVER_NAME,
                        fetch_intraday_candles, fetch_historical_candles,
                        resample, db, alert, write_state)
import orb_journal

def load_day(session_date):
    conn = db()
    row = conn.execute("SELECT atm, sp_high, sp_low FROM orb_summary WHERE session_date=?",
                       (session_date.isoformat(),)).fetchone()
    if not row:
        raise SystemExit("No capture for %s - run orb_capture.py first." % session_date)
    atm, sp_high, sp_low = row
    lv = {}
    for strike, side, ikey, fh, flo in conn.execute(
            "SELECT strike, side, instrument_key, first_high, first_low "
            "FROM orb_levels WHERE session_date=?", (session_date.isoformat(),)):
        lv[(strike, side)] = {"key": ikey, "high": fh, "low": flo}
    return atm, sp_high, sp_low, lv

def ladder_lines(levels, atm, winning_side):
    """Ascending premium levels the winning contract will cross as trend extends.
    CE wins -> underlying rises -> ATM CE premium climbs toward the first-candle
    highs of successively deeper ITM calls (lower strikes). PE mirror."""
    lines = []
    for i in range(1, SIGNAL_STRIKES + 1):
        k = atm - i * STRIKE_GAP if winning_side == "CE" else atm + i * STRIKE_GAP
        rec = levels.get((k, winning_side))
        if rec:
            lines.append(rec["high"])
    return sorted(lines)

class DayState:
    def __init__(self):
        self.position = None          # dict when in a trade
        self.signals = 0
        self.stops = 0
        self.locked = False
        self.daily_pnl_rupees = 0.0

def _snapshot(session_date, atm, sp_high, sp_low, st, note=""):
    write_state(
        app_name=APP_NAME, server=SERVER_NAME,
        session_date=str(session_date), atm=atm, sp_low=sp_low, sp_high=sp_high,
        state=("LOCKED" if st.locked else ("IN_TRADE" if st.position else "NEUTRAL")),
        position=st.position, signals=st.signals, stops=st.stops,
        daily_pnl_rupees=round(st.daily_pnl_rupees, 2),
        max_daily_loss=MAX_DAILY_LOSS, qty=QTY, note=note,
    )

def on_candle_close(ts, ce_c, pe_c, atm, sp_high, sp_low, levels, st, conn, session_date):
    """ce_c / pe_c are the just-closed N-min candles of the ATM CE / ATM PE."""
    implied_spot = atm + ce_c.close - pe_c.close
    atm_ce = levels[(atm, "CE")]
    atm_pe = levels[(atm, "PE")]
    t = ts.time()

    # ---- manage open position first
    if st.position:
        p = st.position
        px = ce_c.close if p["side"] == "CE" else pe_c.close
        exit_reason = None

        if p["side"] == "CE" and implied_spot < sp_high:
            exit_reason = "spot back in zone"
        elif p["side"] == "PE" and implied_spot > sp_low:
            exit_reason = "spot back in zone"
        elif t >= SQUARE_OFF:
            exit_reason = "square off 15:15 (forced flat)"
        else:
            if p["lines"] and px >= p["lines"][0]:
                crossed = p["lines"].pop(0)
                p["crossed"] += 1
                # TSL: trail a fixed buffer behind each ladder line crossed.
                p["trail"] = max(p["trail"], crossed - TSL_STEP_POINTS)
                alert("LINE %d crossed at %.2f | TSL -> %.2f | implied spot %.1f"
                      % (p["crossed"], crossed, p["trail"], implied_spot))
            # Breakeven lock once 1R of profit is banked, independent of ladder lines.
            if px - p["entry"] >= TSL_TRIGGER_R * SL_POINTS:
                p["trail"] = max(p["trail"], p["entry"])
            if px <= p["trail"]:
                exit_reason = "trail hit" if p["trail"] > p["entry"] - SL_POINTS + 1e-9 else "SL hit"

        if exit_reason:
            pnl_pts = px - p["entry"]
            pnl_rupees = pnl_pts * QTY

            if pnl_pts > 0:
                exit_note = ("Profit: %s premium ran from %.2f to %.2f (+%.2f pts, %d ladder "
                             "line(s) crossed) before %s." %
                             (p["side"], p["entry"], px, pnl_pts, p["crossed"], exit_reason))
            elif pnl_pts < 0:
                exit_note = ("Loss: %s premium fell from %.2f to %.2f (%.2f pts) - %s. "
                             "SL/TSL was at %.2f when closed." %
                             (p["side"], p["entry"], px, pnl_pts, exit_reason, p["trail"]))
            else:
                exit_note = ("Breakeven: exited flat at %.2f via %s, no gain/loss." % (px, exit_reason))

            conn.execute("INSERT INTO orb_trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         (session_date.isoformat(), p["ts"], p["side"],
                          atm, p["entry"], ts.isoformat(), px, exit_reason,
                          p["crossed"], pnl_pts, p["entry_note"], exit_note))
            conn.commit()
            st.daily_pnl_rupees += pnl_rupees
            alert("EXIT %s @ %.2f (%s) | PnL %.2f pts (Rs %.2f, qty %d) | lines crossed %d | "
                  "day PnL Rs %.2f"
                  % (p["side"], px, exit_reason, pnl_pts, pnl_rupees, QTY, p["crossed"],
                     st.daily_pnl_rupees))
            try:
                orb_journal.append_trade(session_date, {
                    "entry_ts": p["ts"], "exit_ts": ts.isoformat(), "side": p["side"],
                    "strike": atm, "qty": QTY, "entry_price": p["entry"], "exit_price": px,
                    "pnl_points": round(pnl_pts, 2), "pnl_rupees": round(pnl_rupees, 2),
                    "lines_crossed": p["crossed"], "exit_reason": exit_reason,
                    "why_entered": p["entry_note"], "why_pnl": exit_note,
                })
            except Exception as e:
                alert("journal write failed: %s" % e)
            if pnl_pts < 0:
                st.stops += 1
            if st.daily_pnl_rupees <= -MAX_DAILY_LOSS:
                st.locked = True
                alert("LOCKED OUT: daily loss Rs %.2f hit max Rs %.2f. No more trades today."
                      % (st.daily_pnl_rupees, MAX_DAILY_LOSS))
            elif st.stops >= MAX_STOPS_PER_DAY:
                st.locked = True
                alert("LOCKED OUT: %d stops today. Machine is done. So are you." % st.stops)
            st.position = None
        _snapshot(session_date, atm, sp_high, sp_low, st)
        return

    # ---- no position: look for a winner
    if st.locked or st.signals >= MAX_SIGNALS_PER_DAY or t >= LAST_ENTRY:
        _snapshot(session_date, atm, sp_high, sp_low, st)
        return

    ce_wins = (implied_spot > sp_high
               and ce_c.close > atm_ce["high"]
               and pe_c.close < atm_pe["low"])
    pe_wins = (implied_spot < sp_low
               and pe_c.close > atm_pe["high"]
               and ce_c.close < atm_ce["low"])

    if ce_wins or pe_wins:
        side  = "CE" if ce_wins else "PE"
        entry = ce_c.close if ce_wins else pe_c.close
        direction = "above SP High %d" % sp_high if ce_wins else "below SP Low %d" % sp_low
        if ce_wins:
            ce_note = "ATM CE closed above its 9:15 high %.2f (at %.2f)" % (atm_ce["high"], ce_c.close)
            pe_note = "ATM PE closed below its 9:15 low %.2f (at %.2f)" % (atm_pe["low"], pe_c.close)
        else:
            ce_note = "ATM CE closed below its 9:15 low %.2f (at %.2f)" % (atm_ce["low"], ce_c.close)
            pe_note = "ATM PE closed above its 9:15 high %.2f (at %.2f)" % (atm_pe["high"], pe_c.close)
        entry_note = (
            "%s WINS: implied spot %.1f closed %s (triple confirmation) - %s and %s. "
            "Bought ATM %s at %.2f." % (side, implied_spot, direction, ce_note, pe_note, side, entry)
        )
        st.position = {
            "side": side, "entry": entry, "ts": ts.isoformat(),
            "trail": max(0.0, entry - SL_POINTS),   # initial SL: fixed rupee risk budget
            "lines": ladder_lines(levels, atm, side),
            "crossed": 0,
            "entry_note": entry_note,
        }
        st.signals += 1
        alert("ENTRY: %s WINS | buy ATM %s x%d @ %.2f | implied spot %.1f | zone %d-%d | "
              "SL %.2f (Rs %.0f risk) | targets %s"
              % (side, side, QTY, entry, implied_spot, sp_low, sp_high,
                 st.position["trail"], SL_POINTS * QTY,
                 ["%.1f" % x for x in st.position["lines"]]))
    _snapshot(session_date, atm, sp_high, sp_low, st)

def run_replay(session_date):
    atm, sp_high, sp_low, levels = load_day(session_date)
    ce_key = levels[(atm, "CE")]["key"]
    pe_key = levels[(atm, "PE")]["key"]
    ce = resample(fetch_historical_candles(ce_key, 1, session_date, session_date), CANDLE_MINUTES)
    pe = resample(fetch_historical_candles(pe_key, 1, session_date, session_date), CANDLE_MINUTES)
    pe_by_ts = {c.ts: c for c in pe}
    st, conn = DayState(), db()
    alert("REPLAY %s | ATM %d | SP zone %d-%d" % (session_date, atm, sp_low, sp_high))
    for c in ce:
        mate = pe_by_ts.get(c.ts)
        if mate and c.ts.time() >= datetime.strptime("09:21", "%H:%M").time():
            on_candle_close(c.ts, c, mate, atm, sp_high, sp_low, levels, st, conn, session_date)
    if st.signals == 0:
        alert("No trade all day - NEUTRAL state held. That is a win over sentiment.")

def run_live_for_day(session_date):
    atm, sp_high, sp_low, levels = load_day(session_date)
    ce_key = levels[(atm, "CE")]["key"]
    pe_key = levels[(atm, "PE")]["key"]
    st, conn = DayState(), db()
    seen = set()
    alert("LIVE %s | ATM %d | SP zone %d-%d | waiting for closes..."
          % (session_date, atm, sp_low, sp_high))
    while datetime.now(IST).time() < SQUARE_OFF or st.position:
        try:
            ce = resample(fetch_intraday_candles(ce_key, 1), CANDLE_MINUTES)
            pe = resample(fetch_intraday_candles(pe_key, 1), CANDLE_MINUTES)
            pe_by_ts = {c.ts: c for c in pe}
            now = datetime.now(IST)
            for c in ce[:-1]:                     # last bucket is still forming
                if c.ts in seen:
                    continue
                mate = pe_by_ts.get(c.ts)
                if mate:
                    seen.add(c.ts)
                    on_candle_close(c.ts, c, mate, atm, sp_high, sp_low,
                                    levels, st, conn, session_date)
        except Exception as e:
            alert("live loop error: %s" % e)
        systime.sleep(20)
    alert("Session done. Signals: %d, stops: %d" % (st.signals, st.stops))

def run_live():
    run_live_for_day(datetime.now(IST).date())

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--replay", help="YYYY-MM-DD")
    g.add_argument("--live", action="store_true")
    a = p.parse_args()
    if a.replay:
        run_replay(date.fromisoformat(a.replay))
    else:
        run_live()

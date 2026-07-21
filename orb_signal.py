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
                        MAX_STOPS_PER_DAY, fetch_intraday_candles,
                        fetch_historical_candles, resample, db, alert)

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
            exit_reason = "square off 15:15"
        elif p["lines"] and px >= p["lines"][0]:
            crossed = p["lines"].pop(0)
            p["crossed"] += 1
            p["trail"] = max(p["trail"], crossed * 0.85)  # trail below the crossed line
            alert("LINE %d crossed at %.2f | trail -> %.2f | implied spot %.1f"
                  % (p["crossed"], crossed, p["trail"], implied_spot))
        if not exit_reason and px <= p["trail"]:
            exit_reason = "trail hit"

        if exit_reason:
            pnl = px - p["entry"]
            conn.execute("INSERT INTO orb_trades VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (session_date.isoformat(), p["ts"].isoformat(), p["side"],
                          atm, p["entry"], ts.isoformat(), px, exit_reason,
                          p["crossed"], pnl))
            conn.commit()
            alert("EXIT %s @ %.2f (%s) | PnL %.2f pts | lines crossed %d"
                  % (p["side"], px, exit_reason, pnl, p["crossed"]))
            if pnl < 0:
                st.stops += 1
                if st.stops >= MAX_STOPS_PER_DAY:
                    st.locked = True
                    alert("LOCKED OUT: %d stops today. Machine is done. So are you." % st.stops)
            st.position = None
        return

    # ---- no position: look for a winner
    if st.locked or st.signals >= MAX_SIGNALS_PER_DAY or t >= LAST_ENTRY:
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
        ref   = atm_ce if ce_wins else atm_pe
        st.position = {
            "side": side, "entry": entry, "ts": ts,
            "trail": ref["low"] if ce_wins else ref["low"],   # initial stop: own 09:15 low
            "lines": ladder_lines(levels, atm, side),
            "crossed": 0,
        }
        # tighter initial stop: never risk more than one strike-gap of premium
        st.position["trail"] = max(st.position["trail"], entry * 0.7)
        st.signals += 1
        alert("ENTRY: %s WINS | buy ATM %s @ %.2f | implied spot %.1f | zone %d-%d | "
              "targets %s" % (side, side, entry, implied_spot, sp_low, sp_high,
                              ["%.1f" % x for x in st.position["lines"]]))

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

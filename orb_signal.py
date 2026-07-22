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
from datetime import date, datetime, timedelta
from orb_common import (IST, CANDLE_MINUTES, SIGNAL_STRIKES, STRIKE_GAP,
                        LAST_ENTRY, SQUARE_OFF, MAX_SIGNALS_PER_DAY,
                        MAX_STOPS_PER_DAY, QTY, MAX_DAILY_LOSS, SL_POINTS,
                        TSL_TRIGGER_R, TSL_STEP_POINTS, MIN_PROFIT_POINTS,
                        APP_NAME, SERVER_NAME, get_ltp,
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

def ladder_strikes_ordered(levels, atm, winning_side):
    """Same ladder as ladder_lines(), but keeping (strike, instrument_key, level)
    together and ordered ATM-outward (nearest strike first) - needed so we know
    WHICH contract's own live premium to watch for the early-exit rule below."""
    out = []
    for i in range(1, SIGNAL_STRIKES + 1):
        k = atm - i * STRIKE_GAP if winning_side == "CE" else atm + i * STRIKE_GAP
        rec = levels.get((k, winning_side))
        if rec:
            out.append({"strike": k, "key": rec["key"], "level": rec["high"]})
    return out

def build_watch_pairs(levels, atm, winning_side):
    """Early-exit rule: for each strike in the ladder (ITM1..ITM6 or OTM1..OTM6),
    pair its OWN instrument_key with the NEXT strike's level. If that strike's own
    live premium ever reaches the next rung before our position reaches its own R1,
    the move has already skipped ahead at a different strike - exit now rather
    than waiting for our own target or SL."""
    ladder = ladder_strikes_ordered(levels, atm, winning_side)
    return [(ladder[i]["key"], ladder[i + 1]["level"]) for i in range(len(ladder) - 1)]

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

def on_candle_close(ts, ce_c, pe_c, atm, sp_high, sp_low, levels, st, conn, session_date,
                     ltp_fn=None):
    """ce_c / pe_c are the just-closed N-min candles of the ATM CE / ATM PE.

    ltp_fn: optional callable(instrument_key) -> float, used only for the
    other-strike early-exit check below. Pass None to disable that check
    (e.g. in replay, where we don't have live/intrabar data for every
    strike in the ladder - only its own 09:15 first candle)."""
    implied_spot = atm + ce_c.close - pe_c.close
    atm_ce = levels[(atm, "CE")]
    atm_pe = levels[(atm, "PE")]
    t = ts.time()

    # ---- manage open position first
    if st.position:
        p = st.position
        px = ce_c.close if p["side"] == "CE" else pe_c.close
        exit_reason = None

        # Other-strike early exit: if a DEEPER strike's own live premium has
        # already reached the level one rung further out than IT (not our
        # own R1), the move has skipped ahead somewhere else in the ±6
        # ladder - exit right now, don't wait for our own SL or TSL.
        if ltp_fn and p.get("watch_pairs"):
            for ikey, next_level in p["watch_pairs"]:
                try:
                    if ltp_fn(ikey) >= next_level:
                        exit_reason = "other strike reached its next level first - early exit"
                        break
                except Exception:
                    continue

        # Ladder-line trailing and profit-lock run every candle, BEFORE the
        # zone-reentry check below - so a trade that has already locked in
        # MIN_PROFIT_POINTS is protected by the trail, not by the
        # directional (zone) thesis, which can whipsaw back before the
        # trail is actually touched.
        if exit_reason:
            pass   # early exit already decided above - skip trail/zone logic entirely
        elif p["lines"] and px >= p["lines"][0]:
            crossed = p["lines"].pop(0)
            p["crossed"] += 1
            # TSL: trail a fixed buffer behind each ladder line crossed.
            p["trail"] = max(p["trail"], crossed - TSL_STEP_POINTS)
            alert("LINE %d crossed at %.2f | TSL -> %.2f | implied spot %.1f"
                  % (p["crossed"], crossed, p["trail"], implied_spot))
        # Profit lock once 1R is banked: TSL floor moves to entry + MIN_PROFIT_POINTS
        # (not plain breakeven) so a "win" clears fees/STT/brokerage instead of
        # exiting flat or net-negative after costs. Independent of ladder lines.
        if px - p["entry"] >= TSL_TRIGGER_R * SL_POINTS:
            p["trail"] = max(p["trail"], p["entry"] + MIN_PROFIT_POINTS)
        profit_locked = p["trail"] >= p["entry"] + MIN_PROFIT_POINTS - 1e-9

        zone_reentry = ((p["side"] == "CE" and implied_spot < sp_high)
                         or (p["side"] == "PE" and implied_spot > sp_low))

        if exit_reason:
            pass   # already decided by the other-strike early exit above - highest priority
        elif t >= SQUARE_OFF:
            exit_reason = "square off 15:15 (forced flat)"
        elif zone_reentry and not profit_locked:
            # Directional thesis invalidated before any profit was secured -
            # cut immediately, same as before.
            exit_reason = "spot back in zone"
        elif px <= p["trail"]:
            exit_reason = "trail hit" if profit_locked else "SL hit"

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
            "watch_pairs": build_watch_pairs(levels, atm, side),
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

    # Full-ladder backfill: fetch every ATM +/- SIGNAL_STRIKES contract's 1-min
    # historical candles (not just the ATM's own CE/PE) so the other-strike
    # early-exit rule can be backtested too, not just simulated live. This is
    # the expensive part - up to (2*SIGNAL_STRIKES+1)*2 contracts fetched once
    # per replayed day.
    all_keys = sorted({rec["key"] for rec in levels.values()})
    alert("REPLAY %s | ATM %d | SP zone %d-%d | backfilling %d contracts for the full "
          "+/- %d ladder..." % (session_date, atm, sp_low, sp_high, len(all_keys), SIGNAL_STRIKES))
    hist_by_key = {}
    for key in all_keys:
        try:
            candles = resample(fetch_historical_candles(key, 1, session_date, session_date),
                               CANDLE_MINUTES)
            hist_by_key[key] = {c.ts: c.close for c in candles}
        except Exception as e:
            alert("REPLAY %s | WARN: could not backfill %s (%s) - early-exit checks "
                  "involving this strike will be skipped." % (session_date, key, e))
            hist_by_key[key] = {}

    def historical_ltp_fn(ts):
        def _fn(instrument_key):
            close = hist_by_key.get(instrument_key, {}).get(ts)
            if close is None:
                raise KeyError("no backfilled candle for %s at %s" % (instrument_key, ts))
            return close
        return _fn

    # ATM CE/PE are already in hist_by_key from the full-ladder backfill above -
    # reuse it instead of fetching those two contracts a second time.
    class _Px:
        __slots__ = ("ts", "close")
        def __init__(self, ts, close):
            self.ts, self.close = ts, close

    ce_series = sorted(hist_by_key.get(ce_key, {}).items())
    pe_map = hist_by_key.get(pe_key, {})
    cutoff_time = datetime.strptime("09:21", "%H:%M").time()

    st, conn = DayState(), db()
    for ts, ce_close in ce_series:
        pe_close = pe_map.get(ts)
        if pe_close is not None and ts.time() >= cutoff_time:
            on_candle_close(ts, _Px(ts, ce_close), _Px(ts, pe_close), atm, sp_high, sp_low,
                            levels, st, conn, session_date, ltp_fn=historical_ltp_fn(ts))
    if st.signals == 0:
        alert("No trade all day - NEUTRAL state held. That is a win over sentiment.")

def run_live_for_day(session_date):
    atm, sp_high, sp_low, levels = load_day(session_date)
    ce_key = levels[(atm, "CE")]["key"]
    pe_key = levels[(atm, "PE")]["key"]
    st, conn = DayState(), db()
    seen = set()

    # Catch-up pass: if this process starts (or reconnects) after 09:21,
    # fetching candle history returns the whole morning's backlog at once.
    # Mark every backlog candle as seen WITHOUT running it through
    # on_candle_close - those closes are stale by the time we see them, and
    # acting on them would enter/exit at a price the market left behind
    # minutes or hours ago. Only candles that close from here forward are
    # treated as live signals.
    try:
        ce0 = resample(fetch_intraday_candles(ce_key, 1), CANDLE_MINUTES)
        pe0 = resample(fetch_intraday_candles(pe_key, 1), CANDLE_MINUTES)
        pe0_by_ts = {c.ts: c for c in pe0}
        cutoff = datetime.now(IST) - timedelta(minutes=CANDLE_MINUTES)
        backlog = 0
        for c in ce0[:-1]:
            if c.ts < cutoff and pe0_by_ts.get(c.ts):
                seen.add(c.ts)
                backlog += 1
        if backlog:
            alert("LIVE %s | caught up on %d stale backlog candle(s) without acting on them "
                  "(process started late) - only candles closing from now on are live signals."
                  % (session_date, backlog))
    except Exception as e:
        alert("live loop catch-up failed: %s" % e)

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
                                    levels, st, conn, session_date, ltp_fn=get_ltp)
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

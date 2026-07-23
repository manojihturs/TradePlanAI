# orb_signal.py - CE-wins / PE-wins state machine with triple confirmation.
#
#   NEUTRAL  : implied spot inside SP zone -> NO TRADE (the anti-sentiment rule)
#   CE_WINS  : implied spot close > SP High  AND ATM CE close > its 09:15 high
#                                            AND ATM PE close < its 09:15 low
#   PE_WINS  : the mirror.
#
# Entry  = close of the confirmation candle (5-min), on the winning ATM contract.
# Stop   = implied spot closes back inside the SP zone (before any profit is locked).
# Trail  = cross-plotted ladder: the OPPOSITE side's first-5min LOW at every
#          strike ATM +/- SIGNAL_STRIKES (CE_WINS -> watch PE lows, PE_WINS ->
#          watch CE lows) - not the winning side's own extension.
# Limits = MAX_DAILY_LOSS (rupees, hard lockout), LAST_ENTRY, SQUARE_OFF (time cutoffs).
# No cap on signal count or stop count per day - the machine keeps looking
# for fresh setups all day; only running out of money or time stops it.
#
# Usage:
#   python orb_signal.py --replay 2026-07-21     (after capturing that date)
#   python orb_signal.py --live                  (after today's 09:21 capture)

import argparse, time as systime
from datetime import date, datetime, timedelta
from orb_common import (IST, CANDLE_MINUTES, SIGNAL_STRIKES, STRIKE_GAP, ORB_LOCK,
                        LAST_ENTRY, SQUARE_OFF,
                        QTY, MAX_DAILY_LOSS, SL_POINTS,
                        MIN_PROFIT_POINTS,
                        MIN_ENTRY_MARGIN_POINTS, MIN_COMPETITOR_DISTANCE_POINTS,
                        APP_NAME, SERVER_NAME, get_ltp, is_competitor_exit_enabled,
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

def ladder_strikes_ordered(levels, atm, winning_side):
    """The trader's actual cross-plotted ladder (confirmed in chat):
      TOP    (CE_WINS, holding the CALL) -> watch the PUT's first-5min LOW
             at every strike ATM +/- SIGNAL_STRIKES.
      BOTTOM (PE_WINS, holding the PUT)  -> watch the CALL's first-5min LOW
             at every strike ATM +/- SIGNAL_STRIKES.
    In both cases it's the OPPOSITE side's LOW, never the winning side's own
    high - the ladder is a cross-plot, not a same-side extension. This is
    what makes it a support/resistance ruler on the contract you're actually
    holding, rather than a self-referential extrapolation of its own decay.
    ATM itself is excluded (its opposite-side low is already the entry's own
    triple-confirmation condition, not a further target). Returns
    (strike, instrument_key, level) ascending by level."""
    opposite_side = "PE" if winning_side == "CE" else "CE"
    out = []
    for i in range(-SIGNAL_STRIKES, SIGNAL_STRIKES + 1):
        if i == 0:
            continue
        k = atm + i * STRIKE_GAP
        rec = levels.get((k, opposite_side))
        if rec:
            out.append({"strike": k, "key": rec["key"], "level": rec["low"]})
    out.sort(key=lambda d: d["level"])
    return out

def ladder_lines(levels, atm, winning_side):
    """Just the ascending level values from ladder_strikes_ordered() - the
    numbers the traded contract's own premium is compared against."""
    return [d["level"] for d in ladder_strikes_ordered(levels, atm, winning_side)]

def build_watch_pairs(levels, atm, winning_side):
    """Early-exit rule: for each strike in the ladder (ITM1..ITM6 or OTM1..OTM6),
    pair its OWN (strike, instrument_key) with the NEXT strike's level. If that
    strike's own live premium ever reaches the next rung before our position
    reaches its own R1, the move has already skipped ahead at a different
    strike - exit now rather than waiting for our own target or SL.
    Returns a list of dicts: {strike, key, next_level} - strike is kept
    alongside the key so alerts/journal entries can name which strike
    triggered the exit, not just report an opaque instrument_key."""
    ladder = ladder_strikes_ordered(levels, atm, winning_side)
    return [{"strike": ladder[i]["strike"], "key": ladder[i]["key"],
             "next_level": ladder[i + 1]["level"]} for i in range(len(ladder) - 1)]

# The other-strike (+/- SIGNAL_STRIKES) early-exit rule above is intact but
# switched off for now, per instruction, in favor of the simpler single-
# competitor rule below. Flip this back on to re-enable it.
ENABLE_OTHER_STRIKE_EARLY_EXIT = False

def competitor_reference(levels, atm, our_side, entry):
    """Simplified competitor exit rule (replaces the +/- SIGNAL_STRIKES scan
    for now): only the SAME strike K that feeds our own target1 is used, no
    other strikes are scanned.

    entry: our own entry price, needed to find the SAME strike that
    future_lines[0] (our real target1) uses - the ladder's raw first
    element can be below entry (already-passed, filtered out of our own
    targets), so this must apply the identical entry-price filter, not
    just take ladder_strikes_ordered()[0] blindly.

    Our own ladder at K comes from the OPPOSITE side's LOW (ladder_strikes_
    ordered). The competitor - the ATM contract we did NOT buy - has its own
    symmetric reference at that same strike K, but from OUR side's HIGH field
    instead of LOW:
      TOP    (holding CE, ladder = PE-low @ K) -> competitor (PE) reference
             = CE-high @ K
      BOTTOM (holding PE, ladder = CE-low @ K) -> competitor (CE) reference
             = PE-high @ K
    In both cases that's levels[(K, our_side)]["high"] - reusing data already
    captured, no other-strike scanning. The actual check (see on_candle_close)
    is competitor_close <= level for BOTH sides - the competitor must always
    fall (this is the behavior already validated against real backtest data;
    "the losing side's premium decays as the winning side's move continues,
    regardless of which side is winning" - not a rise for one side and a
    fall for the other). If the competitor's live premium falls to/through
    this level before our own target1 is hit, market leadership has flipped
    to the competitor - exit now.

    MIN_COMPETITOR_DISTANCE_POINTS floor: the raw captured level above can
    land arbitrarily close to the competitor's own ATM 9:15 range (found by
    inspecting raw strike data - this was why PE trades exited in ~9 min on
    average). Since the competitor must always fall to trigger, the floor
    always pushes the level DOWN (stricter = farther below where the
    competitor already sits) relative to the competitor's own 9:15 low,
    whichever of raw/floor is lower (harder to reach).
    Returns (K, level) or (None, None) if there's no real target ahead of entry."""
    ladder = [d for d in ladder_strikes_ordered(levels, atm, our_side) if d["level"] > entry]
    if not ladder:
        return None, None
    k = ladder[0]["strike"]
    rec = levels.get((k, our_side))
    if not rec:
        return None, None
    raw_level = rec["high"]

    competitor_side = "PE" if our_side == "CE" else "CE"
    atm_competitor = levels.get((atm, competitor_side))
    if atm_competitor:
        level = min(raw_level, atm_competitor["low"] - MIN_COMPETITOR_DISTANCE_POINTS)
    else:
        level = raw_level
    return k, level

class DayState:
    def __init__(self):
        self.position = None          # dict when in a trade
        self.signals = 0
        self.stops = 0
        self.locked = False
        self.daily_pnl_rupees = 0.0
        self.pending = None            # {"side": "CE"/"PE"} - candle 1 of a 2-candle confirm
        self.excursion_side = None     # "CE"/"PE"/None - which side of the zone spot is
                                       # currently outside on, across an unbroken run of
                                       # candles (tracked every candle, position or not)
        self.excursion_extreme = None  # best (highest for CE, lowest for PE) implied_spot
                                       # reached so far in the CURRENT excursion

# Off by default - live behavior unchanged. When True, a winning condition
# must hold on two CONSECUTIVE candle closes (same side both times) before
# entering, instead of entering on the first close that satisfies it. Added
# after 2 of 3 live trades on 2026-07-23 lost via "spot back in zone" - the
# breakout confirmed on one candle then reversed before profit ever locked,
# i.e. a single-candle fake breakout. BACKTESTED AND REJECTED 2026-07-23:
# across 14 sessions this turned a +Rs 5905.25 baseline into -Rs 4995.25 -
# it mostly just delays entries into worse fills rather than filtering bad
# ones. Left in place, defaulted off, as a documented negative result.
REQUIRE_TWO_CANDLE_CONFIRMATION = False

# Off by default - live behavior unchanged. When True, blocks a new entry if
# spot has already pulled back more than STALE_REENTRY_PULLBACK_POINTS from
# the best level reached so far in the current excursion outside the zone.
# Targets a specific failure mode found in the 2026-07-23 post-mortem: trade
# #3 that day (CE @171.85, -Rs 1205.75) fired at 11:10 while ALREADY IN A
# POSITION opened at 10:45 blocked the system from acting during the actual
# peak of the move (23994.7 implied at 11:00) - by the time the prior trade
# closed and this one could fire, spot had already pulled back 21pts and was
# falling for two straight candles. This is a genuinely late/stale re-entry,
# distinct from trade #4 that same day (a fresh excursion extreme at entry,
# which this filter would NOT have blocked - that loss was normal exhaustion
# risk, not staleness). Excursion tracking runs every candle regardless of
# position state, specifically so a move that happens WHILE a position is
# open is still correctly remembered once that position closes.
REQUIRE_FRESH_EXTREME_FOR_ENTRY = False
STALE_REENTRY_PULLBACK_POINTS = 10.0

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
                     ltp_fn=None, source="live"):
    """ce_c / pe_c are the just-closed N-min candles of the ATM CE / ATM PE.

    ltp_fn: optional callable(instrument_key) -> float, used only for the
    other-strike early-exit check below. Pass None to disable that check
    (e.g. in replay, where we don't have live/intrabar data for every
    strike in the ladder - only its own 09:15 first candle).

    source: "live" or "replay" - tags every row this call writes to
    orb_trades/the journal, so a real execution and a backtest simulation
    are never indistinguishable in the historical record."""
    implied_spot = atm + ce_c.close - pe_c.close
    atm_ce = levels[(atm, "CE")]
    atm_pe = levels[(atm, "PE")]
    t = ts.time()

    # Excursion tracking: runs every candle regardless of position state, so
    # a move that happens WHILE a position is open (and therefore can't be
    # acted on) is still remembered once that position closes and a new
    # entry is evaluated. Only feeds REQUIRE_FRESH_EXTREME_FOR_ENTRY below.
    if implied_spot > sp_high:
        if st.excursion_side != "CE":
            st.excursion_side, st.excursion_extreme = "CE", implied_spot
        else:
            st.excursion_extreme = max(st.excursion_extreme, implied_spot)
    elif implied_spot < sp_low:
        if st.excursion_side != "PE":
            st.excursion_side, st.excursion_extreme = "PE", implied_spot
        else:
            st.excursion_extreme = min(st.excursion_extreme, implied_spot)
    else:
        st.excursion_side, st.excursion_extreme = None, None   # back inside zone - excursion over

    # ---- manage open position first
    if st.position:
        p = st.position
        px = ce_c.close if p["side"] == "CE" else pe_c.close
        exit_reason = None
        trigger_strike = None   # set below if the other-strike early exit fires

        # Other-strike early exit (±SIGNAL_STRIKES scan) - currently disabled,
        # see ENABLE_OTHER_STRIKE_EARLY_EXIT above.
        if ENABLE_OTHER_STRIKE_EARLY_EXIT and ltp_fn and p.get("watch_pairs"):
            for pair in p["watch_pairs"]:
                try:
                    live_val = ltp_fn(pair["key"])
                    if live_val >= pair["next_level"]:
                        trigger_strike = {"strike": pair["strike"], "live_value": live_val,
                                          "next_level": pair["next_level"]}
                        exit_reason = ("strike %d reached %.2f (its own next level %.2f) first "
                                      "- early exit" % (pair["strike"], live_val, pair["next_level"]))
                        break
                except Exception:
                    continue

        # Simplified competitor exit: the ATM contract we did NOT buy has its
        # own symmetric reference at the SAME strike that feeds our target1
        # (see competitor_reference()). If the competitor's live price has
        # fallen to/through that level BEFORE our own target1 is hit, market
        # leadership has flipped - exit now, don't wait for target1 or SL.
        # Toggleable from the dashboard (orb_ui.py) - read fresh every candle
        # so a live toggle takes effect on the running process immediately.
        if (not exit_reason and is_competitor_exit_enabled()
                and p.get("lines") and p.get("competitor_level") is not None):
            competitor_close = pe_c.close if p["side"] == "CE" else ce_c.close
            if competitor_close <= p["competitor_level"]:
                exit_reason = ("competitor %s reached %.2f (its level %.2f at strike %d) before "
                              "our target1 - leadership flipped, early exit"
                              % ("PE" if p["side"] == "CE" else "CE", competitor_close,
                                 p["competitor_level"], p["competitor_strike"]))

        # Ladder-line trailing and profit-lock run every candle, BEFORE the
        # zone-reentry check below - so a trade that has already locked in
        # MIN_PROFIT_POINTS is protected by the trail, not by the
        # directional (zone) thesis, which can whipsaw back before the
        # trail is actually touched.
        # LINE 1 crossed = confirmed win, take it now. Per instruction: don't
        # hold out trailing for line 2/3/etc - the first target hit IS the
        # exit signal, immediately, so the machine is free to look for the
        # next opportunity right away instead of riding one position and
        # hoping for more.
        if not exit_reason and p["lines"] and px >= p["lines"][0]:
            crossed = p["lines"][0]
            p["crossed"] += 1
            exit_reason = "LINE 1 target hit (%.2f) - confirmed, exit now" % crossed

        # Profit lock the moment we're up by AT LEAST MIN_PROFIT_POINTS - not
        # after a full 1R (~19pt) move. Found live: today's real target gaps
        # (e.g. 172.55 -> 178.30, a ~5.75pt move) are often smaller than 1R,
        # so waiting for 1R meant the 3-point TSL floor could never engage in
        # time to protect a trade that stalled partway and reversed. This
        # makes "TSL must be at least 3 points" a standing guarantee on any
        # real gain, not something that only shows up on unusually large
        # moves. Target1 still takes priority whenever it's actually reached
        # (checked above, before this).
        if px - p["entry"] >= MIN_PROFIT_POINTS:
            p["trail"] = max(p["trail"], p["entry"] + MIN_PROFIT_POINTS)
        profit_locked = p["trail"] >= p["entry"] + MIN_PROFIT_POINTS - 1e-9

        zone_reentry = ((p["side"] == "CE" and implied_spot < sp_high)
                         or (p["side"] == "PE" and implied_spot > sp_low))

        if exit_reason:
            pass   # already decided above (early exit or LINE 1 target) - highest priority
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

            conn.execute("INSERT INTO orb_trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (session_date.isoformat(), p["ts"], p["side"],
                          atm, p["entry"], ts.isoformat(), px, exit_reason,
                          p["crossed"], pnl_pts, p["entry_note"], exit_note, source))
            conn.commit()
            st.daily_pnl_rupees += pnl_rupees
            trigger_txt = (" | trigger strike %d @ %.2f (next level %.2f)"
                          % (trigger_strike["strike"], trigger_strike["live_value"],
                             trigger_strike["next_level"])) if trigger_strike else ""
            alert("EXIT %s @ %.2f (%s) | ATM %d | PnL %.2f pts (Rs %.2f, qty %d) | lines crossed %d | "
                  "day PnL Rs %.2f%s | Competitor: %s [%s]"
                  % (p["side"], px, exit_reason, atm, pnl_pts, pnl_rupees, QTY, p["crossed"],
                     st.daily_pnl_rupees, trigger_txt,
                     "ON" if is_competitor_exit_enabled() else "OFF", source))
            try:
                orb_journal.append_trade(session_date, {
                    "entry_ts": p["ts"], "exit_ts": ts.isoformat(), "side": p["side"],
                    "atm_strike": atm, "strike": atm, "qty": QTY, "source": source,
                    "entry_price": p["entry"], "exit_price": px,
                    "pnl_points": round(pnl_pts, 2), "pnl_rupees": round(pnl_rupees, 2),
                    "lines_crossed": p["crossed"], "exit_reason": exit_reason,
                    "trigger_strike": trigger_strike["strike"] if trigger_strike else "",
                    "trigger_strike_value": (round(trigger_strike["live_value"], 2)
                                            if trigger_strike else ""),
                    "why_entered": p["entry_note"], "why_pnl": exit_note,
                })
            except Exception as e:
                alert("journal write failed: %s" % e)
            if pnl_pts < 0:
                st.stops += 1
            # No stop-count or signal-count cap anymore - per instruction, keep
            # looking for fresh setups all day. The ONLY hard stop left is the
            # rupee daily-loss cap below (real capital protection); everything
            # else (LAST_ENTRY, SQUARE_OFF) is a time cutoff, not a loss cutoff.
            if st.daily_pnl_rupees <= -MAX_DAILY_LOSS:
                st.locked = True
                alert("LOCKED OUT: daily loss Rs %.2f hit max Rs %.2f. No more trades today."
                      % (st.daily_pnl_rupees, MAX_DAILY_LOSS))
            st.position = None
        _snapshot(session_date, atm, sp_high, sp_low, st)
        return

    # ---- no position: look for a winner
    # No cap on number of signals/day anymore - only a locked account (rupee
    # daily-loss cap) or the LAST_ENTRY time cutoff stop new entries.
    if st.locked or t >= LAST_ENTRY:
        _snapshot(session_date, atm, sp_high, sp_low, st)
        return

    # MIN_ENTRY_MARGIN_POINTS applies to the TRADED side's own breakout
    # specifically (the condition backtested): a close that only barely beats
    # its own 9:15 extreme is a much weaker signal than the boolean alone
    # implies. The supporting (opposite-side decay) condition is left as a
    # plain boolean - that wasn't what the data tested.
    ce_wins = (implied_spot > sp_high
               and ce_c.close > atm_ce["high"] + MIN_ENTRY_MARGIN_POINTS
               and pe_c.close < atm_pe["low"])
    pe_wins = (implied_spot < sp_low
               and pe_c.close > atm_pe["high"] + MIN_ENTRY_MARGIN_POINTS
               and ce_c.close < atm_ce["low"])

    if REQUIRE_FRESH_EXTREME_FOR_ENTRY:
        # Block a stale re-entry: only allow the signal through if spot is
        # still within STALE_REENTRY_PULLBACK_POINTS of the best level this
        # excursion has reached so far (usually 0, i.e. THIS candle IS the
        # new extreme). If the excursion already peaked earlier - e.g. while
        # a prior position was open and blocking new entries - and has since
        # pulled back past the tolerance, treat it as already-faded, not a
        # fresh setup, even though the raw triple-confirmation still passes.
        if ce_wins and not (st.excursion_side == "CE"
                             and implied_spot >= st.excursion_extreme - STALE_REENTRY_PULLBACK_POINTS):
            ce_wins = False
        if pe_wins and not (st.excursion_side == "PE"
                             and implied_spot <= st.excursion_extreme + STALE_REENTRY_PULLBACK_POINTS):
            pe_wins = False

    if REQUIRE_TWO_CANDLE_CONFIRMATION:
        raw_side = "CE" if ce_wins else ("PE" if pe_wins else None)
        if raw_side is None:
            st.pending = None
            _snapshot(session_date, atm, sp_high, sp_low, st)
            return
        if not (st.pending and st.pending["side"] == raw_side):
            # First candle to satisfy the condition - flag it, wait for the
            # SAME side to confirm again on the next close before entering.
            st.pending = {"side": raw_side}
            _snapshot(session_date, atm, sp_high, sp_low, st)
            return
        st.pending = None   # confirmed - fall through to the entry below

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
        # Only levels AHEAD of entry are real targets. The cross-plotted ladder
        # spans the opposite side's low across the full +/- SIGNAL_STRIKES
        # range, which naturally includes reference values already below the
        # entry premium (different strike, unrelated magnitude) - counting
        # those as "crossed" the instant the position opens is noise, not
        # trend progress.
        future_lines = [x for x in ladder_lines(levels, atm, side) if x > entry]
        competitor_strike, competitor_level = competitor_reference(levels, atm, side, entry)
        st.position = {
            "side": side, "entry": entry, "ts": ts.isoformat(),
            "trail": max(0.0, entry - SL_POINTS),   # initial SL: fixed rupee risk budget
            "lines": future_lines,
            "watch_pairs": build_watch_pairs(levels, atm, side),
            "competitor_strike": competitor_strike, "competitor_level": competitor_level,
            "crossed": 0,
            "entry_note": entry_note,
        }
        st.signals += 1
        competitor_txt = (" | competitor %s level %.2f @ strike %d"
                          % ("PE" if side == "CE" else "CE", competitor_level, competitor_strike)
                          ) if competitor_level is not None else ""
        alert("ENTRY: %s WINS | ATM %d | buy ATM %s x%d @ %.2f | implied spot %.1f | zone %d-%d | "
              "SL %.2f (Rs %.0f risk) | targets %s%s | Competitor: %s [%s]"
              % (side, atm, side, QTY, entry, implied_spot, sp_low, sp_high,
                 st.position["trail"], SL_POINTS * QTY,
                 ["%.1f" % x for x in st.position["lines"]], competitor_txt,
                 "ON" if is_competitor_exit_enabled() else "OFF", source))
    _snapshot(session_date, atm, sp_high, sp_low, st)

def run_replay(session_date):
    atm, sp_high, sp_low, levels = load_day(session_date)
    ce_key = levels[(atm, "CE")]["key"]
    pe_key = levels[(atm, "PE")]["key"]

    # Full-ladder backfill: fetch every ATM +/- SIGNAL_STRIKES contract's 1-min
    # candles (not just the ATM's own CE/PE) so the other-strike early-exit
    # rule can be backtested too, not just simulated live. This is the
    # expensive part - up to (2*SIGNAL_STRIKES+1)*2 contracts fetched once
    # per replayed day.
    #
    # Upstox's /historical-candle endpoint only serves data for dates strictly
    # before today - it returns an EMPTY list for the current calendar day
    # even hours after close (verified: 0 historical candles vs 375 intraday
    # candles for the same key, same day). Using the wrong endpoint for a
    # same-day replay silently yields zero data -> zero trades, which looks
    # identical to a real "no signal fired all day" result unless we
    # distinguish them explicitly.
    is_today = (session_date == datetime.now(IST).date())
    fetch_fn = (lambda key: fetch_intraday_candles(key, 1)) if is_today else \
               (lambda key: fetch_historical_candles(key, 1, session_date, session_date))

    all_keys = sorted({rec["key"] for rec in levels.values()})
    alert("REPLAY %s | ATM %d | SP zone %d-%d | backfilling %d contracts for the full "
          "+/- %d ladder via %s endpoint..."
          % (session_date, atm, sp_low, sp_high, len(all_keys), SIGNAL_STRIKES,
             "intraday" if is_today else "historical"))
    hist_by_key = {}
    total_candles = 0
    for key in all_keys:
        try:
            candles = resample(fetch_fn(key), CANDLE_MINUTES)
            hist_by_key[key] = {c.ts: c.close for c in candles}
            total_candles += len(candles)
        except Exception as e:
            alert("REPLAY %s | WARN: could not backfill %s (%s) - early-exit checks "
                  "involving this strike will be skipped." % (session_date, key, e))
            hist_by_key[key] = {}

    if total_candles == 0:
        alert("REPLAY %s | ABORTED: 0 candles returned across all %d contracts - this is "
              "missing data, NOT a real 'no trade' result. If this is a same-day replay, the "
              "intraday endpoint may not be populated yet; if historical, Upstox may not retain "
              "data this far back for these contracts, or this wasn't a trading day. Not "
              "reporting a trade count for this day." % (session_date, len(all_keys)))
        return

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
    cutoff_time = ORB_LOCK   # 09:20 - first candle bucket after the opening range itself

    st, conn = DayState(), db()
    for ts, ce_close in ce_series:
        pe_close = pe_map.get(ts)
        if pe_close is not None and ts.time() >= cutoff_time:
            on_candle_close(ts, _Px(ts, ce_close), _Px(ts, pe_close), atm, sp_high, sp_low,
                            levels, st, conn, session_date, ltp_fn=historical_ltp_fn(ts),
                            source="replay")
    if st.signals == 0:
        alert("No trade all day - NEUTRAL state held. That is a win over sentiment.")

def run_live_for_day(session_date):
    atm, sp_high, sp_low, levels = load_day(session_date)
    ce_key = levels[(atm, "CE")]["key"]
    pe_key = levels[(atm, "PE")]["key"]
    st, conn = DayState(), db()
    seen = set()

    # Seed today's already-realized PnL/stops from the DB - DayState is
    # otherwise purely in-memory and starts at 0 on every process restart,
    # which happens routinely for code deploys. Without this, the rupee
    # MAX_DAILY_LOSS lockout - the only hard stop left after the stop/signal
    # count caps were removed - loses track of losses booked before the most
    # recent restart and can't actually stop the account at the real cap.
    # Only "live" rows count (never mix in replay/backtest simulation rows).
    prior = conn.execute(
        "SELECT COALESCE(SUM(pnl_points),0), SUM(CASE WHEN pnl_points<0 THEN 1 ELSE 0 END) "
        "FROM orb_trades WHERE session_date=? AND source='live'",
        (session_date.isoformat(),)).fetchone()
    prior_pts, prior_stops = prior[0] or 0.0, prior[1] or 0
    st.daily_pnl_rupees = prior_pts * QTY
    st.stops = prior_stops
    if prior_pts:
        alert("LIVE %s | resuming with today's already-realized PnL Rs %.2f (%d prior stop(s)) "
              "carried forward from before this restart." % (session_date, st.daily_pnl_rupees, prior_stops))
    if st.daily_pnl_rupees <= -MAX_DAILY_LOSS:
        st.locked = True
        alert("LOCKED OUT on startup: today's already-realized loss Rs %.2f already hit max "
              "Rs %.2f before this restart even began." % (st.daily_pnl_rupees, MAX_DAILY_LOSS))

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
                                    levels, st, conn, session_date, ltp_fn=get_ltp,
                                    source="live")
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

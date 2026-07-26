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
from datetime import date, datetime, time, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from orb_common import (IST, CANDLE_MINUTES, SIGNAL_STRIKES, STRIKE_GAP, ORB_LOCK,
                        LAST_ENTRY, SQUARE_OFF,
                        QTY, MAX_DAILY_LOSS, SL_POINTS,
                        MIN_PROFIT_POINTS, COST_PER_TRADE_RUPEES,
                        MIN_ENTRY_MARGIN_POINTS, MIN_COMPETITOR_DISTANCE_POINTS,
                        APP_NAME, SERVER_NAME, get_ltp, is_competitor_exit_enabled,
                        fetch_intraday_candles, fetch_historical_candles,
                        resample, db, alert, write_state, resolve_future_instrument_key)
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

# Off by default - see itm_strikes() below for why this exists.
ITM_ONLY_LADDER = False

def itm_strikes(atm, side, n=SIGNAL_STRIKES):
    """Strikes from ATM walking toward in-the-money for `side`, n deep - CE
    is ITM BELOW atm (a lower strike has more intrinsic value for a call),
    PE is ITM ABOVE atm (mirror). Added 2026-07-26 per the trader's own
    marking convention (spreadsheet screenshot: 'ATM to ITM', OTM strikes
    not marked at all) - used by ladder_strikes_ordered/pivot_ladder ONLY
    when ITM_ONLY_LADDER is on; default behavior still scans the full
    ATM +/- SIGNAL_STRIKES range on both sides."""
    step = -STRIKE_GAP if side == "CE" else STRIKE_GAP
    return [atm + i * step for i in range(1, n + 1)]

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
    (strike, instrument_key, level) ascending by level.

    Under ITM_ONLY_LADDER, the strike range is restricted to the OPPOSITE
    side's own ITM direction (per the trader's marking convention: PE-low
    is only marked on the CALL chart for PE strikes ITM relative to ATM,
    i.e. above ATM - not the OTM side below it), instead of the full +/-
    SIGNAL_STRIKES scan on both sides."""
    opposite_side = "PE" if winning_side == "CE" else "CE"
    if ITM_ONLY_LADDER:
        strikes = itm_strikes(atm, opposite_side)
    else:
        strikes = [atm + i * STRIKE_GAP for i in range(-SIGNAL_STRIKES, SIGNAL_STRIKES + 1) if i != 0]
    out = []
    for k in strikes:
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

# ---------------------------------------------------------------------------
# Ladder-pivot SL/TSL mode (2026-07-25, under review - OFF by default).
#
# Trader's rule from live chart review: SL should not be a fixed points
# value, it should be the nearest same-side strike level BEHIND entry (e.g.
# entry on 23800CE, SL = 23750CE high 133.45 - the "previous position/pivot"
# that price already cleared to get here). As the trade advances through
# each opposite-side ladder line (the existing p["lines"] targets), the SL
# ratchets forward to the same-side high one rung closer to that new price -
# i.e. always trail behind the LAST rung already cleared, never a flat
# points offset. And per instruction, do NOT exit at LINE 1 the way the
# default competitor/LINE-1 rule does (see "confirmed win, exit immediately"
# above) - keep riding, ladder rung by rung, for "maximum profit", and only
# get out on SL/TSL hit or the square-off cutoff.
#
# Gated behind MAX_PROFIT_LADDER_TRAIL so default live/replay behavior is
# completely unchanged until this is backtested and explicitly turned on.
MAX_PROFIT_LADDER_TRAIL = False

def pivot_ladder(levels, atm, winning_side):
    """Same-side HIGH at every strike ATM +/- SIGNAL_STRIKES, ascending by
    level - the 'previous pivot' rungs used as SL/TSL anchors under
    MAX_PROFIT_LADDER_TRAIL. Mirrors ladder_strikes_ordered's shape/sort but
    reads levels[(K, winning_side)]["high"] (our OWN side, at other
    strikes) instead of the opposite side's low - this is the same field
    competitor_reference() already reads for a single strike, generalized
    across the whole ladder so SL can ratchet through more than one rung.

    Under ITM_ONLY_LADDER, restricted to winning_side's own ITM direction
    (see itm_strikes()) instead of the full +/- SIGNAL_STRIKES scan."""
    if ITM_ONLY_LADDER:
        strikes = itm_strikes(atm, winning_side)
    else:
        strikes = [atm + i * STRIKE_GAP for i in range(-SIGNAL_STRIKES, SIGNAL_STRIKES + 1) if i != 0]
    out = []
    for k in strikes:
        rec = levels.get((k, winning_side))
        if rec:
            out.append({"strike": k, "key": rec["key"], "level": rec["high"]})
    out.sort(key=lambda d: d["level"])
    return out

def initial_pivot_sl(levels, atm, side, entry, fallback):
    """Highest same-side pivot level that is still BELOW entry (the nearest
    rung already cleared to get here) - that's the initial SL under
    MAX_PROFIT_LADDER_TRAIL. Falls back to the normal fixed-points SL if no
    pivot sits below entry (e.g. a trade that fires very close to ATM).

    Capped 2026-07-26 after backtesting 07-24: a raw pivot can land BELOW
    entry - SL_POINTS (looser than the fixed stop, not tighter), which
    defeats the point of using a level-based stop at all - one live trade
    that day lost 3.5pts more than the fixed-SL baseline for exactly this
    reason. The pivot is only ever allowed to TIGHTEN the stop, never
    loosen it - take whichever of pivot/fallback is higher (closer to
    entry)."""
    below = [d["level"] for d in pivot_ladder(levels, atm, side) if d["level"] < entry]
    return max(max(below), fallback) if below else fallback

def next_pivot_sl(levels, atm, side, px, current_sl):
    """Ratchets the SL up to the highest pivot rung still below the current
    price px, but never lower than the SL already held (a ratchet only ever
    moves forward, same guarantee as the existing MIN_PROFIT_POINTS trail)."""
    below = [d["level"] for d in pivot_ladder(levels, atm, side) if d["level"] < px]
    return max(below + [current_sl]) if below else current_sl

# ---------------------------------------------------------------------------
# Momentum-gated ride mode (2026-07-26, under review - OFF by default).
#
# Backtested 07-08 and 07-24: unconditionally riding the ladder from entry
# (MAX_PROFIT_LADDER_TRAIL) is a trend-follower's trade-off - it gives back a
# little on choppy days but multiplies the win on a real trend day (07-08:
# baseline banked +60.30pts at LINE 1, unconditional-ride banked +216.75pts
# on the identical entry, because the move kept going for another hour).
# The risk is paying that "give back a little" cost on EVERY trade just to
# catch the rare trend day. This middle ground only pays that cost when the
# LINE 1 cross itself already shows real momentum: if the confirming close
# clears LINE 1 by more than MOMENTUM_MARGIN_POINTS (a hard breakout, not a
# graze), switch into ride mode (pivot-trailing SL, no more early exits) -
# otherwise take the LINE 1 win immediately exactly like baseline. Days that
# never produce a decisive LINE 1 cross behave IDENTICALLY to baseline.
RIDE_ON_MOMENTUM = False
MOMENTUM_MARGIN_POINTS = 10.0   # provisional - not yet tuned against data

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

# Rejects entries whose margin (close beyond the traded side's own 9:15
# extreme) exceeds this - i.e. blocks chasing an already-extended move.
# ENABLED 2026-07-23 at 20pts after backtesting across 15 sessions: the
# >20pt-margin bucket was unambiguously negative (-50.75 pts over 37 trades,
# the largest bucket by trade count), while capping at 20 raised win rate
# 45.0%->48.9% and total profit Rs4725.50->Rs6363.50. Cross-checked against
# a single-trade overfitting risk (a +60.30pt trade sits right at the noisy
# edge of the 14-18pt range) by re-running with that trade excluded from
# every config - the improvement holds up at cap=20 even without it, unlike
# tighter caps (15-18) whose exact optimum is not trustworthy from 15 days
# of data alone. Does NOT address every loss - e.g. the 2026-07-23 "spot
# back in zone" losses had margins well under 20 and are unaffected by this.
MAX_ENTRY_MARGIN_POINTS = 20.0

# Off by default - live behavior unchanged. When True, requires the SAME
# triple-confirmation pattern (winning side beats its own 9:15 extreme by
# the margin, losing side stays below its own) to ALSO hold at the next
# strike in-the-money for the winning side (ATM-50 for CE, ATM+50 for PE),
# not just at ATM. Based on a manual trading methodology reviewed
# 2026-07-23 (YouTube "Trade Plan" transcripts) whose core discipline rule
# is: a setup is only real when the same premium behavior shows up at
# MULTIPLE strikes simultaneously, not one strike in isolation - one strike
# alone can be noise/manipulation. Reuses ltp_fn (already passed into
# on_candle_close for the competitor/other-strike checks) so it costs no
# extra live API infrastructure; in replay it reads the same full-ladder
# backfill already fetched for those checks. Under test via run_replay
# before ever turned on for --live.
REQUIRE_ADJACENT_STRIKE_CONFIRMATION = False

def adjacent_strike_confirms(levels, atm, side, ltp_fn):
    """Checks whether the next strike in-the-money for `side` independently
    shows the same triple-confirmation pattern as ATM, using its own first-
    5min high/low and a live/backfilled close via ltp_fn. Fails CLOSED (no
    confirmation) if ltp_fn is unavailable, the adjacent strike wasn't
    captured, or the lookup errors - missing data is not a free pass."""
    if not ltp_fn:
        return False
    adj_strike = atm - STRIKE_GAP if side == "CE" else atm + STRIKE_GAP
    ce_rec = levels.get((adj_strike, "CE"))
    pe_rec = levels.get((adj_strike, "PE"))
    if not ce_rec or not pe_rec:
        return False
    try:
        ce_close = ltp_fn(ce_rec["key"])
        pe_close = ltp_fn(pe_rec["key"])
    except Exception:
        return False
    if side == "CE":
        return ce_close > ce_rec["high"] + MIN_ENTRY_MARGIN_POINTS and pe_close < pe_rec["low"]
    else:
        return pe_close > pe_rec["high"] + MIN_ENTRY_MARGIN_POINTS and ce_close < ce_rec["low"]

# ENABLED 2026-07-24. Based on the "Trending OI" methodology (OIPulse
# YouTube explainer, reviewed same day): instead of a plain PCR across ALL
# strikes (which mixes in deep ITM/OTM hedging positions that say nothing
# about trend), sum OI CHANGE separately for calls and puts across just the
# ATM +/- SIGNAL_STRIKES active strikes (this ladder already matches that
# definition almost exactly). diff = total_put_OI_change -
# total_call_OI_change: positive means put WRITERS are aggressively adding
# (they're betting the market won't fall => bullish, since we trade
# opposite the option sellers).
#
# Backtested across 17 sessions (2026-07-01 to 07-23): baseline NET
# -Rs484.25 (51 trades, 39.2% win) -> with this filter (streak=2) NET
# +Rs572.00 (42 trades, 40.5% win) - the first change this week that flips
# the sample from net-loss to net-profit. Cross-checked for the same
# single-trade overfitting risk found earlier (the +60.30pt 07-08 trade):
# excluding it from BOTH configs, baseline is -Rs4273.75 vs filtered
# -Rs3217.50 - still net negative without that trade, but the filter is
# consistently ~Rs1050 better either way, so the RELATIVE improvement is
# real even though the ABSOLUTE positive headline leans on one lucky trade.
#
# OI_TREND_MIN_STREAK=2 is NOT arbitrary - an earlier sweep (1/2/3)
# appeared to show no difference between streak values due to a real bug
# (oi_trend_confirms' min_streak default parameter is bound at function-
# DEFINITION time, so setting orb_signal.OI_TREND_MIN_STREAK afterward
# silently did nothing - every "different streak" test was actually
# testing whatever streak equaled when the module was first imported).
# Fixed by passing OI_TREND_MIN_STREAK explicitly at every call site
# instead of relying on the default. Once genuinely varied: streak=1 gives
# NET -Rs718.25 (worse than no filter at all), streak=2 gives +Rs572.00,
# streak=3 collapses to -Rs5791.50 (over-filtered, too few trades left).
# 2 is a real, sharp optimum on this data, not a flat plateau - treat it
# as provisional pending more sessions, same caveat as every threshold
# tuned on 17 days this week.
#
# DISABLED again same day once REQUIRE_FUTURES_OI_CONFIRMATION (below) was
# backtested and found stronger standalone (+Rs2486.25 vs this filter's
# +Rs572.00, both vs the same baseline) - combining both over-filters down
# to 26 trades and nets only +Rs230.75, worse than either alone. Left
# fully implemented and correct (useful if futures-OI ever needs a second
# opinion later), just not the active filter right now.
REQUIRE_OI_TREND_CONFIRMATION = False
OI_TREND_MIN_STREAK = 2   # consecutive candles required in the confirming direction
# The video is explicit: check OI trend only from 09:45 onward - before that,
# OI hasn't built up enough to mean anything and the diff swings sign
# candle-to-candle (verified 2026-07-24 on real data: the 09:20-09:40 diff
# series flipped sign 5 times in 20 minutes). First backtest attempt ignored
# this and evaluated the filter from 09:20 (ORB_LOCK) - garbage in, garbage
# out. Entries before this time bypass the OI check entirely (same as if
# REQUIRE_OI_TREND_CONFIRMATION were off) rather than being blocked, since
# blocking everything before 9:45 is a time-cutoff decision, not something
# this filter should silently impose as a side effect.
OI_TREND_VALID_FROM = time(9, 45)

def compute_oi_trend_series(levels, atm, oi_by_key):
    """Precomputes {ts: oi_diff} for one full day - oi_diff = candle-over-
    candle change in total PUT open interest minus candle-over-candle
    change in total CALL open interest, summed across every ATM +/-
    SIGNAL_STRIKES strike captured for that side. Call once per day
    (in simulate_day), not per candle - reused by oi_trend_confirms()."""
    ce_keys, pe_keys = [], []
    for i in range(-SIGNAL_STRIKES, SIGNAL_STRIKES + 1):
        k = atm + i * STRIKE_GAP
        rec = levels.get((k, "CE"))
        if rec:
            ce_keys.append(rec["key"])
        rec = levels.get((k, "PE"))
        if rec:
            pe_keys.append(rec["key"])

    all_ts = sorted(set().union(*(oi_by_key.get(k, {}).keys() for k in ce_keys + pe_keys))) \
             if (ce_keys or pe_keys) else []

    call_totals = [(ts, sum(oi_by_key.get(k, {}).get(ts, 0.0) for k in ce_keys)) for ts in all_ts]
    put_totals = [(ts, sum(oi_by_key.get(k, {}).get(ts, 0.0) for k in pe_keys)) for ts in all_ts]

    oi_diff = {}
    for i in range(1, len(all_ts)):
        ts = all_ts[i]
        call_change = call_totals[i][1] - call_totals[i - 1][1]
        put_change = put_totals[i][1] - put_totals[i - 1][1]
        oi_diff[ts] = put_change - call_change
    return oi_diff, all_ts

def oi_trend_confirms(oi_diff, sorted_ts, current_ts, side, min_streak=OI_TREND_MIN_STREAK):
    """True if oi_diff has held the confirming sign for `min_streak`
    consecutive candles ending at current_ts. CE (bullish) needs oi_diff
    consistently positive (put writers aggressive); PE (bearish) needs it
    consistently negative (call writers aggressive). Fails CLOSED if there
    isn't enough history yet or a candle's OI data is missing."""
    if min_streak <= 0:
        return True
    try:
        idx = sorted_ts.index(current_ts)
    except ValueError:
        return False
    if idx + 1 < min_streak:
        return False
    required_sign = 1 if side == "CE" else -1
    for j in range(idx - min_streak + 1, idx + 1):
        diff = oi_diff.get(sorted_ts[j])
        if diff is None or diff * required_sign <= 0:
            return False
    return True

# ENABLED 2026-07-24 - supporting strategy #2, same "Trending OI" video's
# closing point: cross-check the underlying FUTURE contract's own
# price+OI relationship. Standard futures OI interpretation (price
# direction, OI direction):
#   price up   + OI up   = long buildup    (real fresh buying - bullish)
#   price up   + OI down = short covering  (weak, not fresh conviction)
#   price down + OI up   = short buildup   (real fresh selling - bearish)
#   price down + OI down = long unwinding  (weak, not fresh conviction)
# CE_WINS needs "long buildup" on the future; PE_WINS needs "short
# buildup". Same one contract already resolved for the SP-zone parity
# calc, so this costs exactly one extra instrument's candle history per
# day, not a new ladder fetch.
#
# Backtested standalone across the same 17 sessions: true baseline (no
# filters) NET -Rs484.25 (51 trades) -> this filter alone NET +Rs2486.25
# (31 trades, 41.9% win) - clearly stronger than REQUIRE_OI_TREND_
# CONFIRMATION's own +Rs572.00 result, and combining both over-filters to
# only 26 trades / +Rs230.75 (worse than either alone) - so this runs
# ALONE, with REQUIRE_OI_TREND_CONFIRMATION off. Cross-checked against
# the same single-outlier-trade risk (+60.30pt 07-08 trade): excluding it,
# baseline -Rs4273.75 vs filtered -Rs1303.25 - a ~Rs2970 improvement
# either way, the largest robust margin found this week.
REQUIRE_FUTURES_OI_CONFIRMATION = True
FUTURES_OI_VALID_FROM = time(9, 45)   # same reasoning as OI_TREND_VALID_FROM

def classify_futures_oi(price_change, oi_change):
    if price_change > 0 and oi_change > 0:
        return "long_buildup"
    if price_change > 0:
        return "short_covering"
    if price_change < 0 and oi_change > 0:
        return "short_buildup"
    if price_change < 0:
        return "long_unwinding"
    return "flat"

def compute_futures_oi_series(fut_candles):
    """fut_candles: sorted list of Candle (close, oi) for the future contract.
    Returns {ts: classification} for candle i vs candle i-1."""
    out = {}
    for i in range(1, len(fut_candles)):
        prev, cur = fut_candles[i - 1], fut_candles[i]
        out[cur.ts] = classify_futures_oi(cur.close - prev.close, cur.oi - prev.oi)
    return out

def futures_oi_confirms(fut_oi_series, ts, side):
    cls = fut_oi_series.get(ts)
    if cls is None:
        return False
    return cls == "long_buildup" if side == "CE" else cls == "short_buildup"

# Off by default - supporting strategy #3 (2026-07-24): require the
# underlying FUTURE's own price to be on the correct side of its intraday
# VWAP (volume-weighted average price) at entry time. This is the "chart
# setup" cross-check the OI Trending video itself insists on: OI trend
# alone only tells you the DIRECTION of conviction, not whether price
# action agrees right now - the video's explicit example skips a trade
# entirely when OI sentiment and price structure disagree. CE_WINS needs
# the future trading ABOVE its cumulative VWAP; PE_WINS needs it BELOW.
# Computed off the future's own OHLCV (real traded volume, unlike the spot
# index) - the same one contract already fetched for
# REQUIRE_FUTURES_OI_CONFIRMATION, so this costs nothing extra.
#
# Backtested across the same 17 sessions: standalone, it barely filters
# anything (51/51 trades pass, same count as the unfiltered baseline -
# our breakout entries already tend to agree with VWAP direction on their
# own) and nets slightly WORSE than baseline (-Rs640.25 vs -Rs484.25).
# Stacked on top of the deployed Futures OI filter it adds a ~Rs88
# improvement (Rs2574.00 vs Rs2486.25) on the identical 31 trades - noise,
# not a real signal. Left implemented and off; not a useful filter on
# this data as currently defined (typical-price cumulative VWAP on the
# future). A tighter/different VWAP formulation might do better, but
# there's no evidence for THIS one, so it doesn't ship.
REQUIRE_VWAP_CONFIRMATION = False

def compute_vwap_series(fut_candles):
    """Cumulative intraday VWAP, reset at the start of each call (one day's
    candles in, one day's VWAP series out) - standard typical-price VWAP:
    cumsum(((high+low+close)/3) * volume) / cumsum(volume)."""
    out = {}
    cum_pv = cum_vol = 0.0
    for c in sorted(fut_candles, key=lambda x: x.ts):
        typical = (c.high + c.low + c.close) / 3.0
        cum_pv += typical * c.volume
        cum_vol += c.volume
        out[c.ts] = (cum_pv / cum_vol) if cum_vol > 0 else c.close
    return out

def vwap_confirms(vwap_series, fut_close_series, ts, side):
    """Fails closed if either series is missing data at ts."""
    vwap = vwap_series.get(ts)
    price = fut_close_series.get(ts)
    if vwap is None or price is None:
        return False
    return price > vwap if side == "CE" else price < vwap

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
                     ltp_fn=None, source="live", oi_trend_fn=None, fut_oi_fn=None, vwap_fn=None):
    """ce_c / pe_c are the just-closed N-min candles of the ATM CE / ATM PE.

    ltp_fn: optional callable(instrument_key) -> float, used only for the
    other-strike early-exit check below. Pass None to disable that check
    (e.g. in replay, where we don't have live/intrabar data for every
    strike in the ladder - only its own 09:15 first candle).

    oi_trend_fn: optional callable(side) -> bool, used only by
    REQUIRE_OI_TREND_CONFIRMATION. Pass None to disable that check (e.g.
    live, until the full-ladder OI poll is built).

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
        if MAX_PROFIT_LADDER_TRAIL:
            # Ride the ladder instead of exiting at LINE 1: each rung crossed
            # just ratchets the SL up to the nearest pivot behind current
            # price and pops that rung off the target list, so the next
            # candle is judged against the next rung out.
            while p["lines"] and px >= p["lines"][0]:
                p["crossed"] += 1
                p["lines"].pop(0)
            p["trail"] = next_pivot_sl(levels, atm, p["side"], px, p["trail"])
        elif RIDE_ON_MOMENTUM:
            if p.get("riding"):
                # Already switched into ride mode on an earlier candle - keep
                # riding through every further rung, same mechanics as
                # MAX_PROFIT_LADDER_TRAIL from here on.
                while p["lines"] and px >= p["lines"][0]:
                    p["crossed"] += 1
                    p["lines"].pop(0)
                p["trail"] = next_pivot_sl(levels, atm, p["side"], px, p["trail"])
            elif not exit_reason and p["lines"] and px >= p["lines"][0]:
                crossed = p["lines"][0]
                margin = px - crossed
                if margin > MOMENTUM_MARGIN_POINTS:
                    # Decisive breakout through LINE 1, not a graze - trust
                    # it as a real trend and switch to riding instead of
                    # taking the small win now.
                    p["riding"] = True
                    p["crossed"] += 1
                    p["lines"].pop(0)
                    p["trail"] = next_pivot_sl(levels, atm, p["side"], px, p["trail"])
                else:
                    p["crossed"] += 1
                    exit_reason = "LINE 1 target hit (%.2f) - confirmed, exit now" % crossed
        elif not exit_reason and p["lines"] and px >= p["lines"][0]:
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
            pnl_rupees_gross = pnl_pts * QTY
            # Real round-trip cost (brokerage+STT+exchange+GST+SEBI+stamp
            # duty) subtracted once per completed trade - a small positive
            # gross can still be a NET loss once this is applied, so every
            # rupee figure tracked/alerted/journaled from here on is NET,
            # never the raw points*qty number.
            pnl_rupees = pnl_rupees_gross - COST_PER_TRADE_RUPEES

            if pnl_rupees > 0:
                exit_note = ("Profit: %s premium ran from %.2f to %.2f (+%.2f pts, %d ladder "
                             "line(s) crossed) before %s. Net Rs %.2f after Rs %.2f costs." %
                             (p["side"], p["entry"], px, pnl_pts, p["crossed"], exit_reason,
                              pnl_rupees, COST_PER_TRADE_RUPEES))
            elif pnl_rupees < 0:
                exit_note = ("Loss: %s premium fell from %.2f to %.2f (%.2f pts) - %s. "
                             "SL/TSL was at %.2f when closed. Net Rs %.2f after Rs %.2f costs." %
                             (p["side"], p["entry"], px, pnl_pts, exit_reason, p["trail"],
                              pnl_rupees, COST_PER_TRADE_RUPEES))
            else:
                exit_note = ("Breakeven: exited flat at %.2f via %s, no gain/loss after costs." % (px, exit_reason))

            conn.execute("INSERT INTO orb_trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (session_date.isoformat(), p["ts"], p["side"],
                          atm, p["entry"], ts.isoformat(), px, exit_reason,
                          p["crossed"], pnl_pts, p["entry_note"], exit_note, source))
            conn.commit()
            st.daily_pnl_rupees += pnl_rupees
            trigger_txt = (" | trigger strike %d @ %.2f (next level %.2f)"
                          % (trigger_strike["strike"], trigger_strike["live_value"],
                             trigger_strike["next_level"])) if trigger_strike else ""
            alert("EXIT %s @ %.2f (%s) | ATM %d | PnL %.2f pts (Rs %.2f gross, Rs %.2f net of Rs%.0f "
                  "costs, qty %d) | lines crossed %d | day PnL Rs %.2f%s | Competitor: %s [%s]"
                  % (p["side"], px, exit_reason, atm, pnl_pts, pnl_rupees_gross, pnl_rupees,
                     COST_PER_TRADE_RUPEES, QTY, p["crossed"],
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
            if pnl_rupees < 0:   # net of costs - a small gross win can still be a real loss
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
    ce_margin = ce_c.close - atm_ce["high"]
    pe_margin = pe_c.close - atm_pe["high"]
    ce_wins = (implied_spot > sp_high
               and ce_margin > MIN_ENTRY_MARGIN_POINTS
               and pe_c.close < atm_pe["low"])
    pe_wins = (implied_spot < sp_low
               and pe_margin > MIN_ENTRY_MARGIN_POINTS
               and ce_c.close < atm_ce["low"])

    # See MAX_ENTRY_MARGIN_POINTS above for why this cap exists.
    if ce_wins and MAX_ENTRY_MARGIN_POINTS is not None and ce_margin > MAX_ENTRY_MARGIN_POINTS:
        ce_wins = False
    if pe_wins and MAX_ENTRY_MARGIN_POINTS is not None and pe_margin > MAX_ENTRY_MARGIN_POINTS:
        pe_wins = False

    if REQUIRE_ADJACENT_STRIKE_CONFIRMATION:
        if ce_wins and not adjacent_strike_confirms(levels, atm, "CE", ltp_fn):
            ce_wins = False
        if pe_wins and not adjacent_strike_confirms(levels, atm, "PE", ltp_fn):
            pe_wins = False

    if REQUIRE_OI_TREND_CONFIRMATION and t >= OI_TREND_VALID_FROM:
        # Fails closed: no oi_trend_fn (e.g. live, not wired yet) means no
        # confirmation available, so any raw signal is blocked rather than
        # silently let through unchecked. Before OI_TREND_VALID_FROM (09:45)
        # this check is skipped entirely - see OI_TREND_VALID_FROM comment.
        if ce_wins and not (oi_trend_fn and oi_trend_fn("CE")):
            ce_wins = False
        if pe_wins and not (oi_trend_fn and oi_trend_fn("PE")):
            pe_wins = False

    if REQUIRE_FUTURES_OI_CONFIRMATION and t >= FUTURES_OI_VALID_FROM:
        if ce_wins and not (fut_oi_fn and fut_oi_fn("CE")):
            ce_wins = False
        if pe_wins and not (fut_oi_fn and fut_oi_fn("PE")):
            pe_wins = False

    if REQUIRE_VWAP_CONFIRMATION:
        if ce_wins and not (vwap_fn and vwap_fn("CE")):
            ce_wins = False
        if pe_wins and not (vwap_fn and vwap_fn("PE")):
            pe_wins = False

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
        initial_sl = (initial_pivot_sl(levels, atm, side, entry, max(0.0, entry - SL_POINTS))
                      if MAX_PROFIT_LADDER_TRAIL else max(0.0, entry - SL_POINTS))
        st.position = {
            "side": side, "entry": entry, "ts": ts.isoformat(),
            "trail": initial_sl,   # fixed rupee risk budget, or previous pivot under MAX_PROFIT_LADDER_TRAIL
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

class _Px:
    __slots__ = ("ts", "close")
    def __init__(self, ts, close):
        self.ts, self.close = ts, close

def fetch_day_data(session_date, quiet=False):
    """The expensive, network-bound half of a replay: pulls the full ATM +/-
    SIGNAL_STRIKES ladder's 1-min candles once. Returns (atm, sp_high,
    sp_low, levels, hist_by_key, ce_key, pe_key), all of which simulate_day()
    can be called against repeatedly with different strategy-flag settings
    WITHOUT re-fetching - splitting fetch from simulate is what makes A/B
    backtesting multiple rule variants fast instead of re-downloading the
    same candles once per variant (each full-ladder fetch is the dominant
    cost of a replay, not the simulation itself).
    hist_by_key is {} if nothing could be fetched (caller must check)."""
    atm, sp_high, sp_low, levels = load_day(session_date)
    ce_key = levels[(atm, "CE")]["key"]
    pe_key = levels[(atm, "PE")]["key"]

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
    if not quiet:
        alert("REPLAY %s | ATM %d | SP zone %d-%d | backfilling %d contracts for the full "
              "+/- %d ladder via %s endpoint..."
              % (session_date, atm, sp_low, sp_high, len(all_keys), SIGNAL_STRIKES,
                 "intraday" if is_today else "historical"))
    # Fetched concurrently, not one-at-a-time - each fetch_fn(key) call is a
    # single blocking HTTP round trip, and this loop used to be the dominant
    # cost of a replay (up to (2*SIGNAL_STRIKES+1)*2 = 26 sequential
    # requests, ~10+ min across a multi-day backtest). Threads are safe here
    # because these are I/O-bound requests through a shared, pooled
    # requests.Session (see orb_common._SESSION), not CPU-bound work
    # fighting the GIL. FETCH_WORKERS=8 hit Upstox's rate limit hard enough
    # under sustained multi-day backtesting (17 days back-to-back) that even
    # 5-retry backoff in _get() couldn't fully absorb it - 2 of 17 days came
    # back with most contracts missing. Backed off to 4 workers, which
    # cleared the same 17-day run with zero missing contracts. Raise this
    # cautiously and always re-verify with a multi-day run, not a single
    # isolated fetch (which looks deceptively fast/clean either way).
    hist_by_key = {}
    oi_by_key = {}   # {instrument_key: {ts: open_interest}} - parallel to
                     # hist_by_key, feeds the OI-trend confirmation filter.
    total_candles = 0
    FETCH_WORKERS = 4
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        future_to_key = {pool.submit(fetch_fn, key): key for key in all_keys}
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                candles = resample(future.result(), CANDLE_MINUTES)
                hist_by_key[key] = {c.ts: c.close for c in candles}
                oi_by_key[key] = {c.ts: c.oi for c in candles}
                total_candles += len(candles)
            except Exception as e:
                if not quiet:
                    alert("REPLAY %s | WARN: could not backfill %s (%s) - early-exit checks "
                          "involving this strike will be skipped." % (session_date, key, e))
                hist_by_key[key] = {}
                oi_by_key[key] = {}

    if total_candles == 0:
        if not quiet:
            alert("REPLAY %s | ABORTED: 0 candles returned across all %d contracts - this is "
                  "missing data, NOT a real 'no trade' result. If this is a same-day replay, the "
                  "intraday endpoint may not be populated yet; if historical, Upstox may not "
                  "retain data this far back for these contracts, or this wasn't a trading day. "
                  "Not reporting a trade count for this day." % (session_date, len(all_keys)))
        return atm, sp_high, sp_low, levels, {}, ce_key, pe_key, {}, []

    # One extra contract's candle history, for REQUIRE_FUTURES_OI_CONFIRMATION -
    # the same future already resolved for the SP-zone parity calc, not a new
    # ladder fetch. Best-effort: an empty list just means that filter can't
    # confirm anything for this day (fails closed, same as everywhere else).
    fut_candles = []
    try:
        expiry_row = db().execute("SELECT expiry FROM orb_summary WHERE session_date=?",
                                   (session_date.isoformat(),)).fetchone()
        if expiry_row:
            fut_key = resolve_future_instrument_key(date.fromisoformat(expiry_row[0]))
            fut_candles = resample(fetch_fn(fut_key), CANDLE_MINUTES)
    except Exception as e:
        if not quiet:
            alert("REPLAY %s | WARN: could not backfill future contract (%s) - "
                  "REQUIRE_FUTURES_OI_CONFIRMATION will be skipped for this day." % (session_date, e))

    return atm, sp_high, sp_low, levels, hist_by_key, ce_key, pe_key, oi_by_key, fut_candles

def simulate_day(session_date, atm, sp_high, sp_low, levels, hist_by_key, ce_key, pe_key, oi_by_key=None, fut_candles=None):
    """Pure simulation over pre-fetched candle data - no network calls, so
    it's safe (and fast) to call this many times over the same fetched data
    with different global strategy flags set, to A/B test rule variants.
    Returns the resulting DayState (trades already committed to orb_trades
    tagged source='replay')."""
    def historical_ltp_fn(ts):
        def _fn(instrument_key):
            close = hist_by_key.get(instrument_key, {}).get(ts)
            if close is None:
                raise KeyError("no backfilled candle for %s at %s" % (instrument_key, ts))
            return close
        return _fn

    # Precomputed once per day (not per candle) - see compute_oi_trend_series.
    oi_diff, oi_sorted_ts = compute_oi_trend_series(levels, atm, oi_by_key or {})
    def oi_trend_fn_at(ts):
        # min_streak passed explicitly (module-global lookup at CALL time) -
        # oi_trend_confirms()'s own default parameter is baked in at
        # function-DEFINITION time (module import), so relying on it here
        # would silently ignore any later change to OI_TREND_MIN_STREAK -
        # exactly the bug found 2026-07-24 that made a 1/2/3 sweep produce
        # identical results (it was always using whatever OI_TREND_MIN_STREAK
        # equaled when the module was first imported, not what the test
        # script tried to set afterward).
        return lambda side: oi_trend_confirms(oi_diff, oi_sorted_ts, ts, side, OI_TREND_MIN_STREAK)

    fut_oi_series = compute_futures_oi_series(sorted(fut_candles or [], key=lambda c: c.ts))
    def fut_oi_fn_at(ts):
        return lambda side: futures_oi_confirms(fut_oi_series, ts, side)

    fut_sorted = sorted(fut_candles or [], key=lambda c: c.ts)
    vwap_series = compute_vwap_series(fut_sorted)
    fut_close_series = {c.ts: c.close for c in fut_sorted}
    def vwap_fn_at(ts):
        return lambda side: vwap_confirms(vwap_series, fut_close_series, ts, side)

    ce_series = sorted(hist_by_key.get(ce_key, {}).items())
    pe_map = hist_by_key.get(pe_key, {})
    cutoff_time = ORB_LOCK   # 09:20 - first candle bucket after the opening range itself

    st, conn = DayState(), db()
    for ts, ce_close in ce_series:
        pe_close = pe_map.get(ts)
        if pe_close is not None and ts.time() >= cutoff_time:
            on_candle_close(ts, _Px(ts, ce_close), _Px(ts, pe_close), atm, sp_high, sp_low,
                            levels, st, conn, session_date, ltp_fn=historical_ltp_fn(ts),
                            source="replay", oi_trend_fn=oi_trend_fn_at(ts),
                            fut_oi_fn=fut_oi_fn_at(ts), vwap_fn=vwap_fn_at(ts))
    return st

def run_replay(session_date):
    atm, sp_high, sp_low, levels, hist_by_key, ce_key, pe_key, oi_by_key, fut_candles = fetch_day_data(session_date)
    if not hist_by_key or not any(hist_by_key.values()):
        return
    st = simulate_day(session_date, atm, sp_high, sp_low, levels, hist_by_key, ce_key, pe_key, oi_by_key, fut_candles)
    if st.signals == 0:
        alert("No trade all day - NEUTRAL state held. That is a win over sentiment.")

def run_live_for_day(session_date):
    atm, sp_high, sp_low, levels = load_day(session_date)
    ce_key = levels[(atm, "CE")]["key"]
    pe_key = levels[(atm, "PE")]["key"]
    st, conn = DayState(), db()
    seen = set()

    # Full ladder OI, accumulated live for REQUIRE_OI_TREND_CONFIRMATION -
    # polled only once per NEW 5-min candle close (not every 20s loop tick),
    # matching the granularity the filter actually needs and keeping live
    # API load reasonable (~26 contracts every 5 min, not every 20s).
    ladder_keys = sorted({rec["key"] for rec in levels.values()})
    oi_by_key = {k: {} for k in ladder_keys}

    def refresh_oi_for_ts(candle_ts):
        """Best-effort: a failed contract just leaves its OI missing for
        this candle - oi_trend_confirms() already fails closed on missing
        data, so one bad fetch doesn't need to abort the whole cycle."""
        def _fetch_one(key):
            try:
                candles = resample(fetch_intraday_candles(key, 1), CANDLE_MINUTES)
                match = next((c for c in candles if c.ts == candle_ts), None)
                return key, (match.oi if match else None)
            except Exception:
                return key, None
        with ThreadPoolExecutor(max_workers=4) as pool:
            for key, oi in pool.map(_fetch_one, ladder_keys):
                if oi is not None:
                    oi_by_key[key][candle_ts] = oi

    # Single-contract future history, for REQUIRE_FUTURES_OI_CONFIRMATION -
    # refreshed the same way (once per new 5-min candle close).
    fut_candles = []
    fut_key = None
    try:
        expiry_row = conn.execute("SELECT expiry FROM orb_summary WHERE session_date=?",
                                   (session_date.isoformat(),)).fetchone()
        if expiry_row:
            fut_key = resolve_future_instrument_key(date.fromisoformat(expiry_row[0]))
    except Exception as e:
        alert("LIVE %s | could not resolve future contract (%s) - "
              "REQUIRE_FUTURES_OI_CONFIRMATION will be skipped." % (session_date, e))

    def refresh_fut_oi():
        if not fut_key:
            return
        try:
            candles = resample(fetch_intraday_candles(fut_key, 1), CANDLE_MINUTES)
            fut_candles[:] = candles
        except Exception:
            pass   # best-effort - futures_oi_confirms() fails closed on missing data

    # Seed today's already-realized PnL/stops from the DB - DayState is
    # otherwise purely in-memory and starts at 0 on every process restart,
    # which happens routinely for code deploys. Without this, the rupee
    # MAX_DAILY_LOSS lockout - the only hard stop left after the stop/signal
    # count caps were removed - loses track of losses booked before the most
    # recent restart and can't actually stop the account at the real cap.
    # Only "live" rows count (never mix in replay/backtest simulation rows).
    prior_rows = conn.execute(
        "SELECT pnl_points FROM orb_trades WHERE session_date=? AND source='live'",
        (session_date.isoformat(),)).fetchall()
    # Net of the flat per-trade cost, same as on_candle_close's exit path -
    # summing gross points*qty here and subtracting a single lump cost at
    # the end would be wrong (cost is PER TRADE, not proportional to points).
    prior_net_rupees = [r[0] * QTY - COST_PER_TRADE_RUPEES for r in prior_rows]
    st.daily_pnl_rupees = sum(prior_net_rupees)
    st.stops = sum(1 for r in prior_net_rupees if r < 0)
    if prior_rows:
        alert("LIVE %s | resuming with today's already-realized PnL Rs %.2f net of costs (%d prior "
              "stop(s)) carried forward from before this restart." % (session_date, st.daily_pnl_rupees, st.stops))
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
                    oi_trend_fn = None
                    if REQUIRE_OI_TREND_CONFIRMATION and c.ts.time() >= OI_TREND_VALID_FROM:
                        refresh_oi_for_ts(c.ts)
                        oi_diff, oi_sorted_ts = compute_oi_trend_series(levels, atm, oi_by_key)
                        oi_trend_fn = (lambda side, _d=oi_diff, _s=oi_sorted_ts, _t=c.ts:
                                      oi_trend_confirms(_d, _s, _t, side, OI_TREND_MIN_STREAK))
                    fut_oi_fn = None
                    fut_oi_needed = REQUIRE_FUTURES_OI_CONFIRMATION and c.ts.time() >= FUTURES_OI_VALID_FROM
                    if fut_oi_needed:
                        refresh_fut_oi()
                        fut_oi_series = compute_futures_oi_series(sorted(fut_candles, key=lambda x: x.ts))
                        fut_oi_fn = (lambda side, _s=fut_oi_series, _t=c.ts:
                                    futures_oi_confirms(_s, _t, side))
                    vwap_fn = None
                    if REQUIRE_VWAP_CONFIRMATION:
                        if not fut_oi_needed:   # avoid double-fetching the same contract
                            refresh_fut_oi()
                        fut_sorted = sorted(fut_candles, key=lambda x: x.ts)
                        vwap_series = compute_vwap_series(fut_sorted)
                        fut_close_series = {x.ts: x.close for x in fut_sorted}
                        vwap_fn = (lambda side, _v=vwap_series, _c=fut_close_series, _t=c.ts:
                                  vwap_confirms(_v, _c, _t, side))
                    on_candle_close(c.ts, c, mate, atm, sp_high, sp_low,
                                    levels, st, conn, session_date, ltp_fn=get_ltp,
                                    source="live", oi_trend_fn=oi_trend_fn, fut_oi_fn=fut_oi_fn,
                                    vwap_fn=vwap_fn)
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

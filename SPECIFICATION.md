# Strategy Specification

This document states the trading strategy's business rules as
currently implemented by the `strategy/` package. It reflects what has
been explicitly specified and approved, module by module - see
`CHANGELOG.md` for the history of how it got here, and
`INVESTIGATIONS.md` / `TRADINGVIEW_REQUIREMENTS_RECOVERY.md` for
evidence gathered about rules not yet in this document.

Current version: **1.1**

## 1. Opening Range and Strike Generation (Module 1)

- Open = the underlying spot's 09:15 first-5-minute-candle open.
- ATM = spot open rounded to the nearest tradable strike (strike_gap).
- Strike range = ATM ± 6 strikes (13 strikes total), no rounding
  applied to the range itself.
- For each captured strike, the first 5-minute candle's CE High, CE
  Low, PE High, PE Low are recorded.

## 2. Top/Bottom Anchors and Premium Mapping (Module 2)

There is no single shared "ATM" reference for trading. Two independent
anchors exist, each rounded to the nearest tradable strike:

- **TOP anchor**: CE chart ← PE Low; PE chart ← CE High.
- **BOTTOM anchor**: CE chart ← PE High; PE chart ← CE Low.

This produces four ladders per session: `top_ce_ladder`,
`top_pe_ladder`, `bottom_ce_ladder`, `bottom_pe_ladder` - each mapping
strike → reference premium value.

## 3. Entry Signal (Module 3)

A trade is confirmed only when BOTH premiums confirm within the SAME
5-minute candle, checked against candle HIGH/LOW (intrabar touch, not
close):

- **BUY CE**: CE premium crosses ABOVE its mapped CE level AND PE
  premium crosses BELOW its mapped PE level.
- **BUY PE** (mirror): PE premium crosses ABOVE its mapped PE level
  AND CE premium crosses BELOW its mapped CE level.

Checked independently for the TOP and BOTTOM mappings, and
independently for every captured strike - all 13 strikes are scanned
uniformly, with no distance-from-ATM restriction (see
`INVESTIGATIONS.md` #5-#8 for the consequences of this).

A signal only fires on a FRESH cross (transition from not-satisfied to
satisfied between consecutive candles), and never at 09:15 (the same
candle used to capture the levels themselves).

When multiple signals qualify on the same candle, only one trade is
opened; the current implementation picks the first signal in ladder-
iteration order (TOP CE ascending → TOP PE ascending → BOTTOM CE
ascending → BOTTOM PE ascending). This order is a documented
placeholder, not a specified priority rule - see
`TRADINGVIEW_REQUIREMENTS_RECOVERY.md` RTV-2.

## 4. Exit Signal (Module 4) - Version 1.1

Exit priority, evaluated in this order every candle a position is open:

1. **Competitor Exit** (Version 1.1)
2. **Target**
3. **Mapped Stop Loss**

Whichever condition is met first wins; if multiple conditions are met
on the same candle, the higher-priority one always wins (Competitor
Exit over Target over Stop Loss).

### 4.1 Target and Mapped Stop Loss (Version 1.0)

Derived from the SAME field ladder that produced the entry price,
sorted BY VALUE (not by strike - these ladders are not monotonic with
strike). Target is the next-higher value; Mapped Stop Loss is the
next-lower value.

### 4.2 Competitor Exit (Version 1.1 - deliberate strategy enhancement)

For an OPEN CE position: monitor the corresponding PE contract at the
SAME strike. For an OPEN PE position: monitor the corresponding CE
contract at the SAME strike.

- **Competitor ladder**: the SAME-anchor, OPPOSITE-side ladder (TOP CE
  → `top_pe_ladder`; TOP PE → `top_ce_ladder`; BOTTOM CE →
  `bottom_pe_ladder`; BOTTOM PE → `bottom_ce_ladder`).
- **Current level**: the level already stored on the entry itself
  (`entry.pe_level` for a CE position, `entry.ce_level` for a PE
  position) - never recalculated.
- **Trigger level**: the next LOWER rung by VALUE in the competitor
  ladder, below the current level (same adjacent-rung convention as
  Stop Loss).
- **Touch condition**: the competitor contract's candle LOW reaches or
  falls below the trigger level (`competitor_candle.low <= trigger_level`).
  Simple threshold check, evaluated every candle - no fresh-cross
  requirement (same convention as Target/Stop Loss).
- If no lower rung exists in the competitor ladder for a given entry,
  Competitor Exit does not apply to that trade (falls back to
  Target/Stop Loss only) - this is not an error.

**Pricing**: Competitor Exit has no ladder rung on the traded
contract's own side (the trigger comes entirely from the competitor
contract). The realized exit price is the traded contract's own
trigger-candle **OPEN** (never CLOSE) - the earliest own-side price
point available from OHLC data, since this system only ever delivers
already-closed 5-minute candles (no tick feed exists). This is always
recorded as `pricing_method = "CANDLE_APPROXIMATION"`. `"LIVE_TICK"` is
reserved for a future tick-level feed this system does not currently
have.

**Recorded on every Competitor Exit**: exit reason `COMPETITOR_EXIT`,
competitor ladder name, competitor (source) strike, competitor trigger
level, competitor trigger price, trigger timestamp, and pricing method.

## 5. Position Manager (Module 5)

One position at a time. Refuses to open a second position while one is
open; refuses to process an exit candle while flat. Delegates all
exit-condition computation to Module 4.

## 6. Level State Manager (Module 9)

Each mapped level (strike, anchor, side) has a state: ACTIVE, USED, or
DISABLED. A level can trade at most once per day; never reactivated
intraday.

## 7. Ladder Expansion (Module 8)

When Target/Stop Loss computation needs an adjacent rung not yet
captured, one additional strike is fetched on demand and added to the
capture/mapping. Does not apply to Competitor Exit in the current
implementation (Version 1.1 scope was explicitly limited to Modules 4,
5, 11).

## 8. Out of scope (not implemented, per explicit instruction)

Trailing Stop (beyond reporting the Stop Loss value under that field
name), OI, synthetic future, indicator-based, or time-based exits are
not implemented and were explicitly excluded at specification time
(see `INVESTIGATIONS.md` #9).

## Version history

See `CHANGELOG.md`.

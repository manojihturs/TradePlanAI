# Changelog

## Version 1.1 — Competitor Exit (2026-07-27)

**Type: Deliberate strategy enhancement — NOT a defect correction.**

Adds Competitor Exit as a new, highest-priority exit condition,
alongside the existing Target and Mapped Stop Loss. This is a new
business rule, distinct from the scale-mismatch defect investigated in
`INVESTIGATIONS.md` #5-#8 and the (unrelated, explicitly-excluded)
Competitor Exit question closed in `INVESTIGATIONS.md` #9 - #9
established that Competitor Exit did NOT exist in Version 1.0 by
design; this release adds it as new, explicitly-requested behavior.

### New exit priority

1. Competitor Exit
2. Target
3. Mapped Stop Loss

### Rule

For an open CE position, the corresponding PE contract at the same
strike is monitored against a threshold one rung below (by value) the
level already stored on the entry, in the same-anchor PE ladder. The
mirror rule applies to an open PE position, monitoring the
corresponding CE contract. See `SPECIFICATION.md` section 4.2 for the
full rule.

### Pricing

Competitor Exit has no ladder rung on the traded contract's own side.
The exit price is approximated using the traded contract's own
trigger-candle OPEN (never CLOSE), recorded as
`pricing_method = "CANDLE_APPROXIMATION"` - documented explicitly so
historical (backtest) and live results remain comparable under the
same approximation. `"LIVE_TICK"` is reserved for a future tick-level
feed; this system does not currently have one.

### Modules changed

- **Module 4** (`strategy/exit_signal.py`): additive only.
  `check_exit()` (Target/Stop Loss) is unchanged and still used
  standalone by any caller that doesn't pass competitor data. Added
  `ExitReason.COMPETITOR_EXIT`, `CompetitorLevel`,
  `compute_competitor_exit_level()`, `check_exit_with_competitor()`,
  and five new optional fields on `ExitSignal`
  (`competitor_ladder`, `competitor_strike`,
  `competitor_trigger_level`, `competitor_trigger_price`,
  `pricing_method`), all defaulting to `None` for backward
  compatibility.
- **Module 5** (`strategy/position_manager.py`): `Position` gains an
  optional `competitor_level` field, computed at `open()` time.
  `process_candle()` gains an optional `competitor_candle` parameter
  (default `None`, preserving exact pre-1.1 behavior for any caller
  that doesn't pass it) and now calls
  `check_exit_with_competitor()` instead of `check_exit()`.
- **Module 11** (`strategy/live_paper_trading.py`):
  `on_candle_close()` now also looks up the competitor contract's
  candle (same strike, opposite side) and passes it through.
  `LiveTradeRecord` gains the same five optional Competitor Exit
  fields. `export_end_of_day_excel()`'s Trade Log sheet gains five new
  columns: Competitor Ladder, Competitor Strike, Competitor Trigger
  Level, Competitor Trigger Price, Pricing Method.
- **Not changed**: Module 3 (Entry Signal) - explicitly out of scope.
  Module 8 (Ladder Expansion) does not currently extend the ladder for
  Competitor Exit if no lower rung exists; in that case Competitor
  Exit simply does not apply to the trade (falls back to Target/Stop
  Loss only).

### Tests

19 new unit tests added across `test_exit_signal.py`,
`test_position_manager.py`, and `test_live_paper_trading.py`, covering:
Competitor Exit before Target, Competitor Exit before Stop Loss,
Target without Competitor, Stop Loss without Competitor, simultaneous
Competitor+Target, simultaneous Competitor+Stop Loss, no-lower-rung
(`None`) handling, missing competitor-candle-data fallback, exit price
approximation (OPEN not CLOSE), full field recording, and end-to-end
wiring through `LivePaperTradingEngine.on_candle_close()`. Full suite:
133/133 passing (113 pre-existing + 19 new, plus one existing Module 11
fixture adjusted - see note below - with 1 unaffected pre-existing
failure-injection test still producing its expected log output).

**Fixture note**: `test_live_paper_trading.py`'s `_CE_SAFE` constant
was adjusted (low raised from 85.0 to 100.5) because its old value
coincidentally fell below the new Competitor Exit threshold for that
test's fixture data, causing an unrelated Target-focused test to
receive a Competitor Exit instead. No test assertions were weakened;
the fixture was changed to stay outside the new trigger band while
still satisfying the original entry condition it was designed for.

### Deployment note

This release was built and tested during market hours on 2026-07-27
while `run_live_paper_trading.py` was actively running against the
live Upstox feed. Per standing instruction, the running process was
NOT restarted with this code - it continues on the Version 1.0 exit
logic for the remainder of that session. Version 1.1 takes effect the
next time the live process is (re)started, after square-off and with
explicit approval.

---

## Version 1.0 — Modules 1-11 baseline

Initial modular strategy engine: Level Capture, Premium Mapping, Entry
Signal, Exit Signal (Target/Stop Loss only), Position Manager, Paper
Trading Engine, Replay Engine, Ladder Expansion, Level State Manager,
Multi-Day Backtest Framework, Live Paper Trading. See
`INVESTIGATIONS.md` for the post-freeze investigation series (#1-#9)
conducted against this baseline.

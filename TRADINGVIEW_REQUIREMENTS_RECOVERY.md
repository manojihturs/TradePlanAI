# TradingView Requirements Recovery

Living document. Reconstructs the original TradingView strategy's
business rules from verified evidence (screenshots, live market
examples, manual trade observations, chart annotations), independent
of and in addition to the written specification already implemented in
`strategy/` (Modules 1-11, "Version 1.0").

## Purpose

The written specification that Modules 1-11 implement is not assumed
to be the complete original strategy. This document exists to capture
behaviour the TradingView strategy appears to follow that the written
specification never stated, so it can be evaluated on its own merits
rather than silently assumed, guessed, or added to the engine without
evidence.

## Rules of this document

1. **Evidence-driven only.** An entry is added here only in response to
   a concrete observation you provide - a screenshot, a live trade, a
   manual log entry, a chart annotation. Nothing is added speculatively.
2. **No invented rules.** If evidence is ambiguous or insufficient to
   state a rule with confidence, it is recorded as *Insufficient
   Evidence*, not guessed at.
3. **No code changes from this document alone.** Every entry is
   investigation/documentation only. A rule becomes eligible for
   implementation only after you decide to promote it to a Version 1.1
   candidate, as a separate, explicit step.
4. **Comparison against the current implementation is always explicit.**
   Every entry states plainly whether Modules 1-11 already do this,
   don't do this, or actively do something that conflicts with it.

## Classification key

| Classification | Meaning |
|---|---|
| **Already Implemented** | The current Python engine already exhibits this behaviour, per a traced code path. |
| **Missing Requirement** | The evidence shows a rule the current engine does not implement at all. |
| **Contradicts Current Specification** | The evidence shows behaviour that conflicts with what Modules 1-11 currently do. |
| **Insufficient Evidence** | The observation alone does not establish a confident rule; more evidence is needed before classifying further. |

## Version 1.1 candidate criteria

A recovered rule is only proposed as a Version 1.1 candidate once:

- It has been observed consistently across more than one independent
  piece of evidence (not a single screenshot), OR
- A single piece of evidence is unambiguous and directly contradicts
  documented current behaviour in a way you confirm is intentional in
  the original strategy.

Being listed as a candidate does not authorize implementation - that
requires your explicit approval, at which point it becomes its own
tracked change (own commit, own rationale), same as every other change
in this project.

---

## Observation Log

### RTV-1 — CE/PE 23950 charts, 27-Jul-2026 session, with pivot-point overlay and manual Buy/Sell markers

**Evidence provided:** Two TradingView screenshots, NIFTY 23950 CALL and
23950 PUT, 5-minute candles, 27-Jul-2026 ~09:15-11:48. Both charts carry
the cross-plotted premium-ladder reference lines (labelled by strike,
ITM/OTM, Low/High), a Pivot Points overlay (R2/R1/P/S1/S2), and hand-drawn
"Buy"/"Sell" markers at specific candles.

**1. Behaviour the TradingView strategy appears to follow**

Two distinct things are visible on these charts, and they should not be
conflated:

- **(a) The cross-plotted premium ladder itself.** The CE chart's
  reference lines are labelled with PE's Low at each strike (e.g. "23650
  ITM6 | Low: ₹11.3", "23900 ITM1 | Low: ₹53.05", "24000 OTM1 | Low:
  ₹96") - exactly the TOP-anchor "CE chart <- PE Low" relationship
  Module 2 implements. The PE chart's reference lines are labelled with
  CE's High at each strike, the mirrored "PE chart <- CE High"
  relationship.
- **(b) A Pivot Points Standard overlay** (R2, R1, P, S1, S2) drawn on
  both charts, and hand-drawn "Buy"/"Sell" markers that appear to sit at
  local price extremes on each leg's own candles - a Sell near a local
  top on the CE chart around 10:00-10:05, a Buy near a local bottom on
  the CE chart around 10:25-10:30, and the mirror-image Buy/Sell pattern
  on the PE chart at roughly the same two times.

**2. Comparison with the current Python implementation**

- (a) is independently verifiable against today's actual engine output.
  Cross-checked all 7 visible CE-chart reference values against
  `live_paper_trading_stdout.log`'s 09:20:00 signal-evaluation lines for
  2026-07-27 - every one matches exactly:

  | Chart label | Chart value | Log value (`ce_level` at that strike, TOP anchor) |
  |---|---|---|
  | 23650 ITM6 Low | ₹11.3 | 11.30 |
  | 23700 ITM5 Low | ₹14.85 | 14.85 |
  | 23750 ITM4 Low | ₹20.25 | 20.25 |
  | 23800 ITM3 Low | ₹27.7 | 27.70 |
  | 23850 ITM2 Low | ₹38.45 | 38.45 |
  | 23900 ITM1 Low | ₹53.05 | 53.05 |
  | 24000 OTM1 Low | ₹96 | 96.00 |

  This confirms Module 1's level capture and Module 2's TOP-anchor
  ladder are faithfully reproducing the same values TradingView shows
  live, for this session.

- (b) The Pivot Points overlay (R2/R1/P/S1/S2) and support/resistance-
  based Buy/Sell marking do not exist anywhere in Modules 1-11. Module 3
  (Entry Signal) only evaluates the CE/PE cross-confirmation rule; no
  pivot-point calculation or local-extreme detection exists in the
  current implementation.

**3. Classification**

- Premium ladder values (item a): **Already Implemented** - verified
  correct against live data, not just consistent with spec.
- Pivot Points / local-extreme Buy-Sell marking (item b): **Insufficient
  Evidence.** A single annotated example does not establish whether
  this is (i) an entry/exit rule actually used by the original
  TradingView strategy, (ii) a visual aid you use for your own
  discretionary reference without it being a coded rule, or (iii) a
  record of trades you actually took manually that happen to coincide
  with pivot levels by chance. The chart alone cannot distinguish these
  three possibilities.

**Update:** You confirmed the Buy/Sell markers are the actual manual
trades you took today. This resolves RTV-1's open question, and opens a
new, more significant one - see RTV-2.

### RTV-2 — Manual PE@23950 trade vs. the engine's signal-selection at 09:20

**Evidence provided:** RTV-1's two screenshots, now read as real manual
trades: you bought PE@23950 (marker ~10:00) and sold it (marker
~10:30). You also sold CE@23950 (marker ~10:00-10:05) and bought it
back (marker ~10:25-10:30).

**Cross-checked against today's engine log** (`live_paper_trading_stdout.log`,
09:20:00 candle evaluation): at that single candle, 25 signals qualified
simultaneously across every strike/anchor/side combination, including
all three of these:

| Signal | Outcome |
|---|---|
| BUY CE @ 23650 (TOP anchor), ce_level=11.30 | **Chosen** - first in iteration order |
| BUY CE @ 23950 (TOP anchor), ce_level=72.05 | Rejected: "already in position" |
| BUY PE @ 23950 (BOTTOM anchor), pe_level=70.20 | Rejected: "already in position" |

**1. Behaviour the TradingView/manual trading appears to follow**

You traded PE@23950 - the strike right at ATM, the same strike the
engine's own detector also flagged as a qualifying BOTTOM-anchor PE
signal at the identical candle. The engine did not act on it only
because it had already committed its "one position at a time" slot to
CE@23650 - a boundary strike (distance 6 from ATM) that is also the
exact strike Investigations #5-#8 identified as producing the
recurring scale-mismatch defect (target hit off a mismatched reference
value, not real price movement).

**2. Comparison with the current implementation**

`strategy/entry_signal.py:207-241` (`EntrySignalDetector.process_candle`)
builds its signal list by iterating `(TOP anchor strikes ascending) →
(BOTTOM anchor strikes ascending)`, and within each anchor, CE ladder
before PE ladder, strikes in ascending order. `LivePaperTradingEngine.on_candle_close`
(`strategy/live_paper_trading.py:274-293`) then takes the **first**
signal in that list as `chosen` and rejects every other simultaneously-
qualifying signal as "already in position" - there is no ranking,
scoring, or proximity-to-ATM preference anywhere in this selection.
This tie-break was flagged as a placeholder when Module 7 was built
(`replay_engine.py`'s `_select_signal` docstring calls it a "documented
placeholder tie-break"), not a deliberately specified rule.

The practical effect, confirmed by today's live data: when multiple
signals qualify on the same candle, the engine currently always prefers
the lowest-strike TOP-anchor CE signal, regardless of how far that
strike is from ATM - which is how a distance-6 boundary strike
(23650) beat out an ATM strike (23950) for the single trade slot today,
even though you yourself, trading manually, chose the ATM strike.

**3. Classification: Missing Requirement**

There is real, direct evidence (your own simultaneous manual trade)
that a signal-selection preference exists in your actual trading
behaviour - you took the near-ATM signal over the boundary-strike one
when only one trade at a time is possible. The current engine has no
such preference; its choice is an arbitrary artifact of ladder
iteration order, not a rule. This is not yet a fully specified
candidate (a single day's coincidence isn't enough to state the exact
rule - "closest to ATM"? "highest-confidence anchor"? "avoid boundary
strikes"? - these would each pick 23950 today but could differ on
other days), but it is the first strong, non-speculative evidence this
selection logic is genuinely incomplete relative to your original
strategy.

**Open question for you:** when multiple signals qualify on the same
candle, what is your actual rule for choosing which one to trade -
closest to ATM, some other proximity/quality measure, or something
else? A second independent example (a different day, different
strikes) confirming the same pattern would move this from "Missing
Requirement, one example" to a stated Version 1.1 candidate per this
document's promotion criteria.

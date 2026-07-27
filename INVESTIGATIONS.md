# Strategy Engine Investigation Log

Documentation-only record of investigations into discrepancies between the
manual trading journal and the strategy engine (`strategy/` package,
Modules 1-9). No investigation on this page authorizes or implies a code
change by itself - any resulting change is made and committed separately,
with its own rationale.

---

## Investigation #1 — Manual 10:20 trade, 22-July-2026

**Status: CLOSED**

### Subject

The manual trading journal for 22-July-2026 records a PE trade at 10:20
(strike 24000, entry premium 238.75). The strategy engine's replay of that
session does not produce this trade.

### Scope of the investigation

1. Mapping validation — checked every mapped level (TOP and BOTTOM anchor,
   all four fields: CE-High, CE-Low, PE-High, PE-Low) across all 13
   captured strikes for an exact numeric match to the manually logged
   entry price.
2. Historical feed validation — pulled the complete 1-minute and 5-minute
   OHLC series for strikes 24000, 24050, and 24100 (both CE and PE) and
   compared session highs/lows against the manual journal and against
   available chart-screenshot values.
3. Reverse trade reconstruction — replayed the exact entry rule (both
   TOP and BOTTOM anchors, all fields, fresh-cross logic) across every
   captured strike for the 09:15-15:25 session, searching specifically
   for any qualifying signal within an hour of 10:20 in either direction.

### Conclusion

**The manual 10:20 trade on 22-July-2026 cannot be reproduced from the
available historical replay dataset using the current, fully specified
strategy.**

The investigation verified:

- Opening-range capture is correct.
- Mapping rules are correct.
- TOP/BOTTOM anchor selection is correct.
- Fresh-cross logic is functioning as specified.
- No qualifying signal exists on any captured strike or anchor near 10:20.

Therefore the discrepancy remains unresolved and is classified as an
**external data discrepancy**, not a confirmed strategy-engine defect. The
most likely explanations, in order of plausibility given the data checked
(see historical feed validation report): a live-tick/broker-screen price
that the 1-minute historical feed does not reflect, or a manual
transcription error at the time the journal was recorded. Neither could be
confirmed or ruled out without the original timestamped screenshot or
tick-level data for that specific trade, which was not available.

### Disposition

Marked **CLOSED**. No strategy code was modified as a result of this
investigation, and none should be, based on this investigation alone.

Reopen only if new evidence becomes available - specifically, an original
timestamped screenshot of the 10:20 entry, or tick-level (sub-1-minute)
price data for PE(24000) covering that morning.

---

## Strategy Design Review — Version 1.0

**Status: SUMMARY (investigation-only, no code modified, no fixes proposed)**

Summary of all completed investigations to date (#1-#7), each classified and
scored for severity/scope, followed by a single decision matrix. This review
does not authorize or imply any code change by itself.

### Investigation #1 — Manual 10:20 Trade (Unreproducible)

- **Finding:** A trader-logged manual trade at 10:20 could not be reproduced
  by the engine from captured data.
- **Evidence:** Level/timeline reconstruction showed no matching fresh-cross
  condition in the captured candle data for that timestamp; classified as
  external/data discrepancy, not an engine defect.
- **Severity:** Low (isolated, unreproducible — no evidence of a systemic
  cause)
- **Scope:** Single trade, single day
- **Affected Modules:** None identified (inconclusive)
- **Classification:** Data issue (unresolved — insufficient evidence to
  confirm engine fault)

### Investigation #2 — Completed Level Accounting

- **Finding:** No actual defect. Initial concern was based on a misread of
  a printed report (columns transposed).
- **Evidence:** Runtime trace confirmed atomic pairing of `mark_used` and
  `record_trade` calls — level state transitions are consistent.
- **Severity:** None (retracted)
- **Scope:** N/A
- **Affected Modules:** N/A
- **Classification:** Accepted limitation — N/A, no defect existed

### Investigation #3 — Open Positions at Market Close

- **Finding:** Descriptive report of positions still open at square-off
  across 18 sessions; documented reasons (premium never reached
  Target/Stop before close).
- **Evidence:** Per-position report of entry/target/stop/last
  premium/unrealised PnL/minutes remaining.
- **Severity:** Low (expected behavior under the stated exit rules — no
  time-based exit exists by design)
- **Scope:** Multiple sessions, minority of trades
- **Affected Modules:** Module 4 (Exit Signal — no time exit), Module 5
  (Position Manager)
- **Classification:** Accepted limitation (explicitly specified: no
  time-based exit unless requested)

### Investigation #4 — Long Duration Trade (2026-07-10)

- **Finding:** One trade ran unusually long; ranked against all 18
  sessions for trades >3 hours. No unique defect found — premium simply
  stayed trapped between mapped levels.
- **Evidence:** MFE/MAE and closest-distance-to-Target/Stop analysis
  showed normal (if extended) price behavior, not a broken exit
  condition.
- **Severity:** Low
- **Scope:** Single trade, isolated
- **Affected Modules:** Module 4 (Exit Signal)
- **Classification:** Accepted limitation (a natural consequence of
  Target/Stop-only exits with no time cap)

### Investigation #5 — Cross-Premium Scale Mismatch

- **Finding:** Historically (18 days, 64 trades) no material scale
  mismatch occurred (worst ratio 1.79x, max distance reached was 4). The
  live CE@23650 event (distance 6, ratio ≈27.8x) was unprecedented — the
  baseline's apparent safety was a property of the data sampled, not a
  bound enforced by any rule.
- **Evidence:** Full 64-trade ratio/distance table; zero trades exceeded
  3x historically; live event far exceeded anything in the dataset.
- **Severity:** High (produced a materially corrupted live trade when the
  untested region was finally reached)
- **Scope:** Systemic — latent in the design since Module 2, only
  manifested once distance 6 was reached live
- **Affected Modules:** Module 2 (Premium Mapping), Module 3 (Entry
  Signal — no distance restriction)
- **Classification:** Strategy specification gap (the reference-strike /
  traded-strike comparable-scale assumption was never stated or bounded)

### Investigation #6 — Signal Eligibility at Extreme Strike Distance (CE@23650)

- **Finding:** 23650 was part of Module 1's original ATM±6 capture (not
  exposed by Ladder Expansion). Module 3 scans every captured strike
  uniformly with no distance-based eligibility rule, so it qualified
  exactly like any near-ATM strike. Module 8 (Ladder Expansion) played no
  role in eligibility — it only supplied the missing Stop Loss rung
  *after* the trade had already qualified and opened, which is what
  allowed the trade to execute rather than fail with an uncaught
  `ExitSignalError`.
- **Evidence:** Full path trace: Opening Range → Top/Bottom → Strike
  Generation (Module 1) → Premium Mapping (Module 2) → uniform scan
  (Module 3) → entry → edge-of-ladder SL gap → Module 8 fill → execution.
- **Severity:** High (same underlying event as #5, traced to its precise
  causal path)
- **Scope:** Systemic — same latent condition, now localized to two
  distinct causes (eligibility vs. executability)
- **Affected Modules:** Module 3 (Entry Signal — unrestricted scan),
  Module 8 (Ladder Expansion — removed the natural failure-safety-net for
  edge-strike entries)
- **Classification:** Strategy specification gap (eligibility: "explicitly
  specified but never bounded") combined with an accepted-limitation-
  turned-risk for Module 8 (it correctly did its documented job — supply
  a missing rung — but that job had the side effect of letting a
  previously-unreachable failure mode succeed instead of erroring out)

### Investigation #7 — Cross-Premium Mapping Validity

- **Finding:** The mapping ratio (mapped value ÷ own traded premium) stays
  close to parity near ATM (1.03 at distance 0) but diverges with
  acceleration as distance increases, reaching 2.30x at distance 6.
  Distance 6 additionally shows a target/stop inversion anomaly from
  ladder-edge asymmetry.
- **Evidence:** Full 0-6 distance table averaged across 18 sessions (936
  samples); ratio step-size roughly doubles at each further ring outward
  (0.025 → 0.094 → 0.145 → 0.241 → 0.342 → 0.426).
- **Severity:** High (quantitatively confirms #5/#6's root cause and shows
  it is not a one-off — it's a structural property of the mapping rule
  itself)
- **Scope:** Systemic — applies to the mapping rule in general, not just
  the one live incident
- **Affected Modules:** Module 2 (Premium Mapping — the core
  cross-referencing rule)
- **Classification:** Strategy specification gap (the rule's mathematical
  validity was never constrained to a distance range where it holds)

### Decision Matrix

| # | Investigation | Classification | Decision |
|---|---|---|---|
| 1 | Manual 10:20 trade (unreproducible) | Data issue | **DOCUMENT** |
| 2 | Completed level accounting | No defect (retracted) | **DOCUMENT** (closed, no action) |
| 3 | Open positions at market close | Accepted limitation | **KEEP** |
| 4 | Long duration trade (2026-07-10) | Accepted limitation | **KEEP** |
| 5 | Cross-premium scale mismatch (live incident) | Strategy specification gap | **REVISE** |
| 6 | Signal eligibility at extreme distance | Strategy specification gap | **REVISE** |
| 7 | Cross-premium mapping validity (systemic) | Strategy specification gap | **REVISE** |

No implementation defects were found across any of the seven
investigations — every issue traces back to either data/external
discrepancy, accepted-by-design behavior, or an unbounded specification
gap in how far the mapping/eligibility rules were ever meant to extend.
Investigations #5, #6, and #7 describe the same underlying gap from three
angles (incident, causal path, systemic measurement) and should be
treated as one design question when decided on, not three independent
ones.

No fixes or implementation changes are proposed in this review.

---

## Investigation #8 — Mapping Validity Threshold

**Status: CLOSED (investigation-only, no code modified, no fixes proposed)**

### Subject

Investigations #5-#7 established that the Premium Mapping ratio (mapped
value ÷ own traded premium) diverges with distance from ATM, and that the
divergence accelerates. This investigation asks whether a clean threshold
distance exists where the mapping "breaks," and re-examines the target/stop
inversion anomaly averages surfaced in Investigation #7 at the individual
record level rather than the aggregate level.

### Method

Same 18-session dataset as Investigation #7 (936 individual mapped-value
records across all 4 anchor/side ladder combinations, 13 strikes per
session). For every record: computed the ratio (mapped value ÷ own traded
premium), checked for a genuine per-record inversion (target < entry, or
stop > entry), and computed the percentage of records exceeding 1.1x,
1.25x, 1.5x, and 2.0x thresholds at each distance.

### Results

| Dist | Avg Ratio | Min Ratio | Max Ratio | Inversions | N | >1.1x | >1.25x | >1.5x | >2.0x |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.030 | 0.485 | 2.008 | 0 | 72 | 37.5% | 22.2% | 4.2% | 1.4% |
| 1 | 1.055 | 0.325 | 2.897 | 0 | 144 | 38.9% | 27.1% | 12.5% | 2.1% |
| 2 | 1.149 | 0.219 | 4.117 | 0 | 144 | 45.8% | 38.2% | 28.5% | 8.3% |
| 3 | 1.294 | 0.149 | 6.160 | 0 | 144 | 48.6% | 45.1% | 40.3% | 23.6% |
| 4 | 1.535 | 0.100 | 8.884 | 0 | 144 | 50.0% | 48.6% | 46.5% | 36.8% |
| 5 | 1.877 | 0.069 | 12.784 | 0 | 144 | 50.0% | 50.0% | 47.9% | 43.1% |
| 6 | 2.303 | 0.048 | 18.086 | 0 | 144 | 50.0% | 50.0% | 50.0% | 47.2% |

### Findings

1. **No per-record inversions found anywhere (0 at every distance).** This
   corrects Investigation #7's aggregate observation: the "average target <
   average entry" seen there at distance 6 was an artifact of averaging
   mismatched anchor/side combinations at the ladder edge (some records had
   no target, some had no stop), not an actual inversion on any individual
   mapped value.
2. **The real structural break is variance, not the average.** Even at
   distance 0 (ATM), ratios already range from 0.485 to 2.008. By distance
   6, the range is 0.048 to 18.086 — roughly a 375x spread within the same
   distance bucket.
3. **Threshold crossings plateau near 50% by distance 4-5**, not 6 — the
   1.1x/1.25x/1.5x crossing rates saturate there, meaning distance beyond
   4-5 mainly widens the extremes (the >2.0x rate keeps climbing) rather
   than adding new mid-range divergence.
4. **No single clean breakpoint distance exists.** Divergence is present
   even at distance 0 and grows continuously in both average and spread;
   there is no distance at which the mapping is perfectly scale-consistent.

### Conclusion

The live CE@23650 incident (ratio ≈27.8x) falls within — even below — the
maximum ratio already present in this historical dataset at distance 6
(18.086 was the observed max, and the true tail is evidently wider than
that sample caught). Such an outcome was mathematically always possible at
that distance; it had simply never been realized in the 18 sessions sampled
until the live occurrence.

### Disposition

Marked **CLOSED**. No strategy code was modified as a result of this
investigation. Classification: Strategy specification gap (same underlying
gap as Investigations #5-#7 — the mapping rule was never bounded to a
distance/ratio range where it remains meaningful).

---

## Investigation #9 — Competitor Exit Validation

**Status: CLOSED (investigation-only, no code modified)**

### Subject

For the CE@23950 trade open during today's (2026-07-27) live paper
trading session (entry 72.05), verify whether Module 4 (Exit Signal)
implements a competitor-based exit rule (i.e. exiting because the
corresponding PE at the same strike reached some mapped level).

### Task 1 — Identify the competitor exit level per the original specification

There is no competitor exit level anywhere in the specification, and
none was ever defined. The original Module 4 build instruction stated
explicitly:

> "Exit priority 1 Target 2 Mapped Stop Loss ... Never use Trailing
> Stop / Competitor Movement / OI / Synthetic Future / Indicators /
> Time Exit / Unless explicitly requested."

`strategy/exit_signal.py`'s own module docstring documents the same
exclusion: "This module contains NO trailing stop, competitor-movement,
OI, synthetic-future, indicator, or time-based exit logic - out of
scope by specification unless explicitly requested."

Since no competitor exit level was ever specified, Task 1 cannot be
completed with a concrete value - no rule defines "the mapped level one
position below" for the competitor (PE) side, no field carries it in
`PremiumMapping`, and no method computes it. Per the standing "never
invent a rule" instruction, none is defined here.

### Task 2 & 3 — Trace every candle after entry; was the condition evaluated?

`check_exit()` (`strategy/exit_signal.py:172-203`) is the only function
that decides an exit:

```python
if candle.high >= levels.target:
    return ExitSignal(..., reason=ExitReason.TARGET, ...)
if candle.low <= levels.stop_loss:
    return ExitSignal(..., reason=ExitReason.STOP_LOSS, ...)
return None
```

- `candle` is the traded contract's own CE candle - `check_exit` never
  receives a PE candle, and `PositionManager.process_candle` (its only
  caller) never passes one either.
- `ExitLevels` carries exactly two fields: `target`, `stop_loss`. No
  third field for a competitor threshold exists.

The competitor-PE condition was not evaluated on any candle - not
because it failed silently, but because no code path in Modules 4 or 5
ever receives or inspects the PE side of an open CE position. This is
"missing logic" only in the sense that it was never specified to
exist; per Task 1, it is an intentional exclusion from the original
spec, not an omission or defect.

### Task 4 — What does the current implementation check?

Only Target and Mapped Stop Loss, at every layer that performs an exit
check (Module 4's `check_exit`, Module 5's `PositionManager.process_candle`,
and Module 11's `LivePaperTradingEngine.on_candle_close`, which mirrors
the same two-condition check). No Competitor Exit exists anywhere in
the current implementation.

### Conclusion

Module 4 correctly implements what was specified - Target and Stop
Loss only. "Competitor Exit" is not a gap or defect relative to the
original specification; it is a rule that was explicitly named and
explicitly excluded at build time. Adding it would require a new,
fully specified business rule (what counts as "the competitor," which
field/ladder defines its threshold, exit priority relative to
Target/Stop) - not a bug fix.

### Disposition

Marked **CLOSED**. No strategy code was modified as a result of this
investigation. Classification: Accepted limitation (explicitly excluded
from scope at specification time, not a specification gap).

---

## Investigation #11 — Competitor Exit Logic Validation

**Status: CLOSED (investigation-only, no code modified, no optimisation performed)**

### Subject

Version 1.1's regression report (2026-07-27) showed Net P&L declining
~50% against Version 1.0 on the 18-session historical dataset, with 17
trades that were TARGET wins under V1.0 becoming COMPETITOR_EXIT under
V1.1. This investigation determines whether that regression stems from
an implementation defect, or from the implementation faithfully
executing a specification that does not match the originally intended
TradingView behaviour.

### Two competing interpretations of "competitor touch"

- **A. Immediate exit trigger** - the moment the competitor's price
  touches the mapped level, exit unconditionally, independent of the
  traded contract's own current price.
- **B. Mathematical confirmation** - the competitor touch merely
  confirms the traded contract has already entered its expected profit
  zone; exiting on it should never itself produce a loss (only the
  original Stop Loss should).

### Items 1-5: implementation correctness

All 17 TARGET(V1.0)->COMPETITOR_EXIT(V1.1) trades were independently
re-derived from raw historical data (same-anchor opposite-side ladder,
adjacent-rung-by-value threshold, competitor's own LOW field) and
cross-checked against the actually fetched competitor candle at the
recorded trigger timestamp.

| Check | Result |
|---|---|
| Correct competitor ladder | Correct in all 17 |
| Correct competitor level (source strike + value) | Correct in all 17 |
| "Next lower level" = adjacent rung by VALUE | Correct in all 17 |
| Correct candle field (competitor's own LOW) | Correct in all 17 |
| Competitor genuinely touching that level | TOUCHING = True in all 17 |

**No implementation bug exists.** The code executes the Version 1.1
specification exactly as written.

### Items 6-7: was the traded contract already in its profit zone?

For each of the 17 trades, the traded contract's own candle at the
exact Competitor Exit trigger moment was checked against its own
Target:

- **In 10 of 17 cases (59%), the traded contract's own candle HIGH had
  not yet reached Target on the trigger candle** - Competitor Exit
  fired while the trade was still meaningfully below its profit target.
  This matches interpretation A, not B.
- **In 5 of 17 cases (29%), the trade closed at a net LOSS under
  Version 1.1** despite V1.0 recording a genuine Target win on the
  identical entry (2026-07-06, 2026-07-16 11:15, 2026-07-20 11:35,
  2026-07-21, 2026-07-23 12:05) - directly contradicting the stated
  principle that Competitor Exit should never convert a winner into a
  loser.
- **A secondary, compounding effect**: in the remaining 7 of 17 cases
  where Target WAS reached within the trigger candle, the exit price
  (per Version 1.1's `CANDLE_APPROXIMATION` rule, using the traded
  contract's own candle OPEN) still understates the achieved move,
  since OPEN precedes the target-reaching price action within that
  candle.

### Root cause

Not an implementation defect. The root cause is a **mismatch between
the Version 1.1 specification as written and approved, and the
originally intended TradingView behaviour as now described**:

- Version 1.1 was specified, and the code correctly implements, an
  unconditional threshold trigger - interpretation A.
- The originally intended behaviour, as now described, is
  interpretation B - Competitor Exit as confirmation only, gated on
  the traded contract's own profit-zone status.

The measured regression (Net P&L -49%, 5/17 winners converted to
losers) is the direct, expected consequence of interpretation A on
this historical dataset - not a bug in how interpretation A was coded.

### Disposition

Marked **CLOSED**. No strategy code was modified and no optimisation
was performed. Classification: Strategy specification gap between the
Version 1.1 request as written and the originally intended TradingView
behaviour. Whether to revise the business rule (e.g. gate Competitor
Exit on profit-zone status) or accept interpretation A as intended is
a decision for the strategy owner, not addressed by this investigation.

---

## Investigation #12 — Define Profit Zone

**Status: CLOSED (investigation-only, no code modified, no optimisation, no threshold invented)**

### Subject

Following Investigation #11's finding that Competitor Exit currently
behaves as an unconditional trigger (interpretation A) rather than a
profit-zone confirmation (interpretation B), this investigation asks
whether historical evidence supports deriving an exact, non-invented
condition under which Competitor Touch always represents a profitable
exit.

### Method

For every one of the 34 historical Competitor Exit trades (18
sessions, Version 1.1), recomputed Target directly from the actual
Premium Mapping and computed how far the traded contract's own price
had travelled toward its own Target at the moment of trigger
(`progress_ratio = (exit_premium - entry_premium) / (target - entry_premium)`).

### Results

| | Count | % |
|---|---:|---:|
| Total competitor exits | 34 | 100% |
| Reached or exceeded own Target at trigger | 1 | 2.9% |
| Profitable (exit price > entry price) | 21 | 61.8% |
| Profitable but did NOT reach Target | 20 | 58.8% |
| Unprofitable | 13 | 38.2% |

Progress-ratio range: unprofitable trades -60.6% to 0.0%; profitable
trades +2.7% to +239.6%.

### Finding: no independent predictive relationship exists

The apparent split at the 0% progress-ratio boundary is **circular,
not predictive** - `progress_ratio > 0` is mathematically identical to
`exit_premium > entry_premium`, which is identical to "profitable," by
definition of P&L. It is not derivable in advance from the mapped
levels or competitor structure; it can only be known after observing
the very outcome it would need to predict.

Beyond that trivial boundary, no usable margin exists. Adjacent-outcome
trades sit on opposite sides of the zero line only a few premium
points apart (e.g. 2026-07-24 14:10: +2.7% progress, profitable
+Rs42; 2026-07-06 10:45: -4.2% progress, unprofitable -Rs29) - no gap
or threshold in the data would cleanly separate them.

Reaching Target itself is essentially unrelated to Competitor Touch:
in 33 of 34 cases (97.1%) the competitor threshold was touched while
the traded contract's own price was nowhere near its Target. This
reflects the ladders' construction from independent fields (own price
vs. the opposite contract's cross-referenced rung) - there is no
structural guarantee that one reaching its threshold implies any
particular fraction of the other's own distance to Target.

### Conclusion

**The historical data does not support a consistent mathematical
relationship under which Competitor Touch always represents a
profitable exit.** No percentage-of-target, premium-ratio, or
ladder-distance threshold in the data shows a clean, reliable
separating margin. Per instruction, no threshold is proposed or
invented.

### Disposition

Marked **CLOSED**. No strategy code was modified, no optimisation was
performed, and no threshold was invented. Classification: Strategy
specification gap (unresolved) - if a "Competitor Exit must always be
profitable" invariant is required, the evidence here does not support
achieving it through a numerical gate on progress-toward-target or
premium ratios alone. Deciding how to proceed (accept interpretation A,
redesign the rule around a different mechanism, or drop Competitor
Exit as specified) is a decision for the strategy owner.

---

## Investigation #13 — Validate the Mathematical Equivalence

**Status: CLOSED (investigation-only, no code modified, no optimisation, Premium Mapping mathematics only)**

### Subject

Rather than continue analysing Competitor Exit as an independent price
trigger, verify the underlying mathematical assumption: is CE Target
mathematically equivalent to the PE mapped competitor level? No P&L,
candle progress, or profit ratios analysed - Premium Mapping
mathematics only, for all 64 historical trades.

### 1. Field used (structural - true for every trade by construction)

Target always comes from the entry's OWN ladder (the field the entry
itself was confirmed against); Competitor Level always comes from the
SAME-anchor, OPPOSITE-side ladder (a different field). E.g. TOP CE:
Target from `top_ce_ladder` (PE_Low), Competitor from `top_pe_ladder`
(CE_High).

**Measured: Target and Competitor used the same field 0 of 64 times
(0.0%).** This follows directly from `premium_mapping.py`'s
construction and is not data-dependent - they can never be the same
field.

### 2. Source strike (data-dependent)

**Target's and Competitor's source strike coincided 49 of 64 times
(76.6%)** - a real but coincidental finding, arising because each
field is locally close to monotonic with strike near the money, not
because the two quantities are related.

### 3. Magnitude of movement (this is where the mapping diverges)

Even where the source strike coincided, the point-distance to Target
and the point-distance to the Competitor trigger were not equal or
proportionally related:

`delta_competitor / delta_target` ratio across 64 trades: **min 0.039,
max 30.824, mean 1.523** - a ~790x spread. Examples: 2026-07-08
24250 CE BOTTOM (ratio 0.04x - competitor needs almost no move at all);
2026-07-08 24200 PE BOTTOM (ratio 30.82x - competitor needs a
30x-larger move than Target). If the two represented the same mapped
movement, this ratio would cluster near 1.0; it does not.

### Root cause of the divergence

Target and Competitor Level are built from genuinely independent
premium series - two separate option legs' price action - with nothing
in Module 2's construction tying their movements together numerically.
They coincidentally share a neighbouring source strike most of the
time (local monotonicity), but never share field, and never share
magnitude.

### Conclusion

**CE Target and the PE mapped competitor level are not mathematically
equivalent.** They diverge in field (always) and in magnitude
(~790x spread even at matching source strikes). This gives the
underlying mechanical explanation for Investigation #11 and #12's
empirical findings that Competitor Touch rarely coincides with the
traded contract reaching its own profit zone - the two quantities were
never mathematically linked to begin with.

### Disposition

Marked **CLOSED**. No strategy code was modified, no optimisation was
performed. Classification: Strategy specification gap - the assumption
that a competitor touch represents "the same mapped movement" as
reaching Target is not supported by the Premium Mapping's own
mathematics. Whether the original TradingView strategy intended a
different definition of "competitor level," or whether Competitor Exit
as specified should be reconsidered, is a decision for the strategy
owner - this investigation identifies where the mapping diverges, not
what to do about it.

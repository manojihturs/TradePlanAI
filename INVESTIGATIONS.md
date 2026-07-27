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

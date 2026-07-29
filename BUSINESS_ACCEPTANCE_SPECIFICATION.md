# Business Acceptance Specification

**Role of this document:** executable business acceptance targets — not unit tests, not implementation. Each scenario below states what must eventually be true of the *business behaviour* once evidence exists, so that once a capability's evidence is verified, this document (not a fresh design pass) is what implementation is written against. Built from `STRATEGY_FUNCTIONAL_SPECIFICATION.md`, `BUSINESS_WORKFLOW_SPECIFICATION.md`, and `REQUIREMENTS_TRACEABILITY_MATRIX.md` — no new trading rule is introduced. Every unknown is marked `UNRESOLVED – Awaiting Strategy Evidence`.

---

## 1. Reference Collection

**Business Goal:** Capture a fixed, reliable set of CE/PE High/Low reference values that every later stage measures against.

**Preconditions:** The trading session has opened; the first 5-minute candle (09:15–09:20) has completed.

**Trigger:** First-candle completion.

**Expected Outcome:** For each strike in the 13-level ladder (6 ITM, 1 ATM, 6 OTM), a CE High, CE Low, PE High, PE Low value is recorded, taken from that strike's own contract OHLC over the 09:15–09:20 candle (Rule 1, CONFIRMED).

**Failure Conditions:** The candle is not in candle-mode (OHLC not populated) — reference collection must not silently proceed with partial data. UNRESOLVED – Awaiting Strategy Evidence: what happens if a given strike's option contract has no trades in the first candle (no OHLC to capture at all).

**Blocking Dependencies:** None — this capability's evidence is complete and does not wait on Weekly Future or Strike Selection to be *correct*, only on knowing *which* strikes to build the ladder around in a live (non-test) run.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §6, Rule 1 (dictated, 2026-07-29).

**Current Status:** Implemented (`ReferenceBuilder`, Sprint 4), 100% coverage, matches this scenario exactly for the confirmed portion.

**Acceptance Status:** **MET** for the confirmed scope (per-strike CE/PE High/Low capture). Ladder step-size generalization and fixed-vs-recalculated status remain `UNRESOLVED – Awaiting Strategy Evidence`.

---

## 2. Weekly Future

**Business Goal:** Establish the session's Weekly Future High and Low as the foundational reference pair for strike selection.

**Preconditions:** The first 5-minute candle has completed.

**Trigger:** First-candle completion (same trigger as Reference Collection).

**Expected Outcome:** UNRESOLVED – Awaiting Strategy Evidence — no formula exists to state an expected numeric outcome. What can be stated: exactly one High value and one Low value are produced per session (Section 1's overview), from the same first candle Reference Collection uses.

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence. The one available worked example (`TR-001.md`) itself produces a Low exceeding the High for the same candle — a structural impossibility — so even the shape of a "failure" (as opposed to a "wrong but structurally valid" result) is not established.

**Blocking Dependencies:** None upstream (root of the dependency chain) — but this capability is itself the blocker for everything downstream of it.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §4; `WEEKLY_FUTURE_BLOCKER_REPORT.md` (full contradiction record). Confidence: **Low** — evidence exists but fails its own internal consistency check.

**Current Status:** Protocol stub (`WeeklyFutureCalculator`), raises `UnresolvedBusinessRuleError`.

**Acceptance Status:** **BLOCKED.** No acceptance scenario can be written beyond "a High and a Low are produced" until the formula is recovered.

---

## 3. Strike Selection

**Business Goal:** Select the session's Top Strike and Bottom Strike (both "ATM"), anchoring the reference ladder and every downstream stage.

**Preconditions:** A Weekly Future High/Low value exists for the session.

**Trigger:** Weekly Future calculation completing.

**Expected Outcome:** UNRESOLVED – Awaiting Strategy Evidence — no ATM basis or rounding rule is stated. What can be stated: exactly one Top Strike and one Bottom Strike are produced (Section 5's overview), both nominally "ATM."

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence, including whether Top Strike equalling Bottom Strike is itself a valid outcome or a failure.

**Blocking Dependencies:** Weekly Future.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §5. Confidence: **None** — the term "ATM" is used but never operationalized.

**Current Status:** Protocol stub (`StrikeSelector`), raises `UnresolvedBusinessRuleError`.

**Acceptance Status:** **BLOCKED**, transitively on Weekly Future and directly on its own missing ATM rule.

---

## 4. TP Calculation

**Business Goal:** Continuously determine, from 09:21 AM onward, whether Top Strike's and Bottom Strike's CE/PE prices are currently qualifying against a competitor level.

**Preconditions:** Reference Collection complete; Top Strike/Bottom Strike selected; time ≥ 09:21 AM.

**Trigger:** UNRESOLVED – Awaiting Strategy Evidence (tick vs. candle cadence, per Spec §20 item 12).

**Expected Outcome:** For TP High: sustained `Top Strike CE > competitor PE Low` AND `Top Strike PE < competitor CE High` (mirrored for TP Low) — the sustain *test itself* is stated (Spec §7), but its output cannot be fully specified because the competitor's identity is UNRESOLVED – Awaiting Strategy Evidence, and whether the result is a price, a boolean, or both is UNRESOLVED – Awaiting Strategy Evidence.

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence — no breach/failure test is defined beyond "no longer sustains," and "sustains" itself has no formal touch/breach definition given.

**Blocking Dependencies:** Strike Selection, Reference Collection.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7. Confidence: **Medium** — the test's logical form is precise; its inputs are not.

**Current Status:** Protocol stub (`TPEngine`), output typed `object` (shape undecided).

**Acceptance Status:** **BLOCKED.** Even with a competitor rule, the output-shape decision (Spec §20 item 13) must be made before an acceptance scenario can specify a concrete expected outcome.

---

## 5. Qualification

**Business Goal:** Represent the current-state sustain/breach outcome of a strike's TP test — explicitly not a prediction.

**Preconditions:** A TP state exists for the strike being evaluated.

**Trigger:** Each TP Calculation update cycle (inherits TP Calculation's own unresolved cadence).

**Expected Outcome:** UNRESOLVED – Awaiting Strategy Evidence. What can be stated: qualification represents current market state only, and is explicitly warned to be revocable by external events (news/budget/war/natural disaster — Spec §7).

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence — no external-invalidation detection mechanism is specified at all, only that such events "may invalidate" qualification.

**Blocking Dependencies:** TP Calculation. Additionally, whether this is a distinct capability from TP Calculation at all is itself UNRESOLVED – Awaiting Strategy Evidence (Spec §8 explicitly notes the source material never separates the two).

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7–§8. Confidence: **Low**.

**Current Status:** Protocol stub (`QualificationEngine`).

**Acceptance Status:** **BLOCKED.**

---

## 6. Winner Detection

**Business Goal:** Detect, candle by candle, the same-candle CE+PE reference-level touch that triggers a trade.

**Preconditions:** A 13-level reference ladder exists for the session.

**Trigger:** Each candle close, from 09:21 AM onward (candle timeframe itself UNRESOLVED – Awaiting Strategy Evidence, Spec §20 item 7).

**Expected Outcome:** If a CE reference level is touched **and** a PE reference level is touched in the same candle, exactly one side is declared Winner and the other Loser — no tie-break is needed (Rule 3, CONFIRMED). If no such simultaneous touch occurs, no Winner is declared and evaluation continues to the next candle.

**Failure Conditions:** Multiple touches within a single candle are explicitly stated not to occur — this is a confirmed assumption to build against, not a gap. UNRESOLVED – Awaiting Strategy Evidence: whether "CE"/"PE" here refers to Top Strike's CE/PE specifically, every strike's simultaneously, or some other subset.

**Blocking Dependencies:** Reference Collection (met). Strike Selection (for live, non-test-fixture use). **Separately and critically:** whether this capability also depends on TP Calculation/Qualification output is UNRESOLVED – Awaiting Strategy Evidence — the specification text describing Winner Detection (§9) never mentions TP/Qualification state as an input, and this document does not assume a dependency the evidence does not state.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §9, Rule 3. Confidence: **High** for the trigger rule itself; **None** for its relationship (if any) to TP Calculation/Qualification.

**Current Status:** Implemented against caller-supplied CE/PE snapshots and reference levels (`WinnerEngine`, tested, 100% coverage). Live-mode use (against real Strike-Selection-derived strikes) is blocked upstream.

**Acceptance Status:** **MET** for the confirmed trigger logic in test-mode. **BLOCKED** for live-mode use (needs Strike Selection). The TP/Qualification-dependency question is flagged separately — it is not resolvable by evidence gathering about Winner Detection alone; it requires evidence that either confirms or explicitly rules out the dependency.

---

## 7. Entry

**Business Goal:** Convert a Winner into an actual trade entry, enforcing exactly one active trade at a time.

**Preconditions:** A Winner has been declared.

**Trigger:** `WinnerDetectedEvent`.

**Expected Outcome:** If no trade is currently active, a new trade is opened on the winning side/strike, immediately. If a trade is already active, the Winner is ignored outright — not queued, not deferred, no state retained about it (Rule 4, CONFIRMED).

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence: entry price mechanism (market order at signal-candle close vs. limit at the reference level) is not stated at all, so no acceptance scenario can specify an expected entry price.

**Blocking Dependencies:** Winner Detection.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §10, Rule 4. Confidence: **High** for the ignore-while-active rule; **None** for entry price.

**Current Status:** Implemented (`EntryEngine`), matches the confirmed rule exactly.

**Acceptance Status:** **MET** for the single-active-trade rule. **BLOCKED** for anything requiring an exact entry price (not currently tested, because untestable without evidence, not because of a defect).

---

## 8. Position Monitoring

**Business Goal:** Track an active trade's Target, Support, and Competitor-Exit levels, and any trailing-stop state, every candle it remains open.

**Preconditions:** A trade is active.

**Trigger:** Each candle close while the trade remains open.

**Expected Outcome:** For a Winner at strike S: CE → Target = CE(S+1), Support = CE(S-1), Competitor monitored = PE(S-1); PE → Target = PE(S-1), Support = PE(S+1), Competitor monitored = CE(S+1) (Rule 2, CONFIRMED, general form).

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence: trailing-stop tracking state (e.g. a running peak-favorable-excursion value) is not modeled anywhere, so no failure/edge condition for it can be specified yet.

**Blocking Dependencies:** Entry.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11, Rule 2 (general table, resolved from the original 24100-CE worked example). Confidence: **High** for Target/Support/Competitor mapping.

**Current Status:** Implemented (`PositionManager`), matches the confirmed mapping exactly.

**Acceptance Status:** **MET** for Target/Support/Competitor mapping. **BLOCKED** for trailing-stop tracking (Trailing Stop capability, below).

---

## 9. Exit

**Business Goal:** Decide whether the active trade should close this candle, and why.

**Preconditions:** A trade is active.

**Trigger:** Each candle close, evaluated against four possible conditions: Target Hit, Competitor Level Hit, Stop Loss, Trailing Stop.

**Expected Outcome:** Target Hit — trade closes when its own Target reference level (per Position Monitoring) is touched. Competitor Level Hit — trade closes when the monitored competitor option reaches "its own reference level" (Spec §11) — **UNRESOLVED – Awaiting Strategy Evidence** exactly which of the competitor's own two levels (High or Low) is the trigger. Stop Loss / Trailing Stop — see their own sections below.

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence: if multiple exit conditions are met on the same candle, no precedence/priority order is specified by the business evidence. The built `ExitEngine`'s check order (Target → Competitor → StopLoss → TrailingStop) is an engineering default documented as such — this acceptance specification does not treat that order as a verified business rule, and no acceptance scenario may assume it is correct.

**Blocking Dependencies:** Position Monitoring (met, for Target/Competitor); Stop Loss (blocked); Trailing Stop (blocked).

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11, §19. Confidence: **High** (Target/Competitor strike identity), **None** (Stop Loss), **Low** (Trailing Stop), **None** (exit priority).

**Current Status:** Implemented for Target/Competitor (`ExitEngine`); Stop Loss/Trailing Stop calls are wired to Protocol stubs (drop-in ready).

**Acceptance Status:** **MET** for Target Hit. **READY AFTER EVIDENCE** for Competitor Level Hit (needs only the High-vs-Low trigger clarification, not a redesign). **BLOCKED** for Stop Loss and Trailing Stop branches, and for any scenario involving same-candle multi-condition precedence.

---

## 10. Stop Loss

**Business Goal:** Close an active trade when it has moved against the position beyond an acceptable loss.

**Preconditions:** A trade is active.

**Trigger:** Each candle close (already wired into `ExitEngine`'s per-candle evaluation).

**Expected Outcome:** UNRESOLVED – Awaiting Strategy Evidence in full — no price basis, placement rule, or trigger condition is stated anywhere in current evidence (Spec §20 item 4, the single largest unstated rule after Weekly Future itself).

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence.

**Blocking Dependencies:** None technically (the `ExitEngine` call-site already exists) — fully blocked on its own missing business rule.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11 (named only, no content). Confidence: **None**.

**Current Status:** Protocol stub (`StopLossEngine`), already constructor-injected into `ExitEngine` (verified — pure drop-in once the rule exists).

**Acceptance Status:** **BLOCKED.** No acceptance scenario can be written beyond "closes the trade when triggered" until the rule exists — even a placeholder numeric boundary would be an invented rule, which this document does not do.

---

## 11. Trailing Stop

**Business Goal:** Lock in a minimum net profit as a trade moves favorably, closing it if the price retraces beyond the trail.

**Preconditions:** A trade is active.

**Trigger:** Each candle close (already wired into `ExitEngine`'s per-candle evaluation, evaluated after Stop Loss).

**Expected Outcome:** Whenever this engine signals an exit, the trade's realized net result (after brokerage, exchange charges, and tax) must be at least +3 premium points (CONFIRMED — the one numeric constraint in this entire capability). Activation trigger and trail step/distance are UNRESOLVED – Awaiting Strategy Evidence (Spec §20 items 9–10), so no acceptance scenario can state *when* trailing begins or *how far* it trails.

**Failure Conditions:** UNRESOLVED – Awaiting Strategy Evidence — the brokerage/exchange/tax figures needed to compute "net" numerically do not exist in current evidence, so the one confirmed constraint cannot itself be validated in an acceptance test yet.

**Blocking Dependencies:** A genuine architectural prerequisite, not a business-rule one: `TradePosition` (frozen dataclass) has no field for tracking peak favorable excursion, which a trailing stop conventionally requires regardless of the eventual rule's specifics (`BUSINESS_STATE_MODEL.md` §6) — this must be designed as part of implementation, not assumed away.

**Supporting Evidence:** `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §13. Confidence: **Low** — one constraint confirmed, everything else absent.

**Current Status:** Protocol stub (`TrailingStopEngine`), already constructor-injected into `ExitEngine` (verified).

**Acceptance Status:** **BLOCKED.** The one testable invariant (+3 net minimum) cannot be exercised without the cost figures needed to compute "net."

---

## Acceptance Readiness Summary

| Capability | Classification | Basis |
|---|---|---|
| **Reference Collection** | **READY FOR IMPLEMENTATION** | Already implemented and meets its acceptance scenario in full for the confirmed scope |
| **Weekly Future** | **BLOCKED** | Evidence exists but is internally self-contradictory; not "awaiting" evidence so much as "the available evidence has already failed verification" |
| **Strike Selection** | **BLOCKED** | Zero evidence beyond the term "ATM"; transitively blocked on Weekly Future |
| **TP Calculation** | **BLOCKED** | Test logic partially stated but competitor identity and output shape both unresolved; transitively blocked on Strike Selection |
| **Qualification** | **BLOCKED** | Not even confirmed as a distinct capability from TP Calculation |
| **Winner Detection** | **READY AFTER EVIDENCE** (test-mode already **READY FOR IMPLEMENTATION** and met) | Trigger logic fully confirmed and built; live-mode use needs only Strike Selection's output, not new business-rule evidence about Winner Detection itself. The TP/Qualification-dependency question does not block this classification — it is a separate open question tracked in Exit/Position Monitoring's own entries and in `BUSINESS_ARCHITECTURE_REVIEW.md`, not a precondition for Winner Detection's own confirmed trigger rule |
| **Entry** | **READY FOR IMPLEMENTATION** (single-active-trade rule); **BLOCKED** (entry price) | Split status — implemented and correct for the confirmed portion, no path to close the entry-price gap without new evidence |
| **Position Monitoring** | **READY FOR IMPLEMENTATION** (Target/Support/Competitor mapping); **BLOCKED** (trailing-state tracking) | Same split pattern as Entry |
| **Exit** | **READY FOR IMPLEMENTATION** (Target Hit); **READY AFTER EVIDENCE** (Competitor Level Hit — needs only the High/Low clarification); **BLOCKED** (Stop Loss, Trailing Stop, multi-condition precedence) | Three-way split, reflecting the capability's genuinely mixed evidence state |
| **Stop Loss** | **BLOCKED** | Zero evidence; framework-ready (drop-in) once evidence arrives |
| **Trailing Stop** | **BLOCKED** | One numeric constraint confirmed, everything else (including the cost figures needed to test that one constraint) missing; also carries an architectural prerequisite (peak-tracking state) independent of the business rule |

**Net effect:** every capability in this document is either already meeting its acceptance scenario, or has a specific, named piece of missing evidence standing between it and one — none require further architectural design work to become implementable once that evidence arrives.

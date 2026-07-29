# Requirements Traceability Matrix

**Role of this document:** the single answer to "which source evidence justifies each business module, workflow step, event, and future implementation?" — linking every capability across the six artifacts that already exist (`STRATEGY_FUNCTIONAL_SPECIFICATION.md`, `BUSINESS_WORKFLOW_SPECIFICATION.md`, `BUSINESS_ARCHITECTURE.md` + its 4 companions, `BUSINESS_RULE_INTEGRATION_GUIDE.md`, `research/EVIDENCE_INTAKE_PROCESS.md`, `src/`). No new business rule, calculation, or threshold is introduced here — this document only traces what already exists in those six sources back to each other. Every capability field with no supporting evidence is marked `UNRESOLVED – Awaiting Strategy Evidence`.

**Ten capabilities are tracked**, one more than the nine named in the prompt: **Reference Collection** is added because it is a real, already-implemented capability (`ReferenceBuilder`, Sprint 4) sitting between Strike Selection and TP Calculation in the workflow, and omitting it would leave a traceability gap between two capabilities that do appear.

---

## Section 1 — Business Capability Matrix

| Capability | Purpose | Current Status | Evidence Available | Evidence Missing | Implementation Status | Blocking Dependencies |
|---|---|---|---|---|---|---|
| **Weekly Future** | Compute session Weekly Future High/Low | BLOCKED | One self-contradictory worked example (`TR-001.md`) | The formula itself, its inputs, recalculation cadence | Protocol stub only (`UnresolvedBusinessRuleError`) | None (root of chain) |
| **Strike Selection** | Select Top/Bottom Strike (ATM) | BLOCKED | None beyond the term "ATM" | ATM basis, rounding rule, top/bottom-equal case | Protocol stub only | Weekly Future |
| **Reference Collection** | Capture per-strike CE/PE High/Low from the first 5-min candle | **CONFIRMED, BUILT** | Rule 1 (dictated business rules, 2026-07-29) | Ladder step size beyond one example; fixed-vs-recalculated | **Implemented** (`ReferenceBuilder`, Sprint 4, 100% coverage) | None functionally; live use needs Strike Selection's strikes as input |
| **TP Calculation** | Continuously compute TP High/Low qualification test | BLOCKED | Qualification test formula (boolean form only) | Competitor-strike identity, update cadence, output shape (price/flag/both) | Protocol stub only, output typed `object` | Strike Selection, Reference Collection |
| **Qualification** | Represent current-state sustain/breach of TP | BLOCKED | Same source as TP Calculation; explicitly not separated from it | Whether it's a distinct engine at all; external-invalidation mechanism | Protocol stub only | TP Calculation |
| **Winner Detection** | Detect same-candle CE+PE touch, declare Winner | **PARTIALLY CONFIRMED, BUILT (test-mode)** | Trigger condition + Rule 3 (tie-break resolved) | Candle timeframe post-09:21; which strike(s)' CE/PE; whether TP/Qualification gates this at all | **Implemented** against caller-supplied strikes/levels (`WinnerEngine`); live-mode wiring blocked upstream | Reference Collection (built); Strike Selection (live use) |
| **Entry** | Convert Winner into a trade, enforcing single-active-trade | **CONFIRMED, BUILT** | Rule 4 (dictated, fully specified except entry price) | Entry price mechanism | **Implemented** (`EntryEngine`) | Winner Detection |
| **Position Monitoring** | Track Target/Support/Competitor-Exit + trailing state while a trade is open | **CONFIRMED (mapping), BUILT** | Rule 2 (Target/Support/Competitor mapping, general form) | Trailing-stop tracking mechanics (peak/high-water-mark not modeled) | **Implemented** (`PositionManager`) | Entry |
| **Exit** | Decide Target/Competitor/StopLoss/TrailingStop closure | **PARTIALLY CONFIRMED, BUILT (framework)** | Exit-condition list; Target/Competitor confirmed (Rule 2) | Exit-priority order when multiple trigger same candle; which of competitor's High/Low triggers | **Implemented** for Target/Competitor (`ExitEngine`); StopLoss/TrailingStop wired but stubbed | Position Monitoring, Stop Loss, Trailing Stop |
| **Stop Loss** | Evaluate SL breach on active position | BLOCKED | None — named only | The entire rule: price basis, placement, trigger | Protocol stub only; **already wired into `ExitEngine`** (pure drop-in once resolved) | Exit (consumer, already built) |
| **Trailing Stop** | Evaluate trailing-stop breach on active position | BLOCKED | Minimum net +3 premium points guarantee (confirmed) | Activation trigger, trail step/distance, brokerage/exchange/tax figures | Protocol stub only; **already wired into `ExitEngine`**; needs new state (peak favorable excursion) not on `TradePosition` today | Exit (consumer, already built) |

---

## Section 2 — Evidence Traceability

| Capability | Supporting Documents | Supporting Transcript | Worked Examples | Contradictions | Confidence | Missing Evidence |
|---|---|---|---|---|---|---|
| **Weekly Future** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §4; `WEEKLY_FUTURE_BLOCKER_REPORT.md`; `research/analysis/WEEKLY_FUTURE_VERIFICATION.md` | `research/transcripts/TR-001.md` (only transcript in repo) | One (TR-001 lines 2460–2521) | Yes — 4 distinct contradictions logged in `WEEKLY_FUTURE_BLOCKER_REPORT.md` §2 (addend spoken 3 ways; two irreconcilable Low values; Low > High for same candle; PE input stated 2 ways) | **Low** — the one example fails its own internal consistency check | The referenced "Complete Calculation Video," or ≥3 independently consistent worked examples (blocker report §5) |
| **Strike Selection** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §5 | None | None | None (nothing to contradict — term stated, not demonstrated) | **None** | ATM basis, rounding rule |
| **Reference Collection** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §6, Rule 1 | None (dictated directly in chat, not transcript-sourced) | Numeric example only for ladder step (24250, 24200, …) | None | **High** — CONFIRMED (v1.1), directly dictated and unambiguous | Ladder step generalization beyond the one example; fixed-vs-recalculated status |
| **TP Calculation** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7 | None | None (boolean condition given, no numeric walkthrough) | None | **Medium** — the qualification *test* is stated precisely; its *inputs* (competitor identity) are not | Competitor-strike identity rule specific to this test |
| **Qualification** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7–§8 | None | None | None | **Low** — not even confirmed as a distinct capability from TP Calculation | Whether it is a separate engine; external-invalidation mechanism |
| **Winner Detection** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §9; `BUSINESS_WORKFLOW_SPECIFICATION.md` Stage 7 | None | None (rule stated narratively) | None (Rule 3 explicitly closes the one ambiguity that existed — tie-break) | **High** for the trigger rule itself; **None** for its relationship to TP/Qualification (workflow doc finds no evidence either confirming or ruling out a dependency) | Candle timeframe; TP/Qualification-gates-Winner question |
| **Entry** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §10, Rule 4 | None | None | None | **High** | Entry price mechanism only |
| **Position Monitoring** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11, Rule 2 | None | Yes — one fully worked example (24100 CE) generalized in v1.1 to the S±1 table | None | **High** | Which of competitor's own High/Low triggers exit |
| **Exit** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11, §19 | None | Same as Position Monitoring for Target/Competitor | None on Target/Competitor; SL entirely unstated | **High** (Target/Competitor), **None** (Stop Loss), **Low** (Trailing Stop, guarantee only) | SL rule in full; exit-priority order |
| **Stop Loss** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11 (named only) | None | None | None | **None** | Everything |
| **Trailing Stop** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §13 | None | None | None | **Low** — one numeric constraint confirmed, nothing else | Activation, step/distance, cost figures |

---

## Section 3 — Architecture Traceability

| Capability | Business Workflow | Business Architecture | Business State Model | Business Event Flow | Business Dependency Map | Business Rule Integration Guide |
|---|---|---|---|---|---|---|
| **Weekly Future** | Stage 3 | §1 | §1 (cadence UNRESOLVED) | `WeeklyFutureCalculatedEvent` row | Root node | §2.1, §3 step 1, §4, §7 |
| **Strike Selection** | Stage 4 | §2 | §2 (derivative of §1) | `StrikeSelectedEvent` row | Node 2 | §2.2, §3 step 2, §4, §7 |
| **Reference Collection** | Stage 2 | *(not separately sectioned — pre-existing built capability, referenced throughout)* | *(not separately sectioned)* | Not modeled as bus-driven (no bus dependency on `ReferenceBuilder`, per `BUSINESS_ARCHITECTURE_REVIEW.md` Finding 2) | Node "ReferenceBuilder — built" | §1 (pipeline diagram) |
| **TP Calculation** | Stage 5 | §3 | §3 | `TPUpdated` row (proposed, not implemented) | Node "TPEngine" | §2.3, §3 step 3, §4, §7 |
| **Qualification** | Stage 6 | §4 | §4 (derivative of §3) | `QualificationChanged` row (proposed, not implemented) | Node "QualificationEngine" | §2.4, §3 step 4, §4, §7 |
| **Winner Detection** | Stage 7 | Consolidated Cross-Module Gaps section (TP/Qualification→Winner wiring) | *(not separately sectioned — pre-existing built capability)* | `WinnerDetectedEvent` row | Node "WinnerEngine — built" | §1 (pipeline diagram, "today only run against caller-supplied test strikes") |
| **Entry** | Stage 8 | *(not separately sectioned — pre-existing built capability)* | *(not separately sectioned)* | `TradeOpenedEvent` row | Node "PositionManager — built" (entry flows into it) | §1 |
| **Position Monitoring** | Stage 9 | *(not separately sectioned)* | *(not separately sectioned)* | Not modeled as a distinct event; folded into Exit's loop | Node "PositionManager — built" | §1 |
| **Exit** | Stage 10 | §5, §6 (Stop Loss/Trailing Stop framing applies to the whole Exit decision) | §5, §6 | `TargetHitEvent`/`CompetitorHitEvent`/`TradeClosedEvent` rows | Node "ExitEngine — built" | §2.5, §2.6, §3 step 5 |
| **Stop Loss** | Stage 10 (folded in) | §5 | §5 | No dedicated event — folds into `TradeClosedEvent` | Node "StopLossEngine", solid edge from `ExitEngine` (verified wired) | §2.5 |
| **Trailing Stop** | Stage 9–10 (folded in) | §6 | §6 (high-water-mark gap identified) | No dedicated event — folds into `TradeClosedEvent` | Node "TrailingStopEngine", solid edge from `ExitEngine` (verified wired) | §2.6 |

---

## Section 4 — Implementation Traceability

| Capability | Python Protocol | Future Engine | Events Consumed | Events Produced | Downstream Modules | Current Status |
|---|---|---|---|---|---|---|
| **Weekly Future** | `interfaces/weekly_future_calculator.py::WeeklyFutureCalculator.calculate` | `src/weekly_future/` (not created) | None (direct invocation) | `WeeklyFutureCalculatedEvent` (real, unconsumed today) | Strike Selection | Stub, raises `UnresolvedBusinessRuleError` |
| **Strike Selection** | `interfaces/strike_selector.py::StrikeSelector.select` | `src/strike_selector/` (not created) | None (direct invocation) | `StrikeSelectedEvent` (real, unconsumed today) | Reference Collection (live use), TP Calculation | Stub |
| **Reference Collection** | *(no interface — direct class)* `reference_builder/reference_builder.py::ReferenceBuilder.build` | `src/reference_builder/` | None (no bus dependency at all — verified, `BUSINESS_ARCHITECTURE_REVIEW.md` Finding 2) | None | TP Calculation, Winner Detection | **Implemented**, 100% coverage |
| **TP Calculation** | `interfaces/tp_engine.py::TPEngine.update` | `src/tp_engine/` (not created) | Conceptually `ReferenceLevelsGenerated` (not implemented anywhere) | Conceptually `TPUpdated` (not implemented) | Qualification | Stub, output typed `object` (shape undecided) |
| **Qualification** | `interfaces/qualification_engine.py::QualificationEngine.evaluate` | `src/qualification_engine/` (not created) | Conceptually `TPUpdated` (not implemented) | Conceptually `QualificationChanged` (not implemented) | Winner Detection (wiring UNRESOLVED) | Stub |
| **Winner Detection** | *(no interface — direct class)* `winner_engine/winner_engine.py::WinnerEngine.evaluate` | `src/winner_engine/` | None today (no dependency on TP/Qualification — verified) | `WinnerDetectedEvent` (real) | Entry | **Implemented** against caller-supplied CE/PE snapshots |
| **Entry** | *(no interface — direct class)* `entry_engine/entry_engine.py` | `src/entry_engine/` | `WinnerDetectedEvent` (real, subscribed) | `TradeOpenedEvent` (real, via `PositionManager`) | Position Monitoring | **Implemented** |
| **Position Monitoring** | *(no interface — direct class)* `position_manager/position_manager.py` | `src/position_manager/` | None (direct invocation from Entry) | None directly; feeds Exit's checks | Exit | **Implemented** |
| **Exit** | *(no interface — direct class)* `exit_engine/exit_engine.py` | `src/exit_engine/` | None (synchronous per-candle `evaluate()`) | `TargetHitEvent`, `CompetitorHitEvent`, `TradeClosedEvent` (all real) | Session Close (recalculation trigger) | **Implemented** for Target/Competitor; Stop Loss/Trailing Stop calls wired to stubs |
| **Stop Loss** | `interfaces/stop_loss_engine.py::StopLossEngine.check` | `src/stop_loss_engine/` (not created) | None (called synchronously by `ExitEngine`) | None directly (feeds `ExitEngine`'s own `TradeClosedEvent`) | None beyond `ExitEngine` | Stub; **constructor-injected into `ExitEngine` today** (verified) |
| **Trailing Stop** | `interfaces/trailing_stop_engine.py::TrailingStopEngine.check` | `src/trailing_stop_engine/` (not created) | None (called synchronously by `ExitEngine`) | None directly | None beyond `ExitEngine` | Stub; **constructor-injected into `ExitEngine` today** (verified); needs new peak-tracking state not on `TradePosition` |

---

## Section 5 — Verification Matrix

| Capability | Required Tests | Replay Tests | Acceptance Criteria | Evidence Quality Required |
|---|---|---|---|---|
| **Weekly Future** | Unit: exact High/Low from known candle, once formula exists | Yes — fixture historical file, determinism across repeated runs | Per `BUSINESS_RULE_INTEGRATION_GUIDE.md` §6 (all 6 criteria): no `UnresolvedBusinessRuleError` on well-formed input; rule cited to actual evidence; Protocol conformance; 100% coverage + clean lint/type gates; no unrelated file changes; zero circular deps | `WEEKLY_FUTURE_BLOCKER_REPORT.md` §5 gate: the referenced Complete Calculation Video, or ≥3 independently consistent worked examples |
| **Strike Selection** | Unit: exact top/bottom strike from known `WeeklyFuture` | Yes — feed into `ReferenceBuilder.build()`, confirm no validation errors | Same 6-criteria template as above | Confirmed ATM basis + rounding rule, per `EVIDENCE_INTAKE_PROCESS.md`'s classification scheme (Confirmed Rule, not Assumption) |
| **Reference Collection** | Already exists — parametrized fixtures, 100% coverage | Already exists | Already met | Already met (Rule 1, CONFIRMED v1.1) — no further evidence needed |
| **TP Calculation** | Cannot be meaningfully designed until output shape (Section 4 above) is decided | Integration: feed into `QualificationEngine`, confirm downstream state correctness | Same 6-criteria template, plus: output-shape decision documented as part of the implementation itself | Competitor-identity rule confirmed; update-cadence confirmed |
| **Qualification** | Same dependency as TP Calculation | Integration only, no dedicated replay test until TP Calculation exists | Same 6-criteria template | Same as TP Calculation, plus external-invalidation mechanism if that scope is confirmed in-scope |
| **Winner Detection** | Already exists for the built trigger logic; **new** tests needed only if TP/Qualification wiring is confirmed to exist | Already exists (test-mode); live-mode replay blocked on Strike Selection | Already met for current scope; wiring decision (see Section 6) would add new acceptance criteria if made | Candle-timeframe confirmation; TP/Qualification-gates-Winner confirmation (or explicit confirmation that it does not) |
| **Entry** | Already exists | Already exists | Already met | Entry-price mechanism confirmation (currently untested because unstated, not because of a defect) |
| **Position Monitoring** | Already exists for Target/Support/Competitor mapping | Already exists | Already met for current scope; trailing-state tracking untested (doesn't exist yet) | None further needed for the confirmed mapping itself |
| **Exit** | Already exists for Target/Competitor; StopLoss/TrailingStop tests exist only via fakes (`_AlwaysTrueStopLoss`/`_AlwaysFalseStopLoss`) per `BUSINESS_RULE_INTEGRATION_GUIDE.md` §5 | Already exists for Target/Competitor | Exit-priority order remains an engineering default, not a verified business rule — flagged, not silently treated as acceptance-tested | Exit-priority order confirmation; competitor High/Low trigger confirmation |
| **Stop Loss** | Unit: boundary condition at/around trigger, matching existing fake-based test shape | None until rule exists | Same 6-criteria template; explicitly, per §4 of the Integration Guide, must not raise for ordinary "not triggered" cases | Full SL rule (price basis, placement, trigger) — currently zero evidence |
| **Trailing Stop** | Unit: boundary exactly at +3 net and just below it, once brokerage/exchange/tax figures known | None until rule exists | Same 6-criteria template, plus the +3-net invariant must be validated inside the implementation (not type-enforced) | Activation trigger, step/distance, and cost figures — partial evidence (the +3 net guarantee itself is confirmed) |

---

## Section 6 — Gap Summary

| Status | Capabilities |
|---|---|
| **Implemented** | Reference Collection, Entry, Position Monitoring, Exit (Target/Competitor portion only) |
| **Architecturally Ready** (framework complete, drop-in pending evidence) | Stop Loss, Trailing Stop — both already constructor-injected into `ExitEngine`; Trailing Stop additionally needs a new state field not yet designed |
| **Evidence Missing** | Weekly Future (evidence exists but fails its own consistency check — worse than simply absent); Strike Selection; TP Calculation (test formula known, competitor identity missing); Stop Loss (zero evidence); Trailing Stop (partial — one numeric constraint only) |
| **Blocked** | Strike Selection, TP Calculation, Qualification, Stop Loss, Trailing Stop, and Winner Detection's live (non-test) mode — all transitively or directly blocked on Weekly Future per the dependency chain in `WEEKLY_FUTURE_BLOCKER_REPORT.md` §4 |
| **Not Started** | No capability in this matrix has zero design work at all — even the fully blocked ones have Protocol stubs, architecture contracts, and workflow stages defined. There is no "not started" capability in the sense of a total blank; the closest is Qualification, whose status as even a distinct capability (vs. folded into TP Calculation) is itself unresolved |

**One item does not fit cleanly into any status above and is called out separately, matching `BUSINESS_ARCHITECTURE_REVIEW.md`'s own top finding:** whether Winner Detection depends on TP Calculation/Qualification at all is `UNRESOLVED – Awaiting Strategy Evidence` — not as a missing implementation, but as a missing *specification*. No amount of further architecture or traceability work resolves this; only new evidence (or an explicit decision from the domain owner that no such dependency exists) can.

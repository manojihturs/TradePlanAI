# Business Architecture Review

**Reviewer role:** Chief Software Architect, formal architecture review.
**Scope reviewed:** `BUSINESS_ARCHITECTURE.md`, `BUSINESS_SEQUENCE_DIAGRAM.md`, `BUSINESS_EVENT_FLOW.md`, `BUSINESS_DEPENDENCY_MAP.md`, `BUSINESS_STATE_MODEL.md` (drafted, uncommitted).
**Method:** each claim in the five documents was checked against the actual current source (`src/`) and against the four existing governance documents (`BUSINESS_RULE_INTEGRATION_GUIDE.md`, `ARCHITECTURE_REVIEW.md`, `PHASE1_CLOSEOUT.md`, `WEEKLY_FUTURE_BLOCKER_REPORT.md`) and `research/architecture/EVENT_CATALOG.md`, not recalled from memory of drafting them. This document's task is to find flaws, not fix them — no source file and none of the five reviewed documents were modified in producing this review.

---

## Findings

### 1. [High] Reviewed documents are silent on `ARCHITECTURE_REVIEW.md` Finding 6 (`StateMachine` integration), despite that finding explicitly naming Weekly Future as the trigger decision point

**Document:** `BUSINESS_ARCHITECTURE.md` and `BUSINESS_STATE_MODEL.md`
**Section:** §1 `WeeklyFutureCalculator` (both documents)

**Description:** `ARCHITECTURE_REVIEW.md` Finding 6 states that `core.state_machine.StateMachine` is fully built and tested but never integrated, and explicitly recommends: *"worth an explicit decision before Sprint 5, since Weekly Future is the first business engine expected to actually respond to session-lifecycle events."* Neither `BUSINESS_ARCHITECTURE.md`'s `WeeklyFutureCalculator` section nor `BUSINESS_STATE_MODEL.md`'s corresponding section mentions `StateMachine` at all — not to recommend wiring it in, not to defer the decision, not even to acknowledge the open question exists.

**Why it is a problem:** These five documents are framed as "Sprint 5 Preparation." `ARCHITECTURE_REVIEW.md` already flagged this specific decision as belonging to exactly this preparation step. Silently omitting it means a future implementer reading only the new documents (not re-reading `ARCHITECTURE_REVIEW.md`) would have no signal that this decision is still open, and might default to the current implicit-state pattern by omission rather than by an actual choice — which is precisely the ambiguity Finding 6 warned against.

**Suggested resolution:** Add a line to `BUSINESS_ARCHITECTURE.md` §1 State Requirements (and/or a dedicated note in `BUSINESS_STATE_MODEL.md`) stating that whether `WeeklyFutureCalculator` should transition `StateMachine` on calculation (vs. continuing the current implicit-state convention used by `TradeManager`/`PositionManager`) is an **open architectural decision carried over from `ARCHITECTURE_REVIEW.md` Finding 6**, not newly discovered here, and not resolved by this document set.

---

### 2. [High] `ReferenceLevelsGenerated` is framed as a low-cost additive change, but `ReferenceBuilder` has no event-bus dependency today — the event cannot be added without a larger change than the documents imply

**Document:** `BUSINESS_ARCHITECTURE.md` §3, `BUSINESS_SEQUENCE_DIAGRAM.md` (RB→TPE edge), `BUSINESS_EVENT_FLOW.md` (TPEngine row)

**Description:** `BUSINESS_ARCHITECTURE.md`'s consolidated section states adding the four proposed events is "additive implementation work... consistent with how `AmbiguousWinnerError`, `subscribe_all`/`unsubscribe_all`, and the Trailing/StopLoss events were each added." Verified against source: `src/reference_builder/` has **no `EventBusProtocol`/bus parameter anywhere in the package** (confirmed by grep — no `bus`, `_bus`, or `EventBusProtocol` reference exists in `reference_builder/`). Every other event-producing class in this codebase (`TradeManager`, `WinnerEngine`, `ExitEngine`, etc.) was built with bus injection from the start. `ReferenceBuilder` was not, because Sprint 4 had no reason to give it one.

**Why it is a problem:** For `ReferenceBuilder` specifically, adding `ReferenceLevelsGenerated` is not the same class of change as the two cited precedents (`subscribe_all` was an addition to an already bus-aware `EventBus`; the Stop Loss/Trailing Stop events were added to an already bus-aware `ExitEngine`). It requires giving `ReferenceBuilder` a new constructor dependency it doesn't have today — a real, if small, interface change to an already-complete, already-tested Sprint 4 package, which is a different risk profile than "add an event class." The documents' framing understates this.

**Suggested resolution:** Revise the consolidated note in `BUSINESS_ARCHITECTURE.md` to distinguish "adding a new event class" (genuinely trivial, per the cited precedents) from "wiring an existing package to publish it" (which for `ReferenceBuilder` specifically requires a new constructor parameter) — and flag that `ReferenceBuilder`'s currently-frozen, tested Sprint 4 interface would need to change, which `PHASE1_CLOSEOUT.md` §3 ("Architecture Stability — Stable... every addition has been purely additive") should probably also be read alongside, not contradicted by implication.

---

### 3. [Medium] `TPEngine` section doesn't cross-reference `ARCHITECTURE_REVIEW.md` Finding 5 (touch-detection duplication), despite that finding naming `TPEngine`/`QualificationEngine` directly

**Document:** `BUSINESS_ARCHITECTURE.md` §3 `TPEngine`, §4 `QualificationEngine`

**Description:** `ARCHITECTURE_REVIEW.md` Finding 5 states the "candle-touches-level" primitive is already duplicated between `WinnerEngine` and `ExitEngine`, and explicitly predicts: *"`TPEngine`/`QualificationEngine` (Sprint 7-8, per your own revised roadmap) will very likely need this exact same primitive a third time,"* recommending extraction *"before `tp_engine/`/`qualification_engine/` (Sprint 7-8) if this touch-based approach carries forward there."* Neither module's section in `BUSINESS_ARCHITECTURE.md` mentions this.

**Why it is a problem:** This is a dependency the existing review already identified by name for these exact two modules, with a concrete recommended action tied to their implementation timing. Omitting it from the modules' own architecture contracts means the recommendation is easy to lose track of by the time Sprint 7-8 actually arrives.

**Suggested resolution:** Add an Integration Points note to §3/§4 referencing `ARCHITECTURE_REVIEW.md` Finding 5, and noting that `core/touch.py`-style extraction (if the touch-based approach is confirmed to carry forward) should happen no later than these modules' implementation, per that finding's own recommendation.

---

### 4. [Low] Silent inheritance of a naming inconsistency already present in `EVENT_CATALOG.md`

**Document:** `BUSINESS_ARCHITECTURE.md`, `BUSINESS_SEQUENCE_DIAGRAM.md`, `BUSINESS_EVENT_FLOW.md` (all three, wherever `TPUpdated` appears)

**Description:** `research/architecture/EVENT_CATALOG.md`'s own summary table (its row 4) names the event `TPUpdating` while the rest of that same document's body (Section 2.4, the sequence diagram, the priority table) consistently calls it `TPUpdated`. The three reviewed documents use `TPUpdated` throughout, which matches the majority usage — but none of them flags that the source document they cite is itself internally inconsistent on this name.

**Why it is a problem:** Not a defect in the new documents' own logic, but a small provenance gap: a future reader tracing `TPUpdated` back to `EVENT_CATALOG.md` and landing on its summary table first will find `TPUpdating` instead, and may reasonably wonder whether the new documents are citing the wrong name.

**Suggested resolution:** A one-line footnote in `BUSINESS_EVENT_FLOW.md`'s table noting that `EVENT_CATALOG.md`'s own summary table spells this `TPUpdating` while its body uses `TPUpdated`, and that these documents follow the body's (majority) usage.

---

### 5. [Low] Dependency-map claim about interface imports is slightly broader than what was verified

**Document:** `BUSINESS_DEPENDENCY_MAP.md`, "Circular-dependency check" section

**Description:** The document states the six blocked modules' Protocol definitions "import only `core`/`models` types." Verified against `src/interfaces/*.py`: every file imports from `models.*`, `typing`, `uuid`, or `datetime` — **none of the six interface files imports anything from `core` at all.**

**Why it is a problem:** Minor overstatement, not an incorrect conclusion (the actual import set is a strict subset of the claimed one, so the "no cycle" conclusion still holds) — but a review document making a "verified against source" claim should match the source exactly, especially in a section whose whole purpose is precision about dependency direction.

**Suggested resolution:** Change "import only `core`/`models` types" to "import only `models` types (plus stdlib `typing`/`uuid`/`datetime`) — none import `core` directly today."

---

## Criteria checked with no issues found

- **Consistency with `WEEKLY_FUTURE_BLOCKER_REPORT.md`:** All five documents' treatment of `WeeklyFutureCalculator` as fully blocked, and every downstream-dependency claim in `BUSINESS_DEPENDENCY_MAP.md`, matches that report's Section 4 dependency chain exactly. No contradiction found.
- **Consistency with `PHASE1_CLOSEOUT.md`:** The "framework requires no changes for the four already-consumer-side modules" claim, repeated across all five documents, matches `PHASE1_CLOSEOUT.md` §2/§5 verbatim in substance. No contradiction found (Finding 2 above is a scope-precision issue about a *new* event on an *existing* package, not a contradiction of this claim).
- **Event flow correctness (bus mechanics):** Where events are described as flowing through the bus (`WeeklyFutureCalculatedEvent`, `StrikeSelectedEvent`, and the four proposed events), the publish/consume direction matches `EVENT_CATALOG.md`'s own stated sequence (`ReferenceLevelsGenerated` → `TPUpdated` → `QualificationChanged`) with no reordering.
- **Dependency correctness (module-to-module):** The `WeeklyFutureCalculator → StrikeSelector → {ReferenceBuilder, TPEngine} → QualificationEngine` chain matches `BUSINESS_RULE_INTEGRATION_GUIDE.md` Section 3's recommended integration sequence exactly, including the independent, any-time placement of `StopLossEngine`/`TrailingStopEngine`.
- **Hidden state assumptions (Stop Loss / Trailing Stop):** Both engines' sections correctly avoid assuming statelessness or a particular anchor mechanism, matching `BUSINESS_RULE_INTEGRATION_GUIDE.md` Section 4's own hedging on this exact point.
- **Assumptions presented as facts (Weekly Future `close` field / Ambiguity 6):** The citation to `WeeklyFuture_Specification_v1.md`'s "Ambiguity 6" in `BUSINESS_ARCHITECTURE.md` §1 was checked against that file directly and is accurate — both the ambiguity number and its content match.
- **`high >= low` non-enforcement:** Checked against `BUSINESS_RULE_INTEGRATION_GUIDE.md` Section 4 — the new documents' description of this deliberate non-invariant matches word-for-word in substance.
- **`ExitEngine` exit-check ordering:** The four-step order shown in `BUSINESS_SEQUENCE_DIAGRAM.md` (Target → Competitor → StopLoss → TrailingStop) matches `BUSINESS_RULE_INTEGRATION_GUIDE.md` Section 2.5/2.6 exactly.
- **Future extensibility of `TradePosition`:** The frozen-dataclass caveat in `BUSINESS_STATE_MODEL.md` §6 correctly identifies this as a real constraint rather than assuming a mutable field can simply be added.

---

## Summary table

| # | Finding | Severity |
|---|---|---|
| 1 | `StateMachine` integration decision (ARCHITECTURE_REVIEW Finding 6) not carried into new docs | High |
| 2 | `ReferenceLevelsGenerated` framed as low-cost; `ReferenceBuilder` has no bus dependency to add it to | High |
| 3 | Touch-detection duplication risk (ARCHITECTURE_REVIEW Finding 5) not cross-referenced for TPEngine/QualificationEngine | Medium |
| 4 | Silent inheritance of `EVENT_CATALOG.md`'s own `TPUpdated`/`TPUpdating` naming inconsistency | Low |
| 5 | Dependency-map import claim slightly broader than verified (says core+models, actual is models-only) | Low |

**0 Critical findings. 2 High findings — both are omissions of already-documented open questions from prior governance documents, not new architectural defects, and both have a low-cost suggested resolution (add a note, don't redesign).**

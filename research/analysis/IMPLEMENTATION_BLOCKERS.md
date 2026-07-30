# Implementation Blockers

Evidence-only synthesis. Every claim below cites either an actual
`trading_engine/` file (path + class/function) or a `research/analysis/`
or `docs/` file. This document reuses and consolidates
`RULE_DEPENDENCY_GRAPH.md`, `ENTITY_DEPENDENCY_GRAPH.md`,
`FOUNDATIONAL_KNOWLEDGE_MAP.md`, `EXTERNAL_EVIDENCE_BACKLOG.md`, and
`KNOWLEDGE_READINESS_DASHBOARD.md` against the actual state of the
`trading_engine/` codebase as read directly for this task. No claim
here increases any concept's recorded confidence/readiness beyond what
those source documents already establish.

---

## Task 1 — Calculator-by-calculator review

All five existing calculator files follow one identical pattern:
a `RuleReference`-carrying `AbstractCalculator` subclass whose
`calculate()` method unconditionally raises `NotImplementedError`,
citing its Rule ID in both a module-level "Traceability notes"
docstring and an inline `# TODO (<RULE-ID>)` comment. This is
confirmed by direct reading of all five files, not inferred.

### WeeklyFutureCalculator — does not exist as a file
- **Current status:** No file named `weekly_future_calculator.py` (or
  any equivalent) exists in `trading_engine/calculators/`. Directory
  listing confirms only `base.py`, `context.py`, `edge_calculator.py`,
  `exceptions.py`, `opponent_calculator.py`, `protocols.py`,
  `registry.py`, `result.py`, `reversal_calculator.py`,
  `strike_calculator.py`, `trend_calculator.py`. Weekly Future
  (ENT-010) is referenced only as `strike_calculator.py`'s upstream
  input concept, per `RULE_DEPENDENCY_GRAPH.md`'s STRIKE-001 "Depends
  On (deeper evidence)" entry — not as a calculator of its own.
- **Safe to implement:** Not applicable — nothing exists to implement
  yet. A placeholder *file/class* mirroring the other five would be
  Safe Now (see `SAFE_IMPLEMENTATION_SCOPE.md`), but the actual Weekly
  Future arithmetic is Blocked.
- **Reason:** No calculator was ever created for this concept in the
  codebase; `EXTERNAL_EVIDENCE_BACKLOG.md` row 1 treats ENT-010's
  resolution as unblocking `trading_engine/calculators/strike_calculator.py`
  specifically, not a Weekly-Future calculator of its own — the
  codebase's own architecture routes Weekly Future through
  StrikeCalculator rather than giving it a dedicated calculator.
- **Required evidence:** The Weekly Future High/Low arithmetic (a
  clean, self-consistent worked example plus a general sign-flip rule
  statement) — `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker"
  items 1-2; ranked #1 in `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 4.

### StrikeCalculator — `trading_engine/calculators/strike_calculator.py`
- **Current status:** `calculate()` (lines 53-57) unconditionally
  raises `NotImplementedError("TODO (STRIKE-001): Strike mathematics
  awaiting evidence.")`. This is the Milestone 4.3A placeholder design,
  confirmed correct per the task's own framing — not a bug.
- **Safe to implement:** Blocked (math). The class/registration
  scaffolding itself is already built and Safe (see Task 4 table).
- **Reason:** STRIKE-001 is PARTIALLY READY (`KNOWLEDGE_READINESS_DASHBOARD.md`
  row 2), but its evidenced dependency is Weekly Future's first-candle
  High/Low, whose own arithmetic is self-contradictory
  (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker" items 1-3, per
  `RULE_DEPENDENCY_GRAPH.md`'s STRIKE-001 "Blocked By" field).
- **Required evidence:** Weekly Future High/Low arithmetic —
  `EXTERNAL_EVIDENCE_BACKLOG.md` row 1: "Unblocks
  `trading_engine/calculators/strike_calculator.py`'s STRIKE-001 path
  from raising NotImplementedError for its upstream input... resolving
  this makes STRIKE-001 fully READY."

### TrendCalculator — `trading_engine/calculators/trend_calculator.py`
- **Current status:** `calculate()` (lines 61-65) unconditionally
  raises `NotImplementedError("TODO (TREND-001): Trend mathematics
  awaiting evidence.")`. Registers both `_TREND_001` and `_TREND_002`
  RuleReferences (lines 25-39) but implements neither.
- **Safe to implement:** Blocked (math).
- **Reason:** TREND-001's Mathematical Definition is Partially Known —
  no formula connecting a Strike to a TP Low value is evidenced
  (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 82-88, cited in
  `RULE_DEPENDENCY_GRAPH.md` TREND-001 "Blocked By"). TREND-002's
  trigger ("market structure changes") is separately Unknown
  (`docs/DOMAIN_MODEL.md` lines 93-95).
- **Required evidence:** TrendPoint (TP Low) calculation formula
  (ranked #4, `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 4 item 4) and,
  independently, the "market structure change" trigger definition
  (ranked #7, item 7) — `EXTERNAL_EVIDENCE_BACKLOG.md` rows 4 and the
  TREND-002 tie-row.

### OpponentCalculator — `trading_engine/calculators/opponent_calculator.py`
- **Current status:** `calculate()` (lines 71-75) unconditionally
  raises `NotImplementedError("TODO (OPPONENT-001): Opponent
  mathematics awaiting evidence.")`. Registers `_OPPONENT_001`,
  `_OPPONENT_002`, `_OPPONENT_003` (lines 25-47); the latter two carry
  `RuleStatus.AWAITING_EVIDENCE` / `ConfidenceLevel.UNKNOWN` /
  `evidence_count=0` directly in the code, matching the ledger.
- **Safe to implement:** Blocked (math), and the furthest from READY
  of the five calculators.
- **Reason:** OPPONENT-001's "defeat" condition is an explicit
  unresolved Open Question (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines
  344-350), and it further depends on OPPONENT-002/003, both Awaiting
  Evidence with Evidence Count 0 (`docs/RULE_INDEX.md` rows 35-36, per
  `RULE_DEPENDENCY_GRAPH.md` OPPONENT-001 "Blocked By").
- **Required evidence:** A mathematical statement of "defeating" plus
  Opponent High/Low computations, all three co-dependent
  (`EXTERNAL_EVIDENCE_BACKLOG.md` row 5; ranked #5 in
  `FOUNDATIONAL_KNOWLEDGE_MAP.md`). Separately, the Opponent-to-Strike
  relationship question (ranked #6) would need resolving for the
  identity logic even before the defeat math.

### ReversalCalculator — `trading_engine/calculators/reversal_calculator.py`
- **Current status:** `calculate()` (lines 54-58) unconditionally
  raises `NotImplementedError("TODO (REVERSAL-001): Reversal
  mathematics awaiting evidence.")`.
- **Safe to implement:** Blocked (math), but the single most
  self-contained blocker in the project once resolved.
- **Reason:** REVERSAL-001's Mathematical Definition is Unknown —
  "which specific premium behaviour constitutes identification is not
  established anywhere" (`docs/DOMAIN_MODEL.md` lines 168-171, per
  `RULE_DEPENDENCY_GRAPH.md` REVERSAL-001 "Blocked By").
- **Required evidence:** A stated rule connecting Premium (ENT-009)
  behaviour to REVERSAL_IDENTIFIED — no natural-language rule shape
  exists yet at all, unlike Weekly Future (`EXTERNAL_EVIDENCE_BACKLOG.md`
  row 3; ranked #3, `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 4 item 3).

### EdgeCalculator — `trading_engine/calculators/edge_calculator.py`
- **Current status:** `calculate()` (lines 55-59) unconditionally
  raises `NotImplementedError("TODO (TREND-003): Edge mathematics
  awaiting evidence.")`.
- **Safe to implement:** Blocked (math), and doubly blocked —
  quantifying its own threshold would still not make it READY.
- **Reason:** TREND-003's "well below" threshold is not quantified
  (`docs/TERMINOLOGY.md` lines 112-113), and TREND-003 additionally
  depends on both TREND-001 (Partially Known) and OPPONENT-001
  (Unknown, itself blocked by OPPONENT-002/003) per
  `docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 194.
- **Required evidence:** A quantified "well below" threshold, *plus*
  resolution of TREND-001 and OPPONENT-001 — quantifying the threshold
  alone does not unblock this calculator
  (`EXTERNAL_EVIDENCE_BACKLOG.md` "not separately ranked" row;
  `FOUNDATIONAL_KNOWLEDGE_MAP.md` "Blocker: 'Well below' threshold...").

---

## Task 2 — Rule ID review

| Rule ID | Infrastructure complete? | Business mathematics missing? | Fully blocked? |
|---|---|---|---|
| STRIKE-001 | Yes — `StrikeCalculator` class registered with `_STRIKE_001` RuleReference (`strike_calculator.py` lines 25-51); `Strike` domain model exists and is structurally validated (`trading_engine/domain/strike.py`) | Yes — Weekly Future High/Low arithmetic self-contradictory (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`) | No — PARTIALLY READY, closest to READY of the 8 (`KNOWLEDGE_READINESS_DASHBOARD.md` row 2) |
| TREND-001 | Yes — `TrendCalculator` registered with `_TREND_001` (`trend_calculator.py` lines 25-31); `TrendPoint` domain model exists (`trading_engine/domain/trend_point.py`) | Yes — no formula connecting Strike to TP Low value (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 82-88) | No — Partially Known, not fully blocked, but no path to READY without new evidence |
| TREND-002 | Partial — shares `TrendCalculator` with TREND-001 (`_TREND_002`, lines 33-39); no dedicated domain model for "Market Structure" (ENT-004) beyond being referenced as TREND-002's trigger (`docs/DOMAIN_MODEL.md` lines 86-100) | Yes — Mathematical Definition Unknown; trigger itself Unknown (`docs/DOMAIN_MODEL.md` lines 93-95) | No, but additionally gated on TREND-001 resolving too (`RULE_DEPENDENCY_GRAPH.md` TREND-002 "Depends On (ledger)") |
| TREND-003 | Yes — `EdgeCalculator` registered with `_TREND_003` (`edge_calculator.py` lines 26-32); no dedicated stored entity (Edge is a condition, not a domain object, per `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 194-213) | Yes — Mathematical Definition Unknown; "well below" unquantified (`docs/TERMINOLOGY.md` lines 112-113) | Effectively yes for now — depends on both TREND-001 and OPPONENT-001, neither resolved (`RULE_DEPENDENCY_GRAPH.md` TREND-003 "Blocked By") |
| OPPONENT-001 | Yes — `OpponentCalculator` registered with `_OPPONENT_001` (`opponent_calculator.py` lines 25-31); `Opponent` domain model exists with `high`/`low` reserved slots (`trading_engine/domain/opponent.py` lines 56-60) | Yes — "defeat" condition unresolved Open Question (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 344-350) | Effectively yes — also depends on OPPONENT-002/003 (Evidence Count 0) and, per the ledger, on TREND-001 |
| OPPONENT-002 | Partial — reserved `RuleReference` exists in code (`opponent_calculator.py` lines 33-39, `RuleStatus.AWAITING_EVIDENCE`); `Opponent.high` is a reserved `Decimal \| None` slot with no computation or invariant enforced (`trading_engine/domain/opponent.py` lines 58-60) | Yes — "no behaviour defined," Evidence Count 0 (`docs/RULE_INDEX.md` row 35) | Yes — Awaiting Evidence is the ledger's own lowest-readiness status; TR-001 did not define it (`docs/RULE_INDEX.md` lines 45-47) |
| OPPONENT-003 | Same as OPPONENT-002, symmetric (`opponent_calculator.py` lines 41-47; `Opponent.low`) | Yes — Evidence Count 0 (`docs/RULE_INDEX.md` row 36) | Yes — same reasoning as OPPONENT-002 |
| REVERSAL-001 | Yes — `ReversalCalculator` registered with `_REVERSAL_001` (`reversal_calculator.py` lines 26-32); `Premium` domain model exists (`trading_engine/domain/premium.py`) | Yes — "which specific premium behaviour constitutes identification is not established anywhere" (`docs/DOMAIN_MODEL.md` lines 168-171) | No — self-contained; the single rule that would become fully READY immediately once its one blocker resolves (`RULE_DEPENDENCY_GRAPH.md` REVERSAL-001 detail; `FOUNDATIONAL_KNOWLEDGE_MAP.md` item 3) |

All 8 Rule IDs share the same infrastructure pattern: a
`RuleReference` value object (`trading_engine/domain/rule_reference.py`)
instantiated with the ledger's own Status/Confidence/Evidence Count
values, embedded in a calculator class whose `calculate()` raises
`NotImplementedError`. No Rule ID has a working evaluation function
anywhere in `trading_engine/rules/` either — `AbstractRule.evaluate()`
(`trading_engine/rules/base.py` lines 88-96) is abstract with no
concrete subclass in the codebase at all (confirmed: no file under
`trading_engine/rules/` defines a concrete `Rule` implementation for
any of the 8 IDs — only the Calculator layer registers placeholder
RuleReferences).

---

## Task 3 — Entity review

| Entity | Stable / Needs refinement / Blocked by evidence | Domain file (if any) |
|---|---|---|
| ENT-001 Strike | Stable (domain model) — frozen dataclass with `strike_id`/`session_id`/`price`, validated `price > 0` invariant (`trading_engine/domain/strike.py` lines 22-54); selection *mechanism* itself Blocked by evidence | `trading_engine/domain/strike.py` |
| ENT-002 First Candle | Blocked by evidence — not produced by any rule, no dedicated domain file; time-window definition Unknown (`docs/DOMAIN_MODEL.md` lines 52-55) | None |
| ENT-003 TrendPoint (TP Low) | Stable (domain model) — frozen dataclass with `value`/`marked_at`, immutable-update pattern via `with_updated_value()` (`trading_engine/domain/trend_point.py` lines 24-75); value *formula* Blocked by evidence | `trading_engine/domain/trend_point.py` |
| ENT-004 Market Structure | Blocked by evidence — no domain file; referenced only as TREND-002's trigger concept (`docs/DOMAIN_MODEL.md` lines 86-100) | None |
| ENT-005 Opponent | Needs refinement — domain model exists and is structurally valid (`trading_engine/domain/opponent.py` lines 24-67) but `high`/`low` are `None`-defaulted reserved slots with "no cross-field invariant... enforced" by design (lines 30-35); relationship to "competitor" concept Unknown | `trading_engine/domain/opponent.py` |
| ENT-006 Opponent High | Blocked by evidence — reserved attribute slot on `Opponent.high` only, no computation (`trading_engine/domain/opponent.py` line 59) | `trading_engine/domain/opponent.py` (attribute only) |
| ENT-007 Opponent Low | Blocked by evidence — symmetric to ENT-006, `Opponent.low` (line 60) | `trading_engine/domain/opponent.py` (attribute only) |
| ENT-008 Reversal | Blocked by evidence — no dedicated domain file exists (Reversal is not itself a modeled dataclass; only `Premium`, its input, is modeled); identification method Unknown (`docs/DOMAIN_MODEL.md` lines 168-171) | None |
| ENT-009 Premium | Stable (domain model) — frozen dataclass, `value > 0` invariant (`trading_engine/domain/premium.py` lines 23-48); which contract (CE/PE/both) it represents is Unknown | `trading_engine/domain/premium.py` |
| ENT-010 Weekly Future | Blocked by evidence, most evidence-advanced Candidate — no domain file exists at all in `trading_engine/domain/`; inputs and rule shape are stated in natural language but arithmetic is self-contradictory (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`); PARTIALLY READY per `ENTITY_DEPENDENCY_GRAPH.md` discrepancy note | None |
| ENT-011 MidPoint | Blocked by evidence — no domain file; reserved, inactive; Top/Bottom Strike not themselves confirmed Domain objects (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 248-253) | None |
| ENT-012 TriggerPoint | Blocked by evidence — no domain file; one worked example only (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 255-258) | None |
| ENT-013 SellersPerspective | Blocked by evidence — no domain file; named alternative lens, not integrated (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 260-265) | None |
| ENT-014 OpeningRange | Blocked by evidence — no domain file; explicitly distinct from ENT-002/ENT-010 (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 267-272) | None |
| UNK-001 IVL Level | Blocked by evidence — no domain file; used but never defined anywhere in TR-001 (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 278-286) | None |

Supporting infrastructure entities not in ENT-001..014/UNK-001 but
present in `trading_engine/domain/` and structurally stable: `MarketContext`
(`market_context.py`), `SessionState`/`SessionStateType`
(`session_state.py`), `Decision`/`RuleEvaluationResult` (`decision.py`),
`DomainEvent` (`domain_event.py`, deliberately generic — "no concrete
event subtype is defined" per its own docstring, lines 31-34),
`RuleReference` (`rule_reference.py`), `EvidenceReference`
(`evidence_reference.py`). None of these carry their own Rule ID/Entity
ID — they are traceability/orchestration scaffolding, evidence-agnostic
by design.

---

## Task 4 — Consolidated Concept Table

| Concept | Current Readiness | Blocking Evidence | Repository References | Evidence Needed | Downstream Impact |
|---|---|---|---|---|---|
| Weekly Future (ENT-010) | PARTIALLY READY (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` verdict) | Self-contradictory arithmetic: self-corrected subtraction, unexplained "18"→"268" jump, two conflicting Low values, Low > High for same candle | No domain file; no calculator file; consumed only by `trading_engine/calculators/strike_calculator.py` conceptually | Clean worked example + general sign-flip rule statement, or the named "Complete Calculation Video" (`EXTERNAL_EVIDENCE_BACKLOG.md` rows 1-2) | Unblocks STRIKE-001 fully; no other rule/entity affected (`FOUNDATIONAL_KNOWLEDGE_MAP.md` "Blocker: Weekly Future") |
| STRIKE-001 / ENT-001 Strike | PARTIALLY READY (`KNOWLEDGE_READINESS_DASHBOARD.md` row 2) | Depends on Weekly Future's unresolved arithmetic | `trading_engine/calculators/strike_calculator.py` lines 53-57 (`NotImplementedError`); `trading_engine/domain/strike.py` (stable dataclass) | Same as Weekly Future row above | TREND-001, TREND-003, OPPONENT-001 all consume Strike (`docs/DOMAIN_MODEL.md` line 40) but are separately blocked regardless |
| TREND-001 / ENT-003 TrendPoint | NOT READY, Mathematical Definition Partially Known (`KNOWLEDGE_READINESS_DASHBOARD.md` row 3) | No formula connecting Strike to TP Low value | `trading_engine/calculators/trend_calculator.py` lines 61-65; `trading_engine/domain/trend_point.py` (stable dataclass, `with_updated_value()` mechanic only) | TrendPoint calculation formula (ranked #4, `FOUNDATIONAL_KNOWLEDGE_MAP.md`) | Largest fan-out: TREND-002, TREND-003, OPPONENT-001 all list it as a dependency, but resolving it alone does not make any of them READY |
| TREND-002 / ENT-004 Market Structure | NOT READY, Mathematical Definition Unknown (row 4) | Trigger ("market structure change") itself Unknown | `trading_engine/calculators/trend_calculator.py` (shares file with TREND-001, `_TREND_002` lines 33-39); no ENT-004 domain file | Definition of "market structure" and "change" (ranked #7, lowest — `FOUNDATIONAL_KNOWLEDGE_MAP.md` item 7) | Unblocks only TREND-002 itself; no other rule references it |
| TREND-003 / Edge | NOT READY, Mathematical Definition Unknown (row 5) | "Well below" unquantified; also transitively blocked by TREND-001 and OPPONENT-001 | `trading_engine/calculators/edge_calculator.py` lines 55-59; Edge is a condition, not a stored entity (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 194-213) | Quantified threshold, plus TREND-001 and OPPONENT-001 resolved | Leaf-ward; no rule lists TREND-003 as a dependency |
| OPPONENT-001 / ENT-005 Opponent | NOT READY, Mathematical Definition Unknown (row 6) | "Defeat" condition an unresolved Open Question; also depends on OPPONENT-002/003 | `trading_engine/calculators/opponent_calculator.py` lines 71-75; `trading_engine/domain/opponent.py` (stable shell, `high`/`low` unenforced) | "Defeat" math + Opponent High/Low, co-dependent (ranked #5) | Removes one of TREND-003's two blockers if resolved; no effect on STRIKE-001/TREND-002/REVERSAL-001 |
| OPPONENT-002 / ENT-006 Opponent High | NOT READY, Awaiting Evidence, Evidence Count 0 (row 7) | "No behaviour defined," TR-001 silent | `trading_engine/calculators/opponent_calculator.py` lines 33-39 (`_OPPONENT_002`); `trading_engine/domain/opponent.py` line 59 (`high` slot) | Net-new evidence acquisition (`EXTERNAL_EVIDENCE_BACKLOG.md` row 5) | Blocks OPPONENT-001 |
| OPPONENT-003 / ENT-007 Opponent Low | NOT READY, Awaiting Evidence, Evidence Count 0 (row 8) | Symmetric to OPPONENT-002 | `trading_engine/calculators/opponent_calculator.py` lines 41-47; `trading_engine/domain/opponent.py` line 60 (`low` slot) | Same as OPPONENT-002 | Blocks OPPONENT-001 |
| Opponent relationship to Strike (ENT-005 sub-question) | Unknown, definitional only | Not assumed equal to "competitor" concept elsewhere in repo (`docs/TERMINOLOGY.md` lines 78-84) | `trading_engine/domain/opponent.py` module docstring lines 4-12 explicitly declines the equivalence | A single clarifying statement (ranked #6, cheapest fully-Unknown item) | Clarifies OPPONENT-001/TREND-003 but does not itself supply a formula |
| REVERSAL-001 / ENT-008 Reversal / ENT-009 Premium | NOT READY, Mathematical Definition Unknown (row 9) | Which premium behaviour identifies a reversal is unestablished anywhere | `trading_engine/calculators/reversal_calculator.py` lines 54-58; `trading_engine/domain/premium.py` (stable dataclass); no ENT-008 domain file | A stated rule connecting Premium to REVERSAL_IDENTIFIED (ranked #3, fully self-contained) | Zero transitive blockers once resolved — most isolated payoff in the project |
| Weekly Future calculator (no file) | Not started | N/A — infrastructure gap, not an evidence gap | No file exists; contrast with the 5 existing placeholder calculators | None (this is Safe Now infrastructure work, see `SAFE_IMPLEMENTATION_SCOPE.md`) | None on evidence; would give Weekly Future the same registered/discoverable extension-point status the other 5 concepts already have |

---

## Cross-references

This document's tables were built by cross-reading
`RULE_DEPENDENCY_GRAPH.md`, `ENTITY_DEPENDENCY_GRAPH.md`,
`FOUNDATIONAL_KNOWLEDGE_MAP.md`, `EXTERNAL_EVIDENCE_BACKLOG.md`, and
`KNOWLEDGE_READINESS_DASHBOARD.md` against direct reads of every file
in `trading_engine/domain/`, `trading_engine/rules/`,
`trading_engine/engine/`, and `trading_engine/calculators/`, plus a
directory listing (and targeted grep) of `trading_engine/tests/`. No
tool was run against the code (no pytest/mypy/ruff); all statements
about behavior are drawn from reading source directly.

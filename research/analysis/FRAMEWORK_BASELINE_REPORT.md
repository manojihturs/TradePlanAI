# Framework Baseline Report

**Milestone:** 6.5 (Architecture Freeze) — final milestone of Phase 6 ("Infrastructure Only")
**Scope:** `trading_engine/domain/`, `trading_engine/rules/`, `trading_engine/engine/`, `trading_engine/calculators/`, `trading_engine/diagnostics/`, `trading_engine/tests/`
**Method:** Every source file in the five subsystem packages (43 files) was read in full against the actual current repository state, cross-checked against prior Milestone 6.0A–6.4 analysis docs, and re-verified rather than assumed from those docs. Test packages were spot-checked (2–3 files per subpackage plus one full-file sample each). Quality gate (543 tests passing, 100% coverage, mypy/ruff/black clean) is reported as supplied by the orchestrating process and was not re-run here.

---

## 1. Completed Components

| Subsystem | Files | Lines (wc -l) | Responsibility |
|---|---:|---:|---|
| `domain/` | 11 (+`__init__.py`) | 913 | Immutable value objects/entities: `Strike`, `Opponent`, `Premium`, `TrendPoint`, `MarketContext`, `MarketSession`, `SessionState`, `Decision`, `DomainEvent`, `EvidenceReference`, `RuleReference` |
| `rules/` | 8 (+`__init__.py`) | 850 | Rule contract (`protocols.py`, `base.py`), execution context, outcome/exception types, static dependency table, `RuleRegistry` with topological ordering |
| `engine/` | 6 (+`__init__.py`) | 704 | `StrategyEngine`, `ExecutionPipeline`, `EngineConfiguration`, `ExecutionReport`/`ExecutionSummary`, engine-level exceptions |
| `calculators/` | 12 (+`__init__.py`) | 889 | Mathematical-calculation contract mirroring `rules/`: 6 concrete placeholder calculators (Strike, Trend, Opponent, Reversal, Edge, Weekly Future), `CalculatorRegistry`, `CalculationResult`/`CalculationContext` |
| `diagnostics/` | 3 (+`__init__.py`) | 427 | Structured execution-event types (`events.py`), `DiagnosticsSink` protocol with 3 implementations (`sink.py`) |
| **Total (production code)** | **41 files (+5 `__init__.py`)** | **3,783** | |
| `tests/` | 5 subpackages, ~35 files | not counted per instructions | pytest suite, 543 tests, 100% coverage (per orchestrating process) |

Six calculators exist today: `StrikeCalculator`, `TrendCalculator`, `OpponentCalculator`, `ReversalCalculator`, `EdgeCalculator`, and `WeeklyFutureCalculator` (added Milestone 6.1). All six were read in full for this milestone and confirmed present, registered-capable, and structurally identical in shape.

## 2. Architectural Guarantees (each verified directly against code)

1. **Every calculator's `calculate()` unconditionally raises `NotImplementedError`, with no computation before the raise.** Verified by reading all 6 concrete `calculate()` bodies (`edge_calculator.py:55-59`, `opponent_calculator.py:71-75`, `reversal_calculator.py:54-58`, `strike_calculator.py:53-57`, `trend_calculator.py:61-65`, `weekly_future_calculator.py:82-93`) plus the abstract base (`calculators/base.py:81-88`, `...` body). Each raise is preceded only by a `# TODO (<RULE-ID>)` explanatory comment, never by arithmetic.
2. **No hidden business mathematics or inferred thresholds exist anywhere in production code.** Verified by reading every arithmetic/comparison use on a domain numeric value across `domain/`, `engine/`, `rules/`, `calculators/`, `diagnostics/`. Every hit found (positivity/non-negativity guards on `Premium.value`, `Strike.price`, `TrendPoint.value`, `RuleReference.evidence_count`; count/length comparisons in `execution_pipeline.py`, `execution_summary.py`; timestamp-duration subtraction in `execution_report.py`; in-degree bookkeeping in the registry's topological sort) is a structural/telemetry check, not a trading calculation. No two trading-domain values (price, strike, premium, trend value, opponent high/low) are combined arithmetically anywhere. `Opponent.high`/`Opponent.low` are stored fields that are never read or compared in production code — reserved slots only.
3. **No trading decisions are produced anywhere.** `RuleOutcome` is used in production code only once, inside `ExecutionSummary`'s `Counter.get(RuleOutcome.X, 0)` aggregation (pure counting). `CalculationStatus` has zero production usages (test-only). No code branches on either enum to synthesize a buy/sell/entry/exit decision.
4. **A full, working dependency-ordering engine exists**, independent of any rule's mathematics: `rules/registry.py`'s `execution_order()` implements Kahn's-algorithm topological sort with deterministic tie-breaking by registration order, cycle detection (`CircularDependencyError` naming every stuck rule), and dependency-well-formedness/existence validation (`UnresolvedDependencyError` for both malformed IDs and missing registrations), each instrumented with diagnostics events. `rules/dependencies.py` is a static table transcribed from `docs/RULE_INDEX.md`'s "Depends On" column for the 8 confirmed Rule IDs — it deliberately excludes the evidenced-but-undocumented Weekly Future → STRIKE-001 edge because the ledger itself still reads "none yet" for STRIKE-001.
5. **Diagnostics package (`trading_engine/diagnostics/`) has no dependency on `rules/`, `engine/`, or `calculators/`** — it exports only event dataclasses and a sink protocol/implementations; the dependency direction runs the other way (`engine/`, `rules/` import diagnostics, not vice versa). Confirmed by reading `diagnostics/__init__.py`, `events.py`, `sink.py`, `exceptions.py` in full — none import from the other four packages.
6. **Two independent, redundant enforcement points gate diagnostics emission** (`EngineConfiguration.logging_enabled`/`diagnostics_sink`): both `ExecutionPipeline.run()` and `StrategyEngine._resolve_diagnostics_sink()` branch on it, and a `False` default routes everything to `NullDiagnosticsSink`. Confirmed correct by reading the actual branches (`execution_pipeline.py:82-90`, `strategy_engine.py:126-145`, `rules/registry.py:59-67,161-164`).
7. **Test architecture is uniform and exhaustive-per-invariant, not spot-check smoke coverage.** One test file per source module, `conftest.py`-supplied fixtures and test doubles (`FakeRule`, `BuggyRule`, `FrameworkExceptionRule`, `NonConformingRule`) per subpackage, tests grouped into `class Test<Concern>` blocks (construction, validation, equality, immutability, hashability, copy-update, serialization, edge cases). `test_weekly_future_calculator.py` includes an explicit structural guard test, `test_calculate_performs_no_business_mathematics`, asserting the calculator must raise rather than silently compute — this "assert no math happened" pattern recurs deliberately as an architecture-freeze safeguard across calculator tests.

## 3. TODO Inventory and Classification

24 `TODO` occurrences were found across `trading_engine/`. Full list with file:line, exact text, and classification (SAFE / BLOCKED / DEFERRED):

| # | File:line | Text (summarized, full quotes in audit trail) | Classification | Justification |
|---|---|---|---|---|
| 1 | `calculators/edge_calculator.py:56,59` | TREND-003 edge mathematics awaiting evidence | **BLOCKED** | Needs a quantified "well below the strike" threshold — no such threshold is evidenced |
| 2 | `calculators/opponent_calculator.py:72,75` | OPPONENT-001 opponent mathematics awaiting evidence | **BLOCKED** | "Defeat" definition and Opponent High/Low formulas unevidenced (evidence_count 0 for both dependents) |
| 3 | `calculators/reversal_calculator.py:9,55,58` | REVERSAL-001 reversal mathematics awaiting evidence | **BLOCKED** | No natural-language rule shape evidenced at all yet |
| 4 | `calculators/strike_calculator.py:54,57` | STRIKE-001 strike mathematics awaiting evidence | **BLOCKED** | Depends on Weekly Future arithmetic, itself internally contradictory in source transcript |
| 5 | `calculators/trend_calculator.py:62,65` | TREND-001 trend mathematics awaiting evidence | **BLOCKED** | TP Low formula "Partially Known", market-structure-change trigger Unknown |
| 6 | `calculators/weekly_future_calculator.py:83,93` | STRIKE-001 (Weekly Future) mathematics awaiting evidence | **BLOCKED** | Most concretely documented blocker: numeric self-contradictions in transcript (91→81→82; "268" vs "26168"; Low exceeding High), and the referenced external calculation video is absent from the repository |
| 7 | `domain/decision.py:67` | No rule has an implemented evaluation function yet | **SAFE** (informational) | States a fact about current state; not an action item — closes automatically once any rule ships |
| 8 | `domain/decision.py:105` | No synthesis/combination logic across multiple RuleEvaluationResults evidenced | **BLOCKED** | Cross-rule combination (e.g. "IF TREND-003 holds AND REVERSAL-001 fires") is trading-strategy logic; unevidenced |
| 9 | `domain/domain_event.py:58` | SM-004 "Opponent Defeated" is a hypothesis only | **BLOCKED** | Explicitly flagged as unconfirmed in `docs/STATE_MACHINE.md`; needs evidence to promote |
| 10 | `domain/market_session.py:48` | Session start/end triggers and reset rules unevidenced | **BLOCKED** | Session lifecycle is trading-domain state-machine behavior |
| 11 | `domain/opponent.py:69` | OPPONENT-001 "defeat" mathematics Unknown | **BLOCKED** | Same evidence gap as calculator TODO #2 |
| 12 | `domain/opponent.py:72` | OPPONENT-002 "Opponent High" zero recorded behaviour | **BLOCKED** | Evidence Count 0, Awaiting Evidence |
| 13 | `domain/opponent.py:74` | OPPONENT-003 "Opponent Low" zero recorded behaviour | **BLOCKED** | Symmetric to #12 |
| 14 | `domain/premium.py:50` | REVERSAL-001 premium behaviour identifying reversal Unknown | **BLOCKED** | Same gap as calculator TODO #3 |
| 15 | `domain/session_state.py:97` | Entry/exit transitions for 4 of 5 SessionStateType values Unknown | **BLOCKED** | State-machine transition rules, insufficient evidence per `docs/STATE_MACHINE.md` |
| 16 | `domain/strike.py:56` | STRIKE-001 First-Candle→Strike calculation unevidenced | **BLOCKED** | Same gap as calculator TODO #4 |
| 17 | `domain/trend_point.py:77` | TREND-001 initial-value formula "Partially Known" | **BLOCKED** | Not implemented pending fuller evidence |
| 18 | `domain/trend_point.py:79` | TREND-002 "market structure change" trigger Unknown | **BLOCKED** | Trigger-detection logic unevidenced |
| 19 | `domain/__init__.py:14` | General policy statement describing the TODO convention | **SAFE** (documentation-pattern note) | Not itself an actionable item |
| 20 | `engine/engine_configuration.py:14` | Module docstring cross-references a `logging_enabled` TODO in `execution_pipeline.py` | **SAFE, but stale** | `logging_enabled` was fully wired in Milestone 6.4; `execution_pipeline.py` contains no such TODO anymore. This is a documentation-lag defect in a comment, not a code defect — flagged here for visibility, not corrected (see Constraint: no file changes except the two report files) |
| 21 | `engine/execution_report.py:76` | Whether/how ExecutionReport feeds a future Decision Object is unspecified | **DEFERRED** | Architectural wiring question the architecture doc itself leaves silent; connecting these layers is premature relative to `RULE_ENGINE_ARCHITECTURE.md` and to Decision Objects/rule mathematics arriving together in later milestones |
| 22 | `engine/strategy_engine.py:147` | "Resulting Session State updates" (pipeline step 5) unimplemented | **BLOCKED** | No rule defines what a Session State update looks like; trading-state-machine logic |
| 23 | `rules/context.py:71` | Whether a rule may mutate Session State directly vs. return an update is unspecified | **DEFERRED** | A pure software-architecture choice, but tangled with the still-BLOCKED session-state-update question (#22); resolving it standalone would design plumbing for updates that don't exist yet |
| 24 | `rules/outcome.py:109` | No rule has an implemented evaluation function yet | **SAFE** (informational) | Same nature as #7 — closes automatically once any rule ships |

**Totals: 17 BLOCKED, 5 SAFE (informational/no action needed), 2 DEFERRED.** No TODO in the reviewed packages represents ready-to-implement, evidence-independent infrastructure work sitting undone — the closest historical example (the Weekly Future calculator file itself) was already built in Milestone 6.1. This confirms the freeze premise: everything that could be built without new trading evidence has been built; everything left is either blocked on evidence or an architecture question that is itself downstream of that evidence.

## 4. Independence from Business Mathematics (Task 3 findings)

Explicitly verified, not assumed:

- **Hidden calculations:** none found. Every arithmetic/comparison operator applied to a domain numeric value was traced and is structural (positivity/non-negativity validation, length/count comparisons, timestamp-duration subtraction for telemetry, topological-sort in-degree bookkeeping). No two trading values are combined.
- **Inferred thresholds:** none found. No magic number represents a price/point/premium threshold anywhere in production code.
- **Guessed formulas:** none found. All 6 calculators' `calculate()` methods raise unconditionally with no computation preceding the raise; the abstract base's `calculate()` is `...` only.
- **Trading decisions:** none found. `RuleOutcome` is only ever counted (`ExecutionSummary`), never branched on for a decision. `CalculationStatus` has zero production usages.

No questionable code was found during this check; the above is a full account of what was inspected, not a shortened summary.

## 5. Remaining Extension Points

From `EXECUTION_LOGGING_REPORT.md`'s "Extension points" section (still open, none implemented as of current code — confirmed `diagnostics/sink.py` contains exactly the 3 original sink classes):

1. A bounded/rotating in-memory sink.
2. A `CompositeDiagnosticsSink` fanning `emit()` out to multiple sinks.
3. A `ReplayDiagnosticsSink` writing events to durable storage — the natural next step once `IMPLEMENTATION_ROADMAP.md`'s replay/backtest milestones begin.
4. Structured (non-`repr()`-based) log formatting, e.g. JSON lines.

Additional extension points identified in this milestone's review:
5. `rules/dependencies.py` has no automated cross-check against `docs/RULE_INDEX.md`'s own ledger — silent drift risk if the two are edited independently.
6. `Rule` has no `depends_on()` protocol method of its own; only the registry's external static table knows a rule's dependencies.
7. Per `docs/architecture/IMPLEMENTATION_ROADMAP.md`, Milestone 4.5 (Replay Engine) and 4.6 (Unit Tests) are explicitly sequenceable now without new evidence — the roadmap states the Replay Engine "does not require real rule logic to be meaningful for backtesting yet." These are DEFERRED-not-BLOCKED engineering milestones, distinct from the trading-mathematics gap, and would be legitimate SAFE engineering work for a future milestone if the team chooses to pursue infrastructure depth before evidence arrives — though per this report's Task 5 recommendation below, evidence acquisition remains the higher-priority path.

## 6. Known Intentional Limitations

- **STRIKE-001's ledger-vs-deeper-evidence discrepancy** (documented in Milestone 6.3's dependency work): `docs/RULE_INDEX.md`'s "Depends On" column reads "none yet" for STRIKE-001, while `research/analysis/RULE_DEPENDENCY_GRAPH.md` and `REPOSITORY_CHANGE_PROPOSAL.md` establish that strike selection depends on a Weekly Future first-candle High/Low. `rules/dependencies.py` deliberately follows the ledger (not the deeper analysis) to avoid the registry silently encoding an undocumented edge — this is a known, intentional conservatism, not an oversight.
- **The missing "Weekly Future Calculation" / "Complete Calculation Video":** the source transcript twice refers viewers to a separate video not present anywhere in this repository (reconfirmed by `NEW_EVIDENCE_REPORT.md`, Milestone 6.0, which found the user-supplied docx to be a duplicate of already-held evidence, not this missing video).
- **The single-source evidence problem:** essentially all rule mathematics in this codebase trace back to one transcript source per rule area, with internally inconsistent worked examples (e.g. Weekly Future's self-corrected subtraction and contradictory Low values) and no independent corroborating source yet acquired.
- **`engine_configuration.py`'s stale module-docstring cross-reference** to a `logging_enabled` TODO that Milestone 6.4 already resolved (see TODO #20 above) — a minor documentation-lag defect, noted here rather than silently corrected, per this milestone's no-other-file-changes constraint.
- **Four `EXECUTION_LOGGING_REPORT.md` extension points remain unbuilt** (bounded sink, composite sink, replay sink, structured logging) — all explicitly deferred pending the Replay Engine milestone.

## 7. Recommended Starting Point for Phase 7

**This report does not recommend implementing anything — it recommends where Phase 7 should begin.**

Every finding in Tasks 1–4 points the same direction: the engineering framework is complete and internally consistent (domain models, rule framework, calculator framework, registry with full topological ordering and cycle detection, strategy engine, execution pipeline, diagnostics — all verified against current code, all frozen-ready per the checklist below), while every one of the 6 calculators and the majority of domain-layer TODOs remain BLOCKED on the same root cause: **unresolved or contradictory trading-mathematics evidence**, not missing engineering.

Per `research/analysis/KNOWLEDGE_READINESS_DASHBOARD.md` and `research/analysis/EXTERNAL_EVIDENCE_BACKLOG.md`, the single highest-priority unresolved evidence item is the **Weekly Future High/Low arithmetic (ENT-010)**, which blocks STRIKE-001 — itself the most-referenced dependency in the rule graph (`TREND-003` and `OPPONENT-001` both depend on `TREND-001`; STRIKE-001 is the rule every other confirmed rule ultimately supports the entry/exit decision around). The backlog documents the specific, concrete defect: a self-corrected subtraction (91→81→82), an unexplained jump from "difference=18" to "answer=268," two conflicting Low values (≈26268 vs 26168) for the same candle, and a Low that numerically exceeds the High for that candle — plus the source speaker's own reference to an external "Complete Calculation Video for Weekly Future" that has never been located in this repository (reconfirmed as recently as Milestone 6.0's evidence-ingestion attempt, which turned out to be a duplicate rather than new evidence).

**Recommendation: Phase 7 should open with a dedicated evidence-acquisition effort targeting the Weekly Future High/Low calculation** — specifically, either (a) locating and ingesting the referenced "Complete Calculation Video," or (b) sourcing one clean, internally-consistent worked example of the Call/Put first-candle High/Low → Weekly Future High/Low arithmetic, together with a general (non-numeric-example-specific) statement of the combination rule, including its sign-flip behavior. This is not an engineering task and should not begin with code changes to `WeeklyFutureCalculator` or `StrikeCalculator` — those already exist, structurally correct, and are simply waiting for a formula to fill their `calculate()` bodies once evidence resolves the contradiction. This continues the pattern already established across Milestones 5.3 (identifying the video as top priority) and 6.0 (an attempted ingestion that turned out to be a duplicate, not new evidence) — the bottleneck has consistently been evidence, not architecture, and this milestone's full review confirms that remains true with no exceptions found.

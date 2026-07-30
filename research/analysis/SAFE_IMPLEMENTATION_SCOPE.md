# Safe Implementation Scope

Evidence-only synthesis, read-only against `trading_engine/` (no
tests/linters run). Three sections: SAFE NOW, PARTIALLY SAFE, BLOCKED.
"Safe" here means: no business mathematics, not evidence-gated — the
work is either engineering scaffolding (types, validation, wiring) or
would remain so if extended along its existing pattern.

---

## SAFE NOW

Work involving no business mathematics and not evidence-gated. For
each item, whether it ALREADY EXISTS (cited) or is a genuinely open
next item.

### Already exists

- **Domain value objects with structural validation** — `Strike`
  (`trading_engine/domain/strike.py`, `price > 0` invariant),
  `TrendPoint` (`trading_engine/domain/trend_point.py`, `value >= 0`,
  immutable-update via `with_updated_value()`), `Opponent`
  (`trading_engine/domain/opponent.py`, non-`None` ID invariants only),
  `Premium` (`trading_engine/domain/premium.py`, `value > 0`),
  `MarketContext` (`trading_engine/domain/market_context.py`),
  `SessionState`/`SessionStateType` (`trading_engine/domain/session_state.py`),
  `Decision`/`RuleEvaluationResult` (`trading_engine/domain/decision.py`),
  `DomainEvent` (`trading_engine/domain/domain_event.py`). All raise a
  shared `DomainValidationError` on invalid construction — this is
  pure data-shape validation, no trading math.
- **Rule/Evidence traceability value objects** — `RuleReference` and
  its `RuleCategory`/`RuleStatus`/`ConfidenceLevel` enums
  (`trading_engine/domain/rule_reference.py`), `EvidenceReference` and
  `EvidenceLevel` (`trading_engine/domain/evidence_reference.py`).
  Rule ID format validated by regex (`_RULE_ID_PATTERN`, line 19)
  against the `docs/RULE_INDEX.md` convention — a documentation-sync
  check, not a calculation.
- **Rule Framework interfaces and registry** — `Rule` protocol
  (`trading_engine/rules/protocols.py`), `AbstractRule` base
  (`trading_engine/rules/base.py`), `RuleRegistry` with duplicate-ID
  rejection and category lookup (`trading_engine/rules/registry.py`),
  `RuleExecutionContext` (`trading_engine/rules/context.py`),
  `RuleOutcome`/`RuleExecutionResult` (`trading_engine/rules/outcome.py`),
  and the framework's own exception hierarchy
  (`trading_engine/rules/exceptions.py`). None of these evaluate any
  rule's actual mathematics.
- **Calculator Framework interfaces and registry** — mirrors the Rule
  Framework exactly at the mathematical layer: `Calculator` protocol
  (`trading_engine/calculators/protocols.py`), `AbstractCalculator`
  base (`trading_engine/calculators/base.py`), `CalculatorRegistry`
  (`trading_engine/calculators/registry.py`, explicitly "No execution
  ordering" per its own docstring), `CalculationContext`
  (`trading_engine/calculators/context.py`), `CalculationResult`/
  `CalculationStatus` (`trading_engine/calculators/result.py`,
  including the `NOT_IMPLEMENTED` status value used by every current
  placeholder), and `trading_engine/calculators/exceptions.py`.
- **The five placeholder calculators themselves** (as registered,
  discoverable extension points, not as math) — `StrikeCalculator`,
  `TrendCalculator`, `OpponentCalculator`, `ReversalCalculator`,
  `EdgeCalculator` (all in `trading_engine/calculators/`). Each
  correctly registers its RuleReference(s) and raises
  `NotImplementedError` from `calculate()` — this registration
  machinery is itself the safe, already-built precedent.
- **Engine orchestration** — `StrategyEngine`
  (`trading_engine/engine/strategy_engine.py`), `ExecutionPipeline`
  (`trading_engine/engine/execution_pipeline.py`), `ExecutionReport`
  (`trading_engine/engine/execution_report.py`), `ExecutionSummary`
  (`trading_engine/engine/execution_summary.py`, pure `Counter`-based
  aggregation over already-produced `RuleOutcome` values),
  `EngineConfiguration` (`trading_engine/engine/engine_configuration.py`,
  validates `fail_fast`/`continue_on_error` mutual exclusivity and a
  positive `maximum_rule_count`), and the engine's own exception
  hierarchy (`trading_engine/engine/exceptions.py`). `StrategyEngine`'s
  own docstring states the "Architecture Rule": "StrategyEngine may
  orchestrate. Rules may evaluate. Only future calculator modules may
  perform mathematics. This class never mixes those responsibilities"
  (lines 15-19) — confirmed true by reading `execution_pipeline.py`,
  which contains no `if strike`/`if trend`/`if reversal` branch
  anywhere.
- **Test coverage per subpackage** — `trading_engine/tests/domain/`
  (11 test files covering `decision`, `domain_event`,
  `evidence_reference`, `market_context`, `market_session`, `opponent`,
  `premium`, `rule_reference`, `session_state`, `strike`,
  `trend_point`), `trading_engine/tests/rules/` (`test_categories.py`,
  `test_outcome.py`, `test_protocols.py`, `test_registry.py`),
  `trading_engine/tests/engine/` (`test_configuration.py`,
  `test_execution_pipeline.py`, `test_execution_report.py`,
  `test_strategy_engine.py`), `trading_engine/tests/calculators/`
  (`test_context.py`, `test_protocols.py`, `test_registry.py`,
  `test_result.py`). This is genuine coverage of the scaffolding
  layers, confirming Milestone 4.3A's "infrastructure complete" claim
  for domain/rules/engine/calculator *framework* code.

### Genuinely open, safe-to-do-next

- **A `weekly_future_calculator.py` file/class skeleton** — mirroring
  the existing five placeholder calculators' exact pattern (a
  `RuleReference`-free or Candidate-appropriate identity, a
  `calculate()` that raises `NotImplementedError` citing ENT-010 /
  the Weekly Future concept) does not yet exist and would be safe to
  create as a placeholder, since Milestone 4.3A's own precedent shows
  placeholder calculators registering successfully while raising
  `NotImplementedError`. Because Weekly Future is an Entity (ENT-010),
  not a numbered Rule ID, this skeleton would need to reference it by
  entity, not by a `RuleReference` — a genuinely new (if structurally
  trivial) design decision, not a pure copy-paste of the other five.
- **A dedicated `Opponent High`/`Opponent Low` value/behavior module**
  is NOT proposed here — `Opponent.high`/`Opponent.low` already exist
  as reserved `Decimal | None` slots (`trading_engine/domain/opponent.py`
  lines 59-60) with the "no computation, no cross-field invariant"
  posture explicitly documented as deliberate (lines 30-35). No further
  scaffolding is missing for OPPONENT-002/003 beyond what already
  exists.
- **Calculator-level test files for the five concrete placeholder
  calculators** (`test_strike_calculator.py`,
  `test_trend_calculator.py`, `test_opponent_calculator.py`,
  `test_reversal_calculator.py`, `test_edge_calculator.py`) do not
  currently exist under `trading_engine/tests/calculators/` — only
  `test_context.py`, `test_protocols.py`, `test_registry.py`,
  `test_result.py` exist there, and a targeted search of the whole
  `trading_engine/tests/` tree found no reference to any of
  `StrikeCalculator`/`TrendCalculator`/`OpponentCalculator`/
  `ReversalCalculator`/`EdgeCalculator` by name outside
  `test_protocols.py` (which only checks generic protocol
  conformance). Writing tests asserting each concrete calculator
  correctly registers its RuleReference(s) and raises
  `NotImplementedError` from `calculate()` is safe, evidence-agnostic
  work — it tests the placeholder behavior that already exists, not
  any business mathematics.
- **Logging implementation for `EngineConfiguration.logging_enabled`**
  — the field is stored and validated but never read by
  `ExecutionPipeline.run()`; its own `# TODO` (`execution_pipeline.py`
  lines 142-146) states "no logging format/destination is evidenced
  anywhere in the reviewed documents." Building a generic logging
  hook here would be Safe Now (pure orchestration plumbing) provided
  it does not encode any rule-specific behavior.
- **Rule dependency-order execution** — `RuleRegistry.execution_order()`
  (`trading_engine/rules/registry.py` lines 92-106) currently returns
  registration order only; its own `# TODO` states the true dependency
  graph from `docs/RULE_INDEX.md`'s "Depends On"/"Referenced By"
  columns "is not represented anywhere in this framework yet."
  Implementing a topological sort over that already-documented graph
  (the graph itself, e.g. TREND-002 depends on TREND-001, is evidenced
  and stable per `RULE_DEPENDENCY_GRAPH.md`) is Safe Now: it consumes
  already-evidenced dependency *structure*, not undiscovered
  mathematics.

---

## PARTIALLY SAFE

Calculator skeletons, rule orchestration, and context building that
are already safely done in their current, generic form — but would
cross into unsafe territory if extended further without new evidence.

- **`StrategyEngine`/`ExecutionPipeline` orchestration** is safely
  done and evidence-agnostic today, per its own stated Architecture
  Rule (`strategy_engine.py` lines 15-19, confirmed against
  `execution_pipeline.py`'s actual iterate/call/collect implementation,
  lines 65-140 — no rule-specific branching found). It would become
  unsafe the moment anyone added an `if rule.id() == "STRIKE-001":`
  (or equivalent) special case to the Pipeline itself, since that
  would hardcode business logic the evidence does not yet support
  into a layer explicitly designed to stay generic.
- **The five placeholder Calculator classes** are safely done as
  *registration scaffolding*. They become unsafe the moment their
  `calculate()` bodies are filled in with any formula not fully
  evidenced and cross-checked against `docs/RULE_INDEX.md` — e.g.
  writing a "best guess" Weekly Future arithmetic implementation into
  `StrikeCalculator` (there is no dedicated Weekly Future calculator,
  so this guess would likely land inside `strike_calculator.py`'s
  future real implementation) would repeat exactly the mistake
  `REPOSITORY_CHANGE_PROPOSAL.md` Section 4 item 6 warns against
  ("Do NOT populate `docs/MATHEMATICAL_SPECIFICATION.md`... even in
  'best effort' form").
- **`RuleExecutionContext`/`CalculationContext` building** — both
  wrapper types (`trading_engine/rules/context.py`,
  `trading_engine/calculators/context.py`) are safely thin today: they
  carry `MarketContext`/`SessionState` plus untyped `configuration`
  and a clock/timestamp, with no derivation logic. Extending
  `configuration` to carry typed, rule-specific parameters (e.g. a
  quantified "well below" threshold for TREND-003) would cross into
  unsafe territory, since no rule's evidenced behavior currently
  specifies configurable parameters — both context modules' own
  docstrings state this explicitly ("no rule's evidenced behaviour
  currently requires configuration").
- **`RuleRegistry.execution_order()` topological sort** (see SAFE NOW
  above) is safe as long as it sorts by the already-evidenced
  dependency *graph structure*. It would become unsafe if the sort
  needed to break a cycle or resolve an ambiguity by guessing at an
  ordering the evidence does not specify (e.g. `RULE_DEPENDENCY_GRAPH.md`
  flags several "Requires (precondition)" fields as `UNKNOWN` — using
  those to further refine ordering would require inventing precondition
  semantics not evidenced).

---

## BLOCKED

Business mathematics, each blocked by a specific, cited evidence gap
in `EXTERNAL_EVIDENCE_BACKLOG.md`.

- **Weekly Future mathematics (ENT-010).** Blocked by self-contradictory
  arithmetic in the transcript's only worked example: a self-corrected
  subtraction (91→81), an unexplained jump from a stated difference of
  "18" to a final answer of "268," two conflicting Low values (≈26268
  vs. 26168), and a computed Low that is numerically higher than the
  computed High for the same candle — `EXTERNAL_EVIDENCE_BACKLOG.md`
  row 1, citing `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker"
  items 1-3.
- **Strike mathematics (STRIKE-001).** Blocked transitively by the
  Weekly Future gap above — the downstream nearest-strike rounding
  step is itself already "PARTIALLY READY... suitable for a documented
  feature spec and prototype implementation" (`STRIKE_EVIDENCE_SUMMARY.md`
  "Recommended Readiness Verdict," cited in `EXTERNAL_EVIDENCE_BACKLOG.md`
  row 1), but the calculator cannot be implemented end-to-end while its
  required upstream Weekly-Future value is unverified.
- **Trend mathematics (TREND-001/002/003).** TREND-001 blocked by "no
  formula connecting Strike to a TP Low value" being evidenced
  (`EXTERNAL_EVIDENCE_BACKLOG.md` row 4, citing
  `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 82-88). TREND-002
  additionally blocked by "market structure change" being a fully
  Unknown trigger (`EXTERNAL_EVIDENCE_BACKLOG.md` TREND-002 tie-row,
  citing `docs/DOMAIN_MODEL.md` lines 93-95). TREND-003 additionally
  blocked by the unquantified "well below" threshold
  (`EXTERNAL_EVIDENCE_BACKLOG.md` "not separately ranked" row, citing
  `docs/TERMINOLOGY.md` lines 112-113) plus its compound dependency on
  both TREND-001 and OPPONENT-001.
- **Opponent mathematics (OPPONENT-001/002/003).** Blocked by the
  "defeat" condition being an explicit unresolved Open Question, and
  OPPONENT-002/003 both having Evidence Count 0 — "the furthest from
  READY of any concept in this list, requiring net-new evidence
  acquisition from scratch" (`EXTERNAL_EVIDENCE_BACKLOG.md` row 5,
  citing `docs/RULE_INDEX.md` rows 35-36 and
  `docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 344-350).
- **Reversal mathematics (REVERSAL-001).** Blocked by "which specific
  premium behaviour constitutes identification" being unestablished
  anywhere — "no natural-language rule shape has been stated anywhere
  yet," a totally-Unknown concept with no existing partial evidence to
  build from (`EXTERNAL_EVIDENCE_BACKLOG.md` row 3, citing
  `docs/DOMAIN_MODEL.md` lines 168-171).

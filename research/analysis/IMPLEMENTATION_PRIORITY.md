# Implementation Priority

Ranks the SAFE-NOW and PARTIALLY-SAFE implementation work identified in
`SAFE_IMPLEMENTATION_SCOPE.md` (blocked mathematical work is excluded
by definition — it is not implementable yet regardless of priority).
Each item is scored on Engineering value, Evidence readiness (of the
concept it serves), Risk, and Rework probability, with every ranking
justified by citation. No item here proposes writing business
mathematics.

---

## Ranking

### 1. WeeklyFutureCalculator placeholder skeleton

- **Engineering value:** High — closes the one structural gap flagged
  explicitly by this review: `trading_engine/calculators/` has
  placeholder calculators for STRIKE-001, TREND-001/002, OPPONENT-001,
  TREND-003, and REVERSAL-001, but none for Weekly Future (ENT-010),
  even though ENT-010 is "materially further along than 'reserved,
  inactive, no computation designed' suggests"
  (`ENTITY_DEPENDENCY_GRAPH.md` discrepancy note) and is the single
  most evidence-advanced Candidate entity in the project.
- **Evidence readiness of the concept served:** PARTIALLY READY —
  higher than every NOT-READY rule (TREND-*, OPPONENT-*, REVERSAL-001)
  and second only to STRIKE-001 itself on the
  `KNOWLEDGE_READINESS_DASHBOARD.md` table (row 1 vs. row 2).
- **Risk:** Low. The skeleton would raise `NotImplementedError` from
  `calculate()`, identical in shape to the five calculators that
  already do exactly that — no new risk surface is introduced.
- **Rework probability:** Near-zero. It mirrors an already-established,
  five-times-repeated pattern (`base.py`'s `AbstractCalculator`, used
  identically by all five existing calculators) — the only design
  decision (referencing ENT-010 by entity rather than by a numbered
  Rule ID, since Weekly Future has no Rule ID) is small and localized.
- **Why ranked #1:** Highest ratio of engineering value to risk of any
  item in this list — it directly completes an existing, well
  established pattern for the best-evidenced not-yet-scaffolded
  concept in the project.

### 2. Calculator-level test files for the five existing placeholders

- **Engineering value:** Medium-High — closes a genuine, cited test
  gap. `trading_engine/tests/calculators/` currently tests only the
  generic framework (`test_context.py`, `test_protocols.py`,
  `test_registry.py`, `test_result.py`); a targeted search found no
  test file referencing `StrikeCalculator`, `TrendCalculator`,
  `OpponentCalculator`, `ReversalCalculator`, or `EdgeCalculator` by
  name outside `test_protocols.py`'s generic conformance check. This
  means the "infrastructure complete" claim is verified for the
  framework layer but not, today, for the five concrete placeholders
  themselves.
- **Evidence readiness of the concept served:** N/A by design — these
  tests assert placeholder behavior (registers correctly, raises
  `NotImplementedError`), not business mathematics, so no rule's
  evidence readiness gates them.
- **Risk:** Low — testing existing, already-written code paths only.
- **Rework probability:** Low, with one caveat: once any one
  calculator's real mathematics eventually gets implemented (STRIKE-001
  is closest), that calculator's placeholder test (asserting
  `NotImplementedError`) would need to be replaced, not merely
  extended — this is expected churn, not wasted effort, since the test
  still documents current behavior faithfully in the meantime.
- **Why ranked #2:** Slightly behind item 1 because it's pure
  verification of already-existing behavior rather than new discoverable
  surface area, but ranks above the remaining items because the gap is
  concrete and cited (not speculative), and the work is trivially
  low-risk.

### 3. Rule dependency-order execution (`RuleRegistry.execution_order()`)

- **Engineering value:** Medium — implements a capability the
  framework's own code flags as missing: `execution_order()`
  (`trading_engine/rules/registry.py` lines 92-106) currently "returns
  registration order only," with its own `# TODO` stating the true
  `docs/RULE_INDEX.md` dependency graph (e.g. TREND-002 depends on
  TREND-001) "is not represented anywhere in this framework yet."
- **Evidence readiness of the concept served:** The dependency graph
  itself (not the rules' mathematics) is fully evidenced and stable —
  `RULE_DEPENDENCY_GRAPH.md`'s Summary Table records every rule's
  `Depends On` relationship today, sourced from `docs/RULE_INDEX.md`
  directly.
- **Risk:** Medium — a topological sort must handle the parts of the
  graph that are genuinely `UNKNOWN` (e.g. several `Requires
  (precondition)` fields) without silently inventing an ordering the
  evidence doesn't support; the "Depends On (ledger)" vs. "Depends On
  (deeper evidence)" discrepancy flagged for STRIKE-001 in
  `RULE_DEPENDENCY_GRAPH.md`'s discrepancy note is a concrete case
  where naively picking one column over the other would be a judgment
  call, not a mechanical fact.
- **Rework probability:** Medium — `docs/architecture/IMPLEMENTATION_ROADMAP.md`
  Milestone 4.4's own scope note states dependency-order evaluation
  belongs to "Rule Engine" work still to be built ("registration by
  Rule ID, dependency-order evaluation per `RULE_INDEX.md`'s `Depends
  On` graph") — meaning this item sits inside already-planned,
  in-scope work rather than ahead of it, but the plan's exit criteria
  ("provable with test-double rules, not real ones") confirms this
  ordering logic is meant to be built before real rule mathematics
  exists, lowering rework risk relative to deeper infrastructure (see
  item 5 below).
- **Why ranked #3:** Real engineering value and a stable evidence base
  for the *graph structure* being consumed, but the medium risk of
  mis-resolving the ledger/deeper-evidence discrepancy noted above
  keeps it behind items 1-2.

### 4. Logging hook for `EngineConfiguration.logging_enabled`

- **Engineering value:** Low-Medium — closes a narrow, cited gap:
  the field is "stored by `EngineConfiguration` but never read" by
  `ExecutionPipeline.run()` (`execution_pipeline.py` lines 142-146).
- **Evidence readiness of the concept served:** N/A — pure
  orchestration plumbing, not gated by any rule's mathematics.
- **Risk:** Low — additive, does not change existing control flow if
  implemented as a no-op-by-default hook.
- **Rework probability:** Low-Medium — no logging format/destination is
  evidenced anywhere in the reviewed documents (per the same `# TODO`),
  so any concrete implementation is a judgment call about format that
  could need revisiting once real usage patterns emerge (e.g. once
  Milestone 4.5's Replay Engine exists and generates actual log
  volume) — moderate, not high, rework risk since logging plumbing is
  typically loosely coupled to the rest of the system.
- **Why ranked #4:** Genuinely safe and cited, but lower engineering
  value than items 1-3 since it doesn't unblock or verify any other
  component — it's a narrow, isolated improvement.

### 5. Deep replay/backtest infrastructure (Milestones 4.5+)

- **Engineering value:** Potentially high in the abstract, but
  currently low-value to build now, because `docs/architecture/IMPLEMENTATION_ROADMAP.md`'s
  own sequencing note states Milestones 4.7-4.9 (Backtest, Paper
  Trading, Broker Integration) are "functionally blocked, not just
  sequenced, on new evidence: none of them produce a meaningful trading
  outcome until at least one rule's mathematics moves from
  Unknown/Partially Known to Known" (lines 166-170). Even Milestone 4.5
  (Replay Engine) and 4.6 (Unit Tests), while listed as buildable "on
  scaffolding alone (test-double rules)" (line 165-166), exist
  specifically to prepare for the blocked milestones rather than to
  deliver standalone value today.
- **Evidence readiness of the concept served:** Low relative to items
  1-4 — this work's payoff is contingent on rule mathematics that is
  currently NOT READY for 7 of 8 Rule IDs
  (`KNOWLEDGE_READINESS_DASHBOARD.md`).
- **Risk:** Medium — building against `RuleExecutionContext`/
  `CalculationContext`'s current shape is safe today, but per
  `SAFE_IMPLEMENTATION_SCOPE.md`'s PARTIALLY SAFE section, both context
  types are "deliberately thin" specifically because "no rule's
  evidenced behaviour currently requires configuration" — deep replay
  infrastructure built now risks encoding assumptions about what a
  real rule's context needs that later prove wrong once actual
  mathematics is implemented.
- **Rework probability:** HIGH — explicitly, per
  `docs/architecture/IMPLEMENTATION_ROADMAP.md`'s own Milestone 4.7
  scope note: "a backtest run produces no meaningful trading-relevant
  output, only proof that the pipeline mechanics work" until real rule
  implementations exist. Building deep backtest/replay infrastructure
  now, before knowing what data shape even one real rule's mathematics
  will require (e.g. STRIKE-001's eventual real implementation may need
  Call/Put first-candle OHLC data that no current domain object
  carries), risks having to substantially rework that infrastructure
  once the first real rule lands.
- **Why ranked #5 (lowest):** This is the clearest case in the project
  of work whose own governing roadmap document flags it as high-rework
  if built ahead of evidence — contrast with items 1-4, none of which
  carry an explicit "functionally blocked... no meaningful output"
  warning in the roadmap itself.

---

## Summary ordering

1. WeeklyFutureCalculator placeholder skeleton — highest value/risk
   ratio, near-zero rework, serves the best-evidenced un-scaffolded
   concept (PARTIALLY READY).
2. Calculator-level tests for the five existing placeholders — closes
   a concrete, cited coverage gap at low risk.
3. Rule dependency-order execution — real value, stable graph-structure
   evidence, but medium risk from the STRIKE-001 ledger/deeper-evidence
   discrepancy needing a careful resolution choice.
4. Logging hook for `EngineConfiguration.logging_enabled` — safe and
   cited but narrow, isolated value.
5. Deep replay/backtest infrastructure (Milestones 4.5+) — explicitly
   flagged by `docs/architecture/IMPLEMENTATION_ROADMAP.md` itself as
   high rework probability and low present value until real rule
   mathematics exists; should wait.

Every ranking above is grounded in `docs/architecture/IMPLEMENTATION_ROADMAP.md`'s
own stated sequencing and blocking language, `RULE_DEPENDENCY_GRAPH.md`'s
evidenced dependency graph, `KNOWLEDGE_READINESS_DASHBOARD.md`'s
readiness verdicts, and direct reads of the cited `trading_engine/`
source files — no engineering-value or risk judgment above is invented
independent of these sources.

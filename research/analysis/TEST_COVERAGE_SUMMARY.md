# Test Coverage Summary

Milestone 6.2. Per-calculator test inventory, following the
`CALCULATOR_CONSISTENCY_REPORT.md` review. Before this milestone, only
`WeeklyFutureCalculator` (added in Milestone 6.1) had a dedicated test
file — the other 5 calculators were exercised only by
`test_protocols.py`'s generic `_PLACEHOLDER_CALCULATORS` parametrized
checks (identity methods, `supported_rules()` contents, and
`NotImplementedError`), with no calculator-specific
registration/duplicate-registration/never-returns coverage. This
milestone closes that gap by adding one dedicated test file per
pre-existing calculator, mirroring `test_weekly_future_calculator.py`'s
structure exactly. No existing test file was modified.

## Per-calculator inventory

| Calculator | Dedicated test file | Tests in dedicated file | Also covered by `test_protocols.py`'s shared parametrization | Coverage (statements) |
|---|---|---|---|---|
| StrikeCalculator | `test_strike_calculator.py` | 13 | Yes (3 parametrized cases) | 100% (11/11 stmts) |
| TrendCalculator | `test_trend_calculator.py` | 13 | Yes (3 parametrized cases) | 100% (12/12 stmts) |
| OpponentCalculator | `test_opponent_calculator.py` | 14 | Yes (3 parametrized cases) | 100% (13/13 stmts) |
| ReversalCalculator | `test_reversal_calculator.py` | 13 | Yes (3 parametrized cases) | 100% (11/11 stmts) |
| EdgeCalculator | `test_edge_calculator.py` | 14 | Yes (3 parametrized cases) | 100% (11/11 stmts) |
| WeeklyFutureCalculator | `test_weekly_future_calculator.py` (Milestone 6.1) | 14 | No — not in `_PLACEHOLDER_CALCULATORS` tuple (a deliberate Milestone 6.1 choice: adding a new file rather than editing the existing tuple) | 100% (11/11 stmts) |

**Total new tests added this milestone:** 67 (13+13+14+13+14, across the 5 new files; `test_weekly_future_calculator.py`'s 14 pre-date this milestone). Full suite: **466 passed**, up from 399 before this milestone.

## Checklist coverage per calculator (Task 2's 9 required scenarios)

Every one of the 6 dedicated test files now covers all 9 scenarios required by Task 2:

| Scenario | How it's covered |
|---|---|
| Construction | `TestConstruction.test_construction_requires_no_arguments`, `test_two_instances_are_independent_but_equal_in_identity` |
| Protocol conformance | `TestProtocolConformance.test_satisfies_calculator_protocol` |
| Calculator identity | `TestIdentityMethods.test_id`, `test_name`, `test_description_is_non_blank` |
| RuleReference | `TestIdentityMethods.test_supported_rules_cites_*` asserts `isinstance(reference, RuleReference)` for every returned reference |
| `supported_rules()` | Same test, asserts the exact expected rule-ID set |
| Registration | `TestRegistration.test_registers_successfully`, `test_get_returns_the_registered_instance` |
| Duplicate registration protection | `TestRegistration.test_duplicate_registration_raises` (new — this scenario had **zero** calculator-specific coverage before this milestone; it existed only generically, via `test_registry.py`'s `FakeCalculator` test double, never against a real placeholder calculator) |
| `NotImplementedError` | `TestCalculateRaisesNotImplemented.test_calculate_raises_not_implemented_error`, `test_not_implemented_error_references_<rule>` |
| `calculate()` never returns `CalculationResult` | `TestCalculateRaisesNotImplemented.test_calculate_performs_no_business_mathematics` (new — previously only implicit via `pytest.raises`, never an explicit "must raise, must not return" guard) |

## Missing scenarios

None of the 9 required scenarios are missing for any of the 6 calculators, after this milestone's additions. Two calculators have one extra, calculator-specific edge-case test beyond the shared 9:
- `OpponentCalculator`: `TestEdgeCases.test_includes_awaiting_evidence_placeholder_rules` — verifies OPPONENT-002/003 carry `evidence_count == 0`, matching the ledger.
- `EdgeCalculator`: `TestEdgeCases.test_calculator_id_reflects_supported_rule_not_edge_itself` — a structural guard against ever renaming its ID to something Edge-specific, since Edge has no Rule ID of its own.

No comparable repository-fact-specific edge case was identified for StrikeCalculator, TrendCalculator, ReversalCalculator, or WeeklyFutureCalculator beyond the shared 9 scenarios — none was added rather than inventing a scenario without a concrete fact to guard.

## Recommended future tests

These are explicitly **not implemented now** — they depend on evidence or engineering work that is out of this milestone's (and this whole phase's) scope:

1. **Real-math test suites per calculator**, once each rule's mathematics is actually evidenced and implemented (blocked — see `research/analysis/KNOWLEDGE_READINESS_DASHBOARD.md`; every rule remains PARTIALLY READY or NOT READY).
2. **`CalculationContext` variation tests** (e.g. calculators behaving consistently across different `configuration` mapping contents) — not meaningful yet since no calculator reads its `context` argument at all.
3. **Cross-calculator integration tests** (e.g. registering all 6 into one `CalculatorRegistry` and asserting `list_calculators()` ordering/count) — safe to add later per `research/analysis/SAFE_IMPLEMENTATION_SCOPE.md`'s "SAFE NOW" classification of registry behaviour, but not requested by this milestone's scope (per-calculator consistency, not registry-wide integration).
4. **Mutation/negative tests for the `EvidenceReference` dimension** — none of the 6 calculators currently expose or test `required_evidence()`-style evidence citations (only `supported_rules()` exists on the `Calculator` protocol); if a future milestone adds evidence-citation methods to the protocol, tests should be added symmetrically to `RuleReference` coverage.

## Quality Gate Report

| Gate | Command | Result |
|---|---|---|
| ruff | `ruff check trading_engine` | **Clean** — 0 issues |
| black | `black --check trading_engine` | **Clean** — 79 files unchanged |
| mypy --strict | `mypy --strict trading_engine/domain trading_engine/rules trading_engine/engine trading_engine/calculators` | **Clean** — 40 source files, 0 issues |
| pytest | `pytest trading_engine/tests -q` | **466 passed**, 0 failed |
| coverage | `pytest ... --cov=trading_engine.domain --cov=trading_engine.rules --cov=trading_engine.engine --cov=trading_engine.calculators --cov-report=term-missing` | **100%** — 716/716 statements, 0 missed, across all 4 packages |

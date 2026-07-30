# Calculator Consistency Report

Milestone 6.2. Reviews all 6 calculators in `trading_engine/calculators/`
against the canonical placeholder pattern established in Milestone
4.3A (`strike_calculator.py`, `trend_calculator.py`,
`opponent_calculator.py`, `reversal_calculator.py`,
`edge_calculator.py`) and extended in Milestone 6.1
(`weekly_future_calculator.py`). No business mathematics was added or
proposed anywhere in this review.

## Canonical contract checked

For every calculator: inherits `AbstractCalculator`; has a unique
`calculator_id`; carries at least one `RuleReference` via
`supported_rules()`; `__init__()` takes no arguments; `calculate()`
unconditionally raises `NotImplementedError`; a `# TODO (<RULE-ID>)`
comment precedes the raise, citing what evidence is missing; no
arithmetic, comparison, or side-effecting statement exists anywhere in
the file.

## Results

| Calculator | File | Status | Reason | Evidence |
|---|---|---|---|---|
| StrikeCalculator | `trading_engine/calculators/strike_calculator.py` | **PASS** | Inherits `AbstractCalculator`; `calculator_id="STRIKE-001-CALCULATOR"` (unique); `supported_rules()` returns one `RuleReference(rule_id="STRIKE-001", category=STRIKE, ...)`; `calculate()` raises `NotImplementedError("TODO (STRIKE-001): Strike mathematics awaiting evidence.")` preceded by a 3-line TODO comment; no arithmetic present. | `docs/RULE_INDEX.md` row for STRIKE-001; file itself |
| TrendCalculator | `trading_engine/calculators/trend_calculator.py` | **PASS** | Same pattern; `calculator_id="TREND-001-CALCULATOR"`; `supported_rules()` returns two references (TREND-001, TREND-002); TODO/raise cite TREND-001; no arithmetic present. | `docs/RULE_INDEX.md` rows for TREND-001/002 |
| OpponentCalculator | `trading_engine/calculators/opponent_calculator.py` | **PASS** | Same pattern; `calculator_id="OPPONENT-001-CALCULATOR"`; `supported_rules()` returns three references (OPPONENT-001, and the two Awaiting-Evidence placeholders OPPONENT-002/003 with `evidence_count=0`, matching `docs/RULE_INDEX.md` exactly); TODO/raise cite OPPONENT-001; no arithmetic present. | `docs/RULE_INDEX.md` rows for OPPONENT-001/002/003 |
| ReversalCalculator | `trading_engine/calculators/reversal_calculator.py` | **PASS** | Same pattern; `calculator_id="REVERSAL-001-CALCULATOR"`; one reference (REVERSAL-001); TODO/raise correct; no arithmetic present. | `docs/RULE_INDEX.md` row for REVERSAL-001 |
| EdgeCalculator | `trading_engine/calculators/edge_calculator.py` | **PASS** | Same pattern; `calculator_id="TREND-003-CALCULATOR"` (cites the rule it supports, since Edge per `docs/architecture/DOMAIN_ARCHITECTURE.md` "is modeled as a condition... not a standalone entity" and has no Rule ID of its own); one reference (TREND-003); no arithmetic present. | `docs/architecture/DOMAIN_ARCHITECTURE.md` Edge section; `docs/RULE_INDEX.md` row for TREND-003 |
| WeeklyFutureCalculator | `trading_engine/calculators/weekly_future_calculator.py` | **PASS (with a documented, necessary deviation — see WARNING below)** | Same pattern; `supported_rules()` returns one reference to STRIKE-001 (Weekly Future/ENT-010 has no Rule ID of its own, so — mirroring EdgeCalculator's precedent — it cites the rule it serves); TODO/raise cite STRIKE-001 but with a longer, more specific comment naming the exact arithmetic contradictions from `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`; no arithmetic present. | `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`; `docs/architecture/DOMAIN_ARCHITECTURE.md` |

## Inconsistencies identified

### WARNING 1 — `calculator_id` naming pattern deviates for WeeklyFutureCalculator

**Finding:** The other 5 calculators all follow `<cited-Rule-ID>-CALCULATOR` (e.g. `STRIKE-001-CALCULATOR`, `TREND-003-CALCULATOR` for EdgeCalculator, which also cites a rule it doesn't own). `WeeklyFutureCalculator` instead uses `WEEKLY-FUTURE-CALCULATOR`, which does not match its cited rule (`STRIKE-001`).

**Reason this is not a defect requiring correction:** the literal pattern (`STRIKE-001-CALCULATOR`) is already taken by `StrikeCalculator` itself. Using it for `WeeklyFutureCalculator` would either violate calculator-ID uniqueness (if identical) or require an artificial suffix not used anywhere else in the codebase. `WEEKLY-FUTURE-CALCULATOR` is the calculator's own concept-based name (mirroring how `name()` returns "Weekly Future Calculator", a human name, not a rule-ID-based one) — this is a necessary, intentional, and already-documented deviation (see the module docstring in `weekly_future_calculator.py`), not an oversight.

**Action taken:** none. Flagged as WARNING (not FAIL) for traceability; no code change made, since "correcting" it would either break uniqueness or require inventing a naming convention not evidenced anywhere else in the repository.

### WARNING 2 — Module docstring / TODO comment verbosity differs for WeeklyFutureCalculator

**Finding:** The 5 original calculators each carry a 3-4 line TODO comment before their `raise NotImplementedError`. `WeeklyFutureCalculator`'s TODO comment is 9 lines, citing specific numeric contradictions from `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`.

**Reason this is not a defect requiring correction:** Milestone 6.1 explicitly required "TODO comments referencing the unresolved Weekly Future evidence" — Weekly Future's evidence gap is itself more specific and better-documented (a named, multi-part contradiction) than the generic "mathematics awaiting evidence" phrasing sufficient for the other 5 rules, which currently have no comparably detailed root-cause analysis on record. Shortening this comment to match the others' length would remove traceable detail without any corresponding gain in consistency.

**Action taken:** none. Flagged as WARNING for completeness; no code change made.

### No FAIL-level inconsistencies found

Every calculator: inherits `AbstractCalculator`; has a calculator_id unique across all 6 (`STRIKE-001-CALCULATOR`, `TREND-001-CALCULATOR`, `OPPONENT-001-CALCULATOR`, `REVERSAL-001-CALCULATOR`, `TREND-003-CALCULATOR`, `WEEKLY-FUTURE-CALCULATOR` — verified pairwise distinct); carries at least one well-formed `RuleReference` matching `docs/RULE_INDEX.md`'s actual data for that rule (status/confidence/evidence_count all verified against the ledger, not invented); `calculate()` raises `NotImplementedError` and nothing else — no calculator returns a `CalculationResult`, mutates any argument, performs I/O, or contains any arithmetic/comparison operator anywhere in its body. No duplicate calculator IDs, no missing TODOs, no missing evidence references, and no exception-wording pattern that omits the `TODO (<RULE-ID>):` prefix.

## Task 4 — Corrections applied

**None required.** No calculator's code was modified during this milestone; both findings above are documented, intentional deviations rather than defects, and Task 4 only calls for correcting genuine inconsistencies.

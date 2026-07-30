# Dependency Validation Report

Milestone 6.3. Documents exactly which Rule-to-Rule dependency edges
were recognised by `trading_engine/rules/dependencies.py`, which
candidate edges were considered and excluded, and why.

## Rules analysed

All 8 Rule IDs currently in `docs/RULE_INDEX.md`'s Index table:
STRIKE-001, TREND-001, TREND-002, TREND-003, OPPONENT-001,
OPPONENT-002, OPPONENT-003, REVERSAL-001.

## Dependencies recognised

Read directly from `docs/RULE_INDEX.md`'s "Depends On" column, with no
modification:

| Dependent | Depends On | Source |
|---|---|---|
| TREND-002 | TREND-001 | `docs/RULE_INDEX.md` row 32 |
| TREND-003 | TREND-001, OPPONENT-001 | `docs/RULE_INDEX.md` row 33 |
| OPPONENT-001 | TREND-001, OPPONENT-002, OPPONENT-003 | `docs/RULE_INDEX.md` row 34 |

The remaining 5 rules (STRIKE-001, TREND-001, OPPONENT-002,
OPPONENT-003, REVERSAL-001) have no recognised dependencies — their
ledger entries all read "Depends On: none yet."

## Ignored candidate dependencies

### Candidate 1 — Weekly Future → STRIKE-001

**Evidence for this edge:** `research/analysis/RULE_DEPENDENCY_GRAPH.md`
("STRIKE-001... Deeper evidence: Weekly Future first-candle High/Low")
and `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` (the full
input/output/arithmetic analysis) both establish that STRIKE-001's
strike selection depends on a Weekly Future computation, sourced from
the underlying transcript evidence (`research/analysis/STRIKE_EVIDENCE_TABLE.md`,
`research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md`).

**Reason for exclusion — two independent reasons, either one sufficient on its own:**

1. **Ledger disagreement.** `docs/RULE_INDEX.md`'s own row for
   STRIKE-001 still reads `Depends On: none yet`. Milestone 5.2's
   `research/analysis/REPOSITORY_CHANGE_PROPOSAL.md` explicitly
   proposed adding this edge to the ledger, and explicitly flagged
   that the proposal had **not** been applied. This milestone's own
   rules ("Do NOT modify repository documentation," "Do NOT introduce
   unsupported dependencies") forbid both updating the ledger to match
   the deeper evidence *and* encoding an edge in code that the ledger
   itself does not (yet) assert — doing the latter would create a
   second, silently-diverging source of truth about STRIKE-001's
   dependencies.
2. **No graph node exists for Weekly Future.** Weekly Future is
   ENT-010, a Candidate Entity per
   `docs/architecture/DOMAIN_ARCHITECTURE.md` — it has no Rule ID.
   `RuleRegistry`'s dependency graph (and `trading_engine/rules/dependencies.py`'s
   `RULE_DEPENDENCIES` table) is keyed exclusively by Rule ID. There is
   no valid Rule-ID string to use as the source node of this edge even
   if reason 1 did not apply on its own.

**Where this relationship IS represented in the codebase:** at the
*calculator* layer, not the rule-dependency layer —
`trading_engine/calculators/weekly_future_calculator.py`'s
`supported_rules()` cites STRIKE-001 (Milestone 6.1), and
`trading_engine/calculators/strike_calculator.py`'s own module
docstring documents the same relationship in prose. That is a
different, narrower claim ("this calculator's future output would
support this rule") than "this rule cannot be evaluated before that
rule" (`RuleRegistry.execution_order()`'s actual contract) — the two
are not required to use the same representation, and conflating them
would overstate what `RuleRegistry` can validly claim about a Candidate
Entity that has no Rule ID.

### Candidate 2 — "Referenced By" column entries

`docs/RULE_INDEX.md` also lists a "Referenced By" column (e.g.
TREND-001's row lists "TREND-002, TREND-003, OPPONENT-001" as
Referenced By). This is mathematically the inverse of the "Depends On"
relationships already recognised above and was cross-checked for
consistency, not treated as an independent source: every "Referenced
By" entry in the ledger corresponds exactly to a "Depends On" entry
already captured (e.g. TREND-001 being "Referenced By" TREND-002
matches TREND-002's own "Depends On: TREND-001"). No additional edge
was found or needed from this column; it was not used as a second,
separate data source in `trading_engine/rules/dependencies.py` to avoid
maintaining two representations of the same fact.

### Candidate 3 — Edge (TREND-003's calculator relationship)

`trading_engine/calculators/edge_calculator.py` cites TREND-003 as its
supported rule (Milestone 4.3A/6.2), and `docs/architecture/DOMAIN_ARCHITECTURE.md`
describes Edge as "a condition evaluated over two TrendPoints." This is
not a Rule-to-Rule dependency at all — Edge has no Rule ID of its own,
identically to Weekly Future's situation above — so no edge was
proposed or excluded here; there was never a candidate Rule ID pair to
consider.

## Future extension points

1. **If `docs/RULE_INDEX.md`'s STRIKE-001 row is ever updated** to
   formally record a Weekly Future dependency (per the proposal already
   on file in `research/analysis/REPOSITORY_CHANGE_PROPOSAL.md`), and
   if Weekly Future is ever assigned a Rule ID of its own,
   `trading_engine/rules/dependencies.py`'s `RULE_DEPENDENCIES` table
   should be updated to match — this is a one-line change once both
   preconditions are met, not an architectural change.
2. **Cross-validation against the ledger.** A future milestone could
   add an automated check (e.g. a test that parses `docs/RULE_INDEX.md`'s
   "Depends On" column and asserts it matches `RULE_DEPENDENCIES`
   exactly) to prevent the two from silently drifting apart, per the
   "Known limitations" section of `research/analysis/RULE_DEPENDENCY_ENGINE_REPORT.md`.
3. **A `Rule.depends_on()` protocol method**, if a future milestone
   decides dependency data should be declared by each `Rule`
   implementation itself rather than centralised in one lookup module
   — deliberately not done in this milestone to keep the `Rule`
   protocol's surface unchanged (see "Known limitations" #2 in the
   companion report).

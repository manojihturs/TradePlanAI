# Rule Dependency Engine Report

Milestone 6.3. Implements dependency-aware execution ordering for
`RuleRegistry`, replacing the registration-order-only placeholder left
by Milestone 4.2/4.3. Infrastructure only — no business mathematics,
no trading logic, no repository documentation changed.

## Architecture

Three files, one modified two new:

```
trading_engine/rules/
    dependencies.py     -- NEW: RULE_DEPENDENCIES table + depends_on() + is_well_formed_rule_id()
    exceptions.py        -- MODIFIED (additive only): + UnresolvedDependencyError, + CircularDependencyError
    registry.py           -- MODIFIED: execution_order() reimplemented; register()/get()/by_category()/
                              all_rules()/__len__/__contains__ all untouched
```

**`dependencies.py`** is a standalone lookup module keyed purely by Rule ID string, deliberately kept out of the domain layer (`trading_engine/domain/rule_reference.py` was not touched) and out of the `Rule` protocol (`trading_engine/rules/protocols.py` was not touched, so every existing `Rule`-conforming object — including `FakeRule` used across the entire existing test suite — continues to satisfy the protocol unmodified). This is the "minimum infrastructure required" per Task 4: a single dict-backed lookup function, not a change to any existing class's shape.

**`RuleRegistry.execution_order()`** now accepts an optional `dependency_resolver` parameter (`Callable[[str], tuple[str, ...]] | None = None`), defaulting to `dependencies.depends_on`. This is dependency injection, mirroring the pattern already established elsewhere in the codebase (e.g. `RuleExecutionContext.clock`), and exists specifically so this milestone's own tests can exercise cycle-detection and malformed-dependency scenarios without needing to fabricate fake entries in the real, ledger-sourced `RULE_DEPENDENCIES` table.

## Implementation approach

Given a set of registered rules, `execution_order()`:

1. Builds a per-rule dependency list via the resolver, in registration order, deduplicating repeated entries within one rule's own list (e.g. a rule declaring the same dependency twice is treated as declaring it once).
2. Validates every declared dependency: rejects malformed Rule IDs (don't match the `<CATEGORY>-<NNN>` convention) and rejects dependencies on Rule IDs that are not themselves currently registered — both raise `UnresolvedDependencyError`, with distinguishable message text ("unsupported dependency" vs. "missing dependency") so callers/tests can tell the two apart.
3. Runs Kahn's algorithm (repeatedly extracting rules with zero remaining unresolved dependencies) to produce a topological order.
4. If any registered rule is never extracted (a cycle exists among the remaining rules), raises `CircularDependencyError` naming every rule still stuck in the cycle.

## Algorithms used

**Kahn's algorithm** (BFS-style topological sort via in-degree tracking) was chosen over a DFS-based approach specifically because it makes cycle detection and deterministic tie-breaking both simple: any rule left with nonzero in-degree after the queue empties is, by construction, part of a cycle (or depends, transitively, on one) — no separate visited/recursion-stack bookkeeping is needed.

**Deterministic tie-break:** at each step, if multiple rules are simultaneously "ready" (all their dependencies already ordered), the one registered earliest is chosen first (`ready.sort(key=registration_order.index)`). This guarantees `execution_order()` returns the identical tuple across repeated calls on the same registry state, and ties are broken by insertion order rather than left to Python dict/set iteration, which is not a documented ordering guarantee for this purpose even though `dict` preserves insertion order in CPython — the explicit sort makes the guarantee a property of this method's own contract, not an accident of the standard library.

## Repository evidence supporting the dependency model

Every entry in `RULE_DEPENDENCIES` (`trading_engine/rules/dependencies.py`) is copied verbatim from `docs/RULE_INDEX.md`'s "Depends On" column:

| Rule ID | `docs/RULE_INDEX.md` "Depends On" | Encoded as |
|---|---|---|
| STRIKE-001 | none yet | `()` |
| TREND-001 | none yet | `()` |
| TREND-002 | TREND-001 | `("TREND-001",)` |
| TREND-003 | TREND-001, OPPONENT-001 | `("TREND-001", "OPPONENT-001")` |
| OPPONENT-001 | TREND-001, OPPONENT-002, OPPONENT-003 | `("TREND-001", "OPPONENT-002", "OPPONENT-003")` |
| OPPONENT-002 | none yet | `()` |
| OPPONENT-003 | none yet | `()` |
| REVERSAL-001 | none yet | `()` |

No edge was invented, inferred, or sourced from anywhere other than that one ledger column.

**Deliberately excluded edge — Weekly Future → STRIKE-001.** `research/analysis/RULE_DEPENDENCY_GRAPH.md` and `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` establish that STRIKE-001's strike selection depends on a Weekly Future computation. This is *not* encoded as a graph edge, for two independent reasons: (1) `docs/RULE_INDEX.md`'s own ledger still reads `STRIKE-001 | ... | Depends On: none yet` — the proposed ledger update was flagged by `research/analysis/REPOSITORY_CHANGE_PROPOSAL.md` but explicitly never applied, and this milestone's own rules forbid modifying repository documentation, so encoding the edge here without the ledger agreeing would create a second, competing source of truth; (2) Weekly Future has no Rule ID at all (it is ENT-010, a Candidate Entity) — `RuleRegistry`'s dependency graph is keyed by Rule ID exclusively, and there is no rule-ID node for it to attach an edge to. See `research/analysis/DEPENDENCY_VALIDATION_REPORT.md` for the complete reasoning.

## Known limitations

1. **Ledger-lag risk.** If `docs/RULE_INDEX.md`'s "Depends On" column is ever updated (e.g. if the Weekly Future edge is formally added to STRIKE-001's row in a future milestone), `trading_engine/rules/dependencies.py` will silently continue reflecting the old data until someone manually updates `RULE_DEPENDENCIES` to match. No automated cross-check between the ledger document and this Python table exists yet.
2. **No `Rule`-level dependency declaration.** Dependency data lives entirely in the standalone `dependencies.py` module, keyed by Rule ID string — a `Rule` object itself has no `depends_on()` method and cannot report its own dependencies. This was a deliberate scope-minimization choice (see Architecture section) but means a caller inspecting a `Rule` instance directly, without going through `RuleRegistry.execution_order()`, cannot discover its dependencies.
3. **Missing-dependency handling is strict, not permissive.** If a registered rule declares a dependency on a rule that simply hasn't been registered yet (a normal, expected state while a registry is being built up incrementally), `execution_order()` raises immediately rather than computing a partial order over the rules that can be ordered. This was chosen deliberately (see `DEPENDENCY_VALIDATION_REPORT.md`) to avoid silently producing an order that looks complete but omits rules the caller may not realize are missing.
4. **`Referenced By` is not used.** `docs/RULE_INDEX.md` also carries a "Referenced By" column (the inverse of "Depends On"). This implementation derives the `dependents` mapping purely from "Depends On" internally (an implementation detail of the Kahn's-algorithm pass) and never reads "Referenced By" directly — the two columns are redundant by construction in the ledger, and only one was needed as the single source of truth.

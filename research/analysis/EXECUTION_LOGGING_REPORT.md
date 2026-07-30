# Execution Logging Report

Milestone 6.4. Implements infrastructure-level execution logging and
diagnostics for `RuleRegistry`, `ExecutionPipeline`, and
`StrategyEngine`. No business mathematics, no repository documentation
changed, no Rule IDs changed.

## Architecture

A new, foundational package sits below `rules`/`engine`/`calculators`
in the dependency direction (mirroring `domain`'s own placement):

```
trading_engine/diagnostics/
    __init__.py
    events.py       -- 8 frozen dataclasses (see Event model below)
    sink.py          -- DiagnosticsSink protocol + 3 implementations
    exceptions.py     -- DiagnosticsError
```

`trading_engine/diagnostics/` has **zero dependency** on
`trading_engine.rules`, `trading_engine.engine`, or
`trading_engine.calculators` — the reverse is true: those packages
import diagnostics to emit events. This was a deliberate design
constraint, not an accident: `RuleFinished` needs to carry a
`RuleOutcome`'s name, but rather than importing the `RuleOutcome` enum
type (which would create `rules` → `diagnostics` → `rules`
circularity, since `rules/registry.py` also needs to import
`diagnostics` to emit `RuleRegistered`), `RuleFinished.outcome_name` is
typed as a plain `str` (`result.outcome.name`, computed by the caller).

Three existing files were modified to wire emission in:

```
trading_engine/rules/registry.py            -- register(), execution_order() gain
                                                 diagnostics_sink parameters
trading_engine/engine/execution_pipeline.py  -- run() gains diagnostics_sink parameter
trading_engine/engine/strategy_engine.py     -- run() resolves a sink from
                                                 EngineConfiguration and passes it through
trading_engine/engine/engine_configuration.py -- gains diagnostics_sink field
```

Every one of these changes is additive: every new parameter has a
default (`None`) that preserves every pre-existing call site's
behaviour unchanged. All 483 tests passing before this milestone still
pass after it, unmodified.

## Event model

Eight frozen, immutable dataclasses in `trading_engine/diagnostics/events.py`,
one per Milestone 6.4 log point:

| Log point | Event class | Emitted by |
|---|---|---|
| rule registration | `RuleRegistered` | `RuleRegistry.register()` |
| dependency ordering (success) | `DependencyResolved` | `RuleRegistry.execution_order()` |
| unresolved dependency (any failure mode) | `DependencyMissing` | `RuleRegistry.execution_order()` |
| rule execution start | `RuleStarted` | `ExecutionPipeline.run()` |
| rule execution finish | `RuleFinished` | `ExecutionPipeline.run()` |
| execution skipped | `RuleSkipped` | `ExecutionPipeline.run()` |
| exception | `ExecutionFailed` | `ExecutionPipeline.run()` |
| execution summary | `ExecutionSummaryLogged` | `StrategyEngine.run()` |

Every event validates its own fields in `__post_init__` (non-blank IDs,
non-`None` timestamps, non-negative durations/counts), raising
`DiagnosticsError` on violation — the same per-package validation
pattern already used by `DomainValidationError`,
`RuleFrameworkError`, `EngineError`, and `CalculatorFrameworkError`.

**No trading data in any event.** Every field is either an identifier
(Rule ID string, UUID), a timestamp, a count, a duration, or a
framework-level classification name (`RuleOutcome.name` as a plain
string — `"PASS"`/`"FAIL"`/etc., never the computed value a real rule
would eventually produce). No calculator's `computed_values` mapping,
no `MarketContext` contents, and no strike/premium/trend numeric value
is ever passed into a diagnostic event anywhere in this implementation.

`DependencyMissing.reason` takes one of three values, covering all
three ways `execution_order()` can fail: `"unsupported dependency"`
(malformed Rule ID), `"missing dependency"` (well-formed but
unregistered), and `"circular dependency"` (one event per rule caught
in the cycle).

`ExecutionFailed.fatal` distinguishes a failure that stopped the
pipeline (`True` — a `RuleFrameworkError`, a `fail_fast` abort, or the
neither-`fail_fast`-nor-`continue_on_error` stop-without-raise case)
from one that was recorded and iteration continued (`False` — the
`continue_on_error` case).

## Sinks

`DiagnosticsSink` is a `typing.Protocol` (`@runtime_checkable`),
matching this codebase's existing contract style
(`Rule`, `Calculator`). Three implementations:

- **`NullDiagnosticsSink`** — discards every event. This is the
  *effective* sink whenever `EngineConfiguration.logging_enabled` is
  `False`, enforced independently at two levels (see "Where the
  `logging_enabled` guarantee lives" below), so it holds even if a
  real sink is passed by mistake.
- **`InMemoryDiagnosticsSink`** — collects events into an ordered
  list, exposed via `.events()` (returns a snapshot tuple, not the
  live list). This is what this milestone's own tests use to make
  assertions, and what a future replay/backtest consumer would use to
  inspect a run's event sequence programmatically (see
  `research/analysis/DIAGNOSTICS_GUIDE.md`).
- **`StandardLoggingDiagnosticsSink`** — forwards every event to
  Python's standard library `logging` module (logger name
  `"trading_engine.diagnostics"` by default), at `INFO` level, via
  `%r`-formatting (each event's own `repr()`). This is
  `StrategyEngine`'s default when `logging_enabled=True` and no
  `diagnostics_sink` was explicitly configured — a developer flips one
  flag and gets readable log output with zero additional wiring.

## Where the `logging_enabled` guarantee lives

Deliberately enforced in **two independent places**, not one:

1. `ExecutionPipeline.run()` itself resolves its effective sink as
   `diagnostics_sink if configuration.logging_enabled and diagnostics_sink is not None else NullDiagnosticsSink()`
   — so even a caller who constructs an `ExecutionPipeline` directly
   (bypassing `StrategyEngine` entirely, as this framework's own tests
   already do) gets the no-op guarantee without needing to remember to
   arrange it themselves.
2. `StrategyEngine._resolve_diagnostics_sink()` performs the same
   check before calling into either `RuleRegistry.execution_order()`
   or `ExecutionPipeline.run()`, so a full `StrategyEngine.run()` call
   never passes a live sink through to either collaborator when
   logging is disabled.

`RuleRegistry.register()`/`execution_order()`'s `diagnostics_sink`
parameter is the one exception to "gated by `EngineConfiguration`":
registration commonly happens before any `EngineConfiguration` or
`StrategyEngine` exists (a registry is typically built up first, then
handed to a `StrategyEngine`), so `register()`'s emission is opt-in
per call (`None` → no event), not tied to a configuration object it
has no way to know about at that point. This is documented in the
method's own docstring, not left implicit.

## Performance considerations

- **Zero overhead when disabled.** `NullDiagnosticsSink.emit()` is a
  single `return None` — no branching, no string formatting, no I/O.
  The only cost when logging is disabled is constructing the small
  frozen-dataclass event object itself before calling `.emit()` on it
  (a handful of attribute assignments and the `__post_init__`
  validation checks) — this was a deliberate simplicity-over-micro-optimisation
  choice: branching around event construction itself (e.g. `if
  sink is not NullDiagnosticsSink: ...`) would complicate every
  call site for a cost that is, in practice, negligible next to a
  single rule evaluation.
- **Timing cost.** `RuleStarted`/`RuleFinished` bracket every
  `rule.evaluate()` call with `context.clock()` (already a no-argument
  callable on `RuleExecutionContext`, defaulting to `datetime.now`) —
  this call happens unconditionally, not gated on `logging_enabled`,
  since `context.clock()` was already a cheap, already-present
  capability and gating it would add a branch for a negligible saving.
- **`InMemoryDiagnosticsSink` memory growth.** Unbounded — it retains
  every event for the lifetime of the sink instance. Appropriate for
  tests and short-lived programmatic inspection; not intended for a
  long-running process that would accumulate unbounded memory. See
  "Extension points" below.

## Extension points

1. **Bounded/rotating in-memory sink.** `InMemoryDiagnosticsSink`
   could be extended (or a sibling class added) with a maximum size
   and eviction policy for long-running processes — not needed by
   anything in this repository yet (no long-running process exists).
2. **A `CompositeDiagnosticsSink`** that fans a single `emit()` call
   out to multiple sinks (e.g. both `StandardLoggingDiagnosticsSink`
   and an `InMemoryDiagnosticsSink` simultaneously) — not built now
   since no current caller needs more than one sink at a time, but the
   `DiagnosticsSink` protocol makes this trivial to add later without
   touching `RuleRegistry`/`ExecutionPipeline`/`StrategyEngine`.
3. **A `ReplayDiagnosticsSink`** that writes events to durable storage
   (a file, a database) for later replay/backtest analysis — the
   natural next step once `docs/architecture/IMPLEMENTATION_ROADMAP.md`'s
   replay/backtest milestones (4.4+) actually begin, per
   `research/analysis/DIAGNOSTICS_GUIDE.md`'s "How future
   replay/backtest will consume diagnostics" section.
4. **Structured (non-`repr()`-based) log formatting**, e.g. JSON lines,
   for `StandardLoggingDiagnosticsSink` or a new sibling sink, if a
   future milestone needs machine-parseable log output rather than
   Python `repr()` text.

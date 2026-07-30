# Diagnostics Guide

Milestone 6.4. How to use `trading_engine.diagnostics` today, and how
a future replay/backtest consumer is expected to use it. Companion to
`research/analysis/EXECUTION_LOGGING_REPORT.md` (architecture/event
model) — this document is the "how do I use it" side.

## Quick start: turning logging on

```python
from trading_engine.engine.engine_configuration import EngineConfiguration
from trading_engine.engine.strategy_engine import StrategyEngine

configuration = EngineConfiguration(logging_enabled=True)
engine = StrategyEngine(registry, configuration)
report = engine.run(context)
```

With no other configuration, this routes every diagnostic event to
`StandardLoggingDiagnosticsSink`, which forwards to Python's standard
library `logging` module under the logger name
`"trading_engine.diagnostics"`. To see the output, configure that
logger the same way you would any other:

```python
import logging

logging.basicConfig(level=logging.INFO)
```

Each log line is one event's `repr()` — e.g.
`RuleStarted(event_id=..., occurred_at=..., rule_id='STRIKE-001')`.

## Turning logging off (the default)

`EngineConfiguration.logging_enabled` defaults to `False`. When
`False`, no diagnostic event is ever constructed-and-observed by any
caller — `NullDiagnosticsSink` is used internally regardless of what
(if anything) `diagnostics_sink` is set to, at both the
`ExecutionPipeline` and `StrategyEngine` level (see
`EXECUTION_LOGGING_REPORT.md`'s "Where the `logging_enabled` guarantee
lives"). There is nothing else a developer needs to do to keep
diagnostics off — it already is, unless explicitly enabled.

## Capturing events programmatically (tests, tooling, future replay)

Use `InMemoryDiagnosticsSink` instead of the default:

```python
from trading_engine.diagnostics.sink import InMemoryDiagnosticsSink

sink = InMemoryDiagnosticsSink()
configuration = EngineConfiguration(logging_enabled=True, diagnostics_sink=sink)
engine = StrategyEngine(registry, configuration)
report = engine.run(context)

for event in sink.events():
    print(type(event).__name__, event)
```

`sink.events()` returns a tuple snapshot (not the live internal list),
in emission order. This is exactly how this milestone's own test suite
(`trading_engine/tests/diagnostics/`, `trading_engine/tests/rules/test_registry_diagnostics.py`,
`trading_engine/tests/engine/test_execution_logging.py`) makes
assertions — it is the recommended pattern for any future code that
needs to inspect what happened during a run, not just observe it as
log text.

## Interpreting the event sequence

A single `StrategyEngine.run()` call with logging enabled emits, in
order:

1. One `DependencyResolved` (or, on failure, one or more
   `DependencyMissing` followed by a raised exception —
   `UnresolvedDependencyError` or `CircularDependencyError` — and no
   further events for that run).
2. Per rule, in the resolved execution order, **one** of:
   - `RuleSkipped` (dry run, or the maximum-rule-count limit reached) —
     no corresponding `RuleStarted`/`RuleFinished` for that rule.
   - `RuleStarted` followed by `RuleFinished` (successful evaluation).
   - `RuleStarted` followed by `ExecutionFailed` (evaluation raised —
     `fatal=True` always stops the run; `fatal=False` means the
     Pipeline recorded the error and moved on to the next rule).
3. Exactly one `ExecutionSummaryLogged`, last, aggregating the whole
   run's outcome counts.

`RuleRegistered` events are separate from a `StrategyEngine.run()`
call entirely — they only appear if a caller explicitly passes a
`diagnostics_sink` to `RuleRegistry.register()` at registration time
(commonly before any `StrategyEngine` or `EngineConfiguration` even
exists — see `EXECUTION_LOGGING_REPORT.md`).

## What diagnostics are for (and not for)

Diagnostics answer "what did the engine *do*" (which rules ran, in
what order, how long each took, whether anything failed) — never "what
did the engine *conclude*" in a trading sense. No event carries a
strike price, premium value, or any other business-meaningful number;
`RuleFinished.outcome_name` is the closest any event gets to a rule's
result, and it is a framework classification (`"PASS"`/`"FAIL"`/`"UNKNOWN"`/
`"INSUFFICIENT_EVIDENCE"`/`"NOT_APPLICABLE"`), not a computed value. If a
future need arises to record trading-meaningful data for
audit/replay purposes, that is a distinct concern from this milestone's
infrastructure-only diagnostics and should not be added to these event
types without a corresponding evidence-and-architecture review — see
`docs/architecture/RULE_ENGINE_ARCHITECTURE.md`'s existing separation
between Rule Results (which do carry an outcome) and this
milestone's purely operational event stream.

## How future replay/backtest will consume diagnostics

`docs/architecture/IMPLEMENTATION_ROADMAP.md`'s later milestones
(4.4+, Replay Engine and Backtest) are explicitly gated behind real
rule mathematics existing — none of that is built yet, and this
milestone does not build it either. What this milestone does provide,
ready for that future work:

1. **A stable event vocabulary.** Once a Replay Engine exists, it will
   need to reconstruct "what happened, in what order" from a
   completed run — the 8 event types defined here already capture
   exactly that lifecycle (registration → dependency resolution → per-rule
   start/finish/skip/fail → summary), so a Replay Engine's input format
   does not need to be invented from scratch; it can consume this
   event stream directly.
2. **A durable-sink extension point, not yet built.** Per
   `EXECUTION_LOGGING_REPORT.md`'s "Extension points", a future
   `ReplayDiagnosticsSink` (writing events to a file or database
   instead of memory/stdlib logging) is the natural bridge between
   "diagnostics emitted live during a run" and "diagnostics available
   for later replay analysis." The `DiagnosticsSink` protocol already
   supports this without any change to `RuleRegistry`,
   `ExecutionPipeline`, or `StrategyEngine` — a new sink class is a
   drop-in replacement for `StandardLoggingDiagnosticsSink`/
   `InMemoryDiagnosticsSink`, nothing else needs to change.
3. **Deterministic ordering, already guaranteed.** A Replay Engine
   depends on being able to trust that the same registered-rules state
   produces the same event sequence every time (see
   `RuleRegistry.execution_order()`'s deterministic tie-break, and
   this milestone's own `TestDeterministicOutput` test class) — this
   was already a requirement of Milestone 6.3's dependency ordering
   work, and this milestone's diagnostics simply expose that
   determinism as an observable event stream rather than introducing
   new non-determinism of their own (no wall-clock jitter beyond
   `context.clock()`'s own behaviour, no unordered collections used
   anywhere in the emission path).
4. **What replay will still need to add, out of this milestone's
   scope:** persistence format/schema versioning for stored events,
   a way to correlate events across multiple runs/sessions, and (once
   real rule mathematics exists) whatever trading-meaningful audit
   trail a Replay/Backtest engine needs beyond this purely operational
   event stream (see "What diagnostics are for (and not for)" above).

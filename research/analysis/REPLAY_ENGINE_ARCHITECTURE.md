# Replay Engine Architecture

Milestone B1. `trading_engine/replay/` — infrastructure for replaying
historical OHLC market data through the existing trading engine
scaffolding. No trading mathematics, no strategy implementation, no
business rules anywhere in this package.

## Architecture

```
trading_engine/replay/
    __init__.py
    exceptions.py           -- ReplayError, HistoryLoadError, ReplayStateError
    history_loader.py        -- Candle, MissingCandleGap, HistoryLoader
    replay_clock.py           -- ReplayState, ReplayClock
    replay_session.py          -- ReplayStatistics, ReplaySession
    replay_controller.py        -- ContextFactory, ReplayController
```

Six new diagnostic events were added (additively) to the existing,
reused `trading_engine/diagnostics/events.py`: `ReplayStarted`,
`ReplayPaused`, `ReplayResumed`, `ReplayStepped`, `ReplayCompleted`,
`ReplayReset`. No existing event type was modified.

## Responsibilities

**`HistoryLoader`** — reads a CSV file (columns: `Date`, `Time`,
`Open`, `High`, `Low`, `Close`, `Volume`), parses each row into an
immutable, structurally-validated `Candle`, sorts the result
chronologically, and rejects duplicate timestamps. Missing-row
detection is a separate, non-blocking method (`detect_missing_candles`)
rather than a load-time failure — see "Extension points" below for
why.

**`ReplayClock`** — a positional cursor over an immutable candle
sequence. Tracks current/next/previous candle, supports `seek()`,
`reset()`, `step_forward()`/`step_backward()`, `pause()`/`resume()`,
and a non-resumable `stop()`. Exposes `playback_speed` as a stored
value only — see "Known limitations."

**`ReplaySession`** — a thin identity/statistics wrapper around one
`ReplayClock`. Never duplicates the clock's state; every property and
`statistics()` call reads directly from the wrapped clock, so the two
can never disagree.

**`ReplayController`** — coordinates `HistoryLoader` (via
`from_csv()`), a `ReplayClock`/`ReplaySession` pair, and — only if the
caller supplies both a `strategy_engine` and a `context_factory` — a
`StrategyEngine`. Also emits every diagnostic event through an
injected `DiagnosticsSink`, reusing the diagnostics package exactly as
built in Milestone 6.4.

## Reused, unmodified components

Per the milestone's explicit instruction, none of the following had
their business behaviour changed — only imported and called:
`StrategyEngine`, `ExecutionPipeline`, `RuleRegistry`,
`EngineConfiguration`, and the `DiagnosticsSink` protocol/implementations.
`ReplayController` calls `StrategyEngine.run()` exactly as any other
caller would — it does not reach into `StrategyEngine`'s internals or
special-case replay in any way.

## The Strategy Engine integration boundary — the key design decision

`ReplayController` does **not** convert a `Candle` into a
`RuleExecutionContext` itself. Doing so would require building a
`Strike`/`MarketContext` from raw OHLC data — a conversion with no
evidenced formula anywhere in this repository (see
`research/analysis/WEEKLY_FUTURE_VERIFICATION.md`: even the upstream
Weekly Future calculation this would depend on is NOT READY).
Inventing that conversion would violate this milestone's own "No
trading mathematics" rule.

Instead, `ReplayController` accepts an optional
`context_factory: Callable[[Candle], RuleExecutionContext]` via
dependency injection. Both `strategy_engine` and `context_factory`
must be supplied together for any `StrategyEngine.run()` call to
happen on `start()`/`step()`; if either is missing, replay still works
fully as pure position-advancement infrastructure. This is the
explicit, intentional seam where a future milestone — once Candle → Strike
mathematics is evidenced — plugs in real strategy execution without
any change to `ReplayController` itself.

## Extension points

1. **Real Candle → RuleExecutionContext conversion**, once evidenced —
   the single most direct next step for connecting replay to actual
   strategy evaluation, per the boundary above.
2. **Real-time pacing of `playback_speed`.** The field is stored and
   validated (must be positive) but has no effect on `ReplayClock`'s
   own behaviour — there is no timer/sleep loop anywhere in this
   package (explicitly "No GUI" per the milestone). A future
   asyncio/threading-based pacing layer could consume
   `playback_speed` to throttle `step()` calls in real time; not built
   here since nothing in this milestone required actual wall-clock
   pacing.
3. **Missing-row detection as an opt-in policy, not a hard rule.**
   `HistoryLoader.detect_missing_candles()` uses a purely statistical
   heuristic (the sequence's own modal inter-candle interval) rather
   than a market calendar, because no market-calendar evidence exists
   in this repository and inventing one (which trading days/hours are
   "normal") would itself be a business-logic guess. A future
   milestone with evidenced market-hours data could add a
   calendar-aware variant.
4. **A `ReplayDiagnosticsSink`** persisting replay events durably,
   exactly as already flagged as an open extension point in
   `research/analysis/EXECUTION_LOGGING_REPORT.md` — the six new
   replay events flow through the exact same `DiagnosticsSink`
   protocol, so this extension point now serves both rule-execution
   and replay diagnostics uniformly.
5. **A dedicated `ReplayStopped` diagnostic event.** Milestone B1's
   Task 6 names exactly six replay event types, and `ReplayStopped` is
   not among them — `ReplayController.stop()` therefore transitions
   state without emitting a dedicated event. This is a deliberate,
   spec-faithful gap (see `research/analysis/REPLAY_ENGINE_TEST_REPORT.md`'s
   "Known limitations"), not an oversight, and would be a small,
   additive change if a future milestone asks for it.

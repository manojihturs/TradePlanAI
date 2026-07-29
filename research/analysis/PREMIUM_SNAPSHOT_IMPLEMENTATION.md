# Premium Snapshot Implementation Report

Milestone I2. `trading_engine/premium_snapshot/` — captures and stores
the first-5-minute option premium reference. Data capture only: no
Weekly Future calculation, no Strike selection, no Trend, no Winner
logic, no Entry, no Exit, no Risk logic anywhere in this package.

## Files

```
trading_engine/premium_snapshot/
    __init__.py
    exceptions.py                    -- PremiumSnapshotError, SnapshotValidationError,
                                         SnapshotCaptureError, RepositoryError, RecorderError
    premium_snapshot_models.py        -- ContractSnapshot, PremiumSnapshot
    premium_snapshot_events.py         -- re-exports the 6 new diagnostic events
                                          (defined in trading_engine/diagnostics/events.py)
    premium_snapshot_engine.py          -- PremiumSnapshotEngine, _ContractTickAggregator
    premium_snapshot_repository.py       -- PremiumSnapshotRepository (Protocol),
                                             InMemory/Csv/SqlitePremiumSnapshotRepository
    market_recorder.py                    -- TickRecord, TickRecordRepository (Protocol),
                                              InMemory/Csv/SqliteTickRecordRepository,
                                              MarketRecorder
```

6 new diagnostic events added additively to the existing, reused
`trading_engine/diagnostics/events.py`: `SnapshotStarted`,
`SnapshotCompleted`, `SnapshotStored`, `RecorderStarted`,
`RecorderStopped`, `RecorderFlushed`.

## The central design decision: events live in `diagnostics/events.py`, re-exported locally

Milestone I2 asks for a dedicated `premium_snapshot_events.py` file.
Following the precedent set by Milestones B1 (replay events) and I1
(market data events), the six new event *dataclasses* are defined in
the existing, shared `trading_engine/diagnostics/events.py` and added
to its single closed `DiagnosticEvent` union — not duplicated in a
parallel type. Two constraints make this the only sound option:

1. `DiagnosticsSink.emit()` is typed against `DiagnosticEvent`, a
   closed union. Defining new event classes anywhere else and calling
   `sink.emit(...)` with them would fail `mypy --strict` (the argument
   type would not be assignable to the union).
2. `trading_engine.diagnostics` is deliberately foundational — nothing
   in it depends on any other subsystem, and every other subsystem
   (`rules`, `engine`, `replay`, `market_data`, now `premium_snapshot`)
   depends on it, never the reverse. Defining the events in
   `premium_snapshot` and importing them back into `diagnostics` would
   invert that dependency direction.

`trading_engine/premium_snapshot/premium_snapshot_events.py` therefore
exists as the package-local *import surface* Milestone I2 asks for —
the rest of the package imports the six events from their own
package, not from `diagnostics` directly — while the actual
definitions and union membership stay in `diagnostics/events.py`.

## Another key design decision: ticks must be aggregated into OHLC

A single `MarketTick` (from Milestone I1) carries only a
last-traded-price point observation — no open/high/low/close. No
already-built "first 5-minute candle" exists anywhere upstream for a
live option contract. Capturing one therefore requires aggregating
the ticks observed during the capture window: `_ContractTickAggregator`
(private, internal to `premium_snapshot_engine.py`) tracks
first/max/min/last over the prices it sees, per contract, and is
purely mechanical — min/max/first/last over already-observed numbers,
not a trading calculation, exactly like `HistoryLoader`'s own
mechanical CSV-to-`Candle` parsing.

`PremiumSnapshotEngine` is caller-driven and synchronous, matching
this codebase's no-concurrency design: `start_capture()` opens a
window for the four core contracts (Top CE, Top PE, Bottom CE, Bottom
PE — supplied by the caller, never computed here) plus an optional
best-effort ITM/ATM/OTM range; `ingest_tick()` is called repeatedly by
whatever feeds live ticks; `complete_capture()` builds the final
`PremiumSnapshot` once the window has elapsed. A duplicate tick (same
timestamp observed twice for the same contract) is silently ignored,
not re-applied — covered explicitly by `TestDuplicateTicks`.

## Responsibilities

- **`ContractSnapshot`** — one contract's captured
  Instrument/Strike/OptionType/Timestamp/OHLC/LTP/Volume/OI. Deliberately
  distinct from the existing, deliberately-thin
  `trading_engine.domain.premium.Premium` (id/value/timestamp only,
  per `docs/architecture/DOMAIN_ARCHITECTURE.md`) — no CE/PE structure
  or capture formula is evidenced there, so this module does not
  extend or reinterpret it.
- **`PremiumSnapshot`** — the complete first-capture-window reference:
  Top/Bottom strike (caller-supplied), the four core contracts (each
  `None` if unavailable — never a failure), and best-effort range
  contracts.
- **`PremiumSnapshotEngine`** — capture lifecycle described above.
- **`PremiumSnapshotRepository`** (Protocol) — Save/Load/Latest/Historical,
  with `InMemory`/`Csv`/`Sqlite` implementations. CSV and SQLite use
  only Python standard library modules (`csv`, `sqlite3`, `json`) — no
  third-party dependency. Each snapshot is stored as one flattened
  row, with per-contract fields serialised as a JSON blob column, to
  avoid a multi-row reconstruction problem.
- **`MarketRecorder`** / **`TickRecordRepository`** — records every
  observed tick (not just the capture window) as a `TickRecord`
  (Timestamp/Spot/Strike/CE Price/PE Price/Volume/OI/Bid/Ask), via the
  same CSV/SQLite/in-memory Protocol pattern. This is the piece the
  user explicitly asked to have both CSV and SQLite backing: recording
  every tick from the start of Paper Trading is what later makes
  Replay, Backtest, Strategy Validation, and Debugging possible from
  real captured data, rather than invented data.

## Deliberate gaps, stated plainly

- **A single `MarketTick` has no Spot/Strike/CE-vs-PE distinction.**
  Combining several concurrent instruments' observations (spot, one
  strike's CE, that strike's PE) into one `TickRecord` row would
  require a join/tagging rule no document evidences. `TickRecord`
  therefore carries every field as an independently optional column,
  and `TickRecord.from_tick()` lets the caller (who already knows
  which instrument is which) supply whatever context it has, rather
  than this package inventing an auto-detection heuristic.
- **The 6-ITM/ATM/6-OTM range has zero repository evidence anywhere**
  (see `REALTIME_TRADING_SPECIFICATION.md` Section 3's own Known/UNKNOWN
  register). It is implemented as an explicit, caller-supplied,
  best-effort list of `(instrument, strike, option_type)` triples —
  never derived or inferred by this engine.
- **No strike-derivation, tick-parsing, or scheduling logic exists.**
  Exactly as in Milestone I1's `market_data` package: this engine
  receives already-resolved `InstrumentKey`s and already-parsed
  `MarketTick`s; it never talks to a broker, never computes a strike,
  and never runs on a timer — the caller decides when
  `complete_capture()`/`MarketRecorder.stop()` are invoked.

## A bug found and fixed during implementation

`InMemoryDiagnosticsSink` (from Milestone 6.4) defines `__len__`.
`diagnostics_sink or NullDiagnosticsSink()` therefore evaluated an
*empty* `InMemoryDiagnosticsSink` (length 0) as falsy and silently
substituted a null sink — no events were ever recorded in tests that
started from an empty sink. Both `PremiumSnapshotEngine.__init__` and
`MarketRecorder.__init__` were fixed to use an explicit
`diagnostics_sink is not None` check instead of truthiness. This class
of bug (falsy-but-present default-argument values) matches a defect
already fixed once before in this repository's history (see the
`Fix a default-arg late-binding bug` commit) — worth keeping in mind
for any future `x or default` pattern over an object with `__len__`
or `__bool__`.

A related bug: `MarketRecorder.flush()` originally computed how many
records were flushed by diffing `len(repository.all_records())`
before/after calling `repository.flush()`. This is correct for
`Csv`/`SqliteTickRecordRepository` (which buffer in memory and only
become visible in `all_records()` after `flush()`), but wrong for
`InMemoryTickRecordRepository`, whose `all_records()` already reflects
every appended record before `flush()` is ever called — the diff was
always zero. Fixed by having `MarketRecorder` track its own
`_pending_count` (incremented on `record()`, reported and reset on
`flush()`), independent of any repository's own storage semantics.

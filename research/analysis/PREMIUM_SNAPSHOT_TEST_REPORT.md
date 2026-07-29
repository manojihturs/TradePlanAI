# Premium Snapshot Test Report

Milestone I2. Companion to `research/analysis/PREMIUM_SNAPSHOT_IMPLEMENTATION.md`.

## Coverage

| Package/module | Statements | Missed | Coverage |
|---|---:|---:|---:|
| `trading_engine/premium_snapshot/` (7 files) | 474 | 0 | **100%** |
| `trading_engine/diagnostics/events.py` (whole file, all 25 event classes) | 302 | 0 | **100%** |
| Whole `trading_engine` suite | 6,774 | 13 | 99% (13 pre-existing misses, unrelated to this milestone) |

861 tests passing overall (15 new for the 6 premium-snapshot
diagnostic events, ~89 new across `trading_engine/premium_snapshot/`),
zero regressions in the 846 pre-existing tests.

## Test files

```
trading_engine/tests/premium_snapshot/
    __init__.py
    conftest.py                          -- fixtures (window_start/end, session_id,
                                             4 core InstrumentKeys), make_tick() helper
    test_premium_snapshot_models.py       -- ContractSnapshot/PremiumSnapshot validation
    test_premium_snapshot_engine.py        -- capture lifecycle, OHLC aggregation, missing
                                              contracts, duplicate ticks, range contracts,
                                              diagnostics
    test_premium_snapshot_repository.py     -- InMemory/Csv/Sqlite Save/Load/Latest/Historical,
                                               failure handling, malformed-row reconstruction
    test_market_recorder.py                  -- TickRecord validation, InMemory/Csv/Sqlite
                                                repositories, MarketRecorder lifecycle,
                                                diagnostics, failure handling

trading_engine/tests/diagnostics/
    test_premium_snapshot_events.py           -- the 6 new event dataclasses' validation
```

No real network, broker, or filesystem-outside-`tmp_path` I/O happens
anywhere in this suite. CSV/SQLite repository tests use pytest's
`tmp_path` fixture; failure-path tests inject `OSError`/`sqlite3.Error`
via `monkeypatch` rather than relying on real disk-full/permission
conditions.

## Test scenarios (mapped to Milestone I2's own checklist)

| Required scenario | Covered by |
|---|---|
| Snapshot timing | `TestConstruction.test_capture_window_is_configurable` (a tick just inside a non-default window is captured), `TestOHLCCapture.test_tick_outside_window_ignored` (before/after the window is rejected) |
| OHLC capture | `TestOHLCCapture.test_open_high_low_close_aggregation` — 4 ticks with distinct prices verify open=first, high=max, low=min, close/LTP=last, volume/OI=latest |
| Repository | `test_premium_snapshot_repository.py`'s parametrised `repository` fixture (`in_memory`/`csv`/`sqlite`) runs every Save/Load/Latest/Historical test against all three backends identically |
| CSV persistence | `TestCsvSpecific` — reopening a fresh repository instance against the same file round-trips a saved snapshot; write/read failure paths raise `RepositoryError` |
| SQLite persistence | `TestSqliteSpecific` — same reopen round-trip; init/save/query failure paths raise `RepositoryError` |
| Tick recording | `test_market_recorder.py`'s parametrised `repository` fixture (`in_memory`/`csv`/`sqlite`) — append/flush/all_records identical across backends; `TestMarketRecorderLifecycle` for start/record/stop |
| Snapshot retrieval | `TestLatestAndHistorical` — latest returns the most recently saved snapshot per session; historical returns every snapshot for a session, other sessions excluded, in save order |
| Diagnostics | `TestDiagnostics` (engine: `SnapshotStarted`/`SnapshotCompleted`, with correct captured/missing counts) and `TestMarketRecorderDiagnostics` (recorder: `RecorderStarted`/`RecorderFlushed`/`RecorderStopped`, including the case where `stop()`'s own internal flush produces a second `RecorderFlushed` with zero new records) |
| Failure handling | Every repository's init/write/read failure path is exercised via a real `OSError` (a directory where a file is expected) or an injected `sqlite3.Error`/`OSError` via `monkeypatch`, and asserted to raise `RepositoryError`; `MarketRecorder`'s misuse paths (`record()` before `start()`, double `start()`, `stop()` without `start()`) raise `RecorderError` |
| Missing contracts | `TestMissingContracts` — a snapshot with 1, 3, or all 4 core contracts absent builds successfully (`core_contracts()`/`missing_core_contract_count()` reflect exactly what was captured); range contracts that never receive a tick are omitted, not failed |
| Duplicate ticks | `TestDuplicateTicks.test_duplicate_timestamp_tick_ignored` — a second tick at an already-seen timestamp is rejected by `ingest_tick()` (returns `False`) and does not affect the resulting `ContractSnapshot` |

Additional coverage beyond the checklist: `TestCaptureLifecycle`
(double `start_capture()` and `complete_capture()` without a prior
`start_capture()` both raise `SnapshotCaptureError`; a capture can
restart after completing); `TestRangeContracts` (a range contract that
does receive a tick is captured and appears in `range_contracts`);
`TestRowToSnapshotMalformedData` (a CSV/SQLite row with a missing key
or invalid JSON blob raises `RepositoryError` rather than propagating
a raw `KeyError`/`JSONDecodeError`).

## Known limitations

1. **No real 09:15–09:20 market-clock integration is tested** — the
   capture window is exercised entirely against caller-supplied
   `datetime` values and a caller-driven `ingest_tick()`/`complete_capture()`
   sequence; nothing here observes a real wall clock or a live
   `MarketDataProvider`'s tick stream (that wiring is the caller's
   responsibility, matching Milestone I1's own "no scheduler" gap).
2. **No 6-ITM/ATM/6-OTM strike-derivation logic exists or is tested**,
   because none is evidenced anywhere in this repository — only that
   an explicit, caller-supplied list of range instruments is captured
   best-effort.
3. **No concurrency/thread-safety testing** — matches this codebase's
   synchronous, single-pipeline design; `PremiumSnapshotEngine` and
   `MarketRecorder` were not designed or tested for concurrent access.

## Quality Gate Report

| Gate | Result |
|---|---|
| `pytest` | **861 passed** (~104 new, 0 regressions) |
| Coverage (`trading_engine/premium_snapshot/` + `diagnostics/events.py`) | **100%** — 776/776 statements, 0 missed |
| Coverage (whole suite) | 99% — 13 pre-existing misses outside this milestone's scope, unrelated to Milestone I2 |
| `mypy --strict` (`trading_engine/premium_snapshot`, `trading_engine/diagnostics`) | Clean — 11 source files. (The project's own `pyproject.toml` `[tool.mypy] files` list is scoped to `domain`/`rules`/`engine`/`calculators` only, and was never expanded for `market_data`/`replay`/`diagnostics` in earlier milestones either — this report follows the same explicit-directory convention Milestone I1 used.) |
| `ruff check` | Clean |
| `black --check` | Clean |

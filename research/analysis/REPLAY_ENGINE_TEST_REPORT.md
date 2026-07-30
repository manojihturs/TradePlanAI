# Replay Engine Test Report

Milestone B1. Companion to `research/analysis/REPLAY_ENGINE_ARCHITECTURE.md`.

## Coverage

| Package | Statements | Missed | Coverage |
|---|---:|---:|---:|
| `trading_engine/replay/` | 304 | 0 | **100%** |
| `trading_engine/diagnostics/` (incl. 6 new replay events) | 208 | 0 | **100%** |
| Whole `trading_engine` suite (all 6 packages) | 1,315 | 0 | **100%** |

660 tests passing overall (108 new for `trading_engine/replay/`, 12 new
for the replay diagnostic events), zero regressions in the
552 pre-existing tests.

## Test files

```
trading_engine/tests/replay/
    __init__.py
    conftest.py               -- Candle/CSV-row builders, fixtures
    test_history_loader.py     -- Candle validation, CSV loading, ordering,
                                    duplicates, missing-candle detection
    test_replay_clock.py        -- construction, navigation, seek, reset,
                                    start/pause/resume/stop, step forward/backward
    test_replay_session.py       -- identity, delegated properties, statistics
    test_replay_controller.py     -- navigation, lifecycle, StrategyEngine
                                      integration, diagnostics emission

trading_engine/tests/diagnostics/
    test_replay_events.py      -- the 6 new event dataclasses' validation
```

## Test scenarios (mapped to Milestone B1's Task 7 checklist)

| Required scenario | Covered by |
|---|---|
| Loader validation | `TestCandleConstructorValidation`, `TestLoadCsvValidation` |
| Replay Clock | `TestConstructorValidation`, `TestCurrentNextPrevious`, `TestStartStopPauseResume`, `TestStepForward`, `TestStepBackward` |
| Replay Controller | `TestConstruction`, `TestBasicNavigation`, `TestPauseResumeStopRestartReset`, `TestStrategyEngineIntegration` |
| Replay Session | `TestConstruction`, `TestDelegatedProperties`, `TestStatistics` |
| Diagnostics | `TestDiagnosticsEmission` (controller-level), `test_replay_events.py` (event-level) |
| CSV validation | `TestLoadCsvValidation` — missing file, no header, missing column, unparsable Date/Time/price/volume, blank Date, structurally invalid row |
| Duplicate timestamps | `TestDuplicateTimestampDetection` |
| Missing candles | `TestMissingCandleDetection` — regular interval (no gaps), a real gap, fewer-than-3-candles edge case, non-positive-modal-delta edge case |
| Seek | `TestSeek` — mid-sequence, sets RUNNING, sets COMPLETED at last index, out-of-bounds (negative and beyond-end) both raise |
| Step | `TestStepForward`, `TestStepBackward` — normal advance/retreat, completion transition, past-end/past-start raise, blocked while PAUSED/STOPPED |
| Reset | `TestReset` (clock-level), `TestPauseResumeStopRestartReset::test_reset_returns_to_start_and_clears_reports` (controller-level, also clears accumulated `ExecutionReport`s) |

## Known limitations

1. **`playback_speed` has no runtime effect.** Stored and validated
   (must be positive) but not used to pace `step()` calls in real
   time — there is no timer/sleep loop in this package. See
   `REPLAY_ENGINE_ARCHITECTURE.md`'s "Extension points" #2.
2. **No dedicated `ReplayStopped` diagnostic event.** `stop()` changes
   `ReplayClock`'s state to `STOPPED` but emits nothing — Milestone
   B1's Task 6 names exactly six event types and `ReplayStopped` is
   not one of them. Verified explicitly by
   `test_stop_emits_no_dedicated_event` (asserts the sink's length is
   unchanged after `stop()`), so this is a confirmed, intentional
   behaviour, not an untested gap.
3. **Missing-row detection cannot distinguish a data error from a
   legitimate market closure.** `detect_missing_candles()` flags any
   gap exceeding 1.5× the sequence's own modal inter-candle interval —
   a purely statistical heuristic with no market-calendar awareness
   (no such evidence exists in this repository). A real overnight/weekend
   gap in daily data would currently be flagged the same way as a
   genuine missing row. This is documented, not silently assumed away.
4. **`Candle` OHLC validation is structural only.** `high >= low` and
   `open`/`close` within `[low, high]` are enforced (mirroring the
   domain layer's existing "structural validation only" discipline —
   e.g. `Strike.price > 0`), but nothing checks price continuity
   between consecutive candles, unusual volume spikes, or any other
   data-quality signal beyond per-candle internal consistency and
   sequence-level duplicate/gap detection.
5. **No real Candle → RuleExecutionContext conversion exists.**
   `ReplayController`'s `strategy_engine`/`context_factory` integration
   is fully tested (`TestStrategyEngineIntegration`) using a
   deliberately minimal, evidence-free test-only converter — this
   confirms the *wiring* works, not that any particular
   candle-to-context mapping is correct, since no such mapping is
   evidenced anywhere in the repository (see
   `REPLAY_ENGINE_ARCHITECTURE.md`'s integration-boundary section).

## Quality Gate Report

| Gate | Result |
|---|---|
| `pytest` | **660 passed** (120 new, 0 regressions) |
| Coverage | **100%** — 1,315/1,315 statements, 0 missed |
| `mypy --strict` | Clean — 51 source files |
| `ruff check` | Clean |
| `black --check` | Clean |

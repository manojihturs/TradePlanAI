# Architecture Review — Pre-Weekly-Future Audit

**Scope:** `src/` and `tests/` as they exist after Sprint 4 (`core`, `models`, `events`, `trade_manager`, `replay`, `interfaces`, `position_manager`, `winner_engine`, `entry_engine`, `event_recorder`, `trade_history`, `exit_engine`, `reference_builder` — 13 packages, 253 tests, 100% statement+branch coverage, `mypy --strict`/`ruff`/`black` all clean, verified zero circular dependencies).

**Method:** every finding below was checked directly against the current source (grep/read), not recalled from memory of writing it. No code was modified. No commits were made. This document reports only issues actually present in the code today — where something is already well designed, that is stated explicitly rather than left unsaid.

**Severity scale:** Critical (will corrupt data or crash in normal use) / High (will bite the moment a nearby feature is added — fix before Sprint 5) / Medium (real but contained, safe to defer one or two sprints) / Low (stylistic/future-proofing, fix opportunistically).

---

## Findings

### 1. [High] ✅ FIXED — Inconsistent clock defaults will reproduce the naive/aware datetime bug that already occurred once

**Where:** `trade_manager/trade_manager.py:47`, `entry_engine/entry_engine.py:58`, `winner_engine/winner_engine.py:60`, `replay/replay_engine.py:45` all default `clock` to `datetime.now` (naive, no `tzinfo`) when no clock is injected.

**Why it matters:** every test in this codebase constructs `datetime` values with `tzinfo=UTC`, and this exact mismatch already produced a real, caught bug during Sprint 3 development: `TradeManager`'s default naive clock, combined with a tz-aware `opened_at`, raised `TypeError: can't subtract offset-naive and offset-aware datetimes` inside `TradeRecord.from_position()`'s `closed_at - opened_at` computation. That specific instance was fixed by injecting a matching clock into the *test fixture* — the production default (`datetime.now`, naive) was never changed. Any live/replay run that doesn't explicitly inject a tz-aware clock into every one of these four classes will hit the same class of failure the first time a duration or comparison mixes a default-clock timestamp with a market-data timestamp (which will be tz-aware in any real feed).

**Recommended fix:** either (a) standardize on `datetime.now(UTC)` (or an injected `tz`) as the shared default across all four call sites, or (b) make `clock` a required constructor argument everywhere instead of defaulting to a bare `datetime.now`, forcing callers to make a deliberate timezone choice. Option (a) is less invasive.

**Fix before Sprint 5?** **Yes.** This is a landmine that has already gone off once in tests; leaving it in place means the same failure mode will resurface in `weekly_future/`, `strike_selector/`, and every later engine that follows the same `clock: Clock | None = None` pattern (which all of them will, since it's the established convention).

**Resolution (applied):** added `core.protocols.utc_now()` — the single, shared, timezone-aware (`datetime.now(UTC)`) default every injectable-clock class now uses. `TradeManager`, `EntryEngine`, `WinnerEngine`, and `ReplayEngine` all updated to default to `utc_now` instead of the bare `datetime.now` builtin; unused `datetime` imports removed from the three files that no longer needed them directly. Verified: no class in `src/` still defaults to `datetime.now` (grep-confirmed), the default clock now produces a timezone-aware timestamp, and the full suite (256 tests, up from 253 — 3 new tests added for `utc_now` itself) passes at 100% coverage with `mypy --strict`/`ruff`/`black` clean and zero circular dependencies.

---

### 2. [Medium] TradeHistory storage is coupled to ExitEngine, not to TradeClosedEvent itself

**Where:** `exit_engine/exit_engine.py`'s `_close()` method calls `self._trade_history.add_trade(closed)` only if a `TradeHistory` instance was optionally injected into *that specific* `ExitEngine`. `TradeHistory` itself has no subscription to the event bus at all — it is a plain in-memory store with no `EventBusProtocol` dependency.

**Why it matters:** Sprint 3's own instruction was "Every `TradeClosedEvent` should automatically store the completed trade" — worded as an event-driven guarantee. What's actually built is a guarantee that holds *only* if every trade is closed through this one `ExitEngine` instance with `trade_history` populated. If a future sprint adds any other way to close a position (a manual override, a kill-switch, a differently-wired live-trading path), that trade silently never reaches `TradeHistory` — there is no safety net at the event level.

**Recommended fix:** either have `TradeHistory` itself subscribe to `TradeClosedEvent` on an injected bus (requires the event to carry enough data to build a `TradeRecord`, which it currently doesn't — see Finding 5), or keep the current design but document plainly that `TradeHistory` population is `ExitEngine`'s responsibility alone, not a bus-level guarantee, so nobody assumes otherwise later.

**Fix before Sprint 5?** No — `weekly_future/` doesn't touch this path. Worth deciding before a second trade-closing code path is ever introduced (Sprint 6+ live trading is the likely trigger).

---

### 3. [Medium] TradeHistory has no session-scoping; ReferenceRepository does

**Where:** `reference_builder/reference_repository.py`'s `ReferenceRepository` is explicitly keyed by `session_id: uuid.UUID` (`dict[uuid.UUID, tuple[ReferenceLevel, ...]]`). `trade_history/trade_history.py`'s `TradeRecord` has no `session_id` field at all, and `TradeHistory` is a flat, unscoped list.

**Why it matters:** this is a genuine inconsistency between two repository-shaped classes built in adjacent sprints. `filter_by_date()` on `TradeHistory` can approximate session grouping by calendar date, but that's a weaker, indirect substitute for an explicit key — and it will not work cleanly for a session that spans midnight in any timezone edge case, or for two sessions on the same date (unlikely for this instrument, but not structurally prevented). Multi-day backtesting (an explicitly planned future capability per `research/architecture/IMPLEMENTATION_ROADMAP.md` Phase 12) will want to group trades by session, not just by date.

**Recommended fix:** add `session_id: uuid.UUID` to `TradeRecord` (sourced from wherever the session id is available at trade-open time — currently `WinnerDetectedEvent`/`TradeOpenedEvent` both carry it) and add a `filter_by_session()` method to `TradeHistory`, mirroring `ReferenceRepository`'s existing pattern.

**Fix before Sprint 5?** No — not needed until backtest/multi-session work begins. Flagging now because it's cheap to fix today and progressively more disruptive (a breaking model change) the more `TradeRecord` gets used downstream.

---

### 4. [Medium] Only EventBus has a Protocol; TradeManager, PositionManager, and TradeHistory are depended upon by concrete class

**Where:** `position_manager/position_manager.py:50` types its constructor parameter as `trade_manager: TradeManager` (the concrete class). `entry_engine/entry_engine.py:50` and `exit_engine/exit_engine.py:69` both type `position_manager: PositionManager` (concrete). `exit_engine/exit_engine.py:73` types `trade_history: TradeHistory | None` (concrete). Verified: no `Protocol` exists anywhere in `src/` for any of `TradeManager`, `PositionManager`, or `TradeHistory` (grep confirms every `class *Protocol` definition lives in `core/events.py`, `core/protocols.py`, `events/publishers.py`, `events/subscribers.py`, and `interfaces/*.py` only).

**Why it matters:** the project's own stated principle (both in your Sprint 1 instructions and consistently applied for `EventBusProtocol`/`Clock`/`IdFactory`) is dependency injection *against an abstraction*. For `EventBus` that principle is followed exactly. For `TradeManager`/`PositionManager`/`TradeHistory` it isn't — every consumer is coupled to the concrete implementation. In practice this has caused no test friction yet (there is exactly one implementation of each, and tests construct real instances rather than fakes), so it is not currently causing pain — but it is a real, checkable inconsistency in how strictly DIP is applied across the codebase, and it will matter the moment a second implementation is wanted (e.g. a `PositionManager` variant for a paper-trading mode, or mocking `TradeHistory` in a test without touching real `TradeManager`/`PositionManager` construction).

**Recommended fix:** define minimal Protocols (`TradeManagerProtocol`, `PositionManagerProtocol`, `TradeHistoryProtocol`) in the same style as `EventBusProtocol`, covering only the methods actually called by consumers, and re-type the constructor parameters against them. This is a pure, low-risk addition — no behavior changes, existing concrete classes already satisfy the new Protocols structurally.

**Fix before Sprint 5?** No — genuinely optional. Flagging as Medium because "consistent Protocol usage" was an explicit, repeated instruction across every sprint, and this is the one place it wasn't followed through.

---

### 5. [Medium] Touch-detection geometry is duplicated between WinnerEngine and ExitEngine

**Where:** `winner_engine/winner_engine.py:116` (`_touches_any`) and `exit_engine/exit_engine.py:136` (`_touches`) both implement the same "does this candle's `[low, high]` range include this reference-level value" check, independently, with slightly different signatures (one takes `*levels: Decimal` for a pair, the other takes a single `strike` and looks up the level itself).

**Why it matters:** this is the same geometric primitive (candle-touches-level) used for two different purposes today. It isn't a bug — both implementations are individually correct and fully tested — but it's the textbook shape of future drift: if the "touch" definition ever needs a tweak (e.g. to handle a boundary-inclusive/exclusive edge case, or to switch from range-touch to close-only-touch), there are now two places to find and update, and nothing enforces they stay identical. `TPEngine`/`QualificationEngine` (Sprint 7-8, per your own revised roadmap) will very likely need this exact same primitive a third time.

**Recommended fix:** extract a small, pure function (e.g. `core/touch.py` or similar) — `def level_touched(snapshot: MarketSnapshot, *levels: Decimal) -> bool` — and have both `WinnerEngine` and `ExitEngine` call it. Low risk, mechanical refactor; the two existing implementations are already behaviorally identical, so this is a pure de-duplication, not a behavior change.

**Fix before Sprint 5?** No — `weekly_future/` doesn't need this primitive. Worth doing before `tp_engine/`/`qualification_engine/` (Sprint 7-8) if this touch-based approach carries forward there, to avoid a third copy.

---

### 6. [Medium] `core.state_machine.StateMachine` is fully built and tested but never integrated

**Where:** `core/state_machine.py` — confirmed by grep that `StateMachine(` is never instantiated anywhere in `src/` outside its own file. `TradeManager`, `PositionManager`, `EntryEngine`, and `ExitEngine` all track "is a trade active" via `TradePosition.status` (an enum field) and `TradeManager._active` (`TradePosition | None`) directly, never through the `StateMachine` class built in Sprint 1 for exactly this purpose.

**Why it matters:** this isn't dead code in the sense of being unreachable or untested (it has 100% coverage via its own dedicated test file) — but it is an unintegrated component. The actual session-lifecycle state today is implicit and distributed (a `None`-check here, a `TradeState` enum comparison there) rather than flowing through the single `StateMachine` object that was explicitly built, per Sprint 1's own instructions, to be the Idle→Ready→TradeActive→TradeClosed→Ready authority. Two things can happen from here: either `StateMachine` gets wired in properly (e.g. `TradeManager` calls `transition()` on open/close instead of just mutating `_active`), or it's acknowledged as a Sprint-1 artifact that the actual design evolved past, and either removed or explicitly kept as a future integration point.

**Recommended fix:** no code change recommended by this review — this is a decision to make, not a defect to patch. If the intent is for `StateMachine` to eventually gate transitions (e.g. reject `TradeManager.open()` if not in a valid state), wire it in now, before more engines are added that would each need to remember to check it. If the current implicit-state approach is intentionally preferred, say so and drop `StateMachine` from the "used" mental model to avoid future confusion about which one is authoritative.

**Fix before Sprint 5?** No, but worth an explicit decision before Sprint 5, since Weekly Future is the first business engine expected to actually respond to session-lifecycle events (`WeeklyFutureCalculated` firing at a specific state).

---

### 7. [Low] Exception messages are matched by substring in tests, not by distinct exception subtypes

**Where:** every test file uses `pytest.raises(ValidationError, match="...")` with a specific message fragment to distinguish between different failure reasons (e.g. `ReferenceValidator`: "Expected exactly 13 strikes" vs. "duplicate strikes" vs. "is not candle-mode" are three different failure modes, all raised as the same `ValidationError` type).

**Why it matters:** `ValidationError` is deliberately broad (it covers "this data is structurally wrong" across every model and validator in the system) — that's a reasonable design choice, not a mistake, and it matches this project's own established convention from the very first sprint. The cost is that any caller who wants to programmatically distinguish *why* validation failed (as opposed to just "did it fail") must parse the exception's message string, which is inherently more brittle than a `match`/`isinstance` check against a distinct subtype would be. This has not caused any real problem yet — it's a maintainability note, not a bug.

**Recommended fix:** no immediate action. If a future caller genuinely needs to branch on failure *reason* (not just failure/success), that's the signal to introduce more granular `ValidationError` subclasses at that point — doing it preemptively now would be speculative.

**Fix before Sprint 5?** No.

---

### 8. [Low] Repository-shaped classes use inconsistent method names across packages

**Where:** `ReferenceRepository` exposes `save`/`get`/`clear`. `TradeHistory` exposes `add_trade`/`get_trade`/`get_all`/`clear`. `EventRecorder` exposes `record`/`get_events`/`clear`. All three are "store things, retrieve things" collaborators, but none share a common naming pattern beyond `clear`.

**Why it matters:** purely a readability/onboarding cost — each is individually well-named for its own domain (`add_trade` reads better than a generic `save` for a trade, for instance), so this isn't wrong, just inconsistent as a *family* of similar-shaped classes. No functional risk.

**Recommended fix:** none required. If a shared `Repository[T]` Protocol is ever introduced (see Finding 4), that would be the natural point to also standardize naming — not worth a dedicated pass on its own.

**Fix before Sprint 5?** No.

---

### 9. [Low] `ReferenceValidator`/`ExitEngine`'s strike lookups are linear scans

**Where:** `exit_engine/exit_engine.py:150` (`_level_for`) does a linear `for level in self._reference_levels: if level.strike == strike` scan; `ReferenceRepository` and `ReferenceValidator` similarly iterate rather than index.

**Why it matters:** with a fixed 13-strike ladder (confirmed structural size, Specification Section 6), this is O(13) worst case — functionally irrelevant. Flagged only because if this lookup pattern is copy-pasted into a future engine that runs per-tick rather than per-candle, or against a larger structure, the cost profile changes. Not a concern at current scale.

**Recommended fix:** none required now. If/when a hot path needs this, switch the ladder to a `dict[Decimal, ReferenceLevel]` internally.

**Fix before Sprint 5?** No.

---

### 10. [Low] `EventRecorder.get_events()` and every filter re-sort the full event list on every call

**Where:** `event_recorder/event_recorder.py:80-81` (`_ordered()`) calls `sorted(self._events, ...)` fresh on every invocation of `get_events()`/`filter_by_type()`/`filter_by_trade()`/`filter_by_time_range()`, rather than maintaining a pre-sorted structure or caching the sort.

**Why it matters:** for a single trading session's worth of events (dozens to low hundreds), this is trivially fast — not a real performance problem today. It would only matter if `EventRecorder` were queried in a tight loop across a very large recorded history (e.g. a multi-day backtest replaying thousands of sessions' events through one recorder instance). Also worth noting as a *design* point, not just performance: because publish order already equals chronological order in every current single-clock scenario (the only way ties/reordering can occur is via direct out-of-order `record()` calls, which the test suite exercises deliberately), the sort is mostly a correctness safety net for an edge case rather than doing real reordering work in the common path.

**Recommended fix:** none required now. If profiling ever shows this mattering, insert in sorted-position on `record()` instead of sorting on every read.

**Fix before Sprint 5?** No.

---

## Explicitly well-designed — no issue found

To satisfy the instruction not to report only complaints: the following areas were reviewed against the same checklist and found solid, with no changes recommended.

- **Layering / circular dependencies:** independently re-verified (AST-based import graph across all 13 packages) — zero cycles, and the dependency direction consistently matches the intended layering (`core` foundational; `models`/`events` depend only on `core`; every engine depends downward only, never sideways/upward).
- **Immutability / Position lifecycle:** `TradePosition` is a frozen dataclass; `close()` returns a new instance rather than mutating in place, and its own `__post_init__` enforces that active positions carry no `exit_reason`/`closed_at` and closed positions must carry both. This is correctly and consistently enforced everywhere the model is constructed.
- **Trade lifecycle / single-active-trade invariant:** enforced in exactly one place (`TradeManager`), and every other module (`PositionManager`, `EntryEngine`, `ExitEngine`) reads that single source of truth rather than tracking its own copy — this is the correct centralization and was followed through consistently across three sprints.
- **Replay determinism:** every engine that produces a timestamp or an ID accepts an injected `Clock`/`IdFactory`, and `ReplayEngine` itself contains no real-time or random dependency. Aside from Finding 1's *default* being naive, the injection mechanism itself is sound and consistently applied.
- **Thread-safety:** the entire system is explicitly, consistently documented as single-threaded/synchronous (`EventBus`, `InMemoryDiagnosticsSink`-style docstrings throughout), and nothing in the reviewed code contradicts that — no shared mutable state is accessed from more than one execution context anywhere in this codebase today. This is a documented design constraint, correctly upheld, not an oversight.
- **Memory leaks:** none found. `EventRecorder`/`TradeHistory` grow unboundedly across a long-running session by design (they are the history), which is expected behavior for this stage of the project, not a leak — flagged here only as a forward-looking note, not a current defect, since nothing yet caps their growth for a hypothetical very-long-running live process.
- **Event ordering:** within a single publish, handlers run in subscription order, then wildcard handlers — documented and tested. Across the whole event stream, `EventRecorder` sorts by `occurred_at` for retrieval, giving a well-defined chronological view regardless of subscription/publish order.
- **Test quality:** tests consistently assert on business-meaningful outcomes (e.g. exact Target/Support/Competitor-Exit strike values per the confirmed Rule 2 mapping, not just "no exception raised"), and every module's negative/edge-case paths are exercised, not just the happy path — coverage numbers here reflect genuine behavioral testing, not coverage-chasing.
- **Extensibility for unresolved business rules:** the `interfaces/` package's Protocol-only stubs (`WeeklyFutureCalculator`, `StrikeSelector`, `TPEngine`, `QualificationEngine`, `StopLossEngine`, `TrailingStopEngine`) are structurally ready to receive real implementations without any consuming code needing to change — `ExitEngine` already calls `StopLossEngine.check()`/`TrailingStopEngine.check()` polymorphically today, so a real implementation is a drop-in.

---

## Summary table

| # | Finding | Severity | Fix before Sprint 5? |
|---|---|---|---|
| 1 | Naive default clocks (`datetime.now`) across 4 classes | High | **Yes — fixed** |
| 2 | `TradeHistory` storage coupled to `ExitEngine`, not to the event | Medium | No |
| 3 | `TradeHistory`/`TradeRecord` has no session scoping | Medium | No |
| 4 | `TradeManager`/`PositionManager`/`TradeHistory` depended on by concrete class, not Protocol | Medium | No |
| 5 | Touch-detection logic duplicated in `WinnerEngine` and `ExitEngine` | Medium | No (before Sprint 7-8) |
| 6 | `StateMachine` built, tested, never integrated | Medium | Decision needed, not code |
| 7 | Broad `ValidationError` matched by message substring in tests | Low | No |
| 8 | Inconsistent repository method naming across packages | Low | No |
| 9 | Linear strike-ladder lookups | Low | No |
| 10 | `EventRecorder` re-sorts on every read | Low | No |

**Finding 1 has been fixed** (see its "Resolution" note above) — it was the only finding recommended for action before Sprint 5. All other findings remain open by design (correctly deferred, per their own "Fix before Sprint 5?" answers of No).

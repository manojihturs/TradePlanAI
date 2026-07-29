# Business Rule Integration Guide

**Status at time of writing:** Framework COMPLETE (Sprints 1–4, tagged `v0.4.1-framework-stable`). Business logic BLOCKED pending an authoritative Weekly Future specification (see `WEEKLY_FUTURE_BLOCKER_REPORT.md`). This guide describes how each still-blocked business engine plugs into the existing, frozen framework — it does not implement anything, modify anything, or guess at any trading rule.

Every interface signature quoted below was copied directly from the current source in `src/interfaces/` (verified against the files, not recalled from memory) at the time of writing. If the framework changes after this document is written, this document — not the code — is what's stale; treat the source as authoritative.

---

## Section 1 — Current Architecture

The execution pipeline, as built through Sprint 4, with pending stages marked:

```
ReplayEngine (src/replay/)
    │  yields MarketSnapshot candles, publishes MarketOpenEvent/MarketCloseEvent
    ▼
ReferenceBuilder (src/reference_builder/)
    │  builds 13-level ReferenceLevel ladder from first-5-min-candle CE/PE OHLC
    │  (caller supplies the 13 strikes - selection itself is downstream, see below)
    ▼
┌─────────────────────────────────────────────────────────┐
│ (WeeklyFutureCalculator - PENDING, interfaces/weekly_future_calculator.py)
│      ▼
│ (StrikeSelector - PENDING, interfaces/strike_selector.py)
│      ▼
│ (TPEngine - PENDING, interfaces/tp_engine.py)
│      ▼
│ (QualificationEngine - PENDING, interfaces/qualification_engine.py)
└─────────────────────────────────────────────────────────┘
    ▼
WinnerEngine (src/winner_engine/)
    │  evaluate(session_id, candle_timestamp, strike, level, ce_snapshot, pe_snapshot)
    │  publishes WinnerDetectedEvent
    ▼
EntryEngine (src/entry_engine/)
    │  subscribes to WinnerDetectedEvent, builds TradeSignal
    ▼
PositionManager (src/position_manager/)
    │  computes Target/Support/Competitor-Exit strikes (Specification Rule 2, CONFIRMED)
    │  delegates single-active-trade gate to TradeManager (src/trade_manager/)
    ▼
ExitEngine (src/exit_engine/)
    │  checks Target/Competitor (built-in) + StopLossEngine/TrailingStopEngine (PENDING)
    │  closes via PositionManager -> TradeManager (publishes TradeClosedEvent)
    ▼
TradeHistory (src/trade_history/)
       stores completed trades (PnL placeholder, not calculated)

Independently, off to the side:
EventRecorder (src/event_recorder/) - wildcard-subscribes to the bus, captures every
    event published anywhere in the pipeline above, for replay/audit/debugging.
```

**Important structural fact:** `WinnerEngine`, `EntryEngine`, `PositionManager`, and `ExitEngine` are already fully built, tested, and 100%-covered *today*, against caller-supplied strikes and a caller-supplied `ReferenceLevel` ladder. They do not need to change when `WeeklyFutureCalculator`/`StrikeSelector`/`TPEngine`/`QualificationEngine` are implemented — those four modules only need to *produce* the strikes and ladder that `winner_engine.evaluate()` and `entry_engine`'s injected `reference_levels` already consume. This is why the framework is described as "complete": every consumer of the pending modules' output already exists and works.

---

## Section 2 — Blocked Interfaces

### 2.1 `WeeklyFutureCalculator` (`src/interfaces/weekly_future_calculator.py`)

```python
class WeeklyFutureCalculator(Protocol):
    def calculate(self, first_five_minute_candle: MarketSnapshot) -> WeeklyFuture: ...
```

- **Purpose:** Compute the session's Weekly Future High and Low.
- **Inputs:** One `MarketSnapshot` — the first 5-minute candle (09:15–09:20). Must be candle-mode (`is_candle() == True`, i.e. OHLC populated).
- **Outputs:** One `WeeklyFuture` (`models/weekly_future.py`: `weekly_future_id`, `session_id`, `high`, `low`, `calculated_at`). Note: `WeeklyFuture` currently has **no `close` field** — see Section 4's note on this.
- **Current Protocol status:** structural shape only; every real implementation must raise `core.exceptions.UnresolvedBusinessRuleError` until the formula is resolved (matches the convention every other stub in this package already follows).
- **Expected behaviour once resolved:** a pure function of the given candle (plus whatever additional inputs the recovered specification turns out to require — see `WEEKLY_FUTURE_BLOCKER_REPORT.md` Section 3 for the confirmed input list, and Section 8 for what's still unknown even about the input shape).
- **Required business rule:** the Weekly Future High/Low formula. **Not resolvable from existing evidence** — see `WEEKLY_FUTURE_BLOCKER_REPORT.md` in full. This is the actual blocker for the whole pipeline.
- **Modules depending on it:** `StrikeSelector` (direct input), and transitively everything downstream of that (`TPEngine`, `QualificationEngine`, and the live/replay use of `WinnerEngine` onward, which today only run against caller-supplied test strikes).

### 2.2 `StrikeSelector` (`src/interfaces/strike_selector.py`)

```python
class StrikeSelector(Protocol):
    def select(
        self, session_id: uuid.UUID, weekly_future: WeeklyFuture, selected_at: datetime
    ) -> StrikeSelection: ...
```

- **Purpose:** Select the session's Top Strike and Bottom Strike (both "ATM").
- **Inputs:** `session_id`, the session's `WeeklyFuture` (from 2.1), a timestamp.
- **Outputs:** One `StrikeSelection` (`models/strike.py`: `session_id`, `top_strike`, `bottom_strike`, `selected_at`). Note: the model does **not** currently reject `top_strike == bottom_strike` — that case is untested because it's unconfirmed whether it can occur.
- **Expected behaviour once resolved:** derive Top/Bottom Strike from Weekly Future High/Low per whatever ATM/rounding rule is confirmed.
- **Required business rule:** the ATM selection rule and strike-rounding basis. Not specified anywhere in current evidence (Specification Section 20 item 2, Critical).
- **Modules depending on it:** `ReferenceBuilder` needs the resulting strikes to build its 13-level ladder in a live/replay run (today, `ReferenceBuilder` is tested against caller-supplied strike lists directly, bypassing this). `TPEngine`, `WinnerEngine`'s live use.

### 2.3 `TPEngine` (`src/interfaces/tp_engine.py`)

```python
class TPEngine(Protocol):
    def update(self, snapshot: MarketSnapshot, levels: tuple[ReferenceLevel, ...]) -> object: ...
```

- **Purpose:** Continuously compute TP High (Top Strike)/TP Low (Bottom Strike) qualification state.
- **Inputs:** A `MarketSnapshot` (candle or tick — cadence itself is unresolved) and the session's 13-level `ReferenceLevel` ladder.
- **Outputs:** Deliberately typed `object`, **not** a concrete model. Whether "TP" is a price, a boolean qualified/unqualified flag, or both is itself unresolved (Specification Section 20 item 13) — no `TPState` model exists in `models/` yet. **The first sub-task of implementing this interface is deciding this output shape and adding the corresponding model**, not just filling in the method body.
- **Required business rule:** the TP Engine's competitor-strike identity for its own qualification test. Explicitly **not** the same as `ExitEngine`'s already-confirmed competitor mapping (Specification Rule 2) — that mapping is for a different purpose (Exit monitoring of an already-open trade), and nothing in the specification confirms TP Engine's pre-Winner qualification test uses the same S±1 pattern. Do not assume it does when this is eventually implemented.
- **Modules depending on it:** `QualificationEngine` (direct input), `WinnerEngine`'s live use (today `WinnerEngine.evaluate()` takes CE/PE snapshots directly and doesn't consume `TPEngine`'s output at all — how TP state feeds into which strikes get evaluated for Winner detection is itself part of what's unresolved).

### 2.4 `QualificationEngine` (`src/interfaces/qualification_engine.py`)

```python
class QualificationEngine(Protocol):
    def evaluate(self, tp_state: object) -> bool: ...
```

- **Purpose:** Evaluate whether a strike's TP is currently "qualified" (sustaining against its competitor level).
- **Inputs:** `tp_state`, typed `object` for the same reason as 2.3 — its real shape depends on how `TPEngine` is implemented.
- **Outputs:** `bool`.
- **Required business rule:** depends on the same competitor-identity gap as `TPEngine` (2.3), plus external-invalidation handling (news/budget/war/natural disaster — Specification Section 7 names this scenario explicitly but gives no detection mechanism at all).
- **Modules depending on it:** conceptually feeds `WinnerEngine`'s live use, though (as with `TPEngine`) the exact wiring between Qualification state and Winner detection is not yet defined anywhere.

### 2.5 `StopLossEngine` (`src/interfaces/stop_loss_engine.py`)

```python
class StopLossEngine(Protocol):
    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool: ...
```

- **Purpose:** Evaluate whether an active `TradePosition` has hit its Stop Loss.
- **Inputs:** The active `TradePosition`, a `MarketSnapshot`.
- **Outputs:** `bool`.
- **Current integration status:** **already wired in.** `ExitEngine.evaluate()` calls `self._stop_loss_engine.check(position, target_snapshot)` today, as its third of four exit checks (after Target, after Competitor, before Trailing Stop) — see `src/exit_engine/exit_engine.py`. This means implementing `StopLossEngine` for real is a pure drop-in: no `ExitEngine` code needs to change.
- **Required business rule:** the entire Stop Loss rule — price basis, placement, trigger condition. Not stated anywhere in current evidence (Specification Section 20 item 4, Critical — the single largest unstated rule after Weekly Future itself).
- **Modules depending on it:** `ExitEngine` only.

### 2.6 `TrailingStopEngine` (`src/interfaces/trailing_stop_engine.py`)

```python
class TrailingStopEngine(Protocol):
    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool: ...
```

- **Purpose:** Evaluate whether an active `TradePosition` has hit its Trailing Stop.
- **Inputs/Outputs:** identical shape to `StopLossEngine` (2.5).
- **Current integration status:** **already wired in**, as `ExitEngine`'s fourth and final check, after Stop Loss.
- **Required business rule:** trail activation trigger, trail step/distance, and the brokerage/exchange/tax figures needed to compute the one confirmed fact — a minimum net +3 premium points after costs (Specification Section 13). The "+3 net" guarantee itself is confirmed; everything needed to compute it numerically is not.
- **Modules depending on it:** `ExitEngine` only.

---

## Section 3 — Integration Sequence

**Recommended order, and why:**

1. **`WeeklyFutureCalculator`** — the root of the dependency chain (Section 1's diagram). Nothing else can be honestly implemented before this, since Strike Selection's input is this module's output.
2. **`StrikeSelector`** — immediately next; it's the only other module blocking `ReferenceBuilder`'s live (non-test) use, and `ReferenceBuilder` itself is otherwise already complete.
3. **`TPEngine`** — needs strikes (from 2) and the reference ladder (already available from `ReferenceBuilder`). Also needs its own output shape decided as part of implementation (Section 2.3).
4. **`QualificationEngine`** — depends directly on `TPEngine`'s now-defined output shape.
5. **`StopLossEngine`** and **`TrailingStopEngine`** (either order between these two — they're independent of each other and of 1–4) — these can technically be implemented at any point once their own business rules are resolved, since `ExitEngine` already calls them; there is no reason to wait for 1–4 to finish first if Stop Loss evidence arrives before Weekly Future evidence does.

**Why this order minimizes risk:** each step's business rule is a hard prerequisite for validating the next step's correctness (you cannot check `StrikeSelector`'s output against real data without a real `WeeklyFutureCalculator` upstream of it), except for the Stop Loss / Trailing Stop pair, which is already fully decoupled from the rest of the chain by `ExitEngine`'s existing Protocol-based design — that pair can be pulled forward opportunistically without disrupting 1–4's sequence.

---

## Section 4 — Contract Requirements

For each unresolved Protocol:

### `WeeklyFutureCalculator.calculate`
- **Preconditions:** `first_five_minute_candle.is_candle()` must be `True` (has OHLC). No other precondition is enforced by the type system today.
- **Postconditions:** returns a `WeeklyFuture` whose `__post_init__` already enforces `weekly_future_id`/`session_id`/`calculated_at` are non-`None`. **No `high >= low` invariant is enforced by the model, deliberately** — a prior, different evidence source found a worked example where Low exceeded High; do not add this invariant to `models/weekly_future.py` without confirming it's actually always true.
- **Exceptions:** must raise `core.exceptions.UnresolvedBusinessRuleError` until the formula is resolved; once resolved, whatever the formula's own error conditions turn out to require (not specifiable yet).
- **Validation rules:** none beyond the model's existing `__post_init__` — do not add new validation to `models/weekly_future.py` speculatively; add it only once the recovered specification confirms a real invariant (e.g. if it turns out High must always exceed Low, add that check then, not now).

### `StrikeSelector.select`
- **Preconditions:** a valid `WeeklyFuture` (already validated by its own model).
- **Postconditions:** returns a `StrikeSelection` with `top_strike > 0`, `bottom_strike > 0` (already enforced by the model). No `top_strike != bottom_strike` invariant exists — do not add one without confirmation.
- **Exceptions:** same `UnresolvedBusinessRuleError` convention until resolved.
- **Validation rules:** none beyond the model's existing checks.

### `TPEngine.update` / `QualificationEngine.evaluate`
- **Preconditions/Postconditions/Validation rules:** cannot be meaningfully specified yet, because the output type of `TPEngine.update` (currently `object`) has to be decided as part of implementing it — this contract is genuinely open, not just unimplemented.
- **Exceptions:** `UnresolvedBusinessRuleError` until resolved.

### `StopLossEngine.check` / `TrailingStopEngine.check`
- **Preconditions:** `position.is_active()` should be `True` (both are only ever called by `ExitEngine` on the currently-active position; nothing currently enforces this precondition inside the Protocol itself, so a real implementation should not assume it's been checked upstream — verify defensively if the position could theoretically be closed).
- **Postconditions:** return `bool`; `True` triggers `ExitEngine` to close the position with `ExitReason.STOP_LOSS`/`ExitReason.TRAILING_STOP` respectively — no other side effect is expected or handled by `ExitEngine`.
- **Exceptions:** `UnresolvedBusinessRuleError` until resolved; once resolved, any exception raised will propagate uncaught through `ExitEngine.evaluate()` today (verified — `ExitEngine` does not catch exceptions from either engine), so a real implementation should not raise for ordinary "condition not met" cases, only for genuine faults.
- **Validation rules:** the one confirmed numeric constraint (Trailing Stop's minimum net +3 premium points after brokerage/exchange/tax) must hold whenever `TrailingStopEngine.check` returns `True` — but nothing enforces this at the type level; it would need to be validated inside the real implementation.

---

## Section 5 — Testing Strategy

For each future engine, matching this codebase's existing test conventions (parametrized fixtures, injected fakes for Protocol dependencies, `pytest.raises` with message-substring `match=`, 100% statement+branch coverage target):

### `WeeklyFutureCalculator`
- **Unit tests:** given a known candle, assert the exact `WeeklyFuture.high`/`.low` produced, once a real formula exists to test against.
- **Integration tests:** wire a real implementation into a full pipeline run (`ReplayEngine` → `WeeklyFutureCalculator` → `StrikeSelector` → `ReferenceBuilder`) and assert the resulting `ReferenceLevel` ladder matches expectations end-to-end.
- **Replay tests:** run against a fixture historical file with a known, expected Weekly Future value, and confirm reproducibility across repeated replay runs (determinism).
- **Edge cases:** a candle where High == Low (a flat first candle); whatever numeric edge cases the recovered formula itself turns out to have (cannot be enumerated further until the formula exists).

### `StrikeSelector`
- **Unit tests:** given a known `WeeklyFuture`, assert exact `top_strike`/`bottom_strike`.
- **Integration tests:** feed the result directly into `ReferenceBuilder.build()` and confirm it accepts the produced strikes without validation errors.
- **Edge cases:** whether `top_strike == bottom_strike` can occur, and if so what happens — this is currently an open question (Section 4), so a real implementation's test suite should explicitly test whatever the recovered rule says about this case, rather than leaving it implicit.

### `TPEngine` / `QualificationEngine`
- **Unit tests:** cannot be meaningfully designed until the output shape (Section 2.3) is decided; write these once that decision is made, not speculatively now.
- **Integration tests:** feed real `TPEngine` output into a real `QualificationEngine`, and confirm the resulting qualification state correctly informs whatever the eventual Winner-detection wiring turns out to be.

### `StopLossEngine` / `TrailingStopEngine`
- **Unit tests:** given a known `TradePosition` and `MarketSnapshot`, assert `check()` returns the expected boolean at/around the trigger boundary (this pattern is already fully exercised in `tests/exit_engine/test_exit_engine.py` using `_AlwaysTrueStopLoss`/`_AlwaysFalseStopLoss` fakes — a real implementation's tests should follow the same shape).
- **Integration tests:** none needed beyond what already exists — `ExitEngine`'s own integration tests already prove the wiring works with any conforming implementation; a real `StopLossEngine`/`TrailingStopEngine` only needs its own unit tests plus confirmation it satisfies the `Protocol` (`isinstance(real_impl, StopLossEngine)`).
- **Edge cases:** the trailing stop's minimum net +3 points guarantee, once its brokerage/exchange/tax inputs are known — test the boundary exactly at +3 net, and just below it.

---

## Section 6 — Acceptance Criteria

A blocked module may be marked complete only when **all** of the following hold:

1. Its Protocol's `UnresolvedBusinessRuleError` stub is replaced by a real implementation that never raises that exception for a well-formed input.
2. The underlying business rule is cited to actual evidence (a recovered video transcript, a set of confirmed worked examples, or direct confirmation from the domain owner) — not inferred, not guessed, not filled in by "reasonable" assumption. Matches this project's evidence-first discipline, unchanged since Phase 5.
3. `isinstance(real_implementation, <Protocol>)` holds (structural conformance, automatically true if the method signature matches).
4. 100% statement + branch coverage on the new module, `mypy --strict`/`ruff`/`black` all clean, consistent with every prior sprint's bar.
5. No existing file outside the new module (and, where genuinely required for integration, the shared `core`/`models` layer) is modified — matching the "Do NOT modify existing modules unless integration requires it" convention already established across Sprints 2–4.
6. Zero circular dependencies introduced (verify with the same AST-based import-graph check used in every prior sprint's final verification).

---

## Section 7 — Implementation Checklist

For a future developer (or a future session of this assistant) implementing any one blocked module:

- [ ] Confirm the business rule is actually resolved — check `WEEKLY_FUTURE_BLOCKER_REPORT.md` (for Weekly Future) or the equivalent evidence trail for the module in question. If it says DELAY, it is still DELAY until this document (or its successor) is updated to say otherwise.
- [ ] Re-read the current Protocol definition in `src/interfaces/` directly — do not rely on this guide's quoted signatures if time has passed; the source is authoritative.
- [ ] If the module's output requires a new model (e.g. `TPEngine`'s `TPState` — see Section 2.3), design it in `models/`, following the existing pattern: frozen `@dataclass(slots=True)`, `__post_init__` validation raising `core.exceptions.ValidationError`, no invented cross-field invariant unless the recovered evidence actually confirms one.
- [ ] Implement the real class in a new file under the module's own package (create the package if it doesn't exist yet, e.g. `src/weekly_future/`), following the existing constructor-injection convention (no globals, no singletons, `Clock`/`IdFactory`/`EventBusProtocol` injected where needed, defaulting to `core.protocols.utc_now`/`uuid.uuid4` per `CODING_STANDARDS.md`).
- [ ] Write tests achieving 100% statement + branch coverage, following Section 5's guidance for that specific module.
- [ ] Run the full existing suite (`pytest tests -q --cov=src --cov-report=term-missing`) to confirm zero regressions in the 256 tests that exist today.
- [ ] Run `mypy --strict src`, `ruff check src tests`, `black --check src tests`.
- [ ] Re-run the AST-based circular-dependency check across all packages (including the new one).
- [ ] Update `research/architecture/IMPLEMENTATION_ROADMAP.md`'s status for that module from Blocked to whatever its new status is.
- [ ] Stop and let the user review before committing — matches the standing convention for every sprint so far ("Do NOT commit automatically. Wait for review.").

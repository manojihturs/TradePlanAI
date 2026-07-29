# Business Architecture

**Role of this document:** domain modeling, not implementation. Every module below is one of the six already-stubbed Protocols in `src/interfaces/` (Sprint 1–4, `v0.4.1-framework-stable`). This document defines each one's *contract* — responsibility, inputs, outputs, dependencies, events, error conditions, validation, state, and integration points — without defining any calculation, formula, or threshold. Every field whose content depends on a still-unresolved business rule is marked **UNRESOLVED – Awaiting Strategy Evidence**, per `WEEKLY_FUTURE_BLOCKER_REPORT.md` and `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` Section 20.

**A factual note carried through every module below:** `research/architecture/EVENT_CATALOG.md` (Phase 2, a design document) proposed a fuller event set than what Sprint 1 actually implemented. The concrete event classes that exist today, verified directly against `src/core/events.py`, are exactly: `MarketOpenEvent`, `MarketCloseEvent`, `WeeklyFutureCalculatedEvent`, `StrikeSelectedEvent`, `WinnerDetectedEvent`, `TradeOpenedEvent`, `TradeClosedEvent`, `TargetHitEvent`, `CompetitorHitEvent`. Events named in `EVENT_CATALOG.md` but **not yet implemented** — `ReferenceLevelsGenerated`, `TPUpdated`, `QualificationChanged`, `DefeatDetected` — are called out explicitly as such wherever they'd be relevant, not silently assumed to exist.

---

## 1. WeeklyFutureCalculator

**Protocol (`src/interfaces/weekly_future_calculator.py`):** `calculate(first_five_minute_candle: MarketSnapshot) -> WeeklyFuture`

| Field | Content |
|---|---|
| **Responsibility** | Compute the session's Weekly Future High and Low. |
| **Inputs** | One `MarketSnapshot` — the first 5-minute candle (09:15–09:20), candle-mode (`is_candle() == True`). This is the only input CONFIRMED by evidence (Specification Rule 1). |
| **Outputs** | One `WeeklyFuture` (`weekly_future_id`, `session_id`, `high`, `low`, `calculated_at`). Whether a `close` (or a full OHLC "Weekly Future candle") is also required is UNRESOLVED – Awaiting Strategy Evidence (`WeeklyFuture_Specification_v1.md` Section 5/Ambiguity 6). |
| **Dependencies** | `market_data`-equivalent candle source only. No dependency on any other business module. |
| **Events Consumed** | None. This module is invoked directly (by whatever drives the session lifecycle — `replay`/`live`), not triggered by a bus event, in the current implementation. |
| **Events Produced** | `WeeklyFutureCalculatedEvent` (already implemented, `src/core/events.py`). |
| **Error Conditions** | Input not candle-mode → `core.exceptions.ValidationError` (matches this codebase's established convention). All formula-specific failure conditions (e.g. what happens if the candle itself is malformed beyond OHLC-presence) are UNRESOLVED – Awaiting Strategy Evidence. |
| **Validation Requirements** | Output must satisfy `WeeklyFuture`'s existing `__post_init__` (non-`None` IDs/timestamp). **Deliberately not enforced:** a `high >= low` invariant — a different evidence source (`research/analysis/WEEKLY_FUTURE_VERIFICATION.md`) found a worked example where Low exceeded High; this must not be assumed correct or incorrect without further evidence. |
| **State Requirements** | UNRESOLVED – Awaiting Strategy Evidence whether this is computed once per session or recalculated intraday (Specification Section 20 item 16). |
| **Integration Points** | `StrikeSelector` (consumes `WeeklyFuture` directly). No other module reads this output today. |

---

## 2. StrikeSelector

**Protocol (`src/interfaces/strike_selector.py`):** `select(session_id: uuid.UUID, weekly_future: WeeklyFuture, selected_at: datetime) -> StrikeSelection`

| Field | Content |
|---|---|
| **Responsibility** | Select the session's Top Strike and Bottom Strike (both "ATM"). |
| **Inputs** | `session_id`, the session's `WeeklyFuture`, a timestamp. |
| **Outputs** | One `StrikeSelection` (`session_id`, `top_strike`, `bottom_strike`, `selected_at`). |
| **Dependencies** | `WeeklyFutureCalculator`'s output. |
| **Events Consumed** | Conceptually `WeeklyFutureCalculatedEvent` (already implemented) — but no code today actually subscribes `StrikeSelector` to the bus; the current stub interface is invoked directly, mirroring `WeeklyFutureCalculator`. |
| **Events Produced** | `StrikeSelectedEvent` (already implemented). |
| **Error Conditions** | The entire ATM basis and rounding rule is UNRESOLVED – Awaiting Strategy Evidence (Specification Section 20 item 2, Critical). |
| **Validation Requirements** | Output must satisfy `StrikeSelection`'s existing `__post_init__` (`top_strike > 0`, `bottom_strike > 0`). **Deliberately not enforced:** `top_strike != bottom_strike` — whether they can be equal is UNRESOLVED. |
| **State Requirements** | UNRESOLVED – Awaiting Strategy Evidence, same as `WeeklyFutureCalculator` (once vs. recalculated). |
| **Integration Points** | `ReferenceBuilder` (needs Top/Bottom Strike to center its 13-level ladder in a live/replay run — today `ReferenceBuilder` is tested against caller-supplied strikes directly, bypassing this dependency). `TPEngine` (needs to know which strikes are Top/Bottom). |

---

## 3. TPEngine

**Protocol (`src/interfaces/tp_engine.py`):** `update(snapshot: MarketSnapshot, levels: tuple[ReferenceLevel, ...]) -> object`

| Field | Content |
|---|---|
| **Responsibility** | Continuously compute TP High (Top Strike) / TP Low (Bottom Strike) qualification state. |
| **Inputs** | A `MarketSnapshot` and the session's 13-level `ReferenceLevel` ladder. |
| **Outputs** | **Genuinely undecided** — the Protocol returns bare `object` today. Whether TP is a price, a boolean qualified/unqualified flag, or both is UNRESOLVED – Awaiting Strategy Evidence (Specification Section 20 item 13). Deciding this output shape (and adding the corresponding model to `models/`) is itself part of implementing this module, not a pre-existing gap to fill in later. |
| **Dependencies** | `ReferenceBuilder`'s ladder, `StrikeSelector`'s Top/Bottom Strike identity. |
| **Events Consumed** | Conceptually `ReferenceLevelsGenerated` — **not yet implemented anywhere in this codebase** (see this document's opening note). No event-driven trigger currently exists for this module. |
| **Events Produced** | Conceptually `TPUpdated` — **not yet implemented**. Adding it (to `src/core/events.py`, additively, matching the established convention) is an integration task for whichever sprint implements this module. |
| **Error Conditions** | The competitor-strike identity for this module's own qualification test is UNRESOLVED – Awaiting Strategy Evidence (Specification Section 20 item 3, Critical) — **explicitly not the same** as `ExitEngine`'s already-confirmed competitor mapping (Specification Rule 2); that mapping is for a different purpose (Exit monitoring of an already-open trade) and must not be assumed to generalize here. |
| **Validation Requirements** | UNRESOLVED – depends entirely on the undecided output shape. |
| **State Requirements** | UNRESOLVED – Awaiting Strategy Evidence: update cadence (tick vs. candle, Section 20 item 12); whether TP state persists across the whole session or is recomputed fresh each cycle. |
| **Integration Points** | `QualificationEngine` (direct consumer). `WinnerEngine`'s *live* use — **the relationship itself is UNRESOLVED**: today's built `WinnerEngine.evaluate()` takes CE/PE snapshots directly and does not consume `TPEngine`'s output at all; how TP/Qualification state is meant to gate or inform Winner detection is not defined anywhere in current evidence. |

---

## 4. QualificationEngine

**Protocol (`src/interfaces/qualification_engine.py`):** `evaluate(tp_state: object) -> bool`

| Field | Content |
|---|---|
| **Responsibility** | Evaluate whether a strike's TP is currently "qualified" (sustaining against its competitor level). |
| **Inputs** | `tp_state`, typed `object` for the same reason as `TPEngine.update`'s output — its real shape is undecided. |
| **Outputs** | `bool`. |
| **Dependencies** | `TPEngine`'s output shape, once defined. |
| **Events Consumed** | Conceptually `TPUpdated` — not yet implemented (see §3). |
| **Events Produced** | Conceptually `QualificationChanged` — not yet implemented. |
| **Error Conditions** | Same competitor-identity gap as `TPEngine` (§3). Additionally: external-invalidation handling (news/budget/war/natural disaster — Specification Section 7 names this scenario explicitly) has **no detection mechanism specified anywhere** — UNRESOLVED – Awaiting Strategy Evidence, and there is no existing evidence even describing what such a mechanism would look like. |
| **Validation Requirements** | UNRESOLVED – depends on §3's undecided shape. |
| **State Requirements** | Per Specification Sections 7–8, re-evaluated on every `TPEngine` update cycle — its own state lifecycle is therefore entirely tied to `TPEngine`'s unresolved cadence (§3), not independently defined. |
| **Integration Points** | Feeds `WinnerEngine`'s live use — same UNRESOLVED wiring gap noted in §3. |

---

## 5. StopLossEngine

**Protocol (`src/interfaces/stop_loss_engine.py`):** `check(position: TradePosition, snapshot: MarketSnapshot) -> bool`

| Field | Content |
|---|---|
| **Responsibility** | Evaluate whether an active `TradePosition` has hit its Stop Loss. |
| **Inputs** | The active `TradePosition`, a `MarketSnapshot`. |
| **Outputs** | `bool`. |
| **Dependencies** | `PositionManager`/`TradeManager` (reads the active position, via `ExitEngine`). |
| **Events Consumed** | None. `ExitEngine` calls `check()` synchronously on every `evaluate()` cycle — this module is not event-driven. |
| **Events Produced** | None directly. When `check()` returns `True`, `ExitEngine` closes the position (publishing `TradeClosedEvent` with `ExitReason.STOP_LOSS`, transitively via `TradeManager` — already implemented and verified working end-to-end against test doubles). |
| **Error Conditions** | The **entire** Stop Loss rule — price basis, placement, trigger condition — is UNRESOLVED – Awaiting Strategy Evidence (Specification Section 20 item 4, Critical; the single largest unstated rule after Weekly Future itself). |
| **Validation Requirements** | UNRESOLVED in full — no rule exists yet to validate against. |
| **State Requirements** | UNRESOLVED – Awaiting Strategy Evidence whether this check is stateless (evaluable from `position`/`snapshot` alone each call) or requires tracking additional state (e.g. an initial-risk anchor) not currently present on `TradePosition`. |
| **Integration Points** | **Already fully wired into `ExitEngine` today** (`src/exit_engine/exit_engine.py`) — this is the one module in this document already integrated at the call-site level; only its internal logic is unresolved. Implementing it for real is a pure drop-in; no `ExitEngine` code needs to change. |

---

## 6. TrailingStopEngine

**Protocol (`src/interfaces/trailing_stop_engine.py`):** `check(position: TradePosition, snapshot: MarketSnapshot) -> bool`

| Field | Content |
|---|---|
| **Responsibility** | Evaluate whether an active `TradePosition` has hit its Trailing Stop. |
| **Inputs / Outputs** | Identical shape to `StopLossEngine` (§5). |
| **Dependencies** | Same as `StopLossEngine`. |
| **Events Consumed / Produced** | Same pattern as `StopLossEngine` — none consumed; `TradeClosedEvent` with `ExitReason.TRAILING_STOP` produced transitively on a `True` result. |
| **Error Conditions** | Trail activation trigger, trail step/distance, and the brokerage/exchange/tax figures needed to compute the one confirmed fact (a minimum net +3 premium points after costs, Specification Section 13) are all UNRESOLVED – Awaiting Strategy Evidence (Section 20 items 9–10). |
| **Validation Requirements** | The confirmed +3-net-minimum constraint must hold whenever `check()` returns `True` — but this cannot be validated without the missing brokerage/exchange/tax figures. |
| **State Requirements** | **A concrete architectural gap, not a business-rule gap**: a trailing stop conventionally requires tracking the trade's peak favorable excursion (a "high-water mark") over the position's life. `models.trade_position.TradePosition` (as built) has **no field for this today**. Implementing this module will very likely require either extending `TradePosition` or maintaining separate tracking state — this is a design decision for whichever sprint implements it, not something this document resolves, and it is independent of the still-unresolved trailing-stop business rule itself. |
| **Integration Points** | **Already fully wired into `ExitEngine` today**, identically to `StopLossEngine` — pure drop-in once resolved, pending the state-tracking design decision noted above. |

---

## Consolidated Cross-Module Gaps

- **The TP/Qualification → Winner wiring is entirely undefined.** `WinnerEngine` as built takes CE/PE snapshots directly; nothing in current evidence or code describes how `TPEngine`/`QualificationEngine` state is meant to inform or gate Winner detection in a live/replay run. This is a real integration design question, separate from any single module's own business-rule gap.
- **Four events used conceptually throughout this document do not exist in `src/core/events.py` today**: `ReferenceLevelsGenerated`, `TPUpdated`, `QualificationChanged`, and (per `research/architecture/EVENT_CATALOG.md`, not referenced by any module above) `DefeatDetected`. Adding them, additively, is implementation work belonging to whichever sprint first needs them — consistent with how `AmbiguousWinnerError`, `subscribe_all`/`unsubscribe_all`, and the Trailing/StopLoss events were each added only when the sprint that needed them arrived.

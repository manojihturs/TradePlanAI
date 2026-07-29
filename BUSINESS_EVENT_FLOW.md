# Business Event Flow

Scope: the event-level view (as opposed to `BUSINESS_SEQUENCE_DIAGRAM.md`'s call-level view) of how the six blocked business modules relate to the event bus (`src/core/event_bus.py`, `EventBusProtocol` in `src/core/protocols.py`).

## Real vs. proposed events — authoritative list

Verified directly against `src/core/events.py` (`grep -n "^class "`), not against `research/architecture/EVENT_CATALOG.md`, which is a Phase 2 design proposal and includes events beyond what Sprint 1 actually built.

| Event | Status | Producer today | Consumer today |
|---|---|---|---|
| `MarketOpenEvent` | **Implemented** | session driver | — |
| `MarketCloseEvent` | **Implemented** | session driver | — |
| `WeeklyFutureCalculatedEvent` | **Implemented** | `WeeklyFutureCalculator` (stub) | — (no subscriber wired yet) |
| `StrikeSelectedEvent` | **Implemented** | `StrikeSelector` (stub) | — (no subscriber wired yet) |
| `WinnerDetectedEvent` | **Implemented** | `WinnerEngine` | `TradeManager`/`EntryEngine` |
| `TradeOpenedEvent` | **Implemented** | `TradeManager` (via `PositionManager`) | `event_recorder`, `trade_history` |
| `TradeClosedEvent` | **Implemented** | `TradeManager` (via `ExitEngine`→`PositionManager`) | `event_recorder`, `trade_history` |
| `TargetHitEvent` | **Implemented** | `ExitEngine` | `event_recorder` |
| `CompetitorHitEvent` | **Implemented** | `ExitEngine` | `event_recorder` |
| `ReferenceLevelsGenerated` | **Proposed only** (`EVENT_CATALOG.md`) — not in code | n/a | n/a |
| `TPUpdated` | **Proposed only** — not in code | n/a | n/a |
| `QualificationChanged` | **Proposed only** — not in code | n/a | n/a |
| `DefeatDetected` | **Proposed only** — not in code | n/a | n/a |

## Flow by module

**WeeklyFutureCalculator** — Produces `WeeklyFutureCalculatedEvent` (real). No module subscribes to it today; `StrikeSelector` currently would need to be invoked directly with the `WeeklyFuture` value rather than triggered by the event. Whether `StrikeSelector` *should* become event-driven off this event, or stay directly invoked, is an implementation-time design choice, not a business rule — UNRESOLVED only in the sense that it hasn't been decided, not that it awaits strategy evidence.

**StrikeSelector** — Produces `StrikeSelectedEvent` (real). Same non-subscription gap as above applies to whatever consumes Top/Bottom Strike next (`ReferenceBuilder`, `TPEngine`).

**TPEngine** — Would consume a `ReferenceLevelsGenerated` event that does not exist, and would produce a `TPUpdated` event that does not exist. Adding both is additive implementation work, not a redesign — consistent with how this codebase has added events before (e.g. `TargetHitEvent`/`CompetitorHitEvent` were added specifically when `ExitEngine` needed them in Sprint 3).

**QualificationEngine** — Would consume the proposed `TPUpdated` and produce the proposed `QualificationChanged`. Both nonexistent today.

**StopLossEngine / TrailingStopEngine** — Produce **no events directly**. Both are called synchronously inside `ExitEngine.evaluate()`; a `True` result feeds `ExitEngine`'s existing exit path, which already, today, results in a real `TradeClosedEvent` (with the appropriate `ExitReason`) published transitively through `PositionManager.close_position()` → `TradeManager.close()`. This is the one part of this document backed entirely by real, tested code rather than a proposal.

## Structural observation (not a business rule)

The proposed `DefeatDetected` event in `EVENT_CATALOG.md` has no module in the current 6-module blocked set that would obviously own producing it — Specification Section 7 describes an external-invalidation scenario (news/budget/war/etc.) but names no detection mechanism. This is flagged here as an open architecture question, distinct from the per-module UNRESOLVED business-rule gaps in `BUSINESS_ARCHITECTURE.md`.

# Implementation Roadmap

Phase 2 (System Architecture) deliverable. 14 phases, matching the
module boundaries in `MODULE_ARCHITECTURE.md`. This roadmap sequences
*engineering* work — it is a sibling to, and does not replace, the
7-phase spec-then-code workflow already agreed for this project
(Phase 1 Spec → Phase 2 Architecture [this batch of documents] →
Phase 3 Data Model → Phase 4 Replay → Phase 5 Backtest → Phase 6 Live
→ Phase 7 Tests). The 14 phases below are the detailed breakdown of
that higher-level Phase 4–7 work, once Phase 3 (Data Model) is
approved.

**Complexity scale:** Low / Medium / High / Blocked (cannot start —
Critical Missing Information in the way).
**Risk scale:** Low / Medium / High.

---

## Phase 1 — Infrastructure

- **Scope:** `events/`, `diagnostics/`, `storage/` foundational packages; project scaffolding, CI, quality gates (pytest, mypy --strict, ruff, black — matching this repository's existing established convention).
- **Complexity:** Low.
- **Dependencies:** None.
- **Risk:** Low.
- **Deliverables:** `events/` event dataclasses (from `EVENT_CATALOG.md`) and bus contract; `diagnostics/` sink (reuse of `trading_engine.diagnostics` recommended, per `MODULE_ARCHITECTURE.md` 3.19); `storage/` repository Protocol (reuse of `trading_engine.premium_snapshot`'s CSV/SQLite pattern recommended).
- **Acceptance Criteria:** All event dataclasses from `EVENT_CATALOG.md` implemented and unit-tested; diagnostics sink emits/discards correctly; storage round-trips a sample entity; 100% coverage, all quality gates clean (matching this repository's established bar).

## Phase 2 — Market Data

- **Scope:** `market_data/` module — candle/tick ingestion, first-5-minute-candle capture.
- **Complexity:** Medium (Low if `trading_engine/market_data/` + `trading_engine/premium_snapshot/` are reused per `MODULE_ARCHITECTURE.md` 3.1's recommendation).
- **Dependencies:** Phase 1.
- **Risk:** Medium — candle vs. tick cadence for post-09:21 evaluation is **MISSING INFORMATION** (Specification Section 20 item 7); building the wrong shape here has downstream cost.
- **Deliverables:** `MarketSnapshot` stream; first-5-minute-candle OHLC per contract, reusing/matching `ContractSnapshot`'s shape.
- **Acceptance Criteria:** Can replay a historical file and produce a correct first-5-minute-candle capture for a known dataset; live/replay/backtest all consume the same interface.

## Phase 3 — Weekly Future

- **Scope:** `weekly_future/` module.
- **Complexity:** **Blocked** — the Weekly Future formula is Critical Missing Information (Specification Section 20 item 1).
- **Dependencies:** Phase 2.
- **Risk:** High — this repository's own `WEEKLY_FUTURE_VERIFICATION.md` (a different evidence source) found its only worked example internally self-contradictory; do not assume this rule set's Weekly Future is the same concept or shares a formula.
- **Deliverables:** `WeeklyFutureCalculator` implementing `IWeeklyFutureCalculator`, once the formula is supplied.
- **Acceptance Criteria:** Cannot be defined until the formula exists. Interim acceptance criterion: the module's *interface* (`calculate(candle) -> WeeklyFuture`) is implemented and unit-tested against a stub/injected formula, so downstream phases are not blocked on this alone (see "Unblocking Strategy" in Section 2 below).

## Phase 4 — Strike Selection

- **Scope:** `strike_selector/` module.
- **Complexity:** **Blocked** — ATM selection rule is Critical Missing Information (Specification Section 20 item 2).
- **Dependencies:** Phase 3.
- **Risk:** High — same category of risk as Phase 3.
- **Deliverables:** `StrikeSelector` implementing `IStrikeSelector`.
- **Acceptance Criteria:** Cannot be defined until the ATM rule exists (interim: interface + stub, as above).

## Phase 5 — Reference Levels

- **Scope:** `reference_builder/` module.
- **Complexity:** Medium — the core computation (CE/PE High/Low from first 5-minute candle) is **CONFIRMED**; only ladder step size and centering are open.
- **Dependencies:** Phase 4 (for strike centers) — but see "Unblocking Strategy," this can proceed against stubbed strikes.
- **Risk:** Low-Medium.
- **Deliverables:** `ReferenceLevelBuilder` producing 13 `ReferenceLevel` instances per session.
- **Acceptance Criteria:** Given a known first-5-minute candle per contract and a known strike pair, produces exactly 13 levels with correct CE/PE High/Low; 100% branch coverage on OHLC validation.

## Phase 6 — TP Engine

- **Scope:** `tp_engine/` module.
- **Complexity:** **Blocked** — TP Engine's competitor identity is Critical Missing Information (Specification Section 20 item 3); update cadence and TP's own type (price/flag/both) are High-priority gaps.
- **Dependencies:** Phase 5.
- **Risk:** High.
- **Deliverables:** `TPEngine` implementing `ITPEngine`.
- **Acceptance Criteria:** Cannot be defined until competitor identity and TP's type are resolved.

## Phase 7 — Qualification

- **Scope:** `qualification/` module.
- **Complexity:** **Blocked** — depends entirely on Phase 6's resolution (Qualification is a thin wrapper over TP's own sustain test, per `MODULE_ARCHITECTURE.md` 3.6).
- **Dependencies:** Phase 6.
- **Risk:** High (inherits Phase 6's risk).
- **Deliverables:** `QualificationEvaluator`.
- **Acceptance Criteria:** Cannot be defined until Phase 6 unblocks.

## Phase 8 — Winner

- **Scope:** `winner/` module.
- **Complexity:** Medium — the core rule (same-candle CE+PE touch) is stated, and the tie-break question is **CONFIRMED resolved** (Rule 3: no tie-break needed). The remaining open item (which strike(s)' CE/PE are evaluated) is High, not Critical.
- **Dependencies:** Phase 5 (levels), Phase 7 (qualification feed — though Winner's core touch-detection logic does not strictly require Qualification to be resolved; see "Unblocking Strategy").
- **Risk:** Medium.
- **Deliverables:** `WinnerEngine` implementing `IWinnerEngine`.
- **Acceptance Criteria:** Given a `MarketSnapshot` sequence with a known same-candle CE+PE touch, correctly identifies winning side/strike with no ambiguity; unit tests confirm no tie-break code path exists (per Rule 3).

## Phase 9 — Entry

- **Scope:** `entry/`, `position/` modules.
- **Complexity:** Low — the core rules (immediate entry after Winner, single-active-trade, ignore-while-active) are all **CONFIRMED**. Only entry price/order-type is open (High-priority-adjacent, not Critical to the *logic*, only to real order placement).
- **Dependencies:** Phase 8.
- **Risk:** Low.
- **Deliverables:** `EntryEngine`, `PositionManager` implementing `IEntryEngine`/`IPositionManager`.
- **Acceptance Criteria:** Given a `WinnerEvent` and no active position, opens exactly one `Position` with correct Target/Support/Competitor fields (Rule 2, CONFIRMED); given an active position, a second `WinnerEvent` is provably ignored (no `Position` created, no event published) — this is fully testable today without further evidence.

## Phase 10 — Exit

- **Scope:** `exit/`, `risk/` modules.
- **Complexity:** Medium (Target/Competitor conditions) + **Blocked** (Stop Loss, Trailing Stop — Critical/High gaps).
- **Dependencies:** Phase 9.
- **Risk:** High — Stop Loss is entirely unstated (Specification Section 20 item 4, Critical); exit-condition precedence is unresolved (item 11).
- **Deliverables:** `ExitEngine`, `RiskEvaluator`. Target/Competitor-level checks can be fully implemented now (Rule 2, CONFIRMED); Stop Loss/Trailing Stop cannot.
- **Acceptance Criteria:** Target/Competitor exit paths fully tested against the confirmed S±1 mapping. Stop Loss/Trailing Stop acceptance criteria cannot be defined until their rules exist.

## Phase 11 — Replay

- **Scope:** `replay/` module.
- **Complexity:** Low-Medium (Low if `trading_engine/replay/` — Milestone B1 — is reused per `MODULE_ARCHITECTURE.md` 3.15's recommendation).
- **Dependencies:** Phases 1–10 (replay drives the full pipeline; it is only as complete as the engines it drives, but its own machinery — load, step, play, pause — is independent of the blocked business-rule phases).
- **Risk:** Low.
- **Deliverables:** `ReplayController`-equivalent driving `market_data/` from historical files at controllable speed.
- **Acceptance Criteria:** Can step/play/pause through a historical session and produce an identical event stream shape to live trading, using whatever engines are implemented so far (stubs for blocked phases).

## Phase 12 — Backtest

- **Scope:** `backtest/` module.
- **Complexity:** Medium.
- **Dependencies:** Phase 11.
- **Risk:** Medium — P&L/performance-metric definitions are **MISSING INFORMATION** beyond the Trailing Stop's own "+3 net" guarantee (no general scoring formula is evidenced).
- **Deliverables:** Multi-session batch runner, `BacktestReport` aggregation (win rate, exit-reason distribution — metrics beyond these two are unconfirmed).
- **Acceptance Criteria:** Can run N historical sessions unattended and produce a report; the report's *metric set* is limited to what's confirmed (win/loss count, exit-reason distribution) until a scoring formula is supplied.

## Phase 13 — Diagnostics

- **Scope:** `diagnostics/` module wiring across every other module.
- **Complexity:** Low (reuse of `trading_engine.diagnostics` recommended).
- **Dependencies:** All prior phases (diagnostics observes, does not gate).
- **Risk:** Low.
- **Deliverables:** Every module emits diagnostic events for its own lifecycle (start/complete/fail), consistent with this repository's existing convention (diagnostic events carry no trading-meaningful value).
- **Acceptance Criteria:** Every module's diagnostic events are unit-tested in isolation, matching this repository's existing per-milestone diagnostics test pattern.

## Phase 14 — Testing

- **Scope:** Full `tests/` suite, integration/replay/regression coverage. See `TEST_STRATEGY.md` for detail.
- **Complexity:** Medium-High (proportional to how many phases above are unblocked by then).
- **Dependencies:** All prior phases.
- **Risk:** Medium.
- **Deliverables:** Per-module unit tests, cross-module integration tests, replay-driven regression tests, a documented list of tests that **cannot** be written yet because they depend on Blocked phases (Weekly Future, Strike Selection, TP Engine, Stop Loss).
- **Acceptance Criteria:** 100% coverage on every unblocked module (matching this repository's `fail_under = 100` established convention); explicit, tracked test gaps for blocked modules — not silently skipped.

---

## Roadmap Summary Table

| Phase | Module(s) | Complexity | Risk | Blocked? |
|---|---|---|---|---|
| 1 | Infrastructure | Low | Low | No |
| 2 | Market Data | Medium | Medium | No |
| 3 | Weekly Future | Blocked | High | **Yes — formula (Critical)** |
| 4 | Strike Selection | Blocked | High | **Yes — ATM rule (Critical)** |
| 5 | Reference Levels | Medium | Low-Medium | No (core computation confirmed) |
| 6 | TP Engine | Blocked | High | **Yes — competitor identity (Critical)** |
| 7 | Qualification | Blocked | High | **Yes — inherits Phase 6** |
| 8 | Winner | Medium | Medium | No (tie-break confirmed resolved) |
| 9 | Entry | Low | Low | No (fully confirmed) |
| 10 | Exit | Medium/Blocked | High | **Partially — Stop Loss (Critical)** |
| 11 | Replay | Low-Medium | Low | No |
| 12 | Backtest | Medium | Medium | No (metrics limited) |
| 13 | Diagnostics | Low | Low | No |
| 14 | Testing | Medium-High | Medium | Partially, mirrors above |

---

## Unblocking Strategy

Phases 3, 4, 6, 7, and part of 10 are Blocked on Critical Missing
Information. To avoid a fully serial roadmap, this architecture
recommends (an engineering choice, not a business-rule decision):

1. Implement every Blocked module's **interface** (Protocol) and a
   **stub/injected implementation** immediately, so downstream
   modules (Reference Levels, Winner, Entry, Replay) can be built and
   tested against the stub without waiting.
2. Track each stub with a clearly-named marker (e.g.
   `NotImplementedError("Weekly Future formula: MISSING INFORMATION, see Specification Section 20 item 1")`)
   — matching this repository's own established convention
   (`trading_engine/calculators/`'s existing placeholder calculators
   all follow exactly this pattern).
3. Resolve Critical gaps with the domain owner in parallel with
   Phases 1, 2, 5, 8, 9, 11 proceeding on real (non-stubbed) logic.

This lets roughly half the roadmap (Phases 1, 2, 5, 8, 9, 11, 12
partially, 13) proceed today, while Phases 3, 4, 6, 7, and part of 10
wait on you.

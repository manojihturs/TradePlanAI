# Implementation Blueprint

Milestone: Implementation Blueprinting (Phase: post-K, pre-evidence).
This document, and the six documents alongside it in
`research/implementation/`, are a **structural blueprint** of what the
FSD (`research/specification/REALTIME_TRADING_SPECIFICATION.md`,
Milestone K2) would look like as code — module boundaries, class
shapes, interfaces, data models, call sequence, phasing, and readiness
— never the trading mathematics inside any of it. Every calculator in
`trading_engine/calculators/` today raises `NotImplementedError`
unconditionally (`research/analysis/FRAMEWORK_BASELINE_REPORT.md`
Section 2 item 1); this blueprint does not change that fact anywhere,
it only describes the additional structure that would eventually
surround those calculators once evidence resolves their mathematics.

No code or pseudocode appears anywhere in this document or its six
companions. Diagrams are structural (class/sequence/state shape) only.

---

## 1. How the FSD's 15 engines/components map onto the existing package structure

The FSD's 15 engines/components (`REALTIME_TRADING_SPECIFICATION.md`
Sections 2-15) split cleanly into two groups against the existing
`trading_engine/` package layout:

### 1a. Engines that already have a structural home

| FSD engine/component | Existing home | Evidence |
|---|---|---|
| Strike Engine (Sec. 2) | `trading_engine/calculators/strike_calculator.py` + `trading_engine/domain/strike.py` | `KNOWLEDGE_DEPENDENCY_MATRIX.md` STRIKE-001 row: "Yes — `calculators/strike_calculator.py`, `domain/strike.py`" |
| Premium Snapshot Engine (Sec. 3) | `trading_engine/domain/premium.py` | `KNOWLEDGE_DEPENDENCY_MATRIX.md` ENT-009 row |
| Competitor Engine (Sec. 6) | `trading_engine/calculators/opponent_calculator.py` + `trading_engine/domain/opponent.py` | `KNOWLEDGE_DEPENDENCY_MATRIX.md` OPPONENT-001 row |
| Trend Engine (Sec. 7) | `trading_engine/calculators/trend_calculator.py` + `trading_engine/domain/trend_point.py` | `KNOWLEDGE_DEPENDENCY_MATRIX.md` TREND-001/002 rows |
| Winner Engine (Sec. 8), via TREND-003's Edge condition only | `trading_engine/calculators/edge_calculator.py` | `KNOWLEDGE_DEPENDENCY_MATRIX.md` TREND-003 row — Edge is "a condition over two TrendPoints, not a standalone entity" (FSD Sec. 7); Winner itself has no code home (see 1b) |
| Exit Engine (Sec. 10), Reversal sub-concept only | `trading_engine/calculators/reversal_calculator.py` | `KNOWLEDGE_DEPENDENCY_MATRIX.md` REVERSAL-001 row |
| Replay/backtest runtime (not one of the 15, but the one piece of "service"-shaped infrastructure that already exists) | `trading_engine/replay/` (`HistoryLoader`, `ReplayClock`, `ReplaySession`, `ReplayController`) | `research/analysis/REPLAY_ENGINE_ARCHITECTURE.md` |
| Cross-cutting: rule orchestration | `trading_engine/rules/` (`Rule` protocol, `AbstractRule`, `RuleRegistry`) | `research/analysis/FRAMEWORK_BASELINE_REPORT.md` Section 1 |
| Cross-cutting: pipeline orchestration | `trading_engine/engine/` (`StrategyEngine`, `ExecutionPipeline`) | same |
| Cross-cutting: structured event logging | `trading_engine/diagnostics/` (`DiagnosticsSink` + 3 implementations, 8 rule/execution events + 6 replay events) | same |

### 1b. Engines/components with no existing structural home (new top-level packages needed)

The FSD explicitly documents these as **zero-repository-evidence, or
new-in-this-milestone** concepts (FSD Section 16's "Not ranked (out of
scope)" row: "Option Range Engine, Winner Engine, Real-Time Data
Requirements, Upstox Integration, Live Dashboard — all
zero-repository-evidence items introduced by this milestone's own
user-supplied workflow"). None of these has ever been touched by
`trading_engine/`'s existing 9 frozen subsystems
(`research/analysis/ARCHITECTURE_FREEZE_CHECKLIST.md`: "9 of 9
subsystems Frozen = Yes"), because those subsystems were built for a
strategy-engine that evaluates already-captured, static market
context, not live streaming data. Two new top-level packages would be
needed:

- **`trading_engine/market_data/`** — a new package for the real-time
  concerns FSD Sections 12-13 identify (Real-Time Data Requirements,
  Upstox Integration) that the current framework does not touch at
  all. `research/analysis/REPLAY_ENGINE_ARCHITECTURE.md`'s own
  "Extension points" item 1 names exactly this seam: "Real Candle →
  RuleExecutionContext conversion, once evidenced — the single most
  direct next step for connecting replay to actual strategy
  evaluation." A live equivalent of that same seam (tick/candle →
  domain object) is what `market_data/` would hold. Nothing about its
  internals is evidenced (FSD Section 13: "Zero mentions anywhere in
  the repository of any specific broker, REST API, WebSocket protocol,
  or authentication mechanism").
- **`trading_engine/live/`** — a new package for the Option Range
  Engine (FSD Sec. 4), Winner Engine (FSD Sec. 8) as a distinct
  decision-producing component beyond Edge, Entry/Exit/Risk Engine
  orchestration (FSD Secs. 9-11) as live trading-session components
  (as opposed to Replay's historical-data equivalents), and the Live
  Dashboard's backing service (FSD Sec. 14). This mirrors
  `trading_engine/replay/`'s pattern — a package that orchestrates the
  existing domain/rules/engine/calculators layers toward one runtime
  mode (there: historical replay; here: live trading) — without
  duplicating or modifying those layers, exactly as
  `REPLAY_ENGINE_ARCHITECTURE.md`'s "Reused, unmodified components"
  section states was done for replay: "`StrategyEngine`,
  `ExecutionPipeline`, `RuleRegistry`, `EngineConfiguration`, and the
  `DiagnosticsSink` protocol/implementations" had no business
  behaviour changed, only imported and called.

### 1c. Module responsibilities

- **`domain/`** (existing) — immutable value objects/entities
  (`Strike`, `Opponent`, `Premium`, `TrendPoint`, `MarketContext`,
  `MarketSession`, `SessionState`, `Decision`, `DomainEvent`,
  `EvidenceReference`, `RuleReference`). Implements the entity layer
  behind FSD Sections 2, 3, 6, 7 structurally; carries every
  business-behavior gap as a `# TODO (<RULE-ID>)`
  (`ARCHITECTURE_FREEZE_CHECKLIST.md` row 1).
- **`rules/`** (existing) — the `Rule` protocol, `AbstractRule`,
  `RuleRegistry` with dependency-ordered execution. Implements the
  orchestration contract for STRIKE-001, TREND-001/002/003,
  OPPONENT-001/002/003, REVERSAL-001 (FSD Sections 2, 6, 7, 10).
- **`calculators/`** (existing) — the `Calculator` protocol,
  `AbstractCalculator`, and the 6 placeholder calculators. Implements
  the mathematics-holding layer for the same 8 Rule IDs — currently
  all raise `NotImplementedError` (`FRAMEWORK_BASELINE_REPORT.md`
  Section 2 item 1).
- **`engine/`** (existing) — `StrategyEngine`, `ExecutionPipeline`,
  `EngineConfiguration`. Implements FSD's cross-cutting orchestration
  layer that every engine ultimately runs through.
  `strategy_engine.py`'s own docstring "Architecture Rule": "Only
  future calculator modules may perform mathematics. This class never
  mixes those responsibilities" (`SAFE_IMPLEMENTATION_SCOPE.md`,
  quoting `strategy_engine.py` lines 15-19).
- **`diagnostics/`** (existing) — structured event types + sink
  protocol. Supports FSD's implicit observability needs across all 15
  engines; has zero dependency on `rules/`/`engine/`/`calculators/`
  (`FRAMEWORK_BASELINE_REPORT.md` Section 2 item 5).
- **`replay/`** (existing) — historical OHLC replay through the
  existing scaffolding. Implements FSD's implicit "Backtest" runtime
  mode; the `ReplayService` role from the milestone's own class-name
  hint (see Document 2) is already satisfied here — see Document 2's
  explicit note.
- **`market_data/`** (new, per 1b) — implements FSD Sections 12-13
  (Real-Time Data Requirements, Upstox Integration). Entirely
  UNKNOWN/BLOCKED internals; only its existence as a boundary layer is
  blueprint-able.
- **`live/`** (new, per 1b) — implements FSD Sections 4, 8, 9-11, 14
  (Option Range Engine, Winner Engine, Entry/Trade Management/Exit,
  Live Dashboard) as a live-session orchestration package parallel to
  `replay/`. Entirely UNKNOWN/BLOCKED internals for the engines
  themselves; the orchestration shape (a controller analogous to
  `ReplayController`) is describable by analogy to the one existing
  precedent.

## 2. Dependencies (module-to-module)

Consistent with `KNOWLEDGE_DEPENDENCY_MATRIX.md`'s evidenced chain —
no new dependency edge is added beyond what that document, or direct
reading of the existing `trading_engine/` source, evidences:

- `rules/`, `calculators/` depend on `domain/` (both frameworks operate
  over domain value objects; confirmed by reading both packages'
  `protocols.py`).
- `engine/` depends on `rules/` and `domain/` (`StrategyEngine`
  orchestrates `RuleRegistry`/`Rule` over domain context).
- `diagnostics/` depends on nothing in the other four packages — the
  dependency direction runs the other way
  (`FRAMEWORK_BASELINE_REPORT.md` Section 2 item 5).
- `replay/` depends on `engine/`, `rules/`, `diagnostics/`, `domain/`
  (via `Candle`, reusing `StrategyEngine`/`ExecutionPipeline`/
  `RuleRegistry`/`EngineConfiguration`/`DiagnosticsSink` unmodified —
  `REPLAY_ENGINE_ARCHITECTURE.md` "Reused, unmodified components").
- `market_data/` (new) would depend only on `domain/` (to eventually
  produce domain objects from live ticks) — never on `rules/`,
  `engine/`, or `calculators/` directly, by analogy to how `replay/`'s
  `HistoryLoader` produces a `Candle` independent of the rule/engine
  layers.
- `live/` (new) would depend on `engine/`, `rules/`, `calculators/`,
  `diagnostics/`, `domain/`, and `market_data/` — the live-session
  analogue of what `replay/` already does for historical data,
  following the same "does not convert raw data into
  `RuleExecutionContext` itself" boundary design
  (`REPLAY_ENGINE_ARCHITECTURE.md` "The Strategy Engine integration
  boundary"). Whether `live/` would additionally depend on a
  `dashboard`-serving concern (FSD Sec. 14) is itself UNKNOWN — no
  dashboard specification exists (FSD Section 14: "Zero mentions of
  any dashboard/UI specification anywhere in `docs/` or `research/`").

No dependency edge from `calculators/` to `engine/` exists or is
proposed (`calculators/protocols.py`'s own docstring: "No calculator
shall know about the Strategy Engine").

## 3. Implementation order (high-level; detailed in Document 6)

Grounded in `research/analysis/IMPLEMENTATION_UNLOCK_SEQUENCE.md`'s
existing Critical/High/Medium/Low ranking, not re-derived: engineering
scaffolding for `market_data/` and `live/`'s package shells (SAFE NOW,
evidence-independent, per `SAFE_IMPLEMENTATION_SCOPE.md`'s framing)
can proceed in parallel with, but must not race ahead of, the
evidence-acquisition sequence that gates every calculator's actual
mathematics (Weekly Future first, per rank 1; see Document 6 for the
full phase-by-phase breakdown).

---

Sources: `research/specification/REALTIME_TRADING_SPECIFICATION.md`;
`research/analysis/KNOWLEDGE_DEPENDENCY_MATRIX.md`;
`research/analysis/FRAMEWORK_BASELINE_REPORT.md`;
`research/analysis/ARCHITECTURE_FREEZE_CHECKLIST.md`;
`research/analysis/REPLAY_ENGINE_ARCHITECTURE.md`;
`research/analysis/SAFE_IMPLEMENTATION_SCOPE.md`; direct reads of
`trading_engine/domain/*.py`, `trading_engine/rules/*.py`,
`trading_engine/calculators/*.py`, `trading_engine/engine/*.py`,
`trading_engine/diagnostics/*.py`, `trading_engine/replay/*.py`.

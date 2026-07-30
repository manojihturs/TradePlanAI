# Class Diagram

Every production class implied by the FSD's 15 engines/components plus
supporting infrastructure, grounded in FSD sections
(`research/specification/REALTIME_TRADING_SPECIFICATION.md`) and/or
existing `trading_engine/` source. **Repository status** uses three
values: READY (essentially unused here — no business logic is
implemented anywhere in the repository at all, per
`research/analysis/KNOWLEDGE_DEPENDENCY_MATRIX.md`'s closing summary,
"0 of 24 rows... are READY"), PARTIAL (the class's shape/contract is
evidenced even where its algorithm is not), UNKNOWN (no evidence at
all exists for the class's purpose beyond the workflow naming it).

No algorithm, formula, or pseudocode appears in any Purpose/Inputs/
Outputs/Dependencies field below — only structural description.

---

## 1. MarketDataProvider

- **Purpose:** Supply live market data (ticks/candles) to the rest of
  the system, per FSD Section 12 (Real-Time Data Requirements) and
  Section 13 (Upstox Integration).
- **Inputs:** UNKNOWN — no broker/protocol named anywhere
  (`REALTIME_TRADING_SPECIFICATION.md` Section 13: "Zero mentions
  anywhere... of any specific broker, REST API, WebSocket protocol").
- **Outputs:** UNKNOWN — candle/tick granularity itself unevidenced
  (Section 12: "candle interval/timeframe... tick vs. candle-close
  granularity... all UNKNOWN").
- **Dependencies:** None evidenced.
- **Repository status:** UNKNOWN. No existing file in
  `trading_engine/` corresponds to this class; `market_data/` (see
  Document 1) is the proposed new home, itself empty of any
  implementation guidance.

## 2. OptionChainProvider

- **Purpose:** Supply option-contract quote/OHLC data (Call/Put) per
  strike, needed by Strike Engine (FSD Sec. 2) and Premium Snapshot
  Engine (FSD Sec. 3) inputs.
- **Inputs:** UNKNOWN beyond the concept that Call/Put first-candle
  High/Low values are needed (FSD Section 2 "Inputs": "Call option
  first-candle High/Low, Put option first-candle High/Low").
- **Outputs:** UNKNOWN — no option-chain-specific data shape is
  evidenced anywhere.
- **Dependencies:** MarketDataProvider (by workflow position; not
  independently confirmed by any repository document, same caveat FSD
  Section 4 applies to Option Range Engine's own dependency).
- **Repository status:** UNKNOWN. No existing file corresponds; would
  live in the new `market_data/` package.

## 3. StrikeEngine

- **Purpose:** Determine Top Strike and Bottom Strike (FSD Section 2,
  workflow steps 3-4).
- **Inputs:** Weekly Future first-candle High/Low
  (`WEEKLY_FUTURE_EVIDENCE_TABLE.md` row WF-14).
- **Outputs:** Top Strike, Bottom Strike — each an exchange-listed
  strike price (FSD Section 2 "Outputs").
- **Dependencies:** Weekly Future arithmetic (ENT-010).
- **Repository status:** PARTIAL. Already exists as
  `trading_engine/calculators/strike_calculator.py` +
  `trading_engine/domain/strike.py`. The rule *shape* is evidenced
  (PARTIALLY READY per `STRIKE_EVIDENCE_SUMMARY.md`) even though
  `calculate()` raises `NotImplementedError` unconditionally
  (`strike_calculator.py:57`) because its own upstream Weekly Future
  input is NOT READY (`WEEKLY_FUTURE_VERIFICATION.md`).

## 4. WeeklyFutureCalculator (supporting, not one of the 15 named engines — cited because it structurally gates StrikeEngine)

- **Purpose:** Compute the Weekly Future synthetic instrument's
  first-candle High/Low that StrikeEngine consumes (FSD Section 2
  "Inputs").
- **Inputs:** Call option first-candle High/Low, Put option
  first-candle High/Low, ATM strike.
- **Outputs:** Weekly Future High, Weekly Future Low.
- **Dependencies:** OptionChainProvider (by workflow position).
- **Repository status:** PARTIAL (shape only). Already exists as
  `trading_engine/calculators/weekly_future_calculator.py`; registers
  successfully and raises `NotImplementedError` at line 93
  (`FRAMEWORK_BASELINE_REPORT.md` Section 1). Its own arithmetic is
  NOT READY, the worst-evidenced case in the project short of
  Reversal (`WEEKLY_FUTURE_VERIFICATION.md`).

## 5. OptionRangeEngine

- **Purpose:** Container for the "6 ITM, ATM, 6 OTM" option range (FSD
  Section 4).
- **Inputs/Outputs:** UNKNOWN in full — FSD Section 4: "zero
  repository evidence backing it... a direct grep of TR-001.md for
  'ITM' and 'OTM' returns zero matches."
- **Dependencies:** Presumably StrikeEngine output (by workflow
  position only, not confirmed).
- **Repository status:** UNKNOWN. No existing file. Included here
  because the milestone's own workflow asserts its structural
  existence, even though FSD Section 4 finds zero corroborating
  repository evidence for it — consistent with the precedent that a
  class's structural container can be blueprinted even when its
  purpose is otherwise unevidenced by any other source (Milestone
  6.0A/6.1 precedent, `SAFE_IMPLEMENTATION_SCOPE.md` "Genuinely open,
  safe-to-do-next").

## 6. PremiumSnapshotEngine

- **Purpose:** "Capture Premium Levels" (FSD Section 3, workflow step
  5).
- **Inputs:** UNKNOWN beyond "raw observation" (FSD Section 3).
- **Outputs:** A Premium value holder — id/value/timestamp only.
- **Dependencies:** None evidenced.
- **Repository status:** PARTIAL. Already exists as
  `trading_engine/domain/premium.py` ("Confirmed (thin)" per
  `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 179-190). No
  calculator/engine class computes it — Premium is a value holder, not
  a rule output (`KNOWLEDGE_DEPENDENCY_MATRIX.md` ENT-009 row: "raw/
  foundational, no rule computes it").

## 7. LevelEngine

- **Purpose:** Maintain "levels" the workflow's "Capture Premium
  Levels" step and downstream steps use (FSD Section 5).
- **Inputs:** PremiumSnapshotEngine output.
- **Outputs:** UNKNOWN — "no repository entity or rule ID corresponds
  to a distinct 'Level' object separate from Premium (ENT-009) and
  TrendPoint (ENT-003)" (FSD Section 5).
- **Dependencies:** PremiumSnapshotEngine (assumed by workflow
  position only).
- **Repository status:** UNKNOWN. No existing file; FSD Section 5
  itself states this is "UNKNOWN in full."

## 8. TrendEngine

- **Purpose:** Maintain each analyzed Strike's Trend Point Low and
  evaluate the Edge condition (FSD Section 7; TREND-001/002/003).
- **Inputs:** A Strike; ongoing price/candle data for that strike's
  option contract.
- **Outputs:** A TrendPoint value per analyzed strike; a
  market-structure-change-triggered update; an Edge condition.
- **Dependencies:** None for TREND-001 itself; TREND-002 depends on
  TREND-001; TREND-003 depends on TREND-001 and OPPONENT-001.
- **Repository status:** PARTIAL. Already exists as
  `trading_engine/calculators/trend_calculator.py` +
  `trading_engine/domain/trend_point.py` (TREND-001/002) and
  `trading_engine/calculators/edge_calculator.py` (TREND-003). Shape
  evidenced (TREND-001 Mathematical Definition "Partially Known"); all
  three `calculate()` paths raise `NotImplementedError`
  unconditionally.

## 9. CompetitorEngine

- **Purpose:** "Monitor Competitor" (FSD Section 6, workflow step 6;
  OPPONENT-001).
- **Inputs:** A Strike; an Opponent entity with a High and a Low.
- **Outputs:** A "defeated / not defeated" evaluation.
- **Dependencies:** TREND-001 (Trend Engine), OPPONENT-002,
  OPPONENT-003.
- **Repository status:** PARTIAL. Already exists as
  `trading_engine/calculators/opponent_calculator.py` +
  `trading_engine/domain/opponent.py`. Rule shape referenced
  ("Next Opponent Defeat," Evidence Count 2, `docs/RULE_INDEX.md` row
  34) even though the "defeat" condition itself is an explicit
  unresolved Open Question and `calculate()` raises
  `NotImplementedError` unconditionally. FSD Section 6 explicitly flags
  as unresolved whether this class's concept ("Competitor") equals the
  domain's "Opponent" — preserved here, not silently assumed.

## 10. WinnerEngine

- **Purpose:** "Determine Winner" (FSD Section 8, workflow step 7).
- **Inputs/Outputs:** UNKNOWN in full — "No rule ID, entity ID, or
  Bible category corresponds to a 'Winner' concept anywhere" (FSD
  Section 8).
- **Dependencies:** Presumably CompetitorEngine and TrendEngine
  outputs, by workflow position only.
- **Repository status:** UNKNOWN. No existing file, no rule ID, no
  entity ID. This is the clearest example in this document of a class
  named by workflow position alone with zero repository corroboration
  of its purpose beyond that position.

## 11. TradeEngine (Entry Engine)

- **Purpose:** "Entry" (FSD Section 9, workflow step 8).
- **Repository rule status:** `docs/TRADINGVIEW_STRATEGY_BIBLE.md`'s
  ENTRY category is empty.
- **Inputs:** Chosen direction (call/put side); a qualifying
  TrendPoint event in that direction.
- **Outputs:** An entry decision (enter / do not enter).
- **Dependencies:** TrendEngine, WinnerEngine, RiskEngine.
- **Repository status:** UNKNOWN. No existing file. FSD Section 9
  documents an explicit non-rule (entry framed as a "logical"
  judgment, not indicator-based), which is a stronger finding than
  plain UNKNOWN but does not supply a class shape beyond "produces an
  enter/do-not-enter decision."

## 12. ExitEngine

- **Purpose:** "Exit" (FSD Section 10, workflow step 10).
- **Repository rule status:** `docs/TRADINGVIEW_STRATEGY_BIBLE.md`'s
  EXIT category is empty.
- **Inputs:** Open position state; stop-loss/target reference points;
  Reversal identification (REVERSAL-001), if evidenced.
- **Outputs:** An exit decision.
- **Dependencies:** RiskEngine, ReversalCalculator (REVERSAL-001).
- **Repository status:** UNKNOWN for the Exit decision itself
  (documented non-rule, same status class as TradeEngine). Its
  Reversal sub-input has PARTIAL status via the existing
  `trading_engine/calculators/reversal_calculator.py` (registers and
  raises `NotImplementedError`; REVERSAL-001 is however "the
  worst-evidenced rule in the project" per FSD Section 10).

## 13. RiskEngine

- **Purpose:** Support "Trade Management" (FSD Section 11, workflow
  step 9) with stop-loss/risk-factor handling.
- **Inputs:** Entry price; Opponent High/Low (illustrative reference
  point only, per the 650-strike example cited in FSD Section 11).
- **Outputs:** A stop-loss/risk-acceptance decision.
- **Dependencies:** TradeEngine, CompetitorEngine.
- **Repository status:** UNKNOWN. No existing file. FSD Section 11
  documents an explicit, repeated non-rule ("nobody can fix a
  stop-loss for you"), with two mutually inconsistent illustrative
  point-count figures, never reconciled — stronger than plain UNKNOWN
  but still no class-shape evidence beyond "produces a stop-loss/
  risk-acceptance decision."

## 14. PaperTradeEngine

- **Purpose:** Not itself named as one of the FSD's 15
  engines/components (the workflow's final named step is "Exit"), but
  implied by `research/analysis/EVIDENCE_ACQUISITION_ROADMAP.md`'s
  "Long-term" roadmap item, reused verbatim in
  `IMPLEMENTATION_UNLOCK_SEQUENCE.md`: "Paper trading (Milestone 4.8)
  follows Backtest in the roadmap's sequence." Included here per the
  milestone brief's own example-class list.
- **Inputs/Outputs:** UNKNOWN — no paper-trading data shape or
  simulated-fill mechanism is evidenced anywhere.
- **Dependencies:** TradeEngine, ExitEngine, RiskEngine (by roadmap
  sequencing, not by any evidenced data dependency).
- **Repository status:** UNKNOWN. No existing file.
  `IMPLEMENTATION_UNLOCK_SEQUENCE.md` states Paper trading is
  "explicitly gated" behind Backtest, itself gated behind real rule
  implementations existing.

## 15. DashboardService

- **Purpose:** Present the workflow's state and outputs to a user in
  real time (FSD Section 14).
- **Inputs:** Top/Bottom Strike, captured Premium levels, Option range
  contents (if resolved), Competitor/Opponent state, TrendPoint/Edge
  state, Winner determination (if resolved), current state-machine
  state — i.e., read access to every other engine's output, per FSD
  Section 14's own "What can be restated" list.
- **Outputs:** UNKNOWN — "layout, refresh cadence, alerting, charting
  library, historical view... UNKNOWN — no repository evidence
  addresses dashboard specifics beyond restating the data concepts
  already established elsewhere" (FSD Section 14).
- **Dependencies:** StrikeEngine, PremiumSnapshotEngine,
  OptionRangeEngine, CompetitorEngine, TrendEngine, WinnerEngine, the
  State Machine (FSD Section 15) — read-only, by FSD Section 14's own
  restated list.
- **Repository status:** UNKNOWN. No existing file. "Zero mentions of
  any dashboard/UI specification anywhere in `docs/` or `research/`"
  (FSD Section 14).

## 16. StorageService

- **Purpose:** Not itself named as one of the FSD's 15 named
  engines/components, but implied by FSD Section 12's data-retention
  mention and by the existing `HistoryLoader`'s CSV-reading
  responsibility, generalized to a persistence boundary a live system
  would need. Included per the milestone brief's own example-class
  list.
- **Inputs/Outputs:** UNKNOWN — FSD Section 12: "data retention/replay
  requirements beyond what `REPLAY_ENGINE_ARCHITECTURE.md` already
  describes for the existing (business-logic-free) replay engine...
  All UNKNOWN."
- **Dependencies:** None evidenced beyond the general observation that
  every engine above would need some persistence boundary.
- **Repository status:** UNKNOWN for a live-storage service. PARTIAL
  precedent exists for the historical-data case only:
  `trading_engine/replay/history_loader.py`'s `HistoryLoader` already
  reads/parses/validates historical CSV candle data
  (`REPLAY_ENGINE_ARCHITECTURE.md` "Responsibilities").

## 17. ReplayService

- **Purpose:** Replay historical OHLC market data through the existing
  engine scaffolding for backtesting.
- **Repository status:** Already fully covered — **do not propose a
  duplicate.** `trading_engine/replay/replay_controller.py`'s
  `ReplayController` already coordinates `HistoryLoader`, a
  `ReplayClock`/`ReplaySession` pair, and (if supplied) a
  `StrategyEngine`, emitting diagnostic events throughout
  (`REPLAY_ENGINE_ARCHITECTURE.md` "Responsibilities" —
  `ReplayController`). This class satisfies the "ReplayService" role
  from the milestone's own hint list in full; no new class is proposed
  for it.
- **Inputs:** A CSV history file (via `HistoryLoader.from_csv()`); an
  optional `strategy_engine` + `context_factory` pair.
- **Outputs:** Replay position advancement; optional per-candle
  `StrategyEngine.run()` invocation via the injected
  `context_factory: Callable[[Candle], RuleExecutionContext]` seam.
- **Dependencies:** `HistoryLoader`, `ReplayClock`, `ReplaySession`,
  optionally `StrategyEngine`, `DiagnosticsSink`.

## Supporting infrastructure (already exists, cited for completeness)

- **StrategyEngine** (`trading_engine/engine/strategy_engine.py`) —
  orchestrates rule/calculator execution via `ExecutionPipeline` and
  `RuleRegistry`. Repository status: PARTIAL (orchestration shape
  fully built; carries no business mathematics itself by design).
- **ExecutionPipeline** (`trading_engine/engine/execution_pipeline.py`)
  — iteration, fail-fast/continue-on-error handling. Repository
  status: PARTIAL (own logic fully implemented and tested; needs no
  trading evidence to function, per `ARCHITECTURE_FREEZE_CHECKLIST.md`
  row "Execution pipeline").
- **RuleRegistry** (`trading_engine/rules/registry.py`) — topological
  dependency ordering, cycle detection. Repository status: PARTIAL
  (fully built; "Requires Evidence: No" per
  `ARCHITECTURE_FREEZE_CHECKLIST.md`).
- **CalculatorRegistry** (`trading_engine/calculators/registry.py`) —
  calculator registration/lookup, no execution ordering. Repository
  status: PARTIAL (fully built).
- **DiagnosticsSink** and its 3 implementations
  (`trading_engine/diagnostics/sink.py`) — see Document 3, reused
  directly rather than reinvented for ILogger/IDiagnostics.

---

## Status count summary

| Status | Count | Classes |
|---|---|---|
| READY | 0 | — |
| PARTIAL | 9 | StrikeEngine, WeeklyFutureCalculator, PremiumSnapshotEngine, TrendEngine, CompetitorEngine, ExitEngine (Reversal sub-input only), ReplayService, StrategyEngine/ExecutionPipeline/RuleRegistry/CalculatorRegistry (supporting infra, counted once as a group) |
| UNKNOWN | 8 | MarketDataProvider, OptionChainProvider, OptionRangeEngine, LevelEngine, WinnerEngine, TradeEngine, RiskEngine, PaperTradeEngine, DashboardService, StorageService |

(Note: ExitEngine and the supporting-infrastructure group each mix
PARTIAL/READY-adjacent sub-components; see each entry's own Repository
status line for the precise split rather than relying on this summary
row alone.)

---

Sources: `research/specification/REALTIME_TRADING_SPECIFICATION.md`
Sections 2-14; `research/analysis/KNOWLEDGE_DEPENDENCY_MATRIX.md`;
`research/analysis/FRAMEWORK_BASELINE_REPORT.md`;
`research/analysis/REPLAY_ENGINE_ARCHITECTURE.md`;
`research/analysis/SAFE_IMPLEMENTATION_SCOPE.md`;
`research/analysis/IMPLEMENTATION_UNLOCK_SEQUENCE.md`; direct reads of
`trading_engine/domain/*.py`, `trading_engine/calculators/*.py`,
`trading_engine/engine/*.py`, `trading_engine/replay/*.py`.

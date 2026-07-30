# Interface Map

Protocol-style contracts only, matching this repository's existing
`typing.Protocol` convention (`trading_engine/rules/protocols.py`,
`trading_engine/calculators/protocols.py`). Described in prose/
method-signature-as-text, not as actual Python code. Every interface
below corresponds to one or more classes in `CLASS_DIAGRAM.md`.

---

## 1. IMarketDataProvider

- **Would be implemented by:** MarketDataProvider (CLASS_DIAGRAM.md
  §1).
- **Structural shape (prose):** a method returning the provider's
  connection/session state; a method (or subscription mechanism) for
  receiving live tick or candle data; a method for closing/tearing
  down the connection.
- **Status:** UNKNOWN. No repository evidence of any specific method
  names, data shapes, or protocol pattern — FSD Section 13's "Zero
  mentions anywhere... of any specific broker, REST API, WebSocket
  protocol, or authentication mechanism" applies equally to this
  interface's exact shape, which is asserted here only as "a provider
  of live market data," the minimum shape the milestone's own workflow
  position requires.

## 2. IOptionProvider

- **Would be implemented by:** OptionChainProvider (CLASS_DIAGRAM.md
  §2).
- **Structural shape (prose):** a method returning option-contract
  quote/OHLC data for a given strike and side (Call/Put), consistent
  with the Call/Put first-candle High/Low inputs FSD Section 2 names.
- **Status:** UNKNOWN beyond that minimal input/output framing.

## 3. IStrikeCalculator

- **Would be implemented by:** StrikeEngine (CLASS_DIAGRAM.md §3), via
  the existing `Calculator` protocol.
- **Structural shape (prose):** mirrors the existing
  `trading_engine.calculators.protocols.Calculator` protocol exactly —
  an `id()` method, a `name()` method, a `description()` method, a
  `supported_rules()` method returning the `RuleReference`(s) this
  calculator's output supports, and a `calculate()` method taking a
  `CalculationContext` and returning a `CalculationResult`.
- **Status:** PARTIAL — this contract is not net-new; it is the
  existing `Calculator` protocol already satisfied by
  `strike_calculator.py`'s `StrikeCalculator` class. No new interface
  is proposed here; `IStrikeCalculator` is this document's naming
  alias for that already-existing structural contract, applied to the
  Strike Engine specifically.

## 4. ITrendCalculator

- **Would be implemented by:** TrendEngine (CLASS_DIAGRAM.md §8).
- **Structural shape (prose):** same as `IStrikeCalculator` — the
  existing `Calculator` protocol, already satisfied by
  `trend_calculator.py`'s `TrendCalculator` and `edge_calculator.py`'s
  `EdgeCalculator`.
- **Status:** PARTIAL — existing contract, no new interface needed.

## 5. ICompetitorCalculator

- **Would be implemented by:** CompetitorEngine (CLASS_DIAGRAM.md §9).
- **Structural shape (prose):** same as `IStrikeCalculator` — the
  existing `Calculator` protocol, already satisfied by
  `opponent_calculator.py`'s `OpponentCalculator`.
- **Status:** PARTIAL — existing contract, no new interface needed.

## 6. IWinnerEngine

- **Would be implemented by:** WinnerEngine (CLASS_DIAGRAM.md §10).
- **Structural shape (prose):** UNKNOWN — no method names, inputs, or
  outputs can be described beyond "would take the Competitor Engine
  and Trend Engine's outputs (by workflow position only) and produce
  some winner determination," since no rule ID, entity ID, or Bible
  category corresponds to a "Winner" concept anywhere (FSD Section 8).
- **Status:** UNKNOWN. This is the interface with the least structural
  grounding of any in this document — even its method shape cannot be
  stated beyond the input/output framing already given in
  CLASS_DIAGRAM.md §10.

## 7. ITradeExecutor

- **Would be implemented by:** TradeEngine / Entry Engine
  (CLASS_DIAGRAM.md §11).
- **Structural shape (prose):** a method taking a chosen direction and
  a qualifying TrendPoint event, returning an entry decision
  (enter/do-not-enter). No numeric trigger or indicator-based
  parameter is evidenced (FSD Section 9's documented non-rule).
- **Status:** UNKNOWN for the decision logic; the input/output framing
  above is the only structurally describable part.

## 8. IPaperTrader

- **Would be implemented by:** PaperTradeEngine (CLASS_DIAGRAM.md
  §14).
- **Structural shape (prose):** UNKNOWN beyond "would consume
  TradeEngine/ExitEngine/RiskEngine outputs and record a simulated
  trade outcome," per the roadmap sequencing
  `IMPLEMENTATION_UNLOCK_SEQUENCE.md` cites (paper trading gated
  behind Backtest, itself gated behind real rule implementations).
- **Status:** UNKNOWN. No method names or data shapes evidenced.

## 9. ILogger / IDiagnostics

- **Already exists — reuse, not reinvent.** This capability is already
  satisfied by `trading_engine.diagnostics.sink.DiagnosticsSink`, a
  `typing.Protocol` with a single `emit(event: DiagnosticEvent) -> None`
  method, and its 3 existing implementations
  (`NullDiagnosticsSink`, `InMemoryDiagnosticsSink`,
  `StandardLoggingDiagnosticsSink` — `trading_engine/diagnostics/sink.py`).
  `trading_engine/replay/replay_controller.py`'s `ReplayController`
  already reuses this exact protocol for its own 6 replay diagnostic
  events (`REPLAY_ENGINE_ARCHITECTURE.md`: "emits every diagnostic
  event through an injected `DiagnosticsSink`, reusing the diagnostics
  package exactly as built"). Any new engine in `market_data/` or
  `live/` would follow the same reuse pattern — inject a
  `DiagnosticsSink`, do not define a new logging interface.
- **Status:** PARTIAL/existing — no new interface proposed.

## 10. IExitCalculator (companion to ITradeExecutor, not in the milestone's own hint list but implied by ExitEngine's existence in CLASS_DIAGRAM.md §12)

- **Would be implemented by:** ExitEngine.
- **Structural shape (prose):** a method taking open position state
  and stop-loss/target reference points, returning an exit decision.
  Its Reversal sub-input already has a concrete existing contract —
  the same `Calculator` protocol, satisfied by
  `reversal_calculator.py`'s `ReversalCalculator`.
- **Status:** UNKNOWN for the exit-decision logic itself (documented
  non-rule, FSD Section 10); PARTIAL for the Reversal sub-input via
  the existing `Calculator` protocol.

## 11. IRiskEngine (companion, implied by RiskEngine's existence in CLASS_DIAGRAM.md §13)

- **Would be implemented by:** RiskEngine.
- **Structural shape (prose):** a method taking entry price and
  Opponent High/Low as an illustrative reference, returning a
  stop-loss/risk-acceptance decision.
- **Status:** UNKNOWN. Documented non-rule (FSD Section 11); no fixed
  formula evidenced.

---

## Cross-reference to CLASS_DIAGRAM.md

| Interface | Implementing class(es) |
|---|---|
| IMarketDataProvider | MarketDataProvider |
| IOptionProvider | OptionChainProvider |
| IStrikeCalculator | StrikeEngine (existing `Calculator` protocol) |
| ITrendCalculator | TrendEngine (existing `Calculator` protocol) |
| ICompetitorCalculator | CompetitorEngine (existing `Calculator` protocol) |
| IWinnerEngine | WinnerEngine |
| ITradeExecutor | TradeEngine |
| IPaperTrader | PaperTradeEngine |
| ILogger / IDiagnostics | already `DiagnosticsSink` — reused, not new |
| IExitCalculator | ExitEngine |
| IRiskEngine | RiskEngine |

No interface is proposed for DashboardService or StorageService in
this document — FSD Section 14 and Section 12 respectively provide no
evidence of any method shape beyond "reads other engines' outputs" /
"persists data," which CLASS_DIAGRAM.md §15-16 already states at the
class level; inventing a method-level contract beyond that would not
be grounded in any cited source.

---

Sources: `trading_engine/rules/protocols.py`,
`trading_engine/calculators/protocols.py`,
`trading_engine/diagnostics/sink.py`,
`trading_engine/replay/replay_controller.py` (direct reads);
`research/specification/REALTIME_TRADING_SPECIFICATION.md` Sections
2-14; `research/implementation/CLASS_DIAGRAM.md` (this directory).

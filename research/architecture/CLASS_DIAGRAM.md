# Class Diagram

Phase 2 (System Architecture) deliverable. UML class diagrams (Mermaid
`classDiagram`) for the objects in `DATA_DICTIONARY.md` and the
modules in `MODULE_ARCHITECTURE.md`. Design-only — no Python code.
Fields shown as `MISSING` correspond exactly to **MISSING INFORMATION**
markers in `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md`
v1.1; they are included in the diagrams for completeness (a reader
should see the full intended shape of each class) but must not be
treated as resolved.

---

## 1. Core Domain Classes

```mermaid
classDiagram
    class MarketSnapshot {
        +datetime timestamp
        +Decimal underlying_price
        +Decimal open
        +Decimal high
        +Decimal low
        +Decimal close
        +int volume
    }

    class WeeklyFuture {
        +UUID weekly_future_id
        +UUID session_id
        +Decimal high
        +Decimal low
        +datetime calculated_at
        +MISSING formula()
    }

    class StrikeSelection {
        +UUID session_id
        +Decimal top_strike
        +Decimal bottom_strike
        +datetime selected_at
        +MISSING selection_rule()
    }

    class ReferenceLevel {
        +Decimal strike
        +Decimal ce_high
        +Decimal ce_low
        +Decimal pe_high
        +Decimal pe_low
        +LadderPosition ladder_position
    }

    class LadderPosition {
        <<enumeration>>
        ITM_6
        ITM_5
        ITM_4
        ITM_3
        ITM_2
        ITM_1
        ATM
        OTM_1
        OTM_2
        OTM_3
        OTM_4
        OTM_5
        OTM_6
    }

    class TPState {
        +Decimal strike
        +MISSING tp_value_or_flag
        +bool qualified
        +MISSING competitor_strike
        +datetime last_updated
    }

    class WinnerEvent {
        +UUID winner_event_id
        +datetime candle_timestamp
        +Side winning_side
        +Decimal winning_strike
    }

    class Side {
        <<enumeration>>
        CE
        PE
    }

    class TradeSignal {
        +UUID signal_id
        +UUID winner_event_id
        +Side side
        +Decimal strike
        +datetime raised_at
        +bool accepted
    }

    class Position {
        +UUID trade_id
        +Decimal entry_strike
        +Side entry_side
        +MISSING entry_price
        +Decimal target_level
        +Decimal support_level
        +Decimal competitor_monitor_strike
        +MISSING stop_loss_level
        +MISSING trailing_stop_state
        +PositionStatus status
        +ExitReason exit_reason
        +MISSING exit_price
        +datetime opened_at
        +datetime closed_at
    }

    class PositionStatus {
        <<enumeration>>
        Active
        Closed
    }

    class ExitReason {
        +UUID trade_id
        +ExitReasonType reason
        +datetime triggered_at
    }

    class ExitReasonType {
        <<enumeration>>
        TargetHit
        CompetitorLevelHit
        StopLossHit
        TrailingStopTriggered
    }

    class DefeatEvent {
        +UUID event_id
        +Decimal strike
        +MISSING crossed_level
        +datetime occurred_at
        +MISSING effect
    }

    class TradeState {
        +UUID session_id
        +StateName current_state
        +datetime entered_at
        +UUID active_position_id
    }

    WeeklyFuture "1" --> "1" MarketSnapshot : computed from first candle
    StrikeSelection "1" --> "1" WeeklyFuture : derives (relationship MISSING)
    StrikeSelection "1" --> "13" ReferenceLevel : centers ladder on
    ReferenceLevel "1" --> "1" LadderPosition
    ReferenceLevel "1" --> "0..*" TPState : feeds qualification
    TPState "1" --> "0..1" WinnerEvent : feeds touch evaluation
    WinnerEvent "1" --> "1" Side
    WinnerEvent "1" --> "1" TradeSignal : immediately generates
    TradeSignal "0..1" --> "0..1" Position : accepted creates
    Position "1" --> "1" PositionStatus
    Position "1" --> "0..1" ExitReason : closes with
    ExitReason "1" --> "1" ExitReasonType
    ReferenceLevel "1" --> "0..*" DefeatEvent : crossing produces
    TradeState "1" --> "0..1" Position : tracks active
```

---

## 2. Module Interfaces (Protocols)

Following this repository's established pattern (`typing.Protocol`,
structural typing — see `trading_engine.diagnostics.sink.DiagnosticsSink`,
`trading_engine.market_data.upstox_provider.RestTransport`), every
module in `MODULE_ARCHITECTURE.md` exposes a Protocol interface. Shown
here as UML interfaces; no implementation.

```mermaid
classDiagram
    class IWeeklyFutureCalculator {
        <<interface>>
        +calculate(candle) WeeklyFuture
    }

    class IStrikeSelector {
        <<interface>>
        +select(weekly_future) StrikeSelection
    }

    class IReferenceLevelBuilder {
        <<interface>>
        +build(strikes, candle_data) tuple~ReferenceLevel~
    }

    class ITPEngine {
        <<interface>>
        +update(snapshot, levels) TPState
    }

    class IQualificationEvaluator {
        <<interface>>
        +evaluate(tp_state) bool
    }

    class IWinnerEngine {
        <<interface>>
        +evaluate(snapshot, levels) WinnerEvent
    }

    class IEntryEngine {
        <<interface>>
        +try_enter(winner_event, current_position) TradeSignal
    }

    class IExitEngine {
        <<interface>>
        +evaluate(position, snapshot, levels) ExitReason
    }

    class IPositionManager {
        <<interface>>
        +open(signal) Position
        +close(position, reason) Position
        +active() Position
    }

    class IRiskEvaluator {
        <<interface>>
        +check_stop_loss(position, snapshot) bool
        +check_trailing_stop(position, snapshot) bool
    }

    class IDefeatDetector {
        <<interface>>
        +detect(snapshot, levels) DefeatEvent
    }

    class IMarketDataProvider {
        <<interface>>
        +subscribe(instrument) MarketSnapshot
        +get_first_five_minute_candle(instrument) MarketSnapshot
    }

    class IEventBus {
        <<interface>>
        +publish(event) void
        +subscribe(event_type, handler) void
    }

    class IDiagnosticsSink {
        <<interface>>
        +emit(event) void
    }

    class IRepository~T~ {
        <<interface>>
        +save(entity) void
        +load(id) T
    }
```

---

## 3. Composition / Aggregation Detail

```mermaid
classDiagram
    class TradingSession {
        +UUID session_id
        +date trading_date
    }

    class SessionOrchestrator {
        <<state_machine module>>
        +TradeState state
        +advance(event) void
    }

    TradingSession "1" *-- "1" WeeklyFuture : composition - owns exactly one
    TradingSession "1" *-- "1" StrikeSelection : composition
    TradingSession "1" *-- "13" ReferenceLevel : composition
    TradingSession "1" o-- "0..*" Position : aggregation - trades across the session
    TradingSession "1" *-- "1" SessionOrchestrator : composition
    SessionOrchestrator "1" --> "1" TradeState : owns current state

    note for TradingSession "Composition (filled diamond): WeeklyFuture/\nStrikeSelection/ReferenceLevel cannot outlive\ntheir TradingSession - one-per-session, per\nSpecification Section 3's lifecycle.\n\nAggregation (hollow diamond): Position instances\nare created/closed across the session's lifetime\nbut are independently addressable (e.g. by storage/\nfor cross-session backtest analysis)."
```

---

## 4. Inheritance — Used Only Where Necessary

Per instruction 9 (single responsibility) and this repository's own
established convention (`typing.Protocol` over inheritance
hierarchies — see `docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md`'s
existing preference, reflected throughout `trading_engine/`), this
architecture uses **composition and Protocol interfaces almost
everywhere**. The one place inheritance is structurally justified:

```mermaid
classDiagram
    class StrategyError {
        <<exception base>>
    }
    class MarketDataError
    class CalculationError
    class ValidationError
    class RiskError

    StrategyError <|-- MarketDataError
    StrategyError <|-- CalculationError
    StrategyError <|-- ValidationError
    StrategyError <|-- RiskError

    note for StrategyError "Mirrors this repository's established\nper-package exception hierarchy convention\n(one base exception per package, e.g.\ntrading_engine.market_data.exceptions.MarketDataError).\nException inheritance is a Python-idiomatic\nexception; it is not used for domain/behavioral\nclasses anywhere else in this architecture."
```

No other inheritance hierarchy is proposed. `ExitReasonType`,
`PositionStatus`, `Side`, `LadderPosition` are enumerations, not
inheritance; every engine module (`ITPEngine`, `IWinnerEngine`, etc.)
is a Protocol interface with independent implementations, not a class
hierarchy.

---

## 5. Dependency Relationships (Module-Level, UML View)

```mermaid
classDiagram
    class MarketDataModule
    class WeeklyFutureModule
    class StrikeSelectorModule
    class ReferenceBuilderModule
    class TPEngineModule
    class QualificationModule
    class WinnerModule
    class EntryModule
    class ExitModule
    class PositionModule
    class RiskModule
    class DefeatModule
    class EventsModule
    class StateMachineModule
    class DiagnosticsModule

    WeeklyFutureModule ..> MarketDataModule : depends on
    StrikeSelectorModule ..> WeeklyFutureModule : depends on
    ReferenceBuilderModule ..> StrikeSelectorModule : depends on
    ReferenceBuilderModule ..> MarketDataModule : depends on
    TPEngineModule ..> ReferenceBuilderModule : depends on
    TPEngineModule ..> MarketDataModule : depends on
    QualificationModule ..> TPEngineModule : depends on
    WinnerModule ..> ReferenceBuilderModule : depends on
    WinnerModule ..> TPEngineModule : depends on
    WinnerModule ..> QualificationModule : depends on
    EntryModule ..> WinnerModule : depends on
    EntryModule ..> PositionModule : depends on
    ExitModule ..> PositionModule : depends on
    ExitModule ..> ReferenceBuilderModule : depends on
    ExitModule ..> RiskModule : depends on
    RiskModule ..> PositionModule : depends on
    DefeatModule ..> ReferenceBuilderModule : depends on
    DefeatModule ..> MarketDataModule : depends on
    StateMachineModule ..> PositionModule : depends on

    WeeklyFutureModule ..> EventsModule : depends on
    StrikeSelectorModule ..> EventsModule : depends on
    ReferenceBuilderModule ..> EventsModule : depends on
    TPEngineModule ..> EventsModule : depends on
    WinnerModule ..> EventsModule : depends on
    EntryModule ..> EventsModule : depends on
    ExitModule ..> EventsModule : depends on
    PositionModule ..> EventsModule : depends on
    StateMachineModule ..> EventsModule : depends on

    DiagnosticsModule <.. MarketDataModule : observed by
    DiagnosticsModule <.. TPEngineModule : observed by
    DiagnosticsModule <.. WinnerModule : observed by
    DiagnosticsModule <.. ExitModule : observed by

    note for EventsModule "Foundational - zero outgoing dependencies.\nEvery other module depends on it, never\nthe reverse (mirrors trading_engine.diagnostics)."
```

---

## 6. Consolidated MISSING INFORMATION (Class Diagram Scope)

Every field marked `MISSING` in Section 1's class diagram corresponds
1:1 to a `STRATEGY_FUNCTIONAL_SPECIFICATION.md` Section 20 item:
`WeeklyFuture` formula, `StrikeSelection` rule, `TPState.tp_value_or_flag`/`.competitor_strike`,
`Position.entry_price`/`.stop_loss_level`/`.trailing_stop_state`/`.exit_price`,
`DefeatEvent.crossed_level`/`.effect`. None are resolved by this
document.

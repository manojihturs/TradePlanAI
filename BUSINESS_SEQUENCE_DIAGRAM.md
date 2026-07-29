# Business Sequence Diagram

Companion to `BUSINESS_ARCHITECTURE.md`. Shows how the six blocked modules would interact end-to-end once implemented, layered onto the already-built framework. Solid arrows/labels mark events that exist today in `src/core/events.py`; dashed arrows/labels marked *(proposed)* mark events named only in `research/architecture/EVENT_CATALOG.md`, not yet implemented anywhere.

No timing, ordering-within-tick, or trigger cadence shown here is a resolved business rule — sequencing is drawn as a structural sketch of dependency order only, per the already-known dependency chain (`WeeklyFuture → StrikeSelector → ReferenceBuilder/TPEngine → QualificationEngine → WinnerEngine → PositionManager → ExitEngine`), not as a claim about real-time behavior.

```mermaid
sequenceDiagram
    participant MD as Market Data (candle)
    participant WFC as WeeklyFutureCalculator
    participant SS as StrikeSelector
    participant RB as ReferenceBuilder (built)
    participant TPE as TPEngine
    participant QE as QualificationEngine
    participant WE as WinnerEngine (built)
    participant PM as PositionManager (built)
    participant EE as ExitEngine (built)
    participant SLE as StopLossEngine
    participant TSE as TrailingStopEngine
    participant TM as TradeManager (built)

    MD->>WFC: first 5-min candle (MarketSnapshot)
    WFC->>WFC: calculate()
    WFC-->>TM: WeeklyFutureCalculatedEvent

    WFC->>SS: WeeklyFuture
    SS->>SS: select()
    SS-->>TM: StrikeSelectedEvent

    SS->>RB: Top/Bottom Strike (UNRESOLVED: wiring not yet built)
    RB->>RB: build first-candle reference levels (Spec Rule 1, implemented)
    RB--)TPE: ReferenceLevelsGenerated (proposed, not implemented)

    MD->>TPE: MarketSnapshot (cadence UNRESOLVED)
    TPE->>TPE: update()
    TPE--)QE: TPUpdated (proposed, not implemented)

    QE->>QE: evaluate()
    QE--)WE: QualificationChanged (proposed, not implemented)

    Note over TPE,WE: How TP/Qualification state actually informs<br/>WinnerEngine.evaluate() is UNRESOLVED —<br/>WinnerEngine as built takes CE/PE snapshots directly today.

    MD->>WE: CE/PE MarketSnapshots
    WE->>WE: evaluate()
    WE-->>TM: WinnerDetectedEvent

    TM->>PM: open position
    PM-->>TM: TradeOpenedEvent

    loop each evaluation cycle
        MD->>EE: MarketSnapshot
        EE->>EE: check Target
        EE->>EE: check Competitor (Spec Rule 2, implemented)
        EE->>SLE: check(position, snapshot)
        SLE-->>EE: bool (rule UNRESOLVED)
        EE->>TSE: check(position, snapshot)
        TSE-->>EE: bool (rule UNRESOLVED, needs peak-favorable-excursion state)
        alt any check True
            EE->>PM: close_position()
            PM->>TM: close()
            TM-->>MD: TradeClosedEvent / TargetHitEvent / CompetitorHitEvent
        end
    end
```

## Notes

- `WFC`/`SS`/`TPE`/`QE`/`SLE`/`TSE` boxes represent Protocol stubs today (`UnresolvedBusinessRuleError` on any real call) — the diagram shows the *shape* of interaction once implemented, not current runtime behavior.
- The `RB → TPE` and `TPE → QE → WE` links are drawn dashed because the events they'd travel on don't exist in code, **and** because no evidence describes whether this path is event-driven at all versus directly invoked (matching how `WFC`/`SS` are invoked directly today rather than via bus subscription).
- The `EE` loop, `SLE`/`TSE` call shape, and the transitive `TradeClosedEvent` publish path are drawn solid/direct because they are real, already-built, already-tested code — only the boolean *logic inside* `SLE.check()`/`TSE.check()` is unresolved.

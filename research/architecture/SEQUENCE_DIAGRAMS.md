# Sequence Diagrams

Phase 2 (System Architecture) deliverable. Mermaid sequence diagrams
for the 9 required scenarios, built from `EVENT_CATALOG.md` and
`MODULE_ARCHITECTURE.md`. No business rule is invented; every
**MISSING INFORMATION** marker below carries forward a gap already
recorded in `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md`
v1.1.

---

## 1. Market Open

```mermaid
sequenceDiagram
    participant Clock
    participant MarketData as market_data/
    participant WF as weekly_future/
    participant Diag as diagnostics/

    Clock->>MarketData: session start (MISSING: pre-09:15 behavior)
    MarketData->>MarketData: begin capturing first 5-min candle (09:15-09:20)
    MarketData->>Diag: MarketDataConnected (or equivalent)
    Note over MarketData: candle forms over 09:15-09:20
    MarketData->>WF: candle complete (09:20)
```

---

## 2. Weekly Future Calculation

```mermaid
sequenceDiagram
    participant MarketData as market_data/
    participant WF as weekly_future/
    participant StrikeSel as strike_selector/
    participant Events as events/
    participant Storage as storage/

    MarketData->>WF: first 5-min candle (09:15-09:20)
    WF->>WF: calculate(candle) [MISSING: formula]
    alt calculation succeeds
        WF->>Events: publish WeeklyFutureCalculated
        Events->>StrikeSel: WeeklyFutureCalculated
        Events->>Storage: WeeklyFutureCalculated (audit)
    else calculation fails
        Note over WF: MISSING INFORMATION - no failure/retry path specified
    end
```

---

## 3. Strike Selection

```mermaid
sequenceDiagram
    participant WF as weekly_future/
    participant StrikeSel as strike_selector/
    participant RefBuilder as reference_builder/
    participant Events as events/

    WF->>StrikeSel: WeeklyFutureCalculated(high, low)
    StrikeSel->>StrikeSel: select Top Strike (ATM) [MISSING: ATM basis]
    StrikeSel->>StrikeSel: select Bottom Strike (ATM) [MISSING: ATM basis]
    alt top_strike == bottom_strike
        Note over StrikeSel: MISSING INFORMATION - not addressed by Specification
    end
    StrikeSel->>Events: publish StrikeSelected
    Events->>RefBuilder: StrikeSelected(top_strike, bottom_strike)
```

---

## 4. Winner Detection

```mermaid
sequenceDiagram
    participant MarketData as market_data/
    participant RefBuilder as reference_builder/
    participant TP as tp_engine/
    participant Qual as qualification/
    participant Winner as winner/
    participant Events as events/

    RefBuilder->>TP: ReferenceLevelsGenerated (13 levels)
    loop from 09:21 AM, cadence MISSING INFORMATION
        MarketData->>TP: MarketSnapshot
        TP->>TP: update TP High/TP Low [MISSING: competitor identity]
        TP->>Events: publish TPUpdated
        TP->>Qual: evaluate sustain test
        alt qualification flips
            Qual->>Events: publish QualificationChanged
        end
        Events->>Winner: TPUpdated / QualificationChanged
        Winner->>Winner: check same-candle CE+PE touch
        alt both touched this candle
            Winner->>Winner: determine winning side (CONFIRMED - no tie-break needed, Rule 3)
            Winner->>Events: publish WinnerDetected
        end
    end
```

---

## 5. Trade Entry

```mermaid
sequenceDiagram
    participant Winner as winner/
    participant Entry as entry/
    participant Position as position/
    participant Exitm as exit/
    participant Events as events/

    Winner->>Entry: WinnerDetected(side, strike)
    Entry->>Position: active()?
    alt no active position
        Position-->>Entry: None
        Entry->>Entry: build TradeSignal (entry_price MISSING INFORMATION)
        Entry->>Position: open(signal)
        Position->>Position: create Position [status=Active]
        Position->>Events: publish EntryOpened
        Events->>Exitm: EntryOpened(trade_id, target_level, support_level, competitor_monitor_strike)
        Note over Exitm: begin monitoring (Target/Support/Competitor\nmapping CONFIRMED per Spec Rule 2)
    else active position exists
        Position-->>Entry: Position(active)
        Entry->>Entry: ignore signal (CONFIRMED, Spec Rule 4)
        Note over Entry: no event published - signal discarded, not queued
    end
```

---

## 6. Trade Exit

```mermaid
sequenceDiagram
    participant MarketData as market_data/
    participant Exitm as exit/
    participant Risk as risk/
    participant Position as position/
    participant Events as events/

    loop while Position.status == Active, cadence MISSING INFORMATION
        MarketData->>Exitm: MarketSnapshot
        Exitm->>Exitm: check Target(S+1 or S-1) [CONFIRMED, Rule 2]
        Exitm->>Exitm: check Competitor level [which of High/Low: MISSING INFORMATION]
        Exitm->>Risk: check_stop_loss(position, snapshot)
        Risk-->>Exitm: bool [rule itself MISSING INFORMATION]
        Exitm->>Risk: check_trailing_stop(position, snapshot)
        Risk-->>Exitm: bool [activation/step MISSING INFORMATION]
        alt multiple conditions met simultaneously
            Note over Exitm: MISSING INFORMATION - no precedence rule specified
        else exactly one condition met
            Exitm->>Events: publish TargetHit / CompetitorLevelHit / StopLossHit / TrailingStopTriggered
            Exitm->>Position: close(position, reason)
            Position->>Position: status = Closed
            Position->>Events: publish TradeClosed
        end
    end
```

---

## 7. Recalculation

```mermaid
sequenceDiagram
    participant Position as position/
    participant Recalc as recalculation (orchestration)
    participant TP as tp_engine/
    participant Qual as qualification/
    participant Winner as winner/
    participant Entry as entry/
    participant Events as events/

    Position->>Events: TradeClosed
    Events->>Recalc: TradeClosed
    Recalc->>TP: recompute TP High/TP Low [Spec Rule 5, CONFIRMED as required]
    TP-->>Recalc: TPState
    Recalc->>Qual: recompute Qualification
    Qual-->>Recalc: qualification result
    Recalc->>Winner: recompute Winner
    Note over Recalc,Winner: MISSING INFORMATION - against the in-progress\ncandle or the next fresh candle is unstated
    Winner-->>Recalc: WinnerEvent or none
    Recalc->>Events: publish RecalculationCompleted
    Events->>Entry: RecalculationCompleted (next trade now permitted)
```

---

## 8. Replay Engine

```mermaid
sequenceDiagram
    participant User
    participant Replay as replay/
    participant MarketData as market_data/
    participant StateMachine as state_machine/
    participant AllEngines as tp_engine / winner / entry / exit (unmodified)
    participant Storage as storage/

    User->>Replay: load(historical_file)
    Replay->>Storage: read historical OHLC/tick data
    Storage-->>Replay: candle/tick sequence
    User->>Replay: play(speed) / step()
    loop for each historical candle/tick
        Replay->>MarketData: inject MarketSnapshot (as if live)
        MarketData->>StateMachine: forward through normal event pipeline
        StateMachine->>AllEngines: drive tp_engine/winner/entry/exit exactly as in live trading
        AllEngines-->>Storage: persist Position/ExitReason/WinnerEvent history
    end
    User->>Replay: pause() / step backward (if supported - MISSING INFORMATION on rewind semantics)
```

---

## 9. Backtest Engine

```mermaid
sequenceDiagram
    participant User
    participant Backtest as backtest/
    participant Replay as replay/
    participant Storage as storage/
    participant Report as BacktestReport

    User->>Backtest: run(session_date_range)
    loop for each historical session in range
        Backtest->>Replay: load(session_file)
        Replay->>Replay: play at max speed, no manual step
        Replay-->>Storage: persist Position/ExitReason history for this session
    end
    Backtest->>Storage: aggregate all sessions' Position/ExitReason records
    Storage-->>Backtest: aggregated records
    Backtest->>Report: compute win rate, exit-reason distribution
    Note over Backtest,Report: MISSING INFORMATION - no P&L/scoring formula\nbeyond the Trailing Stop's own "+3 net" guarantee\nis defined anywhere in the Specification
    Backtest-->>User: BacktestReport
```

---

## 10. Cross-Cutting Notes

- Every diagram above reuses the **same** `tp_engine/`, `winner/`, `entry/`, `exit/`, `position/`, `risk/` modules — Replay and Backtest are data-source/orchestration wrappers, not parallel strategy implementations, per `MODULE_ARCHITECTURE.md` Section 3.15–3.16's forbidden-dependency rules.
- Every `MISSING INFORMATION` note in these diagrams is a direct carry-forward from `STRATEGY_FUNCTIONAL_SPECIFICATION.md` Section 20 — no new gap is introduced here, and none is resolved.

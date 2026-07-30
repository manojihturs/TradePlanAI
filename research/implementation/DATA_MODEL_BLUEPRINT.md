# Data Model Blueprint

Grounded against what already exists in `trading_engine/domain/` and
`trading_engine/replay/history_loader.py`, versus what would be
net-new. For each model: Properties (plain field list + type, grounded
in evidence — no invented properties for UNKNOWN mechanisms),
Purpose, Relationships to other models in this document.

---

## 1. MarketTick

- **Already exists?** No.
- **Properties:** UNKNOWN — no tick-level schema is evidenced anywhere
  (FSD Section 12: "tick vs. candle-close granularity... UNKNOWN").
- **Purpose:** Would represent a single live price update from
  MarketDataProvider, if/when tick-level (as opposed to candle-level)
  granularity is evidenced as required.
- **Relationships:** Would feed OHLC/Candle aggregation, if evidenced.

## 2. OHLC

- **Already exists as:** `trading_engine.replay.history_loader.Candle`
  (`trading_engine/replay/history_loader.py`).
- **Properties (as they exist today):** `timestamp: datetime`,
  `open: Decimal`, `high: Decimal`, `low: Decimal`, `close: Decimal`,
  `volume: int`.
- **Purpose:** An immutable, structurally-validated OHLC candle,
  currently used for historical replay (`HistoryLoader` parses CSV
  rows into this type). A live equivalent (produced by
  MarketDataProvider rather than `HistoryLoader`) is implied by FSD
  Section 12's data needs but not itself evidenced as a distinct type
  — the existing `Candle` class is the structural precedent this
  blueprint reuses rather than duplicates.
- **Relationships:** Feeds Strike selection (via Weekly Future
  arithmetic, itself computed from Call/Put first-candle High/Low);
  consumed today by `ReplayController`'s `context_factory` seam.

## 3. OptionContract

- **Already exists?** No dedicated domain file.
- **Properties:** UNKNOWN beyond the concept that a contract has a
  side (Call/Put) and first-candle High/Low values — FSD Section 3:
  "No rule defines Premium as a first-class concept yet (which
  contract, CE/PE/both)."
- **Purpose:** Would represent one option contract's identity and
  price series, feeding Weekly Future arithmetic and Premium capture.
- **Relationships:** Feeds Weekly Future High/Low; feeds Premium.

## 4. Strike

- **Already exists as:** `trading_engine.domain.strike.Strike`
  (`trading_engine/domain/strike.py`).
- **Properties (as they exist today):** `strike_id: uuid.UUID`,
  `session_id: uuid.UUID`, `price: Decimal`.
- **Purpose:** The selected Top/Bottom Strike for a session (FSD
  Section 2). `research/analysis/KNOWLEDGE_GAP_INVENTORY.md` Section 3
  notes no price-value type, expiry, or option-side attribute is
  evidenced beyond these three fields.
- **Relationships:** Produced from Weekly Future High/Low; owns a
  TrendPoint (TREND-001: "every analysed strike maintains... a Trend
  Point Low"); referenced by Opponent (`Opponent.strike_id`).

## 5. PremiumLevel

- **Already exists as (thin form):**
  `trading_engine.domain.premium.Premium`
  (`trading_engine/domain/premium.py`).
- **Properties (as they exist today):** `premium_id: uuid.UUID`,
  `value: Decimal`, `observed_at: datetime` — "id/value/timestamp
  only," deliberately thin (`docs/architecture/DOMAIN_ARCHITECTURE.md`
  lines 188-190, quoted in FSD Section 3).
- **Purpose:** A raw observed premium value at a point in time. FSD
  Section 3 explicitly states no CE/PE-specific structure or "capture"
  formula is evidenced — this blueprint does not add such structure.
- **Relationships:** Feeds REVERSAL-001 (Reversal identification, FSD
  Section 10) as its sole evidenced consumer
  (`KNOWLEDGE_DEPENDENCY_MATRIX.md` Chain B).

## 6. TrendState

- **Already exists as:** `trading_engine.domain.trend_point.TrendPoint`
  (`trading_engine/domain/trend_point.py`).
- **Properties (as they exist today):** `trend_point_id: uuid.UUID`,
  `strike_id: uuid.UUID`, `value: Decimal`, `marked_at: datetime`.
- **Purpose:** A per-Strike dynamically-updated Trend Point Low
  (TREND-001). FSD Section 7: no formula connecting a Strike to its TP
  Low value is evidenced — only that the field exists and belongs to a
  Strike.
- **Relationships:** Belongs to a Strike; referenced by Opponent (via
  `Opponent.own_trend_point_id`); feeds the Edge condition (TREND-003,
  compares a Strike's TrendPoint to its Opponent's TrendPoint).

## 7. CompetitorState

- **Already exists as:** `trading_engine.domain.opponent.Opponent`
  (`trading_engine/domain/opponent.py`).
- **Properties (as they exist today):** `opponent_id: uuid.UUID`,
  `strike_id: uuid.UUID`, `own_trend_point_id: uuid.UUID | None`,
  `high: Decimal | None`, `low: Decimal | None` — `high`/`low`
  documented in-code as "reserved attribute slots only," Evidence
  Count 0 for both (OPPONENT-002/003).
- **Purpose:** The Opponent an analyzed Strike must "defeat" to
  progress (OPPONENT-001). FSD Section 6 explicitly flags as
  unresolved whether this equals "competitor" elsewhere in the
  repository — this model is not renamed to avoid conflating the two.
- **Relationships:** Belongs to (via `strike_id`) the Strike it
  opposes; has its own TrendPoint (`own_trend_point_id`); feeds the
  Edge condition and OPPONENT-001's "defeated" evaluation.

## 8. WinnerDecision

- **Already exists?** No.
- **Properties:** Only what the FSD's workflow-step framing implies as
  a concept — which side won (a reference to a Strike or a direction),
  and when the determination was made. No scoring/confidence property
  is included, because "a targeted grep of TR-001.md for 'confidence'
  ... returned zero matches. No evidenced confidence-scoring mechanism
  exists anywhere" (FSD Section 8) — a `confidence` field is
  deliberately NOT listed here, since including it would invent an
  attribute the evidence doesn't support.
- **Purpose:** Would record the Winner Engine's output, if/when its
  mechanism is evidenced.
- **Relationships:** Would be produced from CompetitorEngine and
  TrendEngine outputs (by workflow position only); would feed
  TradeEngine's direction input.

## 9. TradeSignal

- **Already exists?** No.
- **Properties:** UNKNOWN beyond "chosen direction" and "a qualifying
  TrendPoint event" (FSD Section 9's "Inputs"). No entry-price or
  trigger-threshold property is listed, since FSD Section 9 documents
  entry as an explicit non-rule with "no fixed entry price rule, no
  fixed indicator, no numeric trigger."
- **Purpose:** Would represent an entry decision (enter/do-not-enter).
- **Relationships:** Produced from WinnerDecision (direction) and
  TrendState (qualifying event); gated by a RiskEngine risk-tolerance
  check (FSD Section 9 "Dependencies").

## 10. TradePosition

- **Already exists?** No. `research/specification/REALTIME_TRADING_SPECIFICATION.md`
  Section 15 notes: "No FLAT, IN_POSITION, ENTRY, or EXIT states are
  modeled" in `docs/STATE_MACHINE.md`, "since the existing Python
  implementation's FLAT/OPEN model is LEVEL 3 evidence, not assumed to
  reflect original strategy."
- **Properties:** UNKNOWN — no open-position schema is evidenced for
  this repository's Milestone-K2 strategy specifically (as distinct
  from the separate, not-assumed-equivalent `strategy/` package's own
  FLAT/OPEN model).
- **Purpose:** Would represent an open trade's state between Entry and
  Exit.
- **Relationships:** Produced by TradeSignal; consumed by RiskEngine
  and ExitEngine.

## 11. TradeResult

- **Already exists?** No.
- **Properties:** UNKNOWN — no exit/result schema is evidenced; FSD
  Section 10 documents exit as an explicit non-rule ("accept it and
  move on," not a computed target).
- **Purpose:** Would represent the outcome of a closed trade (for
  PaperTradeEngine or live trade recordkeeping).
- **Relationships:** Produced from TradePosition + an exit decision
  (ExitEngine); would feed StorageService, if evidenced.

## 12. SessionState

- **Already exists as:** `trading_engine.domain.session_state.SessionState`
  (`trading_engine/domain/session_state.py`).
- **Properties (as they exist today):** `session_id: uuid.UUID`,
  `current_state: SessionStateType` (default `SessionStateType.NONE`),
  `trend_points: tuple[TrendPoint, ...]`.
- **Purpose:** Tracks the operational state a trading session is in
  (FSD Section 15's State Machine — Waiting For 09:20, Finding
  Strikes, Capturing Levels, Monitoring, Ready, Entered, Managing,
  Exited, Completed — most transitions themselves UNKNOWN per FSD
  Section 15's table).
- **Relationships:** Aggregates TrendPoint values; referenced by
  MarketContext.

## 13. DashboardState

- **Already exists?** No.
- **Properties:** Only what FSD Section 14's "What can be restated"
  list already establishes as existing concepts: Top Strike/Bottom
  Strike (Strike), captured Premium levels (PremiumLevel), Option
  range contents if resolved (OptionRangeEngine output, currently
  UNKNOWN), Competitor/Opponent state (CompetitorState), TrendPoint/
  Edge state (TrendState), Winner determination if resolved
  (WinnerDecision), current state-machine state (SessionState). No
  layout, refresh-cadence, or alerting property is listed — FSD
  Section 14: "Everything else (layout, refresh cadence, alerting,
  charting library, historical view) is UNKNOWN."
- **Purpose:** Would aggregate read-only references to the other
  models in this document for presentation.
- **Relationships:** Composed of references to Strike, PremiumLevel,
  CompetitorState, TrendState, WinnerDecision, SessionState.

---

## Summary: existing vs. net-new

| Model | Status |
|---|---|
| OHLC | Already exists (`Candle`, `trading_engine/replay/history_loader.py`) |
| Strike | Already exists (`trading_engine/domain/strike.py`) |
| PremiumLevel | Already exists, thin (`Premium`, `trading_engine/domain/premium.py`) |
| TrendState | Already exists (`TrendPoint`, `trading_engine/domain/trend_point.py`) |
| CompetitorState | Already exists (`Opponent`, `trading_engine/domain/opponent.py`) |
| SessionState | Already exists (`trading_engine/domain/session_state.py`) |
| MarketTick | Net-new, UNKNOWN shape |
| OptionContract | Net-new, UNKNOWN shape |
| WinnerDecision | Net-new, minimally-evidenced shape (side + timing only) |
| TradeSignal | Net-new, minimally-evidenced shape (direction + trigger event only) |
| TradePosition | Net-new, UNKNOWN shape |
| TradeResult | Net-new, UNKNOWN shape |
| DashboardState | Net-new, aggregation-only shape |

---

Sources: direct reads of `trading_engine/domain/strike.py`,
`trading_engine/domain/premium.py`,
`trading_engine/domain/trend_point.py`,
`trading_engine/domain/opponent.py`,
`trading_engine/domain/session_state.py`,
`trading_engine/replay/history_loader.py`;
`research/specification/REALTIME_TRADING_SPECIFICATION.md` Sections
2-3, 6-9, 12-15; `research/analysis/KNOWLEDGE_GAP_INVENTORY.md`
Section 3; `research/analysis/KNOWLEDGE_DEPENDENCY_MATRIX.md` Chain A/B.

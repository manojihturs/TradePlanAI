# Business State Model

State requirements per blocked module. Distinguishes two categories throughout: (a) state that depends on a still-unresolved *business rule* (marked UNRESOLVED – Awaiting Strategy Evidence), and (b) state that is a genuine *architectural* gap independent of any business rule — something the current data model simply doesn't have a field for yet, regardless of what the eventual rule turns out to be.

## 1. WeeklyFutureCalculator

- **Recalculation cadence** — once per session at 09:20, or recalculated intraday — is UNRESOLVED – Awaiting Strategy Evidence (Specification Section 20 item 16). This is the single most consequential state question in this document, because it determines whether every downstream module (`StrikeSelector` onward) is a one-shot pipeline or a continuously re-evaluated one.
- If once-per-session: no additional state beyond the single computed `WeeklyFuture` value is needed.
- If intraday: would need a defined trigger (time-based? tick-based? re-open of the futures candle?) — entirely unspecified, not just the interval.

## 2. StrikeSelector

- State lifecycle is directly downstream of §1 — same UNRESOLVED cadence question applies, since a strike selection is only meaningful relative to a specific Weekly Future value.
- No independent architectural gap identified beyond that inherited uncertainty.

## 3. TPEngine

- **Undecided output shape** (`object` return type) is itself a state-modeling blocker — until it's decided whether TP is a price, a qualification boolean, or both, no state fields can be defined at all. This is upstream of everything else in this section for this module.
- **Update cadence** (tick vs. candle) is UNRESOLVED – Awaiting Strategy Evidence (Specification Section 20 item 12).
- Whether TP state must persist across the full session (e.g. "has this strike ever qualified") or is only meaningful as a point-in-time snapshot is undefined — depends on the still-unresolved qualification rule itself (Specification Sections 7–8).

## 4. QualificationEngine

- State lifecycle is entirely derivative of §3 (`TPEngine`'s cadence and output shape) — evaluated once per `TPEngine` update, per Spec Sections 7–8, but the update trigger itself is unresolved.
- **External-invalidation handling** (Specification Section 7: news/budget/war/natural-disaster scenarios) implies some state tracking (has this session been externally invalidated?) but no detection mechanism or state shape exists in any evidence — flagged as an open question, not assumed to have any particular shape.

## 5. StopLossEngine

- Whether `check()` can be evaluated statelessly from `(position, snapshot)` alone, or needs additional tracked state (e.g. an initial-risk anchor value fixed at entry), is UNRESOLVED – Awaiting Strategy Evidence — it depends entirely on what the Stop Loss rule (Specification Section 20 item 4) turns out to be.
- If it needs an anchor value fixed at entry time, that would most naturally live as a field on `TradePosition` (`models/trade_position.py`), set once at open and read-only afterward — noted here as a plausible shape, not a commitment, since the rule itself is unknown.

## 6. TrailingStopEngine

- **Architectural gap, independent of the business rule**: a trailing stop conventionally requires tracking the position's peak favorable excursion (a running high-water mark of the best price seen since entry) in order to compute a "have we pulled back too far from the peak" condition. `TradePosition` as built today has **no field for this** — this is true regardless of what the eventual trail-distance/activation rule says, because *some* running extremum needs to be tracked no matter how the distance itself is computed.
  - This would most naturally be implemented as a mutable field on `TradePosition`, updated on every `ExitEngine.evaluate()` cycle when the current price improves on the tracked peak — but `TradePosition` is currently a frozen dataclass (`@dataclass(frozen=True, slots=True)`, per `CODING_STANDARDS.md`), so adding a mutable field is itself a design decision (a controlled exception to immutability, or a separate mutable companion object) to be made when this module is actually implemented, not assumed here.
- **Trail activation trigger and trail distance/step** are UNRESOLVED – Awaiting Strategy Evidence (Specification Section 20 items 9–10).
- The one confirmed constraint (Specification Section 13: minimum net +3 premium points after costs) cannot currently be validated against any state, live or historical, because the brokerage/exchange/tax figures needed to compute "net" are themselves UNRESOLVED (Section 20, same items).

## Cross-cutting observation

Every module above whose state lifecycle is "UNRESOLVED cadence" (§1, §2, §3, §4) traces back to the same single open question — Specification Section 20 item 16 — rather than four independent gaps. Resolving that one question (once-per-session vs. intraday recalculation) would collapse most of this document's state uncertainty at once. This is noted as a prioritization observation for whatever evidence-gathering happens next, not a suggestion to resolve it without evidence.

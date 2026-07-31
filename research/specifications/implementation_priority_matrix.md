# Implementation Priority Matrix

**Status:** Documentation only. Derived directly from `business_engine_portfolio.md` — no new evidence introduced here.

---

## Priority 1 — Already Implemented, No Further Action

| Engine | Status |
|---|---|
| Winner Detection | Implemented (`src/winner_engine/`), HIGH confidence, Rule 3 CONFIRMED |
| Entry Engine | Implemented (`src/entry_engine/`), HIGH confidence, Rule 4 CONFIRMED |
| Target (post-Winner) | Implemented inside `src/position_manager/`, HIGH confidence, Rule 2 CONFIRMED |
| Exit Engine — Target/Competitor legs | Implemented inside `src/exit_engine/`, HIGH confidence, Rule 2 CONFIRMED |

## Priority 2 — Research Candidates (Worth a Targeted Evidence-Intake Request)

| Engine | Why prioritized here | What's needed |
|---|---|---|
| Trailing Stop Engine | One confirmed numeric constraint (+3 net premium points) already exists — the strongest partial foundation of any blocked engine | Activation trigger, trail step/distance, brokerage/exchange/tax figures |
| Stop Loss Engine | Named, Critical-flagged exit condition (Section 20 item 4) with an explicit gap statement | SL price, SL basis (points/percentage/underlying-level), placement rule |
| Exit Engine — SL/Trailing legs & precedence ordering | Blocked only by the two items above plus one workflow question (Section 20 item 11) — the Target/Competitor legs are already done | Same as Stop Loss + Trailing Stop, plus a stated precedence rule for simultaneous exit conditions |

## Priority 3 — Frozen, But Distinguishable From Priority 4 (Has *Some* Evidence)

| Engine | Why here, not fully frozen-and-forgotten |
|---|---|
| Premium Calculator | Legacy Premium Mapping module is complete and working in its own system; the primary-side Reversal concept (REVERSAL-001) has 2 evidence points at Draft/Medium confidence — not zero, but not enough to implement |

## Frozen — No Actionable Evidence Path Identified

| Engine | Reason |
|---|---|
| Qualification Engine | QUAL-007 (competitor identity) — already formally frozen prior to this audit |
| Market State Engine | Same root cause as Qualification Engine (QUAL-007) — not a separate engine |
| Target Engine — pre-Winner TP Engine half | Same root cause as Qualification Engine (QUAL-007) |
| Greeks Engine | Zero evidence anywhere; not even a flagged gap — likely never scoped into this reconstruction |
| Risk Engine | Zero evidence anywhere; section header exists but was never populated, unlike every other blocked engine |

---

## Recommended Next Sprint

**No new engine implementation sprint yet.** Per the portfolio's own findings, Priority 1 work is already done. The only defensible next step is a **research sprint** targeting Trailing Stop Engine and Stop Loss Engine (Priority 2) — specifically requesting Product-Owner evidence for: SL price/basis/placement, trailing-stop activation/step mechanics, and the brokerage/exchange/tax figures needed for the "+3 net" guarantee. If that research succeeds, Exit Engine's remaining two legs and precedence ordering become implementable as a direct follow-on, with no new engineering risk (the orchestration shell already exists and works for Target/Competitor).

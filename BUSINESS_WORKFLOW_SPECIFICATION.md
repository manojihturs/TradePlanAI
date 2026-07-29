# Business Workflow Specification

**Role of this document:** a business analyst's description of the manual process this strategy encodes — independent of software classes, interfaces, or events. Everything here is a direct read of `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` (v1.1, the dictated business-rules source) reorganized as a workflow, not a re-derivation from the software architecture documents (`BUSINESS_ARCHITECTURE.md` etc.) written earlier. No trading rule is invented; every stage-level unknown is marked `UNRESOLVED – Awaiting Strategy Evidence`.

---

## Stage 1 — Market Open

| | |
|---|---|
| **Purpose** | Establish the session start and begin waiting for the reference-setting candle. |
| **Required Inputs** | The trading day's open; a live/replayed market data feed. |
| **Decision** | None — this stage is a wait state, not a decision point. |
| **Output** | Transition to Reference Collection once the first 5-minute candle (09:15–09:20) completes. |
| **Unknowns** | UNRESOLVED – Awaiting Strategy Evidence: what (if anything) happens between session open and 09:20 — a pre-market phase is neither confirmed nor ruled out (Spec §3 MISSING INFORMATION). |
| **Dependencies** | None upstream. |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §1, §3. |

---

## Stage 2 — Reference Collection

| | |
|---|---|
| **Purpose** | Capture the CE/PE High/Low reference values every downstream stage measures against. |
| **Required Inputs** | The first 5-minute candle (09:15–09:20)'s OHLC, per option contract, for every strike that will end up in the 13-level ladder. |
| **Decision** | None — a pure capture step. |
| **Output** | Per-strike CE High, CE Low, PE High, PE Low (CONFIRMED, Rule 1). |
| **Unknowns** | Ladder step size beyond the one 50-point example is UNRESOLVED. Whether these values are held fixed for the rest of the session or ever recalculated is UNRESOLVED (Spec §20 item 17). Whether this same first-candle data is the same underlying capture as the already-implemented `trading_engine/premium_snapshot/` milestone is UNRESOLVED — flagged for reconciliation, not assumed either way (Spec §20 item 19). |
| **Dependencies** | Stage 1 (Market Open) only — this stage does **not** depend on Weekly Future or Strike Selection for *which candle* to read, only (per Stage 4) for *which strikes* the ladder is centered on. This ordering ambiguity is itself an unknown — see the Gap Analysis. |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §6, Rule 1. |

---

## Stage 3 — Weekly Future

| | |
|---|---|
| **Purpose** | Compute a Weekly Future High and Low as the session's foundational reference pair. |
| **Required Inputs** | Per the source message: "the first candle" (confirmed to be the same 09:15–09:20 candle as Stage 2, per Rule 1). No other input is named. |
| **Decision** | None stated as a decision — a calculation step, though its formula is entirely unknown. |
| **Output** | Weekly Future High, Weekly Future Low. |
| **Unknowns** | UNRESOLVED – Awaiting Strategy Evidence (all Critical, Spec §20 item 1): the formula itself; what data actually feeds it (the candle's own OHLC vs. a separate weekly-futures instrument's price vs. something else); why two distinct values emerge from what appears to be a single candle; whether this repeats daily or is computed once per week and reused. This is the project's single largest, longest-standing blocker (`WEEKLY_FUTURE_BLOCKER_REPORT.md`). |
| **Dependencies** | Stage 2, for the candle itself (same candle, not a separate data pull). |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §4; `WEEKLY_FUTURE_BLOCKER_REPORT.md` (why no evidence exists to resolve this today). |

---

## Stage 4 — Strike Selection

| | |
|---|---|
| **Purpose** | Select the Top Strike and Bottom Strike (both "ATM") that will center the reference ladder and anchor every later stage. |
| **Required Inputs** | Weekly Future High/Low (Stage 3's output) — presumed basis, not confirmed. |
| **Decision** | Which strike counts as "ATM" for the Top and Bottom positions respectively. |
| **Output** | Top Strike, Bottom Strike. |
| **Unknowns** | UNRESOLVED (Critical, Spec §20 item 2): what "ATM" is computed against (Weekly Future High/Low specifically, vs. spot price, vs. something else); the strike-rounding rule; whether Top Strike and Bottom Strike can be equal; whether this is a once-only or intraday-recalculated selection. |
| **Dependencies** | Stage 3. |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §5. |

---

## Stage 5 — TP Calculation

| | |
|---|---|
| **Purpose** | Continuously determine, from 09:21 AM onward, whether the Top Strike's and Bottom Strike's CE/PE prices are currently "qualifying" against a competitor level. |
| **Required Inputs** | Live market prices from 09:21 AM onward; the reference ladder (Stage 2); Top/Bottom Strike identity (Stage 4). |
| **Decision** | Per update cycle: does the current price sustain (not yet breach) the stated qualification condition? (`TP High`: `CE > competitor PE Low` AND `PE < competitor CE High`; `TP Low`: mirrored.) |
| **Output** | An updated TP state for Top Strike and Bottom Strike. Whether this output is itself a price, a boolean, or both is UNRESOLVED. |
| **Unknowns** | UNRESOLVED (Critical, Spec §20 item 3): identity of the "competitor" strike/level for this specific test — explicitly **not** assumed to be the same S±1 pattern later confirmed for Exit-stage competitor monitoring (Rule 2 was stated for a Winner's entry strike, a different context). UNRESOLVED (High, item 12): update cadence — tick or candle. UNRESOLVED (Medium, item 13): whether "TP" is a price, a flag, or both. |
| **Dependencies** | Stage 2, Stage 4. |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7. |

---

## Stage 6 — Qualification

| | |
|---|---|
| **Purpose** | Represent the current market state of a strike's TP sustain/breach outcome — explicitly *not* a prediction. |
| **Required Inputs** | Current TP state (Stage 5). |
| **Decision** | Has the sustain condition broken? Has an external event (news/budget/war/natural disaster) invalidated it? |
| **Output** | A qualification state, subject to change on the next update cycle. |
| **Unknowns** | UNRESOLVED: the source message does not clearly separate "TP" from "Qualification" as two distinct computations — this stage may be nothing more than the boolean reading of Stage 5's own sustain test, not an independent stage at all (Spec §8 explicitly notes this ambiguity). External-invalidation detection (news/budget/war/disaster) has no stated mechanism whatsoever — named as a risk, not given as an implementable rule. |
| **Dependencies** | Stage 5. |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7–§8. |

---

## Stage 7 — Winner Detection

| | |
|---|---|
| **Purpose** | Determine, candle by candle, whether a trade should be triggered. |
| **Required Inputs** | Candle-by-candle CE and PE prices; the reference ladder. |
| **Decision** | Did a CE reference level get touched **and** a PE reference level get touched in the *same* candle? If so, one side (by rule, unambiguously — see Unknowns) is Winner, the other Loser. |
| **Output** | A Winner (side + strike), or no Winner this candle. |
| **Unknowns** | UNRESOLVED (High, item 7): the candle timeframe used here from 09:21 AM onward — only the *reference-setting* candle (Stage 2's 5-minute candle) is confirmed; whether ongoing Winner evaluation also runs on 5-minute candles, or some other timeframe, is not stated. UNRESOLVED: "CE touches one of its reference levels" — of which strike(s) specifically (Top Strike's CE/PE only, or every strike's simultaneously) is not stated. **Resolved, not unknown:** the both-sides-touch tie-break scenario is confirmed (Rule 3) not to occur — no tie-break logic is needed. |
| **Dependencies** | Stage 2 (reference ladder). This document does **not** assume Stage 7 consumes Stage 5/6's output at all — see the Gap Analysis below; the source message describes Winner detection purely in terms of candle touches against reference levels, never mentioning TP/Qualification state as an input. |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §9, Rule 3. |

---

## Stage 8 — Entry Decision

| | |
|---|---|
| **Purpose** | Convert a Winner into an actual trade entry, subject to the single-active-trade constraint. |
| **Required Inputs** | Winner (side + strike) from Stage 7; current active-trade status. |
| **Decision** | Is a trade currently active? If yes, ignore this Winner outright (not queued). If no, enter. |
| **Output** | A new active trade, or no action. |
| **Unknowns** | UNRESOLVED: entry price mechanism (market order at signal candle close? limit at the reference level itself?) is not stated at all. |
| **Dependencies** | Stage 7. |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §10, Rule 4. |

---

## Stage 9 — Position Monitoring

| | |
|---|---|
| **Purpose** | Track the active trade's Target, Support, and Competitor-Exit levels, and the Trailing Stop's running state, every candle the trade remains open. |
| **Required Inputs** | The active trade's entry strike S and side; live market prices; the competitor strike's own reference levels. |
| **Decision** | None at this stage itself — it is observation/bookkeeping feeding Stage 10's decision. |
| **Output** | Current distance-to-target, competitor-level state, and trailing-stop tracking state (e.g. a running peak, if the eventual mechanics require one). |
| **Unknowns** | UNRESOLVED (High, item 9): trailing-stop activation trigger and trail step/distance — entirely unstated beyond the minimum net-profit guarantee. UNRESOLVED (High, item 10): the brokerage/exchange/tax figures needed to compute that guarantee numerically. |
| **Dependencies** | Stage 8 (an active trade must exist), Rule 2's confirmed Target/Support/Competitor mapping (S+1/S-1 by side). |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11 (Rule 2 table), §13. |

---

## Stage 10 — Exit Decision

| | |
|---|---|
| **Purpose** | Decide whether the active trade should close this candle. |
| **Required Inputs** | Stage 9's monitoring state. |
| **Decision** | Has any of: Target Hit, Competitor Level Hit, Stop Loss, Trailing Stop occurred? |
| **Output** | Trade closed (with a recorded exit reason), or trade remains open. |
| **Unknowns** | UNRESOLVED (Critical, item 4): the Stop Loss rule — named only, no price basis or trigger condition stated at all. UNRESOLVED (High, item 8): which of the competitor's own two reference levels (its High or its Low) actually triggers a competitor exit — Rule 2 confirmed *which strike/side* is the competitor, not which of its two levels. UNRESOLVED (High, item 11): precedence when multiple exit conditions are met in the same candle — no ordering is given by the source evidence (the exit-check *order* used in the built `ExitEngine` — Target→Competitor→StopLoss→TrailingStop — is an engineering default, not a resolution of this business-rule gap; see `BUSINESS_RULE_INTEGRATION_GUIDE.md` §Integration Sequence). |
| **Dependencies** | Stage 9. |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11, §13, §19. |

---

## Stage 11 — Session Close

| | |
|---|---|
| **Purpose** | End the trading day's cycle: after any exit, recalculate before the next trade; eventually stop for the day. |
| **Required Inputs** | Exit event (Stage 10) or end-of-day condition. |
| **Decision** | After an exit: recalculate TP/Qualification/Winner and return to monitoring (Rule 5, confirmed). At day's end: stop — mechanism unstated. |
| **Output** | Either a return to Stage 5 (Monitoring), or session end. |
| **Unknowns** | UNRESOLVED: what actually ends a trading day (a fixed close time, forced square-off, or the strategy simply ceasing to evaluate) is not stated anywhere (Spec §3, §20 item 15). UNRESOLVED: whether Weekly Future/Strike Selection/Ladder Generation (Stages 2–4) recur intraday or only once per day, and whether any state carries over day-to-day (Spec §20 item 16). |
| **Dependencies** | Stage 10 (post-exit recalculation is confirmed, Rule 5). |
| **Evidence Source** | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §3, §16 (post-exit recalculation), §20 items 15–16. |

---

## Workflow Gap Analysis

For every stage-to-stage transition: can it be implemented today, from current evidence alone?

| Transition | Status | Why |
|---|---|---|
| Market Open → Reference Collection | **YES** | Purely a wait-for-candle-completion step; no business rule needed. Already built (`ReferenceBuilder`, Sprint 4). |
| Reference Collection → Weekly Future | **PARTIALLY** | The *candle* to use is confirmed (Rule 1). The *formula* applied to it is entirely unknown. The transition's trigger condition is implementable; the calculation it triggers is not. |
| Weekly Future → Strike Selection | **NO** | Depends on both an unresolved Weekly Future output and an entirely unstated ATM/rounding rule. Cannot be implemented even partially — there is no confirmed relationship between Weekly Future's output and "ATM" at all yet. |
| Strike Selection → Reference Collection (ladder centering) | **PARTIALLY** | The mechanical act of building a 13-level ladder around given strikes is fully implemented and tested (`ReferenceBuilder`). What's missing is only the upstream strikes themselves — a wiring gap once Strike Selection exists, not a business-rule gap in this transition itself. |
| TP Calculation → Qualification | **NO** | Both stages share the same unresolved "competitor" identity rule; without it, neither the transition nor either stage individually can be implemented. Additionally, whether these are genuinely two stages or one is itself unresolved (Spec §8). |
| Qualification → Winner Detection | **PARTIALLY, leaning NO** | The specification never states that Qualification *gates* Winner Detection at all — Winner Detection (§9) is described purely in terms of candle-level CE/PE touches against reference levels, with no mention of TP/Qualification state as an input. This transition may not exist as a real business dependency; asserting it does would be inventing a rule not present in the evidence. This is the single most consequential open question this document surfaces — see "Does the architecture support this workflow?" below. |
| Winner Detection → Entry Decision | **YES** | Fully specified: immediate entry unless a trade is already active (Rule 4), no ambiguity. Already built (`WinnerEngine`→`EntryEngine`). |
| Entry Decision → Position Monitoring | **PARTIALLY** | The Target/Support/Competitor-Exit mapping is fully confirmed (Rule 2) and built (`PositionManager`). Entry price mechanism itself is unstated, so entry *execution* detail is not implementable, but monitoring *setup* is. |
| Position Monitoring → Exit Decision | **PARTIALLY** | Target-hit and Competitor-level-hit are each individually well-defined enough to implement (modulo the High/Low-of-competitor ambiguity, item 8). Stop Loss and Trailing Stop mechanics are not implementable at all (items 4, 9, 10). Multi-condition precedence is unresolved (item 11), so even the transitions that are individually implementable cannot be composed into a correct combined decision yet. |
| Exit Decision → Session Close (recalculation) | **YES** | Explicitly confirmed (Rule 5): recalculate TP/Qualification/Winner after every exit before permitting the next trade. Already built as far as the recalculation *trigger*; the recalculation's own contents inherit every upstream unresolved rule. |
| Session Close → Market Open (next day) / end-of-day | **NO** | No stated end-of-day condition exists at all. |

---

## Does the current software architecture support this workflow?

**Partially, with one specific, significant gap.**

The software architecture (`BUSINESS_ARCHITECTURE.md` et al.) was built to be structurally ready for every stage above **except** it makes no claim, in either direction, about whether TP/Qualification output feeds Winner Detection — because the software architecture review already surfaced that `WinnerEngine` as built takes CE/PE snapshots directly and has zero dependency on `TPEngine`/`QualificationEngine`. This workflow document's independent, software-blind read of the business specification confirms that absence is **consistent with the evidence, not a software oversight**: the specification itself never states that Qualification gates Winner Detection. The two documents arrived at the same observation from opposite directions (one reading code, one reading the business spec), which increases confidence this is a real, unresolved *process* question rather than an artifact of either reading.

**Missing integration points** (identified only, not redesigned, per instruction):

1. A defined connection — if the evidence eventually confirms one should exist — between the TP/Qualification stage output and the Winner Detection stage input. Today, no interface, event, or data flow exists between `TPEngine`/`QualificationEngine` and `WinnerEngine` in the built code, and this document finds no business-specification text requiring one either. This may mean the intended workflow genuinely runs Winner Detection independently of TP/Qualification (in which case no integration point is "missing" — it was never supposed to exist), or it may mean the specification is itself incomplete on this point. Only new evidence can distinguish these two possibilities; this document does not guess which is true.
2. A defined mechanism for Defeat (Stage-adjacent concept, Spec §14) to interact with Qualification and with an open trade — no stage above currently has a place for this, because the specification names Defeat's trigger but never its effect.
3. A defined end-of-session/end-of-day trigger — Stage 11 has no confirmed entry condition, so nothing in the architecture (or this workflow) can specify what causes the daily cycle to actually stop.

No redesign of `BUSINESS_ARCHITECTURE.md`, `BUSINESS_DEPENDENCY_MAP.md`, or any other existing document is proposed here — these three points are flagged as open questions for future evidence, consistent with this project's evidence-first discipline.

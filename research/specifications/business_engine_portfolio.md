# Business Engine Portfolio Audit

**Status:** Documentation only — Portfolio Audit Mode. No production code, interfaces, tests, or refactoring. Every answer below traces to a quoted source; no threshold, formula, or rule is invented or inferred.

**Scope:** All 10 remaining unimplemented-or-partial business engines, evaluated against every source in `research/`, `docs/`, `src/interfaces/`, `src/` (existing implementations), the legacy `strategy/`/`trading_engine/` code, `CHANGELOG.md`, and `INVESTIGATIONS.md`. Qualification Engine is excluded — already formally frozen (QUAL-007, see `research/specifications/qualification_implementation_plan.md`).

---

## 1. Premium Calculator

1. **Purpose:** No dedicated "Premium Calculator" exists as a named primary-reconstruction concept. The closest evidenced concepts are legacy Premium Mapping (cross-referencing CE/PE High/Low into four ladders) and an inert primary-side `Premium` value object tied to an undefined "Reversal" concept.
2. **Business inputs:** None stated for a primary Premium Calculator. Legacy Premium Mapping inputs: `LevelCapture`'s CE/PE High/Low per anchor strike.
3. **Business outputs:** None stated for a primary engine. Legacy: four cross-plotted premium ladders (TOP/BOTTOM anchors × CE/PE).
4. **Repository evidence:**
   - `strategy/premium_mapping.py:1-25` (legacy, real code): four-ladder cross-referencing logic.
   - `trading_engine/domain/premium.py:1-52`: `Premium` dataclass; docstring: "Referenced only indirectly, as the basis for identifying a Reversal (REVERSAL-001). No rule defines Premium as a first-class concept yet."
   - `trading_engine/calculators/reversal_calculator.py:1-58`: registered but raises `NotImplementedError("TODO (REVERSAL-001): Reversal mathematics awaiting evidence.")`.
   - `docs/RULE_INDEX.md:37`: REVERSAL-001, status Draft, confidence Medium, evidence count 2.
   - `docs/MATHEMATICAL_SPECIFICATION.md:34`, `docs/GAP_ANALYSIS.md:48`: "Premium Mapping / Cross-Referencing" section headers, both empty.
   - **Confidence:** LOW.
5. **Can it be implemented?** NO (as a primary-reconstruction engine). The legacy Premium Mapping module is already complete and working in its own system, but that is a separate codebase/purpose, not evidence for a new primary Premium Calculator.
6. **Blocked by:** Missing business rules (no primary-side concept defined) and missing formulas (REVERSAL-001 mathematics explicitly "awaiting evidence").
7. **Dependencies:** Feeds the unresolved Qualification/TP competitor question only speculatively — no confirmed dependency link exists.
8. **Recommended action:** Freeze (as a primary engine). The legacy Premium Mapping module needs no further work — it already exists and functions in its own system.

---

## 2. Market State Engine

1. **Purpose:** No dedicated "Market State Engine" exists. The only "market state" language found describes Qualification (TP sustain/breach) representing "current market state," not a standalone engine.
2. **Business inputs:** N/A — no distinct engine evidenced.
3. **Business outputs:** N/A.
4. **Repository evidence:**
   - `docs/TERMINOLOGY.md:41`: Qualification "represent[s] current market state... Precise sustain/breach test not fully specified."
   - `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md:139`: "Qualification is NOT future prediction. Qualification represents the current market state... Never assume qualification is permanent."
   - `src/interfaces/qualification_engine.py:1-39`: stub; `evaluate()` always raises `UnresolvedBusinessRuleError`; docstring cites the same unresolved competitor-identity gap as `TPEngine`, plus "external-invalidation handling... has no detection mechanism specified anywhere."
   - **Confidence:** LOW/UNKNOWN.
5. **Can it be implemented?** NO. This is not a distinct engine from the already-frozen Qualification Engine — it is the same blocked concept under a different name in this prompt's list.
6. **Blocked by:** Same as Qualification Engine — QUAL-007 (competitor identity) and missing external-invalidation detection mechanism.
7. **Dependencies:** Identical to Qualification Engine.
8. **Recommended action:** Freeze — merge this line item into the existing Qualification Engine freeze; no separate audit action needed.

---

## 3. Greeks Engine

1. **Purpose:** No evidence of a Greeks Engine (delta, gamma, theta, vega) anywhere in the repository.
2. **Business inputs:** None found.
3. **Business outputs:** None found.
4. **Repository evidence:** Exhaustive grep across `docs/`, `research/`, `src/`, `strategy/`, `trading_engine/`, `CHANGELOG.md`, `INVESTIGATIONS.md` for "greeks", "delta", "gamma", "theta", "vega" (as option-Greeks terms) returned zero matches in any business-rule context.
   - **Confidence:** UNKNOWN.
5. **Can it be implemented?** NO.
6. **Blocked by:** Missing business rules entirely — this engine was apparently never scoped into the reconstruction effort (no gap is even flagged for it in `GAP_ANALYSIS.md`, `RULE_INDEX.md`, `TERMINOLOGY.md`, or `MATHEMATICAL_SPECIFICATION.md`, unlike every other blocked engine below).
7. **Dependencies:** None evidenced.
8. **Recommended action:** Freeze. Do not open a research task for this — there is nothing to research from; it would require an entirely new evidence-intake conversation with the Product Owner to even establish that this engine belongs in the strategy at all.

---

## 4. Winner Detection (WinnerEngine)

1. **Purpose:** "Winner is evaluated candle by candle. If CE touches any one of its reference levels AND PE touches any one of its reference levels during the SAME candle, then one side wins, the opposite side loses. Winner immediately generates Entry Signal." (`src/winner_engine/winner_engine.py:5-8`, Spec §9).
2. **Business inputs:** `session_id`, `candle_timestamp`, `strike`, `level: ReferenceLevel`, `ce_snapshot`, `pe_snapshot`.
3. **Business outputs:** `WinnerDetectedEvent | None`.
4. **Repository evidence:**
   - Rule 3 (v1.1, CONFIRMED): "Multiple winner scenarios do not occur. Do not invent tie-break logic." — implemented as `AmbiguousWinnerError` if both sides touch.
   - "Touch" defined mechanically: level falls within the candle's [low, high] range — implemented directly.
   - **Confidence:** HIGH.
5. **Can it be implemented?** YES — already implemented (`src/winner_engine/winner_engine.py`), real logic, no stub errors.
6. **Blocked by:** Nothing blocking the core logic. One open sub-question — which strike(s)' CE/PE are in scope for evaluation — is Spec §9's "own open question," and the engine is deliberately designed strike-agnostic around it rather than blocked by it.
7. **Dependencies:** Feeds Entry Engine directly (`WinnerDetectedEvent` consumed by `EntryEngine`).
8. **Recommended action:** Implement — already done; no further action needed.

---

## 5. Entry Engine

1. **Purpose:** "Immediately after Winner. Only ONE trade may remain active. Never take another trade until current trade exits." (`src/entry_engine/entry_engine.py:5-6`, Spec §10).
2. **Business inputs:** `WinnerDetectedEvent`, current position-active state.
3. **Business outputs:** `TradeSignal`, accept/reject decision via `PositionManager.open_position`.
4. **Repository evidence:**
   - Rule 4 (v1.1, CONFIRMED): a rejected attempt is discarded outright, not queued or retried — implemented via `accepted: bool = position is not None`.
   - Explicit gap: "Entry price/order-type basis is MISSING INFORMATION (Spec §11) and is not represented anywhere in this module."
   - **Confidence:** HIGH.
5. **Can it be implemented?** YES — already implemented (`src/entry_engine/entry_engine.py`), real logic.
6. **Blocked by:** Nothing for its current scope. Entry price/order-type is explicitly out of this module's evidenced scope, not a blocker to what it does implement.
7. **Dependencies:** Consumes `WinnerDetectedEvent` (Winner Detection); calls into `PositionManager`.
8. **Recommended action:** Implement — already done; no further action needed.

---

## 6. Target Engine

1. **Purpose:** Two distinct concepts share this name in the prompt: (a) post-Winner Target computation (Rule 2, part of `PositionManager`), and (b) pre-Winner "TP Engine" (Top/Bottom Strike qualification "Target Price" — a different concept, not to be conflated).
2. **Business inputs:** Rule 2: entry strike S and side (CE/PE); adjacent-rung lookup over the reference ladder.
3. **Business outputs:** Rule 2: `Target = CE(S+1)` (Winner CE) or `Target = PE(S-1)` (Winner PE).
4. **Repository evidence:**
   - Rule 2 (v1.1, CONFIRMED), quoted in `src/position_manager/position_manager.py:6-12`: full entry/target/support/competitor-exit mapping for both sides.
   - `docs/TERMINOLOGY.md:46`: Target = "the next reference level in the direction of the trade... CONFIRMED (v1.1, Rule 2)."
   - Distinct pre-Winner `TPEngine`: `src/interfaces/tp_engine.py:1-21`, stub; docstring: "the TP Engine's competitor-strike identity for the TP High/TP Low qualification test is undefined... Update cadence and whether 'TP' is a price, a flag, or both are also MISSING INFORMATION."
   - **Confidence:** HIGH (post-Winner Target). LOW (pre-Winner TP Engine).
5. **Can it be implemented?**
   - Post-Winner Target: YES — already implemented inside `PositionManager`.
   - Pre-Winner TP Engine: NO — blocked by the same competitor-identity gap as Qualification Engine (QUAL-007).
6. **Blocked by:** Pre-Winner TP Engine only — missing competitor identity, missing update cadence, missing output shape (price vs. flag vs. both).
7. **Dependencies:** Post-Winner Target has none unresolved. Pre-Winner TP Engine depends on the same unresolved competitor identity as Qualification Engine — effectively the same blocker (QUAL-007).
8. **Recommended action:** Post-Winner Target — Implement (already done). Pre-Winner TP Engine — Freeze, merge into the existing Qualification Engine freeze (same root cause).

---

## 7. Stop Loss Engine

1. **Purpose:** Evaluate whether an active `TradePosition` has hit its Stop Loss (Spec §11).
2. **Business inputs:** `TradePosition`, `MarketSnapshot` (per the interface shape only — no rule content).
3. **Business outputs:** boolean hit/not-hit (interface shape only).
4. **Repository evidence:**
   - `src/interfaces/stop_loss_engine.py:1-34`: "Spec §11, §20 item 4 (Critical): Exit when: ... OR Stop Loss ... with no SL price, basis, or placement rule stated anywhere... Do NOT implement."
   - `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md:228`: "Still not stated at all: SL price, SL basis (premium points? percentage? underlying-level?), or SL placement rule."
   - **Confidence:** LOW.
5. **Can it be implemented?** NO.
6. **Blocked by:** Missing thresholds (SL price), missing formulas (SL basis — points/percentage/underlying-level, all three candidates unresolved), missing business rules (placement rule).
7. **Dependencies:** Consumed by Exit Engine's fourth exit condition — Exit Engine cannot fully resolve this leg until Stop Loss Engine is implementable.
8. **Recommended action:** Research. This is a named, explicitly Critical exit condition (Section 20 item 4) — worth a targeted evidence-intake request to the Product Owner, similar to the process that resolved Weekly Future.

---

## 8. Trailing Stop Engine

1. **Purpose:** Evaluate whether an active `TradePosition` has hit its Trailing Stop (Spec §13).
2. **Business inputs:** `TradePosition`, `MarketSnapshot` (interface shape only).
3. **Business outputs:** boolean hit/not-hit (interface shape only).
4. **Repository evidence:**
   - `src/interfaces/trailing_stop_engine.py:1-16`: "Trailing stop must guarantee minimum +3 premium points to cover brokerage, exchange charges, tax." Quoted directly from Spec §13. "Trail activation trigger, trail step/distance, and the brokerage/exchange/tax figures needed to compute '+3 net' are all MISSING INFORMATION."
   - `docs/TERMINOLOGY.md:48`: confirms the +3 net minimum as the only stated mechanic.
   - **Confidence:** MEDIUM (the numeric minimum is a confirmed, quoted rule; the mechanics needed to act on it are missing).
5. **Can it be implemented?** PARTIAL — the +3 net minimum constraint is real and quotable, but not independently actionable without activation trigger, step/distance, and cost figures.
6. **Blocked by:** Missing thresholds (brokerage/exchange/tax figures), missing formulas (trail step/distance mechanics), missing business rules (activation trigger).
7. **Dependencies:** Consumed by Exit Engine's fourth exit condition, same as Stop Loss Engine.
8. **Recommended action:** Research. The one confirmed numeric constraint (+3 net) makes this a stronger research candidate than Stop Loss — a Product-Owner-supplied answer on activation/step mechanics and cost figures could close this relatively quickly.

---

## 9. Exit Engine

1. **Purpose:** "Exit when: Target Hit OR Competitor Strike Reference Level Hit OR Stop Loss OR Trailing Stop." (`src/exit_engine/exit_engine.py:5-6`, Spec §11).
2. **Business inputs:** `candle_timestamp`, `target_snapshot`, `competitor_snapshot`; injected `StopLossEngine`/`TrailingStopEngine`.
3. **Business outputs:** closed `TradePosition | None`.
4. **Repository evidence:**
   - Target/Competitor legs: reuse `PositionManager`'s Rule 2 computation directly — real, implemented, CONFIRMED.
   - SL/Trailing legs: "are not implemented here (Spec §20 items 4, 9-10, still MISSING INFORMATION). This engine only calls the injected StopLossEngine/TrailingStopEngine check() methods."
   - Precedence: "Exit-condition precedence when multiple conditions are met on the same evaluation is Spec §20 item 11, still MISSING INFORMATION... This is an engineering default for a genuinely simultaneous case, not a resolution of that gap."
   - "Which of the competitor's own two reference levels (High or Low) triggers a competitor exit" is Section 20 item 8 — current code checks both as an implementation choice, not a confirmed rule.
   - **Confidence:** HIGH for Target/Competitor legs. LOW for SL/Trailing legs and precedence ordering.
5. **Can it be implemented?** PARTIAL — already implemented for Target/Competitor exits; the SL/Trailing legs will raise `UnresolvedBusinessRuleError` on every evaluation until those two engines are resolved, and the fixed evaluation order is an unconfirmed engineering default.
6. **Blocked by:** Missing business rules (SL, Trailing — same blockers as items 7-8 above) and missing workflow (exit-condition precedence, Section 20 item 11).
7. **Dependencies:** Depends on Stop Loss Engine and Trailing Stop Engine to be fully functional; depends on `PositionManager`'s Rule 2 (already resolved) for Target/Competitor.
8. **Recommended action:** Research (for the SL/Trailing legs and precedence ordering) — the Target/Competitor portion is already correctly implemented and needs no further work.

---

## 10. Risk Engine

1. **Purpose:** No "Risk Engine" or position-sizing engine exists as a named primary-reconstruction concept.
2. **Business inputs:** None found.
3. **Business outputs:** None found.
4. **Repository evidence:**
   - `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md:54`: "### 5. Position and Risk Management" exists only as a section header in the source outline; no formula content found under it.
   - `docs/GAP_ANALYSIS.md:54`, `docs/MATHEMATICAL_SPECIFICATION.md:40`: same header, both entirely empty — no sub-bullets, no MISSING INFORMATION callout specific to risk/position sizing (unlike SL/Trailing/TP Engine, which each have numbered Section 20 gap items).
   - Legacy-only: `strategy/live_paper_trading.py`'s `CapitalTracker` — explicitly disclaimed as paper-trading bookkeeping, "not a strategy rule."
   - **Confidence:** UNKNOWN.
5. **Can it be implemented?** NO.
6. **Blocked by:** Missing business rules entirely. Unlike Stop Loss/Trailing Stop, this gap has not even been flagged with a specific numbered item — evidence acquisition for this engine has apparently not yet begun.
7. **Dependencies:** None evidenced.
8. **Recommended action:** Freeze, pending a scoping conversation with the Product Owner to establish whether this engine is even part of the strategy (it may not be, given it lacks even a flagged-gap entry, unlike every other blocked engine in this audit).

---

## Cross-cutting observation

Two items in this list (`Market State Engine`, and the pre-Winner half of `Target Engine`) are not independent engines — they are the already-frozen Qualification Engine (QUAL-007) under different names. This audit treats them as the same blocker, not three separate ones, in the priority matrix and release plan that follow.

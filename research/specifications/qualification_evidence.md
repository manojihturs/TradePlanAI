# Qualification Engine — Evidence Audit

**Status:** Documentation only. No production code, no interfaces, no tests were touched to produce this document. Every entry below is a verbatim or near-verbatim quote from an existing repository file — nothing here is estimated or inferred. Where a threshold, mechanism, or identity is genuinely absent from the source material, this document says so explicitly rather than filling the gap.

**Method:** every markdown file under `research/`, `docs/`, and the repository root; the current `src/interfaces/qualification_engine.py` stub and its test; and the legacy `strategy/`/`trading_engine/`/`orb_common.py` code were searched for the ten topics below. Two unrelated systems live in this repository — (1) the TradingView Weekly-Future/Trend-Point reconstruction this project has been building all session (`research/`, `docs/`, `src/`), and (2) an older, already-shipped, structurally different "ORB Ladder" system (`orb_signal.py`, `orb_common.py`, `strategy/`) that predates this reconstruction and follows its own separate rule set. Evidence from each is labeled accordingly — the ORB Ladder system's filters are **not** evidence for this project's Qualification Engine, since they were never derived from the same source material and use an incompatible model (per this project's own established package-boundary rule, e.g. `weekly_future_calculator.py`'s traceability note on why `trading_engine` and `src` are never merged).

---

## 1. Qualification

| Source | Section | Exact wording | Confidence |
|---|---|---|---|
| `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` | §7 (TP Engine) | "TP starts updating after 09:21 AM. TP is dynamic. TP changes continuously. TP is NOT fixed. **TP High** (Top Strike): CE > competitor PE Low; PE < competitor CE High. If market currently sustains without touching competitor PE Low, TP High qualifies. **TP Low** (Bottom Strike): CE > competitor PE High; PE < competitor CE Low. If market currently sustains, TP Low qualifies. Qualification is NOT future prediction. Qualification represents the current market state. News/Budget/War/Natural Disaster may invalidate any qualification. Never assume qualification is permanent." | HIGH (logical form of the test itself is precise) |
| `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` | §8 (Qualification Engine) | "Covered jointly with Section 7 above, since the source message did not separate 'TP' and 'Qualification' into two distinct rule sets — 'TP qualifies' is the only qualification concept given." | HIGH (as a statement that no separate concept exists) |
| `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` | §8, MISSING INFORMATION | "whether Qualification is a separate, independently-computed engine from TP, or simply the boolean outcome of the TP sustain test described in Section 7. The source message uses 'TP' and 'qualification' interchangeably." | UNKNOWN |
| `BUSINESS_ACCEPTANCE_SPECIFICATION.md` | §5 (Qualification) | "**Business Goal:** Represent the current-state sustain/breach outcome of a strike's TP test — explicitly not a prediction." / "**Acceptance Status:** BLOCKED." | HIGH (as an accurate restatement) but the underlying rule is rated **Low** in the same section |
| `research/specifications/QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` | §1 | "Qualification test shape: `TP High` qualifies when `CE > competitor PE Low` AND `PE < competitor CE High`; `TP Low` mirrored" — Confidence column: "High (logical form stated precisely)" | HIGH |
| `BUSINESS_WORKFLOW_SPECIFICATION.md` | Stage 6 — Qualification | "UNRESOLVED: the source message does not clearly separate 'TP' from 'Qualification' as two distinct computations — this stage may be nothing more than the boolean reading of Stage 5's own sustain test, not an independent stage at all" | UNKNOWN |
| `src/interfaces/qualification_engine.py` | module docstring | "This interface defines only the method shape a future implementation must satisfy. Do NOT implement." — `evaluate()` "Raises: `core.exceptions.UnresolvedBusinessRuleError`: always" | HIGH (current implementation status, not a business rule) |

## 2. Trade filtering

No evidence found in the TradingView reconstruction's own source material (`research/`, `docs/`, `STRATEGY_FUNCTIONAL_SPECIFICATION.md`) under this literal term. The only "trade filtering" concepts found belong to the separate legacy ORB Ladder system (`orb_signal.py`, root `README.md`): a triple-confirmation state machine, an OI-trend filter, and cross-strike entry filters. These are evidence for that other, already-shipped system, not for this project's Qualification Engine.

## 3. Entry prerequisites

| Source | Section | Exact wording | Confidence |
|---|---|---|---|
| `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` | §10 (Entry Engine) | "Immediately after Winner. Only ONE trade may remain active. Never take another trade until current trade exits." | HIGH |
| `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` | §10, CONFIRMED (v1.1, Rule 4) | "Only one trade may be active at any time. Ignore all new entry signals until the active trade exits." | HIGH (CONFIRMED status per the spec's own revision history) |
| `BUSINESS_WORKFLOW_SPECIFICATION.md` | transition table | "Qualification → Winner Detection: PARTIALLY, leaning NO. The specification never states that Qualification *gates* Winner Detection at all — Winner Detection (§9) is described purely in terms of candle-level CE/PE touches against reference levels, with no mention of TP/Qualification state as an input. This transition may not exist as a real business dependency; asserting it does would be inventing a rule not present in the evidence." | This is itself the evidence — a documented absence, not a confirmed rule. See Gap Analysis §"Qualification → Winner Detection dependency." |
| `BUSINESS_WORKFLOW_SPECIFICATION.md` | architecture cross-check | "the software architecture review already surfaced that `WinnerEngine` as built takes CE/PE snapshots directly and has zero dependency on `TPEngine`/`QualificationEngine`. This workflow document's independent, software-blind read of the business specification confirms that absence is consistent with the evidence, not a software oversight." | MEDIUM (two independent readings, code and spec, arrived at the same observation — increases confidence this is a real open question, not an oversight) |

**No evidence found** that Qualification (or TP) status is itself an entry prerequisite — the only confirmed entry prerequisite is the single-active-trade rule above, which is independent of Qualification.

## 4. No-trade conditions

| Source | Section | Exact wording | Confidence |
|---|---|---|---|
| `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` | §10 (Entry Engine), Rule 4 | "Ignore all new entry signals until the active trade exits." | HIGH — this is a no-trade condition (an active trade blocks any new one), not derived from Qualification |

No evidence was found of a Qualification-driven no-trade condition (e.g. "do not enter if TP has not qualified") anywhere in the TradingView reconstruction's source material. The legacy ORB Ladder system has its own explicit NEUTRAL/no-trade state, but that is a different system's rule, not evidence for this one.

## 5. Market filters

**No evidence found.** No document in `research/`, `docs/`, or the root-level specification files uses this term, or describes a market-regime/volatility-based filter, for the TP/Qualification system.

## 6. Time filters

**No evidence found**, beyond the structural session-start markers already resolved for Weekly Future (the first 5-minute candle, 09:15–09:20, and TP updates starting "after 09:21 AM" per §7 above). No recurring time-of-day filter (e.g. "do not qualify trades after 2:00 PM") appears anywhere in the source material.

## 7. Strike filters

| Source | Section | Exact wording | Confidence |
|---|---|---|---|
| `BUSINESS_ACCEPTANCE_SPECIFICATION.md` | §3 (Strike Selection) | ATM/strike selection is named as a concept but its own confidence is rated separately — see the already-resolved `StrikeSelector` engine for what *is* confirmed (Top/Bottom Strike = `round(High/50)*50` / `round(Low/50)*50`, an engineering default for the rounding rule, per `WEEKLY_FUTURE_FORMULA_SPECIFICATION.md`) | N/A — this concerns Strike *Selection*, already implemented, not a Qualification-stage *filter* on strikes |
| `research/analysis/TR-001_ANALYSIS.md` | §5 (STRIKE-001 open question) | "'selected based on the first candle' - selected *how*? The quoted fragment ('...First candle... 24050...') shows a resulting strike (24050) but not the calculation connecting the first candle to that strike." | MEDIUM — a strike value is stated but the rule connecting it is not |

No evidence was found of a Qualification-stage filter that excludes/includes specific strikes from consideration (distinct from Strike *Selection*, which chooses Top/Bottom Strike and is already resolved and implemented).

## 8. Premium filters

**No evidence found.** `docs/TRADINGVIEW_STRATEGY_BIBLE.md`'s own `## PREMIUM` section is an empty placeholder heading with no content beneath it (confirmed directly by reading the file — see the earlier evidence review for the Premium Calculator sprint, which reached the same conclusion). No premium-threshold-based qualification filter (e.g. "do not qualify if premium expansion exceeds X") exists anywhere in the source material.

## 9. Trend filters

| Source | Section | Exact wording | Confidence |
|---|---|---|---|
| `research/analysis/TR-001_ANALYSIS.md` | §3.7 | (Tamil, translated in-document) "What I'm saying is this is only Partial Disqualification. For it to count as Complete Disqualification... the intraday low must break AND at the same time the [opposite-side] same-strike TP Low [must also be reached]" | MEDIUM (one clear, extended explanation across two line ranges in a single transcript segment — not yet independently corroborated in another day's segment) |
| `docs/TERMINOLOGY.md` | "Edge (Edge Detection)" | "A condition (TREND-003) where both the current strike's and the opponent's TP Lows remain 'well below' the selected strike, said to significantly reduce the probability of price moving below that strike. 'Well below' is not yet quantified (no fixed distance, percentage, or threshold established)." | LOW/UNKNOWN for the threshold itself; MEDIUM for the concept's existence |

## 10. Risk filters

| Source | Section | Exact wording | Confidence |
|---|---|---|---|
| `BUSINESS_ACCEPTANCE_SPECIFICATION.md` | §10 (Stop Loss) | Named with a rated confidence of "None" per the acceptance doc's own table — no rule content | UNKNOWN |
| `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` | §13 (Trailing Stop, rule content) | Only one confirmed constraint exists: a minimum trailing-stop distance (+3 premium points), per the earlier evidence review for this section | LOW (single constraint, no full mechanism) |

The legacy ORB Ladder system (`orb_common.py`) implements fixed-risk sizing, stop-loss, trailing stop, and a daily-loss cap — but again, this is a separate, already-shipped system's rule set, not evidence for this project's TP/Qualification/Entry chain.

## 11. Confidence scoring

**No evidence found** of confidence scoring as a *runtime trading signal* (e.g. "only qualify if confidence ≥ 70%") anywhere in the source material. The word "confidence" appears throughout this project's own documentation exclusively as an **evidence-quality metadata field** — e.g. `docs/EVIDENCE_MATRIX.md`'s Evidence Count → Confidence mapping (0/1/2/3-4/5+ → Unknown/Low/Medium/High/Confirmed), used to grade how well-sourced a *documented rule* is, not as a value the strategy itself computes or acts on while trading.

---

## Summary of what is genuinely present vs. absent

**Present, with a precise logical form (HIGH on the test shape itself):**
- TP High/TP Low sustain tests (§1)
- Single-active-trade rule (§3, §4)
- Qualification is "current state, not prediction" (§1)
- External-event invalidation is *named* (§1) — but with zero detection mechanism

**Present, but only as an unresolved open question, not a rule:**
- Whether Qualification is a distinct engine from TP at all (§1)
- Whether Qualification gates Winner Detection (§3) — evidence points toward "no," but this is the single most consequential open question in the whole chain
- Partial vs. Complete Disqualification (§9) — a real, quoted concept, Medium confidence, single-source
- "Well below" / Edge Detection threshold (§9) — concept confirmed, magnitude never quantified

**Absent entirely, with no partial statement found anywhere:**
- Market filters (§5)
- Time filters beyond the already-resolved session-start markers (§6)
- Strike filters distinct from Strike Selection (§7)
- Premium filters (§8)
- Confidence scoring as a trading mechanism (§11)

This audit found no new evidence beyond what `research/specifications/QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` already documented for the core sustain-test gaps (competitor identity, cadence, output shape) — but it does add two items that document did not carry: the Partial/Complete Disqualification distinction (§9) and the explicit Qualification→Winner Detection dependency question (§3), both sourced from documents outside that file's own scope.

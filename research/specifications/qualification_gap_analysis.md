# Qualification Engine — Gap Analysis

**Status:** Documentation only. No thresholds are estimated and no missing values are inferred anywhere below — every gap is stated as a gap, not filled with a plausible guess.

---

## Fully Evidenced

Rules whose logical form and operational meaning are both stated clearly enough to implement, with no missing piece:

| Rule | Why it's fully evidenced |
|---|---|
| **QUAL-009** (Single Active Trade) | Explicit CONFIRMED status (v1.1, Rule 4), precise mechanism ("ignore all new entry signals until the active trade exits" — no queueing, no state retention), and it is independent of every other unresolved item in this catalogue. This is the only Qualification-adjacent rule ready to implement today. |

That is the complete list. Nothing else in the catalogue meets the bar of "fully evidenced."

---

## Partially Evidenced

Rules with a real, quoted concept and a precise logical *form*, but missing at least one piece required to actually run them:

| Rule | What's evidenced | What's missing |
|---|---|---|
| **QUAL-001 / QUAL-002** (TP High/Low sustain tests) | The comparison logic itself is stated precisely and consistently in two independent documents (`STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7, `QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` §1) | The competitor's identity (QUAL-007) — without it, there is no concrete value to compare against, so the test cannot execute at all, despite the comparison *shape* being fully known |
| **QUAL-004** (External-event invalidation) | The behavior is named explicitly, with all four trigger categories listed (news/budget/war/natural disaster) | Zero detection mechanism anywhere — "no detection mechanism is specified" is stated directly in the source, not inferred by this analysis |
| **QUAL-005** (Partial vs. Complete Disqualification) | A precise two-part condition for "Complete" is quoted directly, distinguishing it from "Partial" | Single-source, single-transcript-segment — not yet corroborated by a second independent day's segment, the same bar Weekly Future was held to (3 independent, mutually-consistent examples) before it was accepted |
| **QUAL-010** (Edge Detection / "well below") | The concept and its qualitative effect (reduced downside probability) are confirmed | "Well below" has no fixed distance, percentage, or threshold anywhere in the source material — confirmed directly by `docs/TERMINOLOGY.md`'s own "Status: Partial" entry |

---

## Unevidenced

Genuine gaps with **no** partial statement found anywhere in the audited source material — not even a named concept without a mechanism:

| Gap | Notes |
|---|---|
| **Competitor identity for the TP sustain test (QUAL-007)** | The single most consequential blocker in this catalogue — QUAL-001 and QUAL-002 cannot run without it. The only competitor mapping on record (Rule 2) is explicitly scoped to a different stage (Exit Engine, post-Winner), and the specification itself warns against assuming it transfers here. |
| **Qualification cadence** | Tick-by-tick or candle-by-candle re-evaluation is never stated — only "continuously" (`STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7), which is not an implementable execution model on its own. |
| **TP/Qualification output shape** | Whether the result is a price, a boolean qualified/not-qualified flag, or both. `interfaces/tp_engine.py`'s return type is deliberately `object` for exactly this reason. |
| **Whether Qualification is a separate engine from TP (QUAL-006)** | The source material uses "TP" and "qualification" interchangeably and never resolves whether these are one computation or two. |
| **Whether Qualification gates Winner Detection (QUAL-008)** | Evidence leans toward "no dependency exists" (both an independent business-spec-only reading and an independent code-architecture-only reading arrived at the same conclusion), but this is not a confirmed rule in either direction — asserting either answer without further evidence would be inventing a rule. |
| **Market filters** | No document uses this term or describes a market-regime-based qualification filter anywhere. |
| **Time filters** (beyond the already-resolved session-start markers) | No recurring time-of-day qualification filter exists in the source material. |
| **Strike filters** (distinct from Strike Selection) | No qualification-stage filter on which strikes are considered exists — only Strike Selection itself, which is a separate, already-resolved concern. |
| **Premium filters** | `docs/TRADINGVIEW_STRATEGY_BIBLE.md`'s own `## PREMIUM` section is an empty placeholder. |
| **Confidence scoring as a trading mechanism** | "Confidence" exists only as this project's own evidence-quality metadata (`docs/EVIDENCE_MATRIX.md`'s Evidence Count → Confidence mapping) — never as a runtime value the strategy computes or acts on. |
| **Sustain/breach boundary condition** | Whether touching a competitor level exactly (not crossing it) counts as a breach is never addressed in any evidence source reviewed. |
| **Edge-case handling** | What happens if Top Strike's and Bottom Strike's qualification tests conflict, or if inputs are missing/invalid, is never addressed. |

---

## Summary Table

| Category | Count | Rules |
|---|---|---|
| Fully evidenced | 1 | QUAL-009 |
| Partially evidenced | 4 | QUAL-001, QUAL-002, QUAL-004, QUAL-005, QUAL-010 (QUAL-001/QUAL-002 counted together as one mirrored pair) |
| Unevidenced (genuine gaps, no partial statement) | 11 | Competitor identity, cadence, output shape, QUAL-006, QUAL-008, market filters, time filters, strike filters, premium filters, confidence scoring, boundary/edge cases |

**No threshold, identity, or missing value in the "Unevidenced" list has been estimated, guessed, or filled in anywhere in this document or the rule catalogue it accompanies.**

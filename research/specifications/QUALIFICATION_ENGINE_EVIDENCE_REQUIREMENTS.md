# QualificationEngine — Evidence Requirements

**Status:** BLOCKED. This document defines exactly what evidence is required to unblock `QualificationEngine`, per the evidence review performed the same session `WeeklyFutureCalculator`/`StrikeSelector` were resolved. Nothing below infers or guesses at a rule — every "Missing Evidence" item is a direct gap already on record in `STRATEGY_FUNCTIONAL_SPECIFICATION.md` and `WEEKLY_FUTURE_FORMULA_SPECIFICATION.md`.

---

## 1. Current Evidence

| Rule | Source | Confidence | Traceability |
|---|---|---|---|
| Qualification test shape: `TP High` qualifies when `CE > competitor PE Low` AND `PE < competitor CE High`; `TP Low` mirrored | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7 | High (logical form stated precisely) | Direct quote, dictated business rules, 2026-07-29 |
| Qualification represents current market state, not a prediction | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7 | High | Same source |
| External events (news/budget/war/disaster) may invalidate qualification | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7 | High (as a named risk) | Same source — but see §2, no mechanism given |
| Weekly Future High/Low, Top/Bottom Strike | `WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` v1.0 | High (6/6 verified) | 2026-07-30, Product Owner worked examples — a genuine **input** to Qualification, but does not itself resolve the Qualification rule |

That is the complete set. Everything else Qualification needs is in §2.

---

## 2. Missing Evidence

| Gap | Description | Why it blocks implementation |
|---|---|---|
| **Competitor strike identity** | Which strike is "competitor" for the TP High/TP Low test specifically. `STRATEGY_FUNCTIONAL_SPECIFICATION.md` Rule 2 confirms a competitor mapping, but explicitly for a **Winner's entry strike S** (`PE(S-1)`/`CE(S+1)`) — a post-Winner, Exit-stage concept. This is a **pre-Winner** test on Top/Bottom Strike, and the spec explicitly warns not to assume the same S±1 pattern applies | Without this, `CE > competitor PE Low` has no concrete `competitor` to evaluate against — the test cannot run at all |
| **Competitor level definition** | Even once the competitor *strike* is known, which of its levels (High or Low, per side) is the comparison point — the test names both `PE Low`/`CE High` for the High side, so this may already be implicit, but needs confirmation it generalizes the same way for the Low side's mirrored test | Same blocking effect as above |
| **Qualification cadence** | Tick-by-tick or candle-by-candle re-evaluation | Determines the whole engine's execution model — cannot be designed without it |
| **TP output definition** | Whether "TP" (the value being qualified) is a price, a boolean flag, or both — `interfaces/tp_engine.py`'s return type is deliberately `object` for this exact reason | No concrete result model can be built until this is decided |
| **External invalidation mechanism** | What actually triggers "news/budget/war/disaster" invalidation, and how it's detected | Named as a real behavior in the spec but with literally zero detection mechanism anywhere in any evidence source |
| **Edge cases** | What happens if Top Strike and Bottom Strike's qualification tests conflict; what happens if qualification test inputs are missing/invalid; sustain/breach boundary condition (does touching exactly, not crossing, count as breaching?) | None of these are addressed in any evidence source reviewed |

---

## 3. Required Worked Examples

**Minimum dataset:** at least 3 independent, mutually consistent examples (matching the bar that resolved Weekly Future). Each example must supply:

| Field | Description |
|---|---|
| Date | Trading date |
| Reference Strike | The anchor strike used |
| ReferenceLevel | Full CE/PE High/Low for the reference strike (already the `models.reference_level.ReferenceLevel` shape) |
| Weekly Future High | (can be computed via `WeeklyFutureCalculator`, but stating it directly keeps the example self-contained) |
| Weekly Future Low | Same |
| Top Strike | (can be computed via `StrikeSelector`) |
| Bottom Strike | Same |
| **Competitor Strike** | Which strike the example treats as competitor — this is the single most important new field, since it's the core unknown |
| **Competitor Premium OHLC** | The competitor strike's own CE/PE High/Low at the point being evaluated |
| **Qualification Decision** | Whether the setup was judged qualified or not, at that point |
| **Expected Result** | What the engine should output — matching whatever shape §2's "TP output definition" question resolves to (price/boolean/both) |

**Format preference:** the same tabular format the Weekly Future evidence arrived in worked well — plain rows, real numbers, no narration required. That format is directly reusable here.

---

## 4. Acceptance Criteria

`QualificationEngine` implementation may begin **only if all of the following hold**:

- [ ] Competitor mapping (strike + level) is uniquely defined for both TP High and TP Low tests — no ambiguity, no "assume it's the same as Rule 2."
- [ ] The qualification decision is reproducible — recomputing it from the stated inputs, independently, produces the same decision every time (matching the standard already applied to Weekly Future: independent recomputation, not just visual inspection).
- [ ] At least 3 independent worked examples agree with each other (same rule, applied consistently across different dates/strikes).
- [ ] No conflicting examples exist — if any two examples imply different rules for the same input shape, that is a NO-GO, not something to average or guess between.
- [ ] The TP output shape question (§2) is resolved, so a concrete result model can be built rather than continuing to type it `object`.

If any box is unchecked, the correct outcome is the same as this session's: **STOP**, do not implement, update this document instead.

---

## 5. Evidence Intake Checklist

For whoever processes new Qualification evidence, before running it against §4's Acceptance Criteria:

- [ ] Run the source through `research/EVIDENCE_INTAKE_PROCESS.md` in full (Extraction → Verification → Cross-check → Classification → Specification Update → Implementation Approval).
- [ ] Independently recompute every worked example's stated result — do not accept a stated qualification decision without recomputing it from the stated inputs.
- [ ] Check every example against every other example for consistency, not just each one in isolation (this is what caught the sign-flip confusion in `TR-001.md`, and what confirmed the Weekly Future formula's consistency across 3 dates).
- [ ] Explicitly ask, if unclear, whether "competitor" here means the same thing as Rule 2's Exit-stage competitor or something different — do not assume either way.
- [ ] Confirm the TP output shape (price/boolean/both) explicitly, even if it seems obvious from context.
- [ ] Log the source and outcome in `research/evidence_log.md`, whether ACCEPTED or NEEDS MORE EVIDENCE — a negative result is still worth recording, same as `TR-001.md`'s own logged row.
- [ ] If the new evidence resolves the gap, update this document's §1/§2 tables to reflect the new state, and update `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §20 accordingly — do not leave stale UNRESOLVED markers next to a now-resolved rule.

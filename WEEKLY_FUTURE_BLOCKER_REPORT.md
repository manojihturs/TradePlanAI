# Weekly Future Blocker Report

**Status: RESOLVED as of 2026-07-30, for Weekly Future High/Low and Top/Bottom Strike Selection.** See "Resolution (2026-07-30)" at the end of this document. The analysis below is preserved unchanged as the historical record of why this was blocked and for how long — it remains accurate about `TR-001.md` specifically, which is now background/historical evidence rather than the authoritative source.

**Original status (as first written): Implementation BLOCKED.** This document is the formal record of why, built entirely from evidence already extracted from `research/transcripts/TR-001.md` (the only transcript in this repository) and the existing evidence documents (`research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md`, `research/analysis/WEEKLY_FUTURE_VERIFICATION.md`, `research/specification/WeeklyFuture_Specification_v1.md`). No new evidence was sought or fabricated for this report; nothing here is speculation.

---

## 1. Why Weekly Future cannot be implemented today

`weekly_future/` requires an exact, reproducible formula for Weekly Future High and Weekly Future Low. The only source material available (`TR-001.md`) contains exactly **one** attempt at a full worked example of this calculation (lines 2460–2521), and that example:

- Never settles on a single value for its own High-side addend (three different numbers are spoken for the same quantity — see Section 2).
- Produces two different, unreconciled final values for the Low, one of which is numerically *higher* than the High for the same candle — a structural impossibility for a genuine High/Low pair.
- Is built on Put option inputs that are themselves stated two conflicting ways in the same breath.
- Was explicitly framed by its own speaker as an *illustration*, not the from-scratch method — he refers listeners to a separate, uncaptured video twice for "the complete calculation."

An implementation built from this material would necessarily encode a guess dressed up as a formula. Per this project's evidence-first discipline (in force since Phase 5 of this project), that is not an acceptable basis for a trading engine component — the risk is not "the code doesn't work," it is "the code runs, looks correct, and silently computes wrong strike levels."

---

## 2. Every contradiction found in the transcript

All four, quoted and cited exactly as previously extracted and independently re-verified against the raw transcript:

1. **High-side addend, spoken three ways.** "153-72 ... 91" → immediately retracted: "91 இல்லையே ... 81ன்ற வேல்யூ நமக்கு வருது" ("that's not 91 ... we get 81") → then, in the very next sentence, actually adds "82" to the strike: "150 பிளஸ் 82 81 ஓகே ... 26232 இதுதான் ஹை." The final stated High (26,232) is arithmetically consistent with adding ~82, not the 81 the speaker had just corrected to seconds earlier. (TR-001.md, session timestamps 00:03:38–00:05:13.)

2. **Two different Low values for the same candle, same segment.** First: "பிளஸ் பண்ணிங்கன்னா என்ன வரும் 268 இதுதாங்க லோ" (≈26,268, by the same speaking convention used for the High). Minutes later, same continuous walkthrough: "நம்ம ஏற்கனவே சொன்னோம் என்ன லோ வேல்யூ வந்துச்சு 261 168 வரைக்கும் வந்துச்சுன்னு சொன்னோம் லோ" ("we already said the low value came to 26,168"). Neither is reconciled with the other. (TR-001.md, session timestamps 00:06:06 and 00:09:57.)

3. **Low higher than High.** The ≈26,268 reading from contradiction #2 is numerically *greater than* the High computed moments earlier in the same walkthrough (26,232) — for the same candle, the same example. The speaker never notices or addresses this.

4. **Put option's own first-candle High/Low, stated two conflicting ways.** "புட்டுடைய ஃபர்ஸ்ட் கேண்டில் ஹை அண்ட் லோ என்ன இது? 95.5 95 ஓகே 95 72" — two different candidate pairs ("95.5, 95" and "95, 72") given in the same breath for what should be one fact, never disambiguated. Every subsequent number in the worked example depends on this input. (TR-001.md, session timestamp 00:02:46.)

Independently, `research/analysis/WEEKLY_FUTURE_VERIFICATION.md` (Phase E1) applied a stricter rubric requiring at least three internally-consistent worked examples before evidence is accepted, and found **zero** — the transcript contains only this one attempt, and it fails on its own terms.

---

## 3. Every missing business rule

Per `WeeklyFuture_Specification_v1.md`'s Section 2/4/6/8, the following are not answered anywhere in the source at all (not contradicted — simply absent):

- Whether Weekly Future is recalculated intraday, or only ever computed once at the first candle.
- What instrument(s) and expiry type (weekly vs. monthly) the calculation applies to, or whether it differs by either.
- Whether previous-day or previous-week data feeds the calculation in any way.
- Whether "Weekly Future" is a full OHLC candle series (implying an Open must exist) or just a derived High/Low(/Close) pair — no "Weekly Future Open" is ever computed or named.
- A general, symbolic form of the sign-flip rule ("if the subtraction goes negative, add instead of subtract from the strike") — it is only demonstrated narratively, once, for one specific input ordering, with no confirmation it generalizes to the other three possible orderings.
- Rounding/precision rules beyond one ad hoc instance (149.6 rounded to 150, with no stated general rule).

---

## 4. Every downstream module blocked by Weekly Future

Per `research/architecture/MODULE_ARCHITECTURE.md`'s dependency graph and `IMPLEMENTATION_ROADMAP.md`'s phase sequencing, `weekly_future/`'s output (`WeeklyFuture.high`/`.low`) is a direct input to:

- **`strike_selector/`** — Top Strike/Bottom Strike selection consumes Weekly Future High/Low directly (Specification Section 5).
- **`tp_engine/`** — depends transitively on the strikes `strike_selector/` produces.
- **`qualification_engine/`** — depends on `tp_engine/`'s output.
- Transitively, **`winner_engine/`'s full production use** (it is built and tested today against caller-supplied strikes/levels, but in a live/replay run those strikes come from `strike_selector/`, which is itself blocked).

In short: every remaining unbuilt business engine in the roadmap sits downstream of this one blocker, in a straight dependency chain.

---

## 5. What evidence is required before implementation can begin

Unchanged from `WEEKLY_FUTURE_VERIFICATION.md`'s own conclusion, restated here as the formal gate:

1. **Primary path:** locate and transcribe the "Complete Calculation Video for Weekly Future" the speaker explicitly references twice in TR-001 (session-relative, corresponding to lines ~816–820 and 2467) as containing the full method.
2. **Fallback path, absent (1):** at least three additional worked examples, from an equivalent-priority source, that independently and consistently compute a Weekly Future High and Low from stated Call/Put inputs, with every intermediate step reproducible and no internal contradiction — the acceptance bar `WEEKLY_FUTURE_VERIFICATION.md` already applied and found unmet by the existing single example.

No other path (inference from trading-domain general knowledge, reconstruction from the contradictory example by picking whichever numbers seem "more likely correct") satisfies this project's evidence-first discipline.

---

## 6. Final engineering recommendation

**DELAY.**

- **Implement** — rejected. The only available worked example is self-contradictory in its inputs and outputs; implementing from it means shipping a formula nobody can currently prove is correct, in the one component every other unbuilt module depends on.
- **Reject implementation** (permanently abandon Weekly Future as a concept) — rejected. Nothing in the evidence suggests the underlying idea is wrong, only that this transcript's explanation of it is incomplete by its own speaker's admission. There is a stated, locatable path to resolving it (the referenced video).
- **Delay** — recommended. Hold `weekly_future/` (and everything downstream of it) exactly where it is now: framework complete and frozen through Sprint 4, `interfaces/weekly_future_calculator.py` remaining a Protocol-only stub, no placeholder logic anywhere. Resume only when Section 5's evidence bar is met.

This report is the design-decision record for that delay, so that neither a future session of this assistant nor another contributor implements `weekly_future/` from the current contradictory evidence without first seeing this document.

---

## Resolution (2026-07-30)

On 2026-07-30, the Product Owner supplied 3 independent, fully worked examples (6 data points: Weekly Future High and Low for each of 3 trading dates) directly in chat. Every value was independently recomputed and matched exactly — zero contradictions, meeting the fallback evidence bar this report set in §5.

**Formula (see `research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` v1.0 for the full specification):**

```
Weekly Future High = Strike + (CE High(1st 5-min) − PE Low(1st 5-min))
Weekly Future Low  = Strike − (PE High(1st 5-min) − CE Low(1st 5-min))
Top Strike         = round(Weekly Future High / 50) * 50
Bottom Strike      = round(Weekly Future Low / 50) * 50
```

This single signed-subtraction formula also resolves the sign-flip ambiguity flagged in §3 of this report — no special-case ordering rule is needed; the subtraction goes negative automatically when required (demonstrated directly in the 2026-07-28 example).

**`TR-001.md`'s status:** reclassified from sole/blocking source to historical/background evidence. Every contradiction documented in §2 of this report remains an accurate description of `TR-001.md` itself — nothing there was wrong. `TR-001.md` is simply no longer the source consulted for the numeric formula; `research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` is.

**Still unresolved, per the new specification's own §6–§8:** Entry rules, Exit rules (Stop Loss, Time Exit), and Exceptions (Holiday, Gap Up, Gap Down, Invalid Data). Only Weekly Future High/Low and Top/Bottom Strike Selection are resolved by this evidence.

**Downstream effect:** `WeeklyFutureCalculator` and `StrikeSelector` move from BLOCKED to READY FOR IMPLEMENTATION. `TPEngine`, `QualificationEngine`, `StopLossEngine`, `TrailingStopEngine` remain BLOCKED — their own evidence gaps (competitor identity, SL rule, trailing mechanics) are untouched by this resolution.

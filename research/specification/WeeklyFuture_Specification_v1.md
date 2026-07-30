# Weekly Future Specification v1

**Role of this document:** strategy reverse-engineering, not software engineering. Every statement below is either a direct extraction from `research/transcripts/TR-001.md` (the only transcript file in this repository — confirmed by directory listing; `research/videos/` contains nothing usable) or explicitly marked `NOT SPECIFIED IN SOURCE`. Nothing is inferred, completed, or corrected. Line numbers refer to `research/transcripts/TR-001.md` as it currently exists in the repository; I additionally re-read the raw transcript at the cited lines directly (not only the prior evidence tables) before writing this document, to confirm the quotes below are accurate.

**Source material used:** `research/transcripts/TR-001.md` (4,245 lines, Tamil, informal spoken transcript of what appears to be a trading-education video/livestream). This is the only source available in the repository. Two prior evidence-extraction passes over this same file already exist — `research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md` and `research/analysis/WEEKLY_FUTURE_VERIFICATION.md` — and this document draws on their line references, independently re-verified against the raw transcript, rather than re-deriving them from scratch.

---

## Section 1 — Overview

**What Weekly Future is**, per the source (lines 347–348):

> "வீக்லி பியூச்சர் ஒன்னு அஃபிஷியலி கிடையாது. நாம பிரீமியம் அனாலிசிஸ் வழியா வீக்லி பியூச்சர் புரிஞ்சுக்கிட்டு அதன்படி லெவல்ஸ் எடுத்து தான் நாம இந்த ஸ்ட்ரைக் பிரைஸ் சூஸ் பண்றோம்."

Translation: "There's no such thing as an official 'Weekly Future.' We understand the Weekly Future through premium analysis, and based on that we take levels and choose the strike price."

**Why it exists**, per the source (lines 2467–2470, paraphrased from direct quotation): the speaker states there is no NSE-listed "Weekly Future" instrument for the underlying being traded; it must be derived manually from option-premium (Call/Put) data as a substitute reference level.

**When it is used**, per the source: as the basis for choosing the strike price (line 2461: "வீக்லி ஃியூச்சரின் அடிப்படையில் தான் நாம வந்து ஸ்ட்ரைக் பிரைஸ் செலக்ட் பண்றோம்" — "It's on the basis of the Weekly Future that we select the strike price").

---

## Section 2 — Inputs

| Input | Status | Source |
|---|---|---|
| First candle's High and Low (of the option premium, not the underlying) | **Specified** | Line 2464: "ஃபியூச்சர எடுத்துப்போம். ஓகே அந்த வீக்லி பியூச்சரோட கால்குலேஷன் ஹை ஃபர்ஸ்ட் கேண்டிலோட ஹை லோ ஓபன் உங்களுக்கு என்னென்ன டேட்டா எனக்கு ஹை லோவே போதுமானது" — "For the Weekly Future calculation — high, first candle's high, low, open — what data do you need? For me, high and low alone are enough." |
| Call option's first-candle High | **Specified** (one example value given) | Line 2473: "காலுடைய ஹை அண்ட் லோ என்ன? கால் வந்து 153 113" — Call High/Low = 153/113 |
| Put option's first-candle High | **Specified, but internally inconsistent** | Line 2476: "புட்டுடைய ஃபர்ஸ்ட் கேண்டில் ஹை அண்ட் லோ என்ன இது? 95.5 95 ஓகே 95 72" — the speaker states two different candidate pairs ("95.5, 95" and then "95, 72") in the same breath, without reconciling them |
| Put option's first-candle Low | Same passage as above — ambiguous between 95 and 72, never disambiguated | Line 2476 |
| ATM strike (as the anchor value) | **Specified** (one example value given) | Line 2473: "26 150" used as the strike anchor throughout the worked example |
| Open (of the first candle) | **Named as available but not required** | Line 2464: Open is listed alongside High/Low as available data, but the speaker states "எனக்கு ஹை லோவே போதுமானது" ("for me, High/Low alone is enough") |
| Close (of the first candle) | **Specified for a separate, additional computation** (see Section 5) | Line 2508–2509: Call close 149.6 ("150 எடுத்துப்போம்" — "let's take 150"), Put close 75 |
| Instrument | NOT SPECIFIED IN SOURCE | No instrument name is stated in the cited passages; strike values (26150, etc.) imply NIFTY-scale, but this is not confirmed anywhere as a stated rule |
| Expiry | NOT SPECIFIED IN SOURCE | — |
| Previous Day Data | NOT SPECIFIED IN SOURCE | The phrase "நேத்தைக்கு" ("yesterday") appears (line 2461) referring to which trading day's example is being walked through, not as a calculation input |
| Previous Week Data | NOT SPECIFIED IN SOURCE | — |
| Option Chain (full chain vs. single strike) | NOT SPECIFIED IN SOURCE | Only one strike's Call/Put pair is used in the worked example |

---

## Section 3 — Calculation

**Rule as stated in natural language** (two separate, mirror-image statements):

- **High** (line 2476): "ஹை அப்படினாலே காலுடைய ஹையும் புட்டுடைய லோவும்" — "High means: the Call's High and the Put's Low."
- **Low** (line 2479): "வீக்லி ஃியூச்சர்ல நான் லோ கால்குலேட் பண்ண போறேன் அப்படின்னா புட்டுடைய ஹையும் காலுடைய லோவும்" — "For the Weekly Future's Low: the Put's High and the Call's Low."

**Sign rule for High** (line 2482): once the difference (Call-High − Put-Low) is obtained, "இது வந்து ஹை ஹைனாலே கால் இப்ப வந்து ப்ளஸ் பண்ணனும் ஹைனாலே ஸ்ட்ரைக் ப்ரைஸ் கூட பிளஸ் பண்ணனும்" — "since it's a high, add it — add it to the strike price too."

**Sign rule for Low** (lines 2485–2488): "யூசுவலா நம்ம லோனா என்ன பண்ணனும்? ஸ்ட்ரைக் ப்ரைஸ் கூட மைனஸ் பண்ணனும் ... இப்ப - இங்க ஒரு மைனஸ், இந்த -. சோ, ரெண்டுத்துக்கும் - + ஆயிடும்." — "Normally for the Low, subtract from the strike price... but here there's a minus, and this is also a minus, so the two minuses become a plus." I.e., if (Put-High − Call-Low) is negative, the subtraction from the strike is replaced by an addition.

**Worked arithmetic, exactly as spoken (High side, lines 2479–2485):**

> "153-72 153-72 எவ்வளவு வரும்? 53 இது ஒரு 72னா 28 சோ 53+2 53னா 61 91 ஓகே சோ 91ன்னு ஒரு வேல்யூ கிடைக்கும்னு நினைக்கிறேன்"
> → then: "91 இல்லையே ஓகே ... 81ன்ற வேல்யூ நமக்கு வருது"
> → then: "150 பிளஸ் 82 81 ஓகே 26 150 பிளஸ் 82 ஓகே இதை ஆட் பண்ணிங்கன்னா என்ன வருது 2 83 1 2 26 232 இதுதான் ஹை"

The speaker computes 153 − 72, states "91," immediately says that's wrong, self-corrects to "81," then in the very next breath adds "82" (not 81) to the strike to reach a final stated High of **26,232**.

**Worked arithmetic, exactly as spoken (Low side, lines 2485–2488):**

> "லோ பாத்தீங்கன்னா புட்டுடைய ஹையும் காலுடைய லோவும் அப்ப ஹை மை லோ ... ஹை வந்து 95 ஓகே - 113 ... 95-க்கும் 113-க்கும் என்ன டிஃபரன்ஸ் இருக்கு? ஒரு 13 ஒரு 5. சோ, 18 18 வந்து டிஃபரன்ஸ். ஆனா பெரிய நம்பர் வந்து 113. அதனால நெகட்டிவ் ... ரெண்டுத்துக்கும் - + ஆயிடும். சோ, + ஓகே. இப்ப பிளஸ் பண்ணிங்கன்னா என்ன வரும் 268 இதுதாங்க லோ"

The stated difference is "18," the sign-flip rule is invoked, and the final stated Low is **"268"** (spoken the same way the High's "232" was spoken, i.e. presumably meaning 26,268 by the same convention — this equivalence is not stated explicitly by the speaker, only inferred by the pattern of speech used for the High).

**No formula is ever written down symbolically, in a table, or on-screen (as transcribed) — only spoken procedurally, once for each of the High and Low sides.**

**Multiple, non-reconciled versions of the same value exist** (see Section 8 for the full list):
- High-side addend: spoken as 91, then corrected to 81, then 82 is actually used in the final sum.
- Low value: computed as "268" (≈26,268) in this passage, then restated minutes later (line 2506) as "26168" — a different number, for what the speaker calls the same value, never reconciled.
- Put High/Low inputs: stated as both "95.5, 95" and "95, 72" in the same breath (line 2476), never disambiguated.

---

## Section 4 — Timing

- **First candle only, computed once per stated example** (line 2461–2464): "ஃபர்ஸ்ட் கேண்டில் ஓபன் ஆனதுமே நம்ம வீக்லி ஃபியூச்சர எடுத்துப்போம்" — "As soon as the first candle opens, we take our Weekly Future."
- No statement anywhere in the cited passages describes recalculation later in the day, on every candle, on a timer, or on any other trigger.
- **Whether it is ever recalculated intraday: NOT SPECIFIED IN SOURCE.**
- **Whether it is recalculated only once per week, once per day, or some other cadence beyond "at the first candle": NOT SPECIFIED IN SOURCE.**

---

## Section 5 — Output

- **Weekly Future High**: one worked example gives **26,232** (line 2485).
- **Weekly Future Low**: one worked example gives two different, non-reconciled values — **"268"** (≈26,268 by inferred convention, line 2488) and, minutes later in the same continuous segment, **"26168"** (line 2506: "நம்ம ஏற்கனவே சொன்னோம் என்ன லோ வேல்யூ வந்துச்சு 261 168 வரைக்கும் வந்துச்சுன்னு சொன்னோம் லோ" — "we already said the low value came to 26,168").
- **A "Weekly Future Close" is also computed** in the same segment (lines 2508–2509), via a different, simpler method with no sign-flip logic at all: Call close (149.6, rounded to "150" by the speaker) plus Put close (75) added directly to the strike: 26150 + 75 = **26,225**. The speaker calls this "இது வீக்லி ஃியூச்சர்ட கேண்டில் க்ளோஸ்" — "this is the Weekly Future candle's close."
- **Intermediate values**: differences are computed (e.g. "153 − 72," "95 vs 113 difference of 18") but the intermediate values themselves are inconsistently stated (91 → 81 → 82 used).
- **Round-off rules**: the speaker rounds 149.6 to 150 ("150 எடுத்துப்போம்") for the Close calculation, with no stated general rounding rule (nearest integer? nearest strike step? not stated).
- **Precision**: **NOT SPECIFIED IN SOURCE** beyond the one rounding instance above.
- **Whether Weekly Future is itself an OHLC candle series (with its own Open in addition to the computed High/Low/Close) is NOT SPECIFIED IN SOURCE.** Only High, Low, and (separately) a Close-derived value are computed; no "Weekly Future Open" is computed or named anywhere in the cited passages.

---

## Section 6 — Dependencies

| Dependency | Status |
|---|---|
| Reference Levels (i.e., a specific strike's Call/Put first-candle data) | **Yes** — the calculation is anchored to one specific ATM strike's Call and Put option premiums (line 2470: "நான் வந்து 150 கால் புட் எடுத்துருக்கேன்" — "I've taken the 150 Call/Put") |
| Expiry (weekly vs. monthly contract) | NOT SPECIFIED IN SOURCE |
| Weekly Contract specifically vs. any other | NOT SPECIFIED IN SOURCE — the term "Weekly Future" is used, but no statement distinguishes weekly-expiry from monthly-expiry option data as the source of the Call/Put premiums used |
| Previous Day | NOT SPECIFIED IN SOURCE as a calculation dependency (see Section 2) |
| Previous Week | NOT SPECIFIED IN SOURCE |
| Underlying spot price | NOT SPECIFIED IN SOURCE as a direct input — only the ATM strike's own option premiums are used in the worked example |
| A separately-referenced external video ("Weekly Future Calculation video" / "Complete Tutorial Complete Calculation Video for Weekly Future") | **Explicitly referenced twice** (line 816–820 area, and line 2467) as containing the complete method — **not part of this transcript** |

---

## Section 7 — Examples

**Exactly one full worked example exists in the entire 4,245-line transcript** (lines 2460–2521, session-internal timestamps 00:00:04–00:13:06). It is reproduced across Sections 3 and 5 above in full, quoted verbatim. No other worked example of a Weekly Future High/Low calculation appears anywhere else in the source. No new example is calculated here — per instruction, only extracted examples are reported.

Summary of the one example's stated inputs and outputs, exactly as spoken:

| Quantity | Value(s) stated |
|---|---|
| Strike (anchor) | 26150 ("150") |
| Call first-candle High | 153 |
| Call first-candle Low | 113 |
| Put first-candle High/Low | "95.5, 95" then "95, 72" (two different, unreconciled pairs) |
| Weekly Future High | 26,232 |
| Weekly Future Low | "268" (≈26,268) — later restated as "26,168" |
| Call first-candle Close | 149.6 (rounded to 150) |
| Put first-candle Close | 75 |
| Weekly Future Close | 26,225 |

---

## Section 8 — Ambiguities

**Ambiguity 1**
**Question:** What is the exact, correct addend used to compute Weekly Future High from the strike?
**Why it matters:** The speaker computes the Call-High-minus-Put-Low difference three different ways in immediate succession (91, then corrected to 81, then actually adds 82) without ever settling on one value on camera.
**Blocks:** `WeeklyFutureCalculator`, and transitively `StrikeSelector` and `TPEngine` (both of which the architecture already treats as depending on Weekly Future's output).

**Ambiguity 2**
**Question:** What is the correct Weekly Future Low for the one worked example — 26,268 or 26,168?
**Why it matters:** Two different final values are stated by the speaker for what he calls the same computed Low, minutes apart in the same continuous segment, and never reconciled. Additionally, the ≈26,268 reading is numerically *higher* than the stated High (26,232) for the same candle — a structural impossibility for a genuine High/Low pair, which the speaker never notices or addresses.
**Blocks:** `WeeklyFutureCalculator`, `StrikeSelector`, `TPEngine`.

**Ambiguity 3**
**Question:** What are the Put option's actual first-candle High and Low values?
**Why it matters:** The speaker states "95.5, 95" and then, in the same breath, "95, 72" as the Put's first-candle High/Low — two different candidate pairs for what should be a single fact, never disambiguated. Every downstream number in the worked example depends on this input.
**Blocks:** `WeeklyFutureCalculator` (this specific worked example cannot be independently reproduced/checked because its own inputs are self-contradictory).

**Ambiguity 4**
**Question:** Is the sign-flip rule ("if the subtraction goes negative, addition replaces subtraction from the strike") a complete, general rule, or does it only cover the one case demonstrated?
**Why it matters:** The rule is described narratively, once, for the specific case where Put-High (95) is less than Call-Low (113) on the Low side. No symbolic/general form covering all four possible orderings (Call-High vs. Put-Low; Put-High vs. Call-Low) is given.
**Blocks:** `WeeklyFutureCalculator` — an implementer cannot derive behavior for input combinations the transcript doesn't happen to demonstrate.

**Ambiguity 5**
**Question:** Where does the "complete/correct" version of this calculation live?
**Why it matters:** The speaker explicitly and repeatedly (at least twice, lines ~816–820 and 2467) defers to a separate, named "Weekly Future Calculation" / "Complete Tutorial Complete Calculation Video" that is not part of this transcript. Everything in TR-001 is presented as an *illustrative* worked example assuming that separate video's method as a given baseline, not as the from-scratch definition of the method.
**Blocks:** All downstream modules — this is the most consequential gap, since it means TR-001 was never intended by its own speaker to be a complete specification of this rule.

**Ambiguity 6**
**Question:** Does "Weekly Future" refer to a single computed High/Low/Close pair, or a full OHLC candle series with its own Open?
**Why it matters:** High, Low, and (separately, via a different method) Close are each computed in the example, but no "Weekly Future Open" is ever computed or named, and no statement clarifies whether Weekly Future is conceptually a candle (implying an Open must exist) or just a pair/triple of derived reference numbers.
**Blocks:** `WeeklyFutureCalculator`'s output shape — the existing engine's `models.weekly_future.WeeklyFuture` model (built in Sprint 1) currently has only `high`/`low` fields, with no `close`; whether that is correct or incomplete cannot be determined from this transcript alone.

**Ambiguity 7**
**Question:** What instrument, expiry, and (if applicable) previous-day/previous-week data does this calculation depend on, if any?
**Why it matters:** None of these are mentioned in the cited passages at all. The one worked example is self-contained (one strike, one first candle), so it's unclear whether the method generalizes across instruments/expiries or was implicitly instrument-specific.
**Blocks:** `WeeklyFutureCalculator`'s full input contract.

---

## Section 9 — Confidence

| Extracted rule/fact | Confidence | Basis for rating |
|---|---|---|
| Weekly Future is not an exchange-listed instrument; it must be manually derived | **High** | Stated plainly, multiple times, with no contradiction anywhere in the source |
| First candle's High/Low are the primary required input (Open/Close available but not required for High/Low) | **High** | Stated plainly and consistently |
| High = f(Call-High, Put-Low); Low = f(Put-High, Call-Low), mirror-image rule | **High** (as a stated procedural rule) | Stated clearly, twice, in immediate succession, using parallel language for both sides |
| Sign-flip rule ("negative subtraction becomes addition") | **Medium** | Stated narratively and applied once; no general symbolic form; only demonstrated for one specific input ordering |
| The specific numeric example's Call inputs (153, 113) | **High** | Stated once, cleanly, no contradiction |
| The specific numeric example's Put inputs (95/95.5, 72) | **Low** | Two different, unreconciled pairs stated for the same fact |
| The specific numeric example's High output (26,232) | **Low** | Reached via an addend (91→81→82) that is never cleanly pinned down; the final total is consistent with adding ~82, not the "81" the speaker had just settled on |
| The specific numeric example's Low output | **Low** | Two different final values (≈26,268 and 26,168) stated for the same computed quantity, never reconciled; also numerically inconsistent with the High (Low > High) |
| The Close-derived value (26,225) | **Medium-High** | The arithmetic itself (26150 + 75 = 26225) is internally consistent and verifiable, but its relationship to "Weekly Future High/Low" (a third, differently-computed quantity) is not explained |
| A complete/authoritative version of this method exists in a separate, uncaptured video | **High** | Stated explicitly, twice, by the speaker himself |
| Timing: computed once at the first candle, not recalculated intraday | **Low** | Only "computed at the first candle" is stated; absence of any recalculation statement is not the same as a confirmed "never recalculated" rule |
| Expiry/instrument dependency | **None (not specified)** | No statement addresses this at all |

---

## Consolidated verdict

This document extracts everything the source contains on this topic. It does not resolve, average, or pick among the contradictory numbers reported above — per instruction, contradictions are quoted and flagged, not adjudicated. Combined with the independent, stricter re-verification already performed in `research/analysis/WEEKLY_FUTURE_VERIFICATION.md` (which found zero internally-consistent worked examples against a three-example acceptance bar), the material available in `TR-001.md` does not constitute a complete, unambiguous, implementable specification of the Weekly Future calculation. The speaker's own repeated references to a separate "Complete Calculation Video for Weekly Future" (Ambiguity 5) indicate this transcript was never intended to be the full method on its own.

**Recommendation (analysis only, not an engineering decision):** the most direct path to resolving this is locating and transcribing the video the speaker references twice (Ambiguity 5). Absent that, at least three additional, internally-consistent worked examples from an equivalent-priority source would be needed before `weekly_future/` can be implemented without guessing.

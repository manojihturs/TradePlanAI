# Weekly Future Calculation — Dependency Analysis — TR-001.md

Source: `research/transcripts/TR-001.md` only. Companion to `WEEKLY_FUTURE_EVIDENCE_TABLE.md` (row references WF-1 through WF-15 below refer to that table).

**Readiness verdict: PARTIALLY READY.** The transcript names the required inputs and states the intended combination rule in natural language, but does not provide a clean, internally-consistent, fully-verifiable numeric derivation, and it twice explicitly points to a separate, uncaptured video as the place where the "complete" calculation is taught. This file documents, as a dependency chain, exactly which steps a StrikeCalculator/WeeklyFutureCalculator implementation would be blocked on.

## Dependency chain (text-described, no code/pseudocode)

Weekly Future High requires:
- Input A: Call option's first-candle High (spoken value in the worked example: 153 — WF-7)
- Input B: Put option's first-candle Low (spoken value in the worked example: stated ambiguously as either 72 or part of "95.5 95" in the same breath — WF-8)
- Input C: the day's chosen ATM strike price (spoken value: 150, i.e. 26150 — WF-7)
- Combined via an operation the transcript states only as: "ஹை அப்படினாலே காலுடைய ஹையும் புட்டுடைய லோவும்" ("high means Call's high and Put's low") followed by a subtraction of B from A, then addition of the result to C — narrated as "153-72 ... 91 ... [self-corrected to] 81 ... 150 பிளஸ் 82 81 ... 26232" (WF-10 through WF-13)
- **Blocking issue:** the subtraction itself is performed incorrectly on-camera and self-corrected once (91 → 81), and the value actually added in the final step ("82") does not clearly match the corrected subtraction result ("81") — so even the ONE worked example does not give an implementer a clean, checkable (input → output) pair for the High side.

Weekly Future Low requires:
- Input A: Put option's first-candle High (spoken value: 95 — WF-8/WF-14)
- Input B: Call option's first-candle Low (spoken value: 113 — WF-7/WF-14)
- Input C: the same ATM strike price (26150)
- Combined via an operation stated only as: "லோ பாத்தீங்கன்னா புட்டுடைய ஹையும் காலுடைய லோவும் அப்ப ஹை மை லோ" ("for the low: Put's high and Call's low, so High minus Low") — i.e. Put-High minus Call-Low — followed by a conditional sign rule narrated as: "ஆனா பெரிய நம்பர் வந்து 113. அதனால நெகட்டிவ் ... ரெண்டுத்துக்கும் - + ஆயிடும்" ("but the bigger number is 113, so it's negative ... the two negatives become a plus") — i.e., if Put-High < Call-Low (making the subtraction negative), the usual "subtract the difference from the strike" step flips to "add the difference to the strike" instead.
- **Blocking issue #1:** the transcript shows the difference being identified as "18" (95 vs 113) but then jumps directly to a final answer of "268" without displaying the addition step that would let an implementer verify 26150 + 18 (or any other combination) actually produces 268 (WF-14). The intermediate step is missing from the transcript, not just condensed.
- **Blocking issue #2:** moments later in the SAME walkthrough, the speaker restates the Low as "26168" ("நம்ம ஏற்கனவே சொன்னோம் என்ன லோ வேல்யூ வந்துச்சு 261 168 வரைக்கும் வந்துச்சு" — WF-15), a different number from the "268" (≈26268) just computed, with no reconciliation of the two.
- **Blocking issue #3:** a Low of ≈26268 (or even 26168) is not clearly less than the High of 26232 computed for the same candle in the same breath — for ≈26268, the Low would numerically exceed the High, which is structurally impossible for a genuine High/Low pair and is never flagged by the speaker as an error requiring correction.

Weekly Future Close (a separate, secondary output mentioned only once) requires:
- Input A: Call option's first-candle Close (149.6, rounded by the speaker to 150 — WF-15)
- Input B: Put option's first-candle Close (75 — WF-15)
- Input C: the ATM strike (26150)
- Combined via simple addition, with NO sign/conditional logic shown or apparently needed in this instance: "26 150 பிளஸ் 75 225 ஓகே 26 225" (WF-15)
- **Note:** this is the one clean, internally-consistent, checkable piece of arithmetic in the whole passage (26150+75=26225 is correct), but it covers only the Close, not the High or Low, and the speaker does not explain why the Close computation needs no conditional sign-flip step while the High and Low computations do.

Weekly Future "Open" (named as an available input, never computed):
- The speaker lists Open as one of the data fields available ("ஃபர்ஸ்ட் கேண்டிலோட ஹை லோ ஓபன்" — WF-5) but immediately states it is not needed ("எனக்கு ஹை லோவே போதுமானது" — "for me, high and low alone are enough") and never demonstrates an Open calculation anywhere in the file.

Downstream (already covered by STRIKE_EVIDENCE_TABLE.md, not re-analyzed here):
- Once a Weekly-Future-High and Weekly-Future-Low value exist (however computed), the speaker's rounding step — "choose the strike nearest to that computed value" — is well documented and largely consistent across STRIKE_EVIDENCE_TABLE.md rows 10-12, 14. That downstream step is not the blocker; the blocker is entirely upstream, in getting a clean, verifiable Weekly-Future-High/Low in the first place.

## Root blocker, stated plainly

The transcript explains the INTENDED mechanism (Call-High/Put-Low combination for the High side; Put-High/Call-Low combination with a conditional sign-flip for the Low side) clearly enough in natural language that the general shape of the rule is not in doubt. What is missing is:

1. A single example where the arithmetic is carried out correctly and consistently from stated inputs to stated output, without self-correction, without an unexplained jump from "difference = 18" to "answer = 268," and without two different numbers ("268" and "26168") being given for what is described as the same value.
2. An explicit, general statement of the sign-flip rule that would apply to all four possible orderings of (Call-High vs Put-Low) and (Put-High vs Call-Low), rather than the one specific case narrated ad hoc in this passage.
3. The content of the video the speaker himself points to twice as the authoritative source ("வீக்லி ஃியூச்சர் கால்குலேஷன் வீடியோ," line 816; "கம்ப்ளீட் டுடோரியல் கம்ப்ளீட் கால்குலேஷன் வீடியோ ஃபார் வீக்லி ஃியூச்சர்," line 2467) — which is not part of `research/transcripts/TR-001.md` and, per the directory listing, does not exist anywhere else in this repository (`research/videos/` and the rest of `research/transcripts/` contain only `.gitkeep`).

Until either (a) the referenced "Complete Calculation Video for Weekly Future" is obtained and transcribed, or (b) a clean, self-consistent worked example is found elsewhere in this transcript (none was found in this review), a StrikeCalculator/WeeklyFutureCalculator implementation can be scaffolded around the stated input fields and the general shape of the rule, but cannot be validated against a trustworthy numeric example from source material, and the exact sign/operator logic for all cases cannot be stated with full confidence.

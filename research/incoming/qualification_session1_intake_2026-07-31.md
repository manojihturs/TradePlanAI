# Session 1 — Qualification Evidence Intake (Product Owner)

**Status:** Blank intake document — to be filled in by/with the Product Owner. Nothing in this file is evidence yet; it becomes evidence only once the fields below are answered. Once filled in, this file moves through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification) and is scored against `research/specifications/evidence_acceptance_checklist.md`.

**Targets:** This session exists to close **QUAL-007** (the TP-stage competitor identity) — the single blocker keeping `QualificationEngine` frozen. See `research/specifications/qualification_remaining_unknowns.md` for exactly what's missing and why: no source anywhere in this repository names, defines, or gives a worked example of the competitor used in the TP High / TP Low sustain tests. This session is the artifact that document said would be required.

**Do not fill in a field with a guess.** If the Product Owner doesn't know or isn't sure, write `UNKNOWN` — an honest "I don't know" is usable input to the intake process; a guessed value is not (it will be classified as an Assumption, not a Confirmed Rule, per `EVIDENCE_INTAKE_PROCESS.md` Section 2).

---

## Instructions for the session

Open **one historical trading day at a time**, and for each, walk through the four questions below while looking at the actual chart/data together with the Product Owner. Repeat for 3–5 separate days — this project's own acceptance bar (`evidence_acceptance_checklist.md`, "minimum three worked examples") requires at least three, and a fourth/fifth is valuable specifically for surfacing a **Counter Example** (a day where the pattern looks different, or doesn't hold).

For each day, capture enough raw detail that someone with no memory of the conversation could independently recompute the qualification decision from what's written here — that's the same bar Weekly Future was held to before its formula was accepted (`WEEKLY_FUTURE_BLOCKER_REPORT.md` §5).

---

## General Rule Statement (Product Owner, supplied in chat, 2026-07-31)

**Status of this section: a conceptual rule statement, not yet a dated Worked Example.** Recorded verbatim per `EVIDENCE_INTAKE_PROCESS.md`'s "quoted verbatim, nothing paraphrased away" rule. This does **not** by itself satisfy the "minimum three worked examples" acceptance bar (`evidence_acceptance_checklist.md`) — no specific date/trade/outcome was walked through, only the general shape of the rule. Worked Examples 1-5 below are still needed with real dated instances before this can move to Implement.

**Verbatim statement:**

> After 9.20AM candle you have to find the top and bottom strike. Then finalize which strike you want to proceed either top or bottom, if possible keep both.
>
> Top Instructions: Mark the top premium price (First 5 minute). CE - Mark PE Low (PE TOP Low price and 6ITM and OTM First 5 minute value) - These levels act as Entry, Target, SL, Support, Resistance. PE - Mark CE High (CE TOP High price and 6ITM and OTM First 5 minute value) - These levels act as Entry, Target, SL, Support, Resistance.
>
> Bottom Instructions: Mark the Bottom premium price (First 5 minute). CE - Mark PE High (PE Bottom High price and 6ITM and OTM First 5 minute value) - These levels act as Entry, Target, SL, Support, Resistance. PE - Mark CE Low (CE Bottom Low price and 6ITM and OTM First 5 minute value) - These levels act as Entry, Target, SL, Support, Resistance.
>
> Then find who is going to win - Based on the market trend.
>
> Now the game starts. If you found the confident trade then its entry point act as a support choose the first resistance as R1 target - this will go upward direction. Meanwhile watch the competitor movement who will going to touch the line first - must go to downward and looks for the next support. When anyone touches the line the trade should exit immediately - means its profit trade.
>
> STL - should be same as previously told (Need 3 points to cover the exchange fee and taxes).

**Cross-check against existing confirmed evidence (per `EVIDENCE_INTAKE_PROCESS.md` Section 4):**

| Statement | Cross-check result |
|---|---|
| "Choose the first resistance as R1 target" (adjacent strike, direction of trade) | **CONFIRMS EXISTING** — matches Specification Rule 2 (v1.1, CONFIRMED), already implemented in `src/position_manager/position_manager.py` |
| "Watch the competitor... exit immediately when touched" | **CONFIRMS EXISTING** — matches Rule 2's Competitor Exit mapping, already implemented in `src/exit_engine/exit_engine.py` |
| "STL... 3 points to cover exchange fee and taxes" | **CONFIRMS EXISTING** — matches the already-confirmed Trailing Stop minimum net quoted in `STRATEGY_FUNCTIONAL_SPECIFICATION.md:246` |
| "CE - Mark PE Low (Top)"; "PE - Mark CE High (Top)"; "CE - Mark PE High (Bottom)"; "PE - Mark CE Low (Bottom)" | **NEW — directly answers QUAL-007.** Word-for-word structural match to `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7's TP High/TP Low sustain test (`CE > competitor PE Low`, `PE < competitor CE High`). Identifies the competitor as the **same strike's own opposite side** (Top or Bottom strike, opposite CE/PE), not the adjacent-strike Rule 2 mapping — the two concepts are now confirmed distinct, exactly as `BUSINESS_ARCHITECTURE.md` had warned they must not be conflated. |

**Real reference ladder pulled for context** (NIFTY, 2026-07-30, Top Strike 24250, Bottom Strike 24200, first 5-minute CE/PE High/Low, all 13 strikes = the "6 ITM and OTM" the statement describes — fetched live via the Upstox backtest harness, `src/backtest/`):

| Strike | CE High | CE Low | PE High | PE Low |
|---|---|---|---|---|
| 23950 | 332.95 | 276.10 | 46.80 | 32.65 |
| 24000 | 291.50 | 236.60 | 63.00 | 41.10 |
| 24050 | 252.00 | 201.85 | 72.90 | 51.50 |
| 24100 | 215.60 | 167.60 | 91.00 | 64.30 |
| 24150 | 181.40 | 137.55 | 108.20 | 80.00 |
| 24200 (Bottom) | 150.00 | 110.30 | 131.60 | 98.30 |
| 24250 (Top) | 121.50 | 87.00 | 159.00 | 120.10 |
| 24300 | 103.20 | 67.05 | 189.00 | 145.20 |
| 24350 | 74.75 | 50.50 | 222.35 | 173.55 |
| 24400 | 56.40 | 37.30 | 259.40 | 205.10 |
| 24450 | 45.55 | 27.00 | 297.95 | 240.50 |
| 24500 | 30.10 | 19.45 | 340.60 | 279.20 |
| 24550 | 23.85 | 13.90 | 383.45 | 318.40 |

Applying the rule to this table: a CE trade at Top (24250) would compare against **Top's own PE Low = 120.10**; a PE trade at Top against **Top's own CE High = 121.50**; a CE trade at Bottom (24200) against **Bottom's own PE High = 131.60**; a PE trade at Bottom against **Bottom's own CE Low = 110.30**. This is the confirmed 13-level ladder `ReferenceBuilder` already builds — no new data-capture logic needed if this rule is accepted, only a new comparison.

**Open questions this statement does not yet resolve** (do not guess at these — ask the Product Owner directly):

1. **Entry trigger order** — is the TP High/Low sustain test (this statement) a *gate* that must pass before a Winner (already-implemented `WinnerEngine`) becomes a real entry, or does Winner Detection alone still trigger entry with Qualification only describing the state afterward? "If you found the confident trade then its entry point act as a support" suggests Qualification comes first, but this isn't stated unambiguously enough to implement.
2. **"These levels act as Entry, Target, SL, Support, Resistance"** — five roles for the same captured level. What determines which role a given level plays in a given moment?
3. **No dated worked example yet** — a specific day, a specific strike, the actual PE Low/CE High values, and the actual qualify/don't-qualify outcome, so this can be independently recomputed the way Weekly Future was.

---

## Worked Example 1

**Date:** _______________
**Strike(s) involved:** _______________

1. **Why was this trade qualified?**
   (What did the Product Owner actually look at? Quote/paraphrase their exact reasoning, don't summarize it into a rule yet.)

2. **Which competitor was compared?**
   (The specific strike/level — e.g. "the strike one below," "the Weekly Future level," "PE Low of strike X" — named as concretely as possible.)

3. **Why this competitor?**
   (What made that particular strike/level the right one to compare against, on this specific day?)

4. **Would another competitor have changed the result?**
   (Ask the Product Owner to consider at least one alternative candidate — e.g. the Exit-stage Rule 2 mapping, `PE(S-1)`/`CE(S+1)` — and say concretely whether qualification would have come out differently using it.)

**Raw supporting data** (CE/PE High/Low values, timestamps, reference levels — attach a screenshot or paste the numbers):

**Counter Example for this day, if any** (a moment the same day where the pattern did *not* hold, or UNKNOWN):

---

## Worked Example 2

**Date:** _______________
**Strike(s) involved:** _______________

1. **Why was this trade qualified?**

2. **Which competitor was compared?**

3. **Why this competitor?**

4. **Would another competitor have changed the result?**

**Raw supporting data:**

**Counter Example for this day, if any:**

---

## Worked Example 3

**Date:** _______________
**Strike(s) involved:** _______________

1. **Why was this trade qualified?**

2. **Which competitor was compared?**

3. **Why this competitor?**

4. **Would another competitor have changed the result?**

**Raw supporting data:**

**Counter Example for this day, if any:**

---

## Worked Example 4 (optional — strongly recommended for a Counter Example)

**Date:** _______________
**Strike(s) involved:** _______________

1. **Why was this trade qualified?**

2. **Which competitor was compared?**

3. **Why this competitor?**

4. **Would another competitor have changed the result?**

**Raw supporting data:**

**Counter Example for this day, if any:**

---

## Worked Example 5 (optional)

**Date:** _______________
**Strike(s) involved:** _______________

1. **Why was this trade qualified?**

2. **Which competitor was compared?**

3. **Why this competitor?**

4. **Would another competitor have changed the result?**

**Raw supporting data:**

**Counter Example for this day, if any:**

---

## Cross-cutting questions (answer once, after all examples above are filled in)

- **Does the competitor change during replay** (i.e., within a single session, does which strike/level counts as "the competitor" ever shift), or is it fixed for the day? _______________
- **Is there more than one competitor** — do TP High and TP Low use the same competitor, or different ones? _______________
- **How is the competitor selected**, in the Product Owner's own words, as a general rule (not tied to one day)? _______________
- **Is the competitor any of**: Weekly Future / Top Strike / Bottom Strike / Reference Level / Premium / ORB / the Exit-stage Rule 2 mapping (`PE(S-1)`/`CE(S+1)`) / something else entirely? **Per the General Rule Statement above: the same strike's own opposite side** — Top's PE Low (for CE)/CE High (for PE), Bottom's PE High (for CE)/CE Low (for PE). Distinct from the Exit-stage Rule 2 mapping. Still needs a dated Worked Example to move from "stated" to "Confirmed."

## Expected Result

(Once the above is filled in, state in one paragraph what a correct `QualificationEngine` implementation should now be able to do, independent of any single worked example above — this becomes the regression-test target per `evidence_traceability_standard.md`.)

## Confidence

(Product Owner's own honest rating for the full session: High / Medium / Low — how sure are they this captures a real, consistent rule rather than day-specific judgment calls.)

---

## After this session

1. This filled-in file gets a **Rule ID** assigned (reuse `QUAL-007` — it already exists in `docs/RULE_INDEX.md`) and stays in `research/incoming/` under its current filename.
2. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification).
3. Score the result against `research/specifications/evidence_acceptance_checklist.md`.
4. Log the outcome as a new row in `research/evidence_log.md` (Evidence Complete → Implement / Evidence Partial → Research / Evidence Missing → Freeze, per `research/specifications/product_owner_evidence_process.md`'s Decision Matrix).
5. Only on an **Implement** outcome does Sprint 10 (Qualification Engine) become eligible to start.

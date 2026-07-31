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

1. ~~**Entry trigger order**~~ — **substantially answered by the Entry Trigger Rule section below** (2026-07-31, second message): the crossover condition *is* the entry trigger itself, checked continuously from 9:20 onward. Still open: exact relationship to the already-implemented `WinnerEngine` touch logic (see cross-check below).
2. **"These levels act as Entry, Target, SL, Support, Resistance"** — five roles for the same captured level. The Entry Trigger Rule + 22 July Worked Example below clarify Entry and Target; SL/Support/Resistance roles still unclarified.
3. ~~**No dated worked example yet**~~ — **now supplied**, see Worked Example 1 below (22 July, PE Buy). Still need 2 more independent dated examples per `evidence_acceptance_checklist.md`.

---

## Entry Trigger Rule (Product Owner, supplied in chat, 2026-07-31, second message)

**Status: a real, executable entry condition — the strongest evidence recorded in this document so far.** Recorded verbatim (Tamil original), with an English paraphrase for clarity (paraphrase is NOT the evidence of record — the Tamil original is).

**Verbatim (Tamil):**

> Entry Rule: உங்கள் excel-ல இருந்து. PE Buy Condition: PE Premium crosses 24050 CE High AND CE Premium crosses 24050 PE Low. இரண்டும் ஒரே நேரத்தில். இதுதான் மிகவும் powerful condition. இதுதான் false breakout filter.
>
> CE Buy Condition: CE crosses 24000 PE Low AND PE crosses 24000 CE High. இரண்டும் confirmation.
>
> Workflow: 9:20 → Fetch ATM → Generate 4 ITM, 4 OTM → Get CE High → Get CE Low → Get PE High → Get PE Low → Draw Lines → Wait → Premium Cross → Competitor Cross → BUY → Trail → Exit.

**English paraphrase (not the evidence of record):** At 9:20, fetch the ATM strike, generate a 9-strike ladder (ATM ± 4 ITM/OTM), capture each strike's first-5-minute CE/PE High/Low, draw those as lines. From then on, watch for a **simultaneous dual crossover**: for a PE Buy at a given strike, its own PE premium must cross that strike's CE High *at the same time* its own CE premium crosses that strike's PE Low. Source: "from your Excel" — i.e. the Product Owner's own trade log, not a fresh invention. Described explicitly as "the most powerful condition" and "a false breakout filter" — the dual, same-instant requirement is the point, not incidental.

**Cross-check against existing confirmed evidence:**

| Statement | Cross-check result |
|---|---|
| Same-strike CE+PE dual touch, same candle, as the entry trigger | **Structurally similar to already-implemented `WinnerEngine`** (Rule 3, CONFIRMED: "If CE touches any of its reference levels AND PE touches any of its reference levels during the SAME candle... Winner immediately generates Entry Signal"). **Not yet confirmed identical** — `WinnerEngine` checks touch against *any* of a strike's own CE/PE High/Low band; this statement specifies a more precise cross pattern (PE crosses CE High specifically, CE crosses PE Low specifically) and ties it explicitly to "false breakout filter" framing that `WinnerEngine`'s existing docstring does not mention. **Open question, do not assume equivalence without asking:** is this the same event as Winner Detection under a different name, or a stricter refinement of it? |
| ATM ± 4 ITM/OTM = 9 strikes | **Possible structural difference from the earlier General Rule Statement** (Top/Bottom, "6 ITM and OTM" = 13 strikes total across two anchors). **Open question, do not guess:** is ATM here the same concept as Top/Bottom Strike, or a third, distinct anchor point? Ask the Product Owner directly before assuming either way. |

---

## Worked Example 1

**Date:** 22 July (year not stated in the message — context suggests 2026, given NIFTY spot ≈24140 is consistent with the 2026-07-30 session already fetched via Upstox; **please confirm the exact year/date before this is treated as fully specified**).
**Strike(s) involved:** Entry strike 24150 PE. Competitor strike 24150 CE (same strike, opposite side).

1. **Why was this trade qualified?**
   Per the Entry Trigger Rule above: PE premium crossed the competitor's (24150 CE) High/Low band at the same instant CE premium crossed the same strike's PE Low/High band — the "dual crossover, false breakout filter" condition. Exact crossed values (which specific High vs Low triggered) were not itemized separately from the Entry price below — **UNKNOWN at this level of detail; would need to ask the Product Owner to point to the exact two numbers crossed at 206.35.**

2. **Which competitor was compared?**
   24150 CE (same strike, opposite side) — consistent with both the General Rule Statement above (Top/Bottom same-strike-opposite-side) and the Entry Trigger Rule (same-strike CE/PE dual cross).

3. **Why this competitor?**
   Not stated separately from the general rule above (same strike's opposite side, by the stated rule itself) — **UNKNOWN whether there was day-specific reasoning beyond applying the general rule.**

4. **Would another competitor have changed the result?**
   **UNKNOWN — not asked/answered yet.** Worth asking directly: would the adjacent-strike Rule 2 mapping (`PE(S-1)`/`CE(S+1)` = 24100 CE for this PE trade) have produced a different qualification outcome on this same candle?

**Raw supporting data:**

- Entry: **206.35**
- Target 1: **238.75**
- Target 2: **269.95**
- Pattern stated: "Entry line → Next CE High → Next CE High → Next CE High" — i.e. the ladder target sequence walks up through successive CE High values on the (competitor-side) ladder, one rung per target, not a single fixed Target.
- NIFTY Spot at the time: 24140 (from the introductory example in the same message — not explicitly re-stated for this exact 22 July trade, **please confirm this spot value belongs to this specific trade**).

**Cross-check against already-implemented Target logic:** this "ladder of successive Next CE Highs" is **structurally different from Rule 2's single fixed Target** (`CE(S+1)`/`PE(S-1)`, already implemented in `PositionManager`/`ExitEngine`, currently used unmodified by `src/backtest/`). Rule 2 gives one target; this describes multiple sequential targets as price moves favorably. **Open question, do not assume equivalence:** is this ladder a description of Trailing Stop behavior (moving the exit point as each successive level is passed) applied to the target side, or a genuinely different, additional targeting rule Rule 2 doesn't capture? Needs to be asked directly rather than guessed.

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

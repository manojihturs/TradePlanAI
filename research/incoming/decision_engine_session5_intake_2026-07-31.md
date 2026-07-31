# Session 5 — Decision Engine Evidence Intake (Product Owner)

**Status:** Blank intake document — to be filled in by/with the Product Owner. Nothing in this file is evidence yet; it becomes evidence only once the fields below are answered. Once filled in, this file moves through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification) and is scored against `research/specifications/evidence_acceptance_checklist.md`.

**Targets:** No "Decision Engine" gap exists yet in `research/specifications/business_engine_portfolio.md` — this is a new synthesis concept (per Sprint 13 in the backlog), not a re-audit of an existing frozen engine. Its job is to combine Weekly Future, Strike Selection, ORB, Qualification, Stop Loss, and Trailing Stop into a single BUY / SELL / NO TRADE decision with a stated reason. Three of its six named inputs (Qualification, Stop Loss, Trailing Stop) are themselves still frozen (see Sessions 1, 3, 4) — this session is **not** blocked on those being resolved first, though. Its job is different and answerable independently: to establish whether a Decision Engine is even a distinct synthesis step at all, or whether "decision" is just whatever `WinnerEngine`/`EntryEngine` already do mechanically once their own inputs are available. That question can be investigated now, using only the already-resolved engines (Weekly Future, Strike, ORB) as concrete worked material, with the frozen engines' contribution marked `UNKNOWN`/hypothetical where relevant.

**Do not fill in a field with a guess.** If the Product Owner doesn't know or isn't sure, write `UNKNOWN` — an honest "I don't know" is usable input to the intake process; a guessed value is not (it will be classified as an Assumption, not a Confirmed Rule, per `EVIDENCE_INTAKE_PROCESS.md` Section 2).

---

## Instructions for the session

Open **one historical trading day at a time**, and for each, walk through the questions below while looking at the actual chart/data together with the Product Owner. Repeat for **3–5 separate days** — this project's own acceptance bar (`evidence_acceptance_checklist.md`, "minimum three worked examples") requires at least three.

Include at least one day that ended **NO TRADE** — a day where a Winner was never even reached, or one that reached a Winner but the Product Owner still chose not to trade it. That contrast — what makes a day tradeable vs. not — is itself the core of what this engine needs to capture, and it's the one thing `WinnerEngine`/`EntryEngine`'s existing mechanical logic doesn't currently express: they are strike-agnostic and take single-active-trade as given, but neither states a NO TRADE *decision* rule of its own beyond "no Winner occurred."

For each day, capture enough raw detail — the actual values each named input produced — that someone with no memory of the conversation could independently reconstruct why the decision came out the way it did.

---

## Worked Example 1

**Date:** _______________
**Final decision:** BUY / SELL / NO TRADE _______________

For this day, record what each of the six named inputs actually was (mark `UNKNOWN`/hypothetical for Qualification, Stop Loss, or Trailing Stop if their evidence isn't resolved yet):

- **Weekly Future** (High/Low, Top/Bottom Strike): _______________
- **Strike Selection** (which strike was selected, and why): _______________
- **ORB** (opening range high/low, and whether/how it factored in): _______________
- **Qualification** (was the strike qualified? by what test, if known — or `UNKNOWN`): _______________
- **Stop Loss** (what would the stop have been, if known — or `UNKNOWN`): _______________
- **Trailing Stop** (would trailing have applied, if known — or `UNKNOWN`): _______________

1. **Given all of the above, why was this the final decision?**
   (Not "because a Winner occurred" — what did the Product Owner actually weigh, in their own words, to arrive at BUY/SELL/NO TRADE specifically?)

2. **Did any input conflict with another?**
   (E.g. Winner Detection said one side won, but something about Qualification, ORB, or another input argued against taking it — what happened in that case?)

3. **If this was NO TRADE, what specifically stopped it?**
   (No Winner ever occurred? A Winner occurred but was overridden? Something else?)

4. **Would a different outcome on any single input have flipped the decision?**
   (E.g. "if ORB hadn't confirmed, would this still have been a BUY?" — walk through at least one what-if with the Product Owner.)

**Raw supporting data** (attach a screenshot or paste the numbers for each input above):

---

## Worked Example 2

**Date:** _______________
**Final decision:** BUY / SELL / NO TRADE _______________

- **Weekly Future:** _______________
- **Strike Selection:** _______________
- **ORB:** _______________
- **Qualification:** _______________
- **Stop Loss:** _______________
- **Trailing Stop:** _______________

1. **Given all of the above, why was this the final decision?**

2. **Did any input conflict with another?**

3. **If this was NO TRADE, what specifically stopped it?**

4. **Would a different outcome on any single input have flipped the decision?**

**Raw supporting data:**

---

## Worked Example 3

**Date:** _______________
**Final decision:** BUY / SELL / NO TRADE _______________

- **Weekly Future:** _______________
- **Strike Selection:** _______________
- **ORB:** _______________
- **Qualification:** _______________
- **Stop Loss:** _______________
- **Trailing Stop:** _______________

1. **Given all of the above, why was this the final decision?**

2. **Did any input conflict with another?**

3. **If this was NO TRADE, what specifically stopped it?**

4. **Would a different outcome on any single input have flipped the decision?**

**Raw supporting data:**

---

## Worked Example 4 (recommended: a NO TRADE day)

**Date:** _______________
**Final decision:** NO TRADE _______________

- **Weekly Future:** _______________
- **Strike Selection:** _______________
- **ORB:** _______________
- **Qualification:** _______________
- **Stop Loss:** _______________
- **Trailing Stop:** _______________

1. **Given all of the above, why was this the final decision?**

2. **Did any input conflict with another?**

3. **If this was NO TRADE, what specifically stopped it?**

4. **Would a different outcome on any single input have flipped the decision?**

**Raw supporting data:**

---

## Worked Example 5 (optional)

**Date:** _______________
**Final decision:** BUY / SELL / NO TRADE _______________

- **Weekly Future:** _______________
- **Strike Selection:** _______________
- **ORB:** _______________
- **Qualification:** _______________
- **Stop Loss:** _______________
- **Trailing Stop:** _______________

1. **Given all of the above, why was this the final decision?**

2. **Did any input conflict with another?**

3. **If this was NO TRADE, what specifically stopped it?**

4. **Would a different outcome on any single input have flipped the decision?**

**Raw supporting data:**

---

## Cross-cutting questions (answer once, after all examples above are filled in)

- **Is there a "Decision Engine" at all as a distinct step**, or is the decision just whatever `WinnerEngine` + `EntryEngine` already produce mechanically once every input is available — i.e., does the Product Owner do anything *beyond* what those two already-implemented engines do? _______________
- **Is there a fixed priority order among the six inputs** when they disagree, or is it case-by-case judgment? _______________
- **Can a Winner occur (per `WinnerEngine`'s existing CE+PE-same-candle-touch logic) and still result in NO TRADE?** If yes, under what condition — this would be new information `EntryEngine`'s current implementation doesn't account for (it currently accepts every Winner subject only to the single-active-trade rule). _______________
- **Is "Decision Reason" and "Decision Trace" (from the Sprint 13 backlog spec) something the Product Owner already tracks in some form** (a trading journal, notes, a checklist), or would it need to be defined from scratch based on this session? _______________

## Expected Result

(Once the above is filled in, state in one paragraph what a correct `DecisionEngine` implementation should now be able to do, independent of any single worked example above — this becomes the regression-test target per `evidence_traceability_standard.md`. If the answer to the first cross-cutting question above is "no distinct engine exists," state that explicitly here instead — that is itself a valid, actionable outcome.)

## Confidence

(Product Owner's own honest rating for the full session: High / Medium / Low — how sure are they this captures a real, consistent rule rather than day-specific judgment calls.)

---

## After this session

1. This filled-in file gets a **new Rule ID** assigned from `docs/RULE_INDEX.md`'s existing numbering convention (no Decision Engine ID exists yet — this session's outcome determines whether one is needed at all, per the first cross-cutting question above).
2. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification).
3. Score the result against `research/specifications/evidence_acceptance_checklist.md` — note that full "Evidence Complete" here is inherently capped by whatever state Sessions 1/3/4 (Qualification, Stop Loss, Trailing Stop) are in, since three of this engine's six named inputs come from those sessions. A "Decision Engine synthesis logic is confirmed" outcome does not by itself unfreeze those three engines.
4. Log the outcome as a new row in `research/evidence_log.md` (Evidence Complete → Implement / Evidence Partial → Research / Evidence Missing → Freeze, per `research/specifications/product_owner_evidence_process.md`'s Decision Matrix).
5. Only on an **Implement** outcome — for both this session's synthesis logic **and** its three still-frozen input engines — does Sprint 13 (Decision Engine) become eligible to start.

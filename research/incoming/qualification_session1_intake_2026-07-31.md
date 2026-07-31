# Session 1 — Qualification Evidence Intake (Product Owner)

**Status:** Blank intake document — to be filled in by/with the Product Owner. Nothing in this file is evidence yet; it becomes evidence only once the fields below are answered. Once filled in, this file moves through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification) and is scored against `research/specifications/evidence_acceptance_checklist.md`.

**Targets:** This session exists to close **QUAL-007** (the TP-stage competitor identity) — the single blocker keeping `QualificationEngine` frozen. See `research/specifications/qualification_remaining_unknowns.md` for exactly what's missing and why: no source anywhere in this repository names, defines, or gives a worked example of the competitor used in the TP High / TP Low sustain tests. This session is the artifact that document said would be required.

**Do not fill in a field with a guess.** If the Product Owner doesn't know or isn't sure, write `UNKNOWN` — an honest "I don't know" is usable input to the intake process; a guessed value is not (it will be classified as an Assumption, not a Confirmed Rule, per `EVIDENCE_INTAKE_PROCESS.md` Section 2).

---

## Instructions for the session

Open **one historical trading day at a time**, and for each, walk through the four questions below while looking at the actual chart/data together with the Product Owner. Repeat for 3–5 separate days — this project's own acceptance bar (`evidence_acceptance_checklist.md`, "minimum three worked examples") requires at least three, and a fourth/fifth is valuable specifically for surfacing a **Counter Example** (a day where the pattern looks different, or doesn't hold).

For each day, capture enough raw detail that someone with no memory of the conversation could independently recompute the qualification decision from what's written here — that's the same bar Weekly Future was held to before its formula was accepted (`WEEKLY_FUTURE_BLOCKER_REPORT.md` §5).

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
- **Is the competitor any of**: Weekly Future / Top Strike / Bottom Strike / Reference Level / Premium / ORB / the Exit-stage Rule 2 mapping (`PE(S-1)`/`CE(S+1)`) / something else entirely? _______________

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

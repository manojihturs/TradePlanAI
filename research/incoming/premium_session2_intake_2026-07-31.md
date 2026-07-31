# Session 2 — Premium Evidence Intake (Product Owner)

**Status:** Blank intake document — to be filled in by/with the Product Owner. Nothing in this file is evidence yet; it becomes evidence only once the fields below are answered. Once filled in, this file moves through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification) and is scored against `research/specifications/evidence_acceptance_checklist.md`.

**Targets:** This session exists to close **REVERSAL-001** and, more broadly, to establish whether a primary-side "Premium Calculator" concept exists at all. See `research/specifications/business_engine_portfolio.md` §1 (Premium Calculator): only 2 evidence points exist today (Draft/Medium confidence), no primary-reconstruction Premium engine is evidenced as a discrete concept, and the docstring on `trading_engine/domain/premium.py` states outright: "No rule defines Premium as a first-class concept yet." This session is the artifact that gap requires.

**Do not fill in a field with a guess.** If the Product Owner doesn't know or isn't sure, write `UNKNOWN` — an honest "I don't know" is usable input to the intake process; a guessed value is not (it will be classified as an Assumption, not a Confirmed Rule, per `EVIDENCE_INTAKE_PROCESS.md` Section 2).

---

## Instructions for the session

Open **one historical trade at a time**, and for each, walk through the four questions below while looking at the actual chart/data together with the Product Owner. Repeat for **5 separate trades** — this project's own acceptance bar (`evidence_acceptance_checklist.md`, "minimum three worked examples") requires at least three, and five gives enough spread to distinguish a real, consistent rule from a day-specific judgment call, and to surface a genuine Counter Example.

For each trade, capture enough raw detail that someone with no memory of the conversation could independently recompute "premium expansion" from what's written here — that's the same bar Weekly Future was held to before its formula was accepted (`WEEKLY_FUTURE_BLOCKER_REPORT.md` §5).

---

## Worked Example 1

**Date:** _______________
**Strike / side (CE or PE):** _______________

1. **What premium values were used?**
   (The actual CE/PE premium numbers at the relevant moments — entry, any decision point, exit. Concrete rupee figures, not "it went up.")

2. **What does "premium expansion" mean here?**
   (In the Product Owner's own words, for this specific trade — what were they looking at that they'd call "expansion"?)

3. **Is it absolute change, percentage, or something else?**
   (E.g. "premium moved from 42 to 58" = absolute +16, or "+38%" = percentage, or some other basis entirely — pin down which one the Product Owner was actually using in the moment.)

4. **What threshold makes it meaningful?**
   (At what point did the expansion become significant enough to act on — a specific number, a specific percentage, or a qualitative judgment the Product Owner made in the moment?)

**Raw supporting data** (premium values at each relevant timestamp, attach a screenshot or paste the numbers):

**Counter Example for this trade, if any** (a moment where premium moved but it did *not* count as "expansion," or UNKNOWN):

---

## Worked Example 2

**Date:** _______________
**Strike / side (CE or PE):** _______________

1. **What premium values were used?**

2. **What does "premium expansion" mean here?**

3. **Is it absolute change, percentage, or something else?**

4. **What threshold makes it meaningful?**

**Raw supporting data:**

**Counter Example for this trade, if any:**

---

## Worked Example 3

**Date:** _______________
**Strike / side (CE or PE):** _______________

1. **What premium values were used?**

2. **What does "premium expansion" mean here?**

3. **Is it absolute change, percentage, or something else?**

4. **What threshold makes it meaningful?**

**Raw supporting data:**

**Counter Example for this trade, if any:**

---

## Worked Example 4

**Date:** _______________
**Strike / side (CE or PE):** _______________

1. **What premium values were used?**

2. **What does "premium expansion" mean here?**

3. **Is it absolute change, percentage, or something else?**

4. **What threshold makes it meaningful?**

**Raw supporting data:**

**Counter Example for this trade, if any:**

---

## Worked Example 5

**Date:** _______________
**Strike / side (CE or PE):** _______________

1. **What premium values were used?**

2. **What does "premium expansion" mean here?**

3. **Is it absolute change, percentage, or something else?**

4. **What threshold makes it meaningful?**

**Raw supporting data:**

**Counter Example for this trade, if any:**

---

## Cross-cutting questions (answer once, after all examples above are filled in)

- **Is "premium contraction" also a concept** (the inverse of expansion), and if so, does it use the same basis (absolute/percentage/other) and threshold, or a different one? _______________
- **Is expansion measured against the option's own prior value, or against something else** (e.g. its competitor's premium, a reference level, the underlying's own move)? _______________
- **Does the relevant threshold change by strike, by time of day, or by market condition, or is it fixed?** _______________
- **Is "Premium" here the same concept as the legacy system's Premium Mapping** (`strategy/premium_mapping.py` — CE/PE High/Low cross-referenced into four ladders), a related-but-distinct concept, or something entirely separate? _______________
- **Is this concept connected to a "Reversal"** (`trading_engine/domain/premium.py`'s own unresolved question, REVERSAL-001) — does premium expansion/contraction ever signal a reversal, and if so how? _______________

## Expected Result

(Once the above is filled in, state in one paragraph what a correct Premium Calculator implementation should now be able to do, independent of any single worked example above — this becomes the regression-test target per `evidence_traceability_standard.md`.)

## Confidence

(Product Owner's own honest rating for the full session: High / Medium / Low — how sure are they this captures a real, consistent rule rather than trade-specific judgment calls.)

---

## After this session

1. This filled-in file gets a **Rule ID** assigned (reuse `REVERSAL-001` if the content turns out to be about reversal detection specifically, or a newly assigned ID from `docs/RULE_INDEX.md`'s numbering convention if it's a distinct "Premium Expansion/Contraction" concept — do not force it into REVERSAL-001 if the evidence doesn't actually connect the two).
2. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification).
3. Score the result against `research/specifications/evidence_acceptance_checklist.md`.
4. Log the outcome as a new row in `research/evidence_log.md` (Evidence Complete → Implement / Evidence Partial → Research / Evidence Missing → Freeze, per `research/specifications/product_owner_evidence_process.md`'s Decision Matrix).
5. Only on an **Implement** outcome does a Premium Calculator sprint become eligible to start.

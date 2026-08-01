# Session 3 — Stop Loss Evidence Intake (Product Owner)

**Status:** Blank intake document — to be filled in by/with the Product Owner. Nothing in this file is evidence yet; it becomes evidence only once the fields below are answered. Once filled in, this file moves through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification) and is scored against `research/specifications/evidence_acceptance_checklist.md`.

**Targets:** This session exists to resolve the Stop Loss gap identified in `research/specifications/business_engine_portfolio.md` §7. Today, `src/interfaces/stop_loss_engine.py` is a stub whose own docstring states: "no SL price, basis, or placement rule stated anywhere," citing Specification Section 20 item 4 as **Critical**. `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md:228` confirms: "Still not stated at all: SL price, SL basis (premium points? percentage? underlying-level?), or SL placement rule." This session is the artifact that gap requires. It also directly unblocks `ExitEngine`'s third exit condition, which today calls this stub on every evaluation.

**Do not fill in a field with a guess.** If the Product Owner doesn't know or isn't sure, write `UNKNOWN` — an honest "I don't know" is usable input to the intake process; a guessed value is not (it will be classified as an Assumption, not a Confirmed Rule, per `EVIDENCE_INTAKE_PROCESS.md` Section 2).

**Partial evidence already landed (2026-08-01), cross-referenced here, not duplicated:** `research/incoming/qualification_session1_intake_2026-07-31.md`'s "Entry/Target/SL/TSL Clarification" section records the Product Owner's first-ever SL statement: **SL = S-1, the marked level one rung below entry** (S = the entry's own marked level on the 13-level ladder).

**Analysis (2026-08-01), using only already-confirmed code, no new evidence requested for this step:** `src/position_manager/position_manager.py`'s already-confirmed Rule 2 implementation distinguishes Support from Competitor Exit **by side, not just strike position** — for a CE trade at strike S: `Target = CE(S+1)`, `Support = CE(S-1)` (same side as the trade), `Competitor Exit = PE(S-1)` (opposite side, same strike-position). Both Support and Competitor Exit sit at "the S-1 rung," but are two different premiums (own contract vs. opposite contract).

An SL is naturally expressed on the trader's *own* position's premium — exactly what Support already is. **The most consistent reading: SL = Support = `CE(S-1)`/`PE(S+1)`, the same-side level — not the opposite-side Competitor Exit level.** Under this reading, SL isn't a new, third concept; it's the already-confirmed Support level under a name the earlier evidence hadn't yet connected to it. Competitor Exit remains genuinely distinct (opposite side).

**This is a strong inference from consistent naming, not something the Product Owner has confirmed outright.** Treat "SL = Support" as a hypothesis to explicitly confirm, not a settled fact, until the Product Owner says so directly or a worked example demonstrates it (e.g. a trade where the SL price and the already-known Support price are shown to be numerically identical).

**Product Owner confirmation (2026-08-01):** answered `CE(S-1)` — **confirms SL = Support for the CE side**, exactly matching the hypothesis above (`Support = CE(S-1)` for a CE trade, per Rule 2). This is now a **Confirmed Rule for the CE side**, not merely an inference.

**Not yet confirmed:** the PE-side equivalent. By the same symmetric logic Rule 2 already uses elsewhere (`Support = PE(S+1)` for a PE trade), SL for a PE trade would be expected to equal `PE(S+1)` — but the Product Owner was only asked about, and only answered, the CE case. **Do not assume the PE side without asking directly** — this symmetric extension is a reasonable guess, not confirmed evidence, and should be verified the same way the CE side just was.

---

## Instructions for the session

Open **one historical trade at a time**, and for each, walk through the four questions below while looking at the actual chart/data together with the Product Owner. Repeat for **5 separate trades** — this project's own acceptance bar (`evidence_acceptance_checklist.md`, "minimum three worked examples") requires at least three, and five gives enough spread to distinguish a real, consistent rule from a trade-specific judgment call, and to surface a genuine Counter Example (a trade where the stop was placed differently, or wasn't moved when you might expect).

Include at least one trade where the stop **did** move and one where it explicitly **did not** — the difference between those two is itself part of the rule.

For each trade, capture enough raw detail that someone with no memory of the conversation could independently recompute the stop-loss placement from what's written here — that's the same bar Weekly Future was held to before its formula was accepted (`WEEKLY_FUTURE_BLOCKER_REPORT.md` §5).

---

## Worked Example 1

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium / entry reference level:** _______________

1. **Where was the stop placed?**
   (The actual price/level — concrete number, not "just below entry.")

2. **Based on premium, price, ORB, or another reference?**
   (Which of these — or something else entirely — was the basis? Was it a fixed number of premium points, a percentage, the underlying's own price level, an ORB level, the Exit-stage competitor level, or something not on this list?)

3. **When did it move?**
   (The specific moment/condition that caused the stop to be adjusted, if it was adjusted at all during this trade.)

4. **When did it not move?**
   (A moment during this same trade where the price/premium moved but the stop stayed exactly where it was — and why, in the Product Owner's own words.)

**Raw supporting data** (entry price, initial stop price, any stop adjustments with timestamps, exit price — attach a screenshot or paste the numbers):

**Counter Example for this trade, if any** (a moment where the same conditions held but the stop behaved differently, or UNKNOWN):

---

## Worked Example 2

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium / entry reference level:** _______________

1. **Where was the stop placed?**

2. **Based on premium, price, ORB, or another reference?**

3. **When did it move?**

4. **When did it not move?**

**Raw supporting data:**

**Counter Example for this trade, if any:**

---

## Worked Example 3

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium / entry reference level:** _______________

1. **Where was the stop placed?**

2. **Based on premium, price, ORB, or another reference?**

3. **When did it move?**

4. **When did it not move?**

**Raw supporting data:**

**Counter Example for this trade, if any:**

---

## Worked Example 4

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium / entry reference level:** _______________

1. **Where was the stop placed?**

2. **Based on premium, price, ORB, or another reference?**

3. **When did it move?**

4. **When did it not move?**

**Raw supporting data:**

**Counter Example for this trade, if any:**

---

## Worked Example 5

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium / entry reference level:** _______________

1. **Where was the stop placed?**

2. **Based on premium, price, ORB, or another reference?**

3. **When did it move?**

4. **When did it not move?**

**Raw supporting data:**

**Counter Example for this trade, if any:**

---

## Cross-cutting questions (answer once, after all examples above are filled in)

- **Is the stop-loss placement basis fixed, or does it vary by strike, side (CE/PE), or market condition?** _______________
- **Is there a single stated formula for the initial stop, or was it judgment-based each time** (in which case, what factors went into that judgment, consistently across trades)? _______________
- **Does Stop Loss ever interact with the already-confirmed Exit-stage competitor mapping** (Rule 2: `PE(S-1)`/`CE(S+1)`) — e.g. is the stop ever placed at or derived from the competitor level, or are they fully independent concepts? _______________
- **Is there a maximum stop distance or minimum stop distance** (a floor/ceiling on how far the stop can be from entry), or is it unbounded? _______________
- **Does Stop Loss ever get overridden by Trailing Stop, or are they evaluated independently** (relevant to `ExitEngine`'s existing but unresolved exit-condition precedence question, Specification Section 20 item 11)? _______________

## Expected Result

(Once the above is filled in, state in one paragraph what a correct `StopLossEngine` implementation should now be able to do, independent of any single worked example above — this becomes the regression-test target per `evidence_traceability_standard.md`.)

## Confidence

(Product Owner's own honest rating for the full session: High / Medium / Low — how sure are they this captures a real, consistent rule rather than trade-specific judgment calls.)

---

## After this session

1. This filled-in file gets a **Rule ID** assigned from `docs/RULE_INDEX.md`'s existing numbering convention (Stop Loss does not yet have one — this session's outcome is what determines whether it should be a single new ID or split into sub-rules, e.g. separate IDs for "SL basis/placement" vs. "SL movement conditions," depending on what the evidence actually supports).
2. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification).
3. Score the result against `research/specifications/evidence_acceptance_checklist.md`.
4. Log the outcome as a new row in `research/evidence_log.md` (Evidence Complete → Implement / Evidence Partial → Research / Evidence Missing → Freeze, per `research/specifications/product_owner_evidence_process.md`'s Decision Matrix).
5. Only on an **Implement** outcome does a Stop Loss Engine sprint become eligible to start — which also directly unblocks `ExitEngine`'s third exit condition, currently a pass-through to this stub.

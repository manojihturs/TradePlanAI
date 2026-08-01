# Session 4 — Trailing Stop Evidence Intake (Product Owner)

**Status:** Blank intake document — to be filled in by/with the Product Owner. Nothing in this file is evidence yet; it becomes evidence only once the fields below are answered. Once filled in, this file moves through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification) and is scored against `research/specifications/evidence_acceptance_checklist.md`.

**Targets:** This session exists to resolve the Trailing Stop gap identified in `research/specifications/business_engine_portfolio.md` §8. This is the **strongest research candidate of any frozen engine** — one concrete rule is already confirmed and quoted directly from source material (`research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md:246`): *"Trailing stop must guarantee minimum +3 premium points to cover brokerage, exchange charges, tax. Net exit should remain positive."* But `src/interfaces/trailing_stop_engine.py`'s own docstring states: "Trail activation trigger, trail step/distance, and the brokerage/exchange/tax figures needed to compute '+3 net' are all MISSING INFORMATION." This session exists to supply exactly those missing pieces — not to re-derive the +3 net rule itself, which is already settled.

**Do not fill in a field with a guess.** If the Product Owner doesn't know or isn't sure, write `UNKNOWN` — an honest "I don't know" is usable input to the intake process; a guessed value is not (it will be classified as an Assumption, not a Confirmed Rule, per `EVIDENCE_INTAKE_PROCESS.md` Section 2).

**Partial evidence already landed (2026-08-01), cross-referenced here, not duplicated:** `research/incoming/qualification_session1_intake_2026-07-31.md`'s "Entry/Target/SL/TSL Clarification" section confirms the already-known +3 net premium points minimum, and adds "keeps on travel" — i.e. a continuously-updating trail, not a one-time move. The same document's corrected 22-July Worked Example shows a concrete numeric pattern consistent with this: each sequential re-entry trade's SL sits exactly at the previous trade's own entry price.

**Step size — Product Owner-supplied (2026-08-01), verbatim:**

> Minimum need 3 points to cover fees, if premium moved 5 points move the TSL 2 points.

**Reading (not the evidence of record — the quote above is):** activation/minimum guarantee = 3 points (confirms the already-accepted rule, states its purpose explicitly as covering fees). Step ratio: **for every 5 points the premium moves favorably, the trailing stop itself moves up 2 points** — i.e. the stop trails at 2/5 (0.4) of the premium's own favorable movement, not point-for-point. This is the **first stated step-size rule** for this engine — previously entirely MISSING INFORMATION.

**Still missing:**
- The exact activation trigger (does trailing start the instant the +3 point minimum is reached, or is there a separate, distinct trigger condition?).
- The brokerage/exchange/tax figures needed to compute "+3 net" as an exact number (still not supplied).
- A dated worked example showing this 5-points-in/2-points-of-trail ratio applied to real numbers, to confirm it the same way other rules in this project have been (per `evidence_acceptance_checklist.md`).

---

## Instructions for the session

Open **one historical trade at a time**, and for each, walk through the five items below while looking at the actual chart/data together with the Product Owner. Repeat for **5 separate trades** — this project's own acceptance bar (`evidence_acceptance_checklist.md`, "minimum three worked examples") requires at least three, and five gives enough spread to distinguish a real, consistent rule from a trade-specific judgment call.

Include at least one trade where the trailing stop **activated and moved multiple times**, and one where it **never activated at all** — the difference between those two is itself part of the rule (what specifically separates a trade that qualifies for trailing from one that doesn't).

For each trade, capture enough raw detail that someone with no memory of the conversation could independently recompute every stop adjustment from what's written here — that's the same bar Weekly Future was held to before its formula was accepted (`WEEKLY_FUTURE_BLOCKER_REPORT.md` §5).

---

## Worked Example 1

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium:** _______________
**Initial stop (before any trailing):** _______________

1. **Trigger** — what specific condition caused the trailing stop to begin moving at all? (A premium level reached? A number of points in profit? Something else? Give the exact value, not "once it was in profit.")

2. **Step size** — each time the stop moved, by how much did it move, and in relation to what? (E.g. "moved up 5 points for every 10 points the premium gained" — give the exact ratio/increment used, for every adjustment in this trade, not just the first.)

3. **Maximum movement** — did the stop ever stop moving even though price kept moving favorably? If so, at what point, and why?

4. **Exit condition** — exactly what caused this trade to close via the trailing stop (as opposed to Target, Stop Loss, or Competitor)? Give the exact premium/price value at exit.

5. **Net result vs. the +3 minimum** — after brokerage, exchange charges, and tax, what was the actual net premium-point result on this trade, and did it meet the confirmed +3 minimum? (This is the one piece of this engine already confirmed — use this trade to sanity-check it, not to re-derive it.)

**Raw supporting data** (entry price, initial stop, every stop adjustment with its timestamp and new price, exit price and timestamp — attach a screenshot or paste the numbers):

**Brokerage / exchange charge / tax figures used for this trade** (the exact fixed amounts, percentages, or per-lot figures — this is explicitly named as missing in the current interface stub and is required to make "+3 net" computable at all):

---

## Worked Example 2

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium:** _______________
**Initial stop (before any trailing):** _______________

1. **Trigger**

2. **Step size**

3. **Maximum movement**

4. **Exit condition**

5. **Net result vs. the +3 minimum**

**Raw supporting data:**

**Brokerage / exchange charge / tax figures used for this trade:**

---

## Worked Example 3

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium:** _______________
**Initial stop (before any trailing):** _______________

1. **Trigger**

2. **Step size**

3. **Maximum movement**

4. **Exit condition**

5. **Net result vs. the +3 minimum**

**Raw supporting data:**

**Brokerage / exchange charge / tax figures used for this trade:**

---

## Worked Example 4 (recommended: a trade where trailing never activated)

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium:** _______________
**Initial stop (before any trailing):** _______________

1. **Trigger** — was the trigger condition ever reached? If not, why not — what happened instead?

2. **Step size** — N/A if trailing never activated; confirm explicitly.

3. **Maximum movement** — N/A if trailing never activated; confirm explicitly.

4. **Exit condition** — what actually closed this trade instead (Target / Stop Loss / Competitor)?

5. **Net result vs. the +3 minimum** — did this trade still meet +3 net, or is that guarantee specific to trades where trailing activates?

**Raw supporting data:**

**Brokerage / exchange charge / tax figures used for this trade:**

---

## Worked Example 5

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Entry premium:** _______________
**Initial stop (before any trailing):** _______________

1. **Trigger**

2. **Step size**

3. **Maximum movement**

4. **Exit condition**

5. **Net result vs. the +3 minimum**

**Raw supporting data:**

**Brokerage / exchange charge / tax figures used for this trade:**

---

## Cross-cutting questions (answer once, after all examples above are filled in)

- **Are the brokerage/exchange/tax figures fixed values, or do they vary** by broker, lot size, or trade type? If fixed, state the exact figures once here so they don't need to be repeated per trade above. _______________
- **Is the trigger condition the same across all trades, or does it vary by strike/side/market condition?** _______________
- **Is the step size a fixed increment, a fixed ratio, or something else** (e.g. tied to the reference-level ladder itself)? _______________
- **Does Trailing Stop ever interact with Stop Loss** — e.g. does trailing simply move the same stop that Stop Loss would otherwise check, or are they two independent mechanisms evaluated separately? (Relevant to `ExitEngine`'s existing but unresolved exit-condition precedence question, Specification Section 20 item 11 — see also Session 3's Stop Loss intake, if already completed.) _______________
- **Once the stop has trailed, can it ever move backward** (loosen), or only ever tighten? _______________

## Expected Result

(Once the above is filled in, state in one paragraph what a correct `TrailingStopEngine` implementation should now be able to do, independent of any single worked example above — this becomes the regression-test target per `evidence_traceability_standard.md`.)

## Confidence

(Product Owner's own honest rating for the full session: High / Medium / Low — how sure are they this captures a real, consistent rule rather than trade-specific judgment calls.)

---

## After this session

1. This filled-in file gets a **Rule ID** assigned from `docs/RULE_INDEX.md`'s existing numbering convention (the +3 net minimum rule itself is already referenced via Specification Section 20 items 9-10; this session's new content — trigger, step size, cost figures — extends that same rule rather than starting a new one, unless the evidence reveals it should be split).
2. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification).
3. Score the result against `research/specifications/evidence_acceptance_checklist.md`.
4. Log the outcome as a new row in `research/evidence_log.md` (Evidence Complete → Implement / Evidence Partial → Research / Evidence Missing → Freeze, per `research/specifications/product_owner_evidence_process.md`'s Decision Matrix).
5. Only on an **Implement** outcome does a Trailing Stop Engine sprint become eligible to start — which also directly unblocks `ExitEngine`'s fourth exit condition, currently a pass-through to this stub.

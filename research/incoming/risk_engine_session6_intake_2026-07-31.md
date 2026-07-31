# Session 6 — Risk Engine Evidence Intake (Product Owner)

**Status:** Blank intake document — to be filled in by/with the Product Owner. Nothing in this file is evidence yet; it becomes evidence only once the fields below are answered. Once filled in, this file moves through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification) and is scored against `research/specifications/evidence_acceptance_checklist.md`.

**Important difference from Sessions 1–5:** Every other frozen engine has *some* evidence trail — a named concept, a partial rule, or at least a flagged gap in `docs/RULE_INDEX.md`/`GAP_ANALYSIS.md`. Risk Engine has **none of that**. Per `research/specifications/business_engine_portfolio.md` §10: "### 5. Position and Risk Management" exists only as an empty section header in the source outline; `docs/GAP_ANALYSIS.md` and `docs/MATHEMATICAL_SPECIFICATION.md` both list it as entirely unpopulated — no sub-bullets, no MISSING INFORMATION callout, unlike Stop Loss/Trailing Stop/TP Engine, which each have explicit numbered gap items. The only related code is a legacy `CapitalTracker` (`strategy/live_paper_trading.py`) explicitly disclaimed as paper-trading bookkeeping, "not a strategy rule."

**This means Part A below (Scoping) must come first and honestly.** It is entirely possible the answer to Part A is "this was never a defined part of the strategy" — that is a valid, useful outcome, not a failed session. Do not let Part B (worked examples) proceed on the assumption that a rule must exist just because this session was scheduled.

**Do not fill in a field with a guess.** If the Product Owner doesn't know or isn't sure, write `UNKNOWN` — an honest "I don't know" is usable input to the intake process; a guessed value is not (it will be classified as an Assumption, not a Confirmed Rule, per `EVIDENCE_INTAKE_PROCESS.md` Section 2).

---

## Part A — Scoping (answer this first, before any worked example)

1. **Was position sizing or risk management ever part of the original strategy as taught/designed** (the TradingView source this whole reconstruction is based on), or is it something you've applied separately, on your own judgment, on top of the strategy? _______________

2. **If it was part of the original strategy: was it ever explicitly stated** (in the transcript, a video, notes) — or is this the first time it's being written down? _______________

3. **If it was never part of the original strategy: do you still want it captured as a rule for this system**, even though it wouldn't trace back to the same TradingView source as the other engines? (This changes how it gets classified and traced — see `evidence_traceability_standard.md`'s "Source" link, which currently assumes every rule traces to `research/specification/`.) _______________

4. **Does "Risk Engine" mean position sizing (how many lots/contracts per trade), loss limits (daily/weekly max loss), or both?** Be specific — these could be two separate rules, not one. _______________

**If the answer to Q1 is "never part of the strategy" and the answer to Q3 is "no, don't formalize it" — stop here.** Record that outcome in the Expected Result section below and skip Part B entirely. This is a legitimate, complete Session 6 outcome: it confirms Risk Engine should remain frozen not for lack of a documented rule, but because no rule was ever intended to exist in the first place, which is a stronger and more final conclusion than "evidence is missing."

---

## Part B — Worked Examples (only if Part A established that a real rule exists or should be formalized)

Open **one historical trade at a time**, and for each, walk through the questions below. Repeat for **3–5 separate trades** — this project's own acceptance bar (`evidence_acceptance_checklist.md`, "minimum three worked examples") requires at least three.

Include at least one trade with a **different position size or outcome** than the others, if position sizing varies at all — a session where every example uses an identical fixed size will confirm consistency but won't reveal whether sizing ever changes, or under what condition.

### Worked Example 1

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Position size used (lots/contracts):** _______________

1. **What determined this specific size?** (Account capital? A fixed rule? Confidence in the setup? Something else?)
2. **What was the maximum loss this size implied**, and was that number decided in advance or realized only after the fact?
3. **Was there a daily or weekly loss limit in effect**, and did this trade's sizing account for it?
4. **Would a different day's capital or prior results have changed this size?**

**Raw supporting data** (account capital at the time, lots taken, premium per lot, total capital at risk — attach a screenshot or paste the numbers):

### Worked Example 2

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Position size used:** _______________

1. **What determined this specific size?**
2. **What was the maximum loss this size implied?**
3. **Was there a daily or weekly loss limit in effect?**
4. **Would a different day's capital or prior results have changed this size?**

**Raw supporting data:**

### Worked Example 3

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Position size used:** _______________

1. **What determined this specific size?**
2. **What was the maximum loss this size implied?**
3. **Was there a daily or weekly loss limit in effect?**
4. **Would a different day's capital or prior results have changed this size?**

**Raw supporting data:**

### Worked Example 4 (recommended if sizing ever varies)

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Position size used:** _______________

1. **What determined this specific size — and specifically, what was different about this trade vs. Examples 1-3?**
2. **What was the maximum loss this size implied?**
3. **Was there a daily or weekly loss limit in effect?**
4. **Would a different day's capital or prior results have changed this size?**

**Raw supporting data:**

### Worked Example 5 (optional)

**Date:** _______________
**Strike / side (CE or PE):** _______________
**Position size used:** _______________

1. **What determined this specific size?**
2. **What was the maximum loss this size implied?**
3. **Was there a daily or weekly loss limit in effect?**
4. **Would a different day's capital or prior results have changed this size?**

**Raw supporting data:**

---

## Cross-cutting questions (Part B only — answer once, after all examples above are filled in)

- **Is position size fixed, or does it scale with account capital, confidence, or something else?** _______________
- **Is there a hard daily/weekly/monthly loss limit that stops trading entirely**, independent of any single trade's own stop loss? _______________
- **Does Risk Engine interact with Stop Loss** (Session 3) — e.g. is position size chosen so that the Stop Loss's known loss-in-rupees stays within a fixed risk-per-trade cap? _______________
- **Is this a strategy rule, or an account-management practice that's independent of which strategy is being traded?** (This affects whether it belongs in `TradingEngine` at all, or in a separate account-management layer — relevant given the legacy `CapitalTracker` already exists as paper-trading bookkeeping, not a strategy rule.) _______________

## Expected Result

(If Part A concluded "no rule was ever intended," state that explicitly here — this is a complete, valid outcome. Otherwise, once Part B is filled in, state in one paragraph what a correct `RiskEngine` implementation should now be able to do, independent of any single worked example above — this becomes the regression-test target per `evidence_traceability_standard.md`.)

## Confidence

(Product Owner's own honest rating for the full session: High / Medium / Low.)

---

## After this session

1. If Part A concluded no rule exists or should be formalized: log this outcome directly in `research/evidence_log.md` as a scoping conclusion (not a rejected submission) — this permanently resolves why Risk Engine has zero evidence, rather than leaving it as an open question to be re-asked later.
2. If Part B was completed: assign a **new Rule ID** from `docs/RULE_INDEX.md`'s existing numbering convention (none exists yet for Risk/Position Sizing).
3. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification).
4. Score the result against `research/specifications/evidence_acceptance_checklist.md`.
5. Log the outcome as a new row in `research/evidence_log.md` (Evidence Complete → Implement / Evidence Partial → Research / Evidence Missing → Freeze, per `research/specifications/product_owner_evidence_process.md`'s Decision Matrix).
6. Only on an **Implement** outcome does a Risk Engine sprint become eligible to start.

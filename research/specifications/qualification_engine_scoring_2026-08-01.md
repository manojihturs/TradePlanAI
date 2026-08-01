# Qualification Engine — Formal Scoring Pass (2026-08-01)

**Status:** Documentation only. Scores the evidence accumulated in `research/incoming/qualification_session1_intake_2026-07-31.md`, `stop_loss_session3_intake_2026-07-31.md`, `trailing_stop_session4_intake_2026-07-31.md`, and `daily_data_2026-07-31.md` against `research/specifications/evidence_acceptance_checklist.md`, item by item, honestly — including where it doesn't pass.

**Scope of this scoring:** the core Qualification/Entry rule — Entry = a marked level S, Target = S+1, Competitor Exit = touch of S-1, Stop Loss = S-1 (CE side confirmed) — sourced from the 13-level marked ladder (anchor ± 6), gated by an underlying-trend pre-check and a simultaneous dual crossover. This is now the best-evidenced version of QUAL-007's answer. Stop Loss (Session 3) and Trailing Stop (Session 4) are scored separately at the end, since they're distinct engines with their own checklists.

---

## Checklist — Qualification / Entry / Target / Competitor Exit

- [x] **Minimum three worked examples.** **PASS.** 4 independent dated examples exist: 22-July, 29-July, 30-July, 31-July 2026 — 16 individual trade rows total. Exceeds the minimum of three.

- [x] **Consistent outputs.** **PASS, for the core structure.** Every one of the 16 trades follows the same shape without exception: Entry at a marked level, Target = the next marked level in the trade's direction, Competitor Exit = touch of the opposite-side level at the prior rung, SL = the prior rung on the trade's own side. The self-verifying arithmetic (`Total = Captured points × 65`) holds exactly on all 16 rows — a strong, independent internal-consistency signal that this isn't coincidental agreement.

- [~] **No conflicting documentation.** **PASS for the substantive rule; one small open item remains.** Both contradictions originally found in this evidence set are now resolved: (1) the same-strike vs. adjacent-strike competitor question — resolved 2026-08-01, the competitor is any marked level, not fixed to one strike; (2) the 29-July 24150 discrepancy (165.8/116 vs. 137.3/141) — resolved 2026-08-01, Product Owner confirmed 165.8/116 is correct. **Not fully closed:** 31-July's Trade 1 has a minor textual mismatch between its Entry/Exit reason prose (names strike 24300) and its own Ref Label columns (name strike 24350) — flagged in Worked Example 4 as likely a transcription slip, not a business-rule contradiction, since it doesn't affect any of the actual traded numbers. Recorded, not yet explicitly confirmed by the Product Owner as immaterial.

- [x] **Replay validation possible.** **PASS.** The rule's inputs (per-strike CE/PE candle data, a marked-level ladder) are exactly what `src/backtest/`'s existing Upstox connector and `ReferenceBuilder` already fetch and compute today — confirmed directly, not hypothetically, by the two live backtest runs already performed against 30-July-2026 real data this session.

- [ ] **Counter example provided, or explicitly marked UNKNOWN.** **FAIL — genuine gap, not glossed over.** No Worked Example has an explicit "Counter Example" field filled in, not even as `UNKNOWN`. The underlying *substance* of counter-examples already exists in the data (SL-hit trades, "market closed, no level touched" trades — cases where Target was not simply hit cleanly), but per `evidence_submission_template.md`'s own rule, an unfilled field is incomplete regardless of what other data might imply it. This should be explicitly filled in, even if only pointing back to "row 1, 30-July, SL Hit" as the answer.

- [ ] **No unresolved `Unknown` on a required input or output.** **FAIL — two concrete Unknowns remain.** (1) The **PE-side SL** is not yet confirmed — only `SL = CE(S-1)` has been confirmed; the symmetric `SL = PE(S+1)` is a reasonable but unconfirmed extension. (2) The **`WinnerEngine` scope question** — whether entry crossover must be checked against the full 13-level marked ladder or only the entry strike's own reference band — was explicitly deferred by the Product Owner ("need example") rather than answered, and is still open.

---

## Score: 4 of 6 checked (2 explicit fails, both concrete and fixable)

## Verdict

**Evidence Partial — not Evidence Complete.** Per `evidence_acceptance_checklist.md`'s own scoring rule ("Some boxes checked, at least one Confirmed Rule or consistent Worked Example exists → Evidence Partial → proceed to Research"), this is **not** yet an Implement outcome, despite how far it's come. This is real, substantial progress — QUAL-007 went from zero worked examples (the state that failed the original 2026-07-31 audit) to clearing 4 of 6 checklist items with concrete, arithmetic-verified data — but the two remaining gaps are specific and answerable, not vague.

## Targeted follow-up (Research, not Freeze)

Exactly two items would flip this to Evidence Complete for the core rule:

1. **PE-side SL confirmation** — one line from the Product Owner: does `SL = PE(S+1)` for a PE trade, matching the CE side's already-confirmed pattern?
2. **The `WinnerEngine` scope question** — the Product Owner already said this needs a worked example rather than a one-line answer. The next dated trade log should specifically note whether the crossover that triggered entry involved a level from the entry strike's own band, or a level from elsewhere in the wider ladder — ideally an example where the two would give different answers, to make the distinction unambiguous.

Two more items are small housekeeping, not blockers to Evidence Complete once done:

3. Fill the Counter Example field explicitly in at least one Worked Example (pointing to an existing SL-hit or forced-close row is sufficient).
4. Get the Product Owner's confirmation (or correction) on the minor 31-July strike-label mismatch (24300 vs 24350 in the prose vs. the Ref Label columns).

## What this scoring does NOT cover

- **Stop Loss as its own engine (Session 3):** CE side is now a Confirmed Rule (`SL = CE(S-1)`), same status as reflected in `stop_loss_session3_intake_2026-07-31.md`. PE side is the one open item (see above). Scored as **Evidence Partial** for the same reason.
- **Trailing Stop (Session 4):** the +3 minimum and the 5-points-in/2-points-of-trail step ratio are both stated, but the activation trigger and the brokerage/exchange/tax figures needed to compute "+3 net" precisely are still missing. Scored as **Evidence Partial**.
- **The new "market closed (no level touched)" exit type** and the deferred "standard pivot points" (Resistance) concept are both real findings from this evidence, but neither has been scored against the checklist — they are new scope, not part of QUAL-007's original blocker, and should go through their own Request→Submission cycle if the Product Owner wants to pursue them (Resistance/pivot points was explicitly deferred; the forced-close exit type has not yet been discussed either way).

## Recommendation

Do not start Sprint 10 (Qualification Engine implementation) yet. Two short, specific answers away from a genuine Evidence Complete verdict for the core rule — worth getting those two answers before writing any code, rather than implementing 90% of a confirmed rule and having to revisit it.

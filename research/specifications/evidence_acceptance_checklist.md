# Evidence Acceptance Checklist

**Status:** Documentation only. This is the minimum bar a submission must clear before a frozen or research-stage engine may move to Implementation. It restates, as a checklist, the bar already set by `research/EVIDENCE_INTAKE_PROCESS.md` Section 6 (Implementation Gate) and already applied in practice by `WEEKLY_FUTURE_BLOCKER_REPORT.md` §5 (the fallback bar that accepted the Weekly Future formula) and `research/specifications/qualification_implementation_plan.md` (the bar QUAL-007 failed to clear). No new bar is introduced here — this document exists so the same bar is checked explicitly, the same way, every time.

---

## Checklist

- [ ] **Minimum three worked examples.** At least three independent `Worked Example` fields (from one or more `evidence_submission_template.md` submissions) exist for this rule. Exactly the bar `WEEKLY_FUTURE_VERIFICATION.md` set and Weekly Future met; exactly the bar QUAL-007 never reached (zero worked examples found in the entire forensic re-audit).
- [ ] **Consistent outputs.** The worked examples agree with each other — same formula, same rule shape, producing internally-consistent results across all of them. Not merely "three examples exist," but "three examples that don't contradict each other."
- [ ] **No conflicting documentation.** No `CONTRADICTS EXISTING` finding (per `EVIDENCE_INTAKE_PROCESS.md` Section 4) remains unresolved for this specific rule. If a contradiction exists, it must be explicitly resolved by the user (not by this process) before this box can be checked — see `qualification_conflict_matrix.md` for what an *unresolved-but-not-conflicting* gap looks like, as a contrast case: QUAL-007 has no conflicting documentation, but it also has no worked examples, so it still fails this checklist overall.
- [ ] **Replay validation possible.** The rule's inputs are values that exist, or can be derived, from the project's existing replay data (session captures, reference ladders, market snapshots) — i.e., once implemented, the rule can actually be exercised and checked against a real replay session, not just against the submission's own worked examples in isolation.
- [ ] **Counter example provided, or explicitly marked UNKNOWN.** A submission that supplies only confirming examples and leaves Counter Example blank (not marked UNKNOWN) is incomplete per `evidence_submission_template.md` and should be sent back for that field before this checklist is scored.
- [ ] **No unresolved `Unknown` on a required input or output.** Every value the rule's own Inputs/Outputs fields name must have a stated source — an input whose value is itself Unknown blocks the rule even if the formula connecting inputs to outputs is fully evidenced (this is exactly how Trailing Stop Engine's "+3 net premium points" rule is Confirmed as a constraint but not yet actionable — the constraint is known, but the brokerage/exchange/tax figures it depends on are not).

## Scoring

- **All boxes checked → Evidence Complete.** Proceed to Approval per `product_owner_evidence_process.md`'s Decision Matrix.
- **Some boxes checked, at least one Confirmed Rule or consistent Worked Example exists → Evidence Partial.** Proceed to Research (a targeted follow-up Request for exactly the unchecked items).
- **No box checked, or every submitted statement is a Contradiction/Assumption → Evidence Missing.** Freeze.

This scoring is a direct restatement of the three-way Decision Matrix already used for the 10-engine Business Engine Portfolio Audit — nothing here introduces a fourth outcome or a different bar.

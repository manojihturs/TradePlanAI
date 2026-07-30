# Sprint Gate — Evidence Readiness Review (Reusable Template)

**Purpose:** the formal gate between evidence arriving and implementation starting, for any of the six blocked engines. Run this *before* the Sprint 5+ implementation prompt (`SPRINT5_ENGINE_IMPLEMENTATION_TEMPLATE.md`), not instead of it — this produces a GO/NO-GO decision; the other template is what you send once the answer is GO.

## How to use this

1. New evidence arrives for one engine.
2. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` for classification first (Confirmed Rule / Worked Example / Contradiction / Unknown / Assumption / Open Question).
3. Fill in the bracketed placeholder below with the target engine, send the prompt, and let it produce `SPRINT5_READINESS_REVIEW.md` (or `SPRINT6_READINESS_REVIEW.md` etc. — name it for the sprint the target engine belongs to, per `BUSINESS_RULE_INTEGRATION_GUIDE.md`'s numbering: 5=Weekly Future, 6=Strike Selector, 7=TP Engine, 8=Qualification Engine, 9=Stop Loss/Trailing Stop).
4. Only if the outcome is GO or GO WITH LIMITATIONS, proceed to `SPRINT5_ENGINE_IMPLEMENTATION_TEMPLATE.md` for the cleared scope.
5. If NO-GO, stop — do not implement, do not infer, collect the specified additional evidence and repeat.

This mirrors the same gate `WEEKLY_FUTURE_BLOCKER_REPORT.md` already applied once to the original TR-001.md evidence (that review's own outcome was NO-GO/DELAY) — use this template for that same review the next time new evidence shows up, rather than writing the review from scratch.

---

## Prompt template

```text
You are acting as the Chief Domain Architect for TradePlanAI.

=========================================================
PROJECT STATUS
=========================================================

Framework Version

[current version tag — check `git tag`, e.g. v0.6.0-business-orchestration]

Engineering Status

✓ Framework Complete
✓ Business Orchestration Complete
✓ Architecture Complete
✓ Documentation Complete
✓ Tests Passing
✓ CI Passing

Business Engines

⏸ Awaiting Strategy Evidence

=========================================================
OBJECTIVE
=========================================================

Review the newly supplied [ENGINE NAME] evidence and determine
whether Sprint [N] can begin.

This is NOT an implementation task.

This is a readiness review.

=========================================================
INPUT
=========================================================

Review every new source provided, including:

- Videos
- Transcripts
- Screenshots
- PDFs
- Worked examples
- Notes

Compare them against the existing project documentation.

=========================================================
EVALUATION
=========================================================

For [ENGINE NAME], determine whether the evidence is sufficient to
define:

1. Inputs
2. Outputs
3. Calculation sequence
4. Validation rules
5. Error conditions
6. Timing rules
7. State transitions
8. Edge cases

For each category classify:

COMPLETE

PARTIAL

MISSING

CONTRADICTORY

=========================================================
CONTRADICTION ANALYSIS
=========================================================

List every contradiction.

Do not resolve them.

Do not guess.

For each contradiction identify:

- Source
- Statement
- Why implementation would be unsafe

=========================================================
READINESS DECISION
=========================================================

Choose exactly one outcome:

GO

GO WITH LIMITATIONS

NO-GO

=========================================================
IF GO
=========================================================

Specify exactly which implementation tasks may begin.

=========================================================
IF GO WITH LIMITATIONS
=========================================================

Specify which parts of [ENGINE NAME] can be implemented safely and
which must remain blocked.

=========================================================
IF NO-GO
=========================================================

List exactly what additional evidence is required.

=========================================================
OUTPUT
=========================================================

Produce only:

SPRINT[N]_READINESS_REVIEW.md

Do not write code.

Do not modify specifications.

Do not update architecture.

Do not infer missing trading rules.
```

---

## Reminders for whoever fills this in

- This gate applies to every one of the six engines, not just Weekly Future — reuse it for Strike Selector, TP Engine, Qualification Engine, Stop Loss, and Trailing Stop when their own evidence eventually arrives.
- A NO-GO here is a valid, complete outcome — it is not a failure of the review, it's the review doing its job (exactly what happened with `WEEKLY_FUTURE_BLOCKER_REPORT.md`'s own DELAY verdict against `TR-001.md`).
- Keep the readiness review and the implementation prompt as two separate steps/documents even when the answer is GO — the review is the audit trail for *why* implementation was allowed to start.

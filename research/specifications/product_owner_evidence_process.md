# Product Owner Evidence Intake Process

**Status:** Documentation only. This process governs future submissions specifically *from the Product Owner* (a person answering a specific, named gap — e.g. QUAL-007, Stop Loss basis, Trailing Stop mechanics), as distinct from `research/EVIDENCE_INTAKE_PROCESS.md`, which governs raw source material of any kind (transcripts, videos, PDFs) arriving without a specific gap attached. This document does not replace that process — it sits on top of it, adding the request/review/approval steps that only apply when a human is actively supplying evidence in response to a known blocker.

---

## Workflow

```
1. Request
   │  A specific, named gap is identified (an existing Rule ID — QUAL-007,
   │  REVERSAL-001, or a newly assigned one for Stop Loss/Trailing Stop —
   │  from research/specifications/*_gap_analysis.md or docs/RULE_INDEX.md)
   │  and a request is made to the Product Owner using
   │  evidence_submission_template.md's field list as the ask.
   ▼
2. Submission
   │  The Product Owner supplies material in any form (text, worked
   │  numbers, screenshots, TradingView references). It is dropped
   │  unmodified into research/incoming/, exactly as
   │  EVIDENCE_INTAKE_PROCESS.md Section 1 already requires for any
   │  incoming material.
   ▼
3. Validation
   │  The submission is run through EVIDENCE_INTAKE_PROCESS.md's existing
   │  Extraction → Verification → Cross-check → Classification steps
   │  (Sections 1-4) unchanged. This step produces a NEW / CONFIRMS
   │  EXISTING / CONTRADICTS EXISTING tag per statement, exactly as
   │  today.
   ▼
4. Review
   │  The validated submission is scored against
   │  evidence_acceptance_checklist.md. This is a new step: it asks not
   │  just "is each statement verified" (Validation already does that)
   │  but "collectively, is there enough to implement" — the same bar
   │  research/EVIDENCE_INTAKE_PROCESS.md Section 6 (Implementation Gate)
   │  already sets, checked explicitly and up front rather than
   │  discovered only when a Sprint tries to reopen.
   ▼
5. Approval
   │  The user (not this process, not any automated rule) reviews the
   │  Review step's checklist result and the Decision Matrix outcome
   │  below, and explicitly approves, requests more evidence, or
   │  declines. This mirrors EVIDENCE_INTAKE_PROCESS.md Section 6 item 5
   │  exactly — no automatic unblock.
   ▼
6. Implementation
   │  Only after Approval: the relevant src/interfaces/*.py stub is
   │  replaced with a real implementation, following
   │  evidence_traceability_standard.md so the new code links back to
   │  its evidence.
   ▼
7. Regression Validation
      The existing pytest --cov=src (100% required), mypy --strict src,
      ruff/black gate is run, per this project's standard sprint
      verification. Additionally, if replay data exists that exercises
      the newly-implemented rule, a replay run is used to sanity-check
      the new engine's output against the worked examples that unblocked
      it — the same worked examples become regression fixtures.
```

Steps 1-3 reuse `research/EVIDENCE_INTAKE_PROCESS.md` directly rather than duplicating it. Steps 4-7 are the new material this document adds.

---

## Where this fits the existing project

- **Rule IDs already in use** that this process will resolve, if evidence arrives: `QUAL-007` (competitor identity), `REVERSAL-001` (Premium/Reversal mathematics), plus two not-yet-assigned IDs for Stop Loss basis and Trailing Stop mechanics (to be assigned from `docs/RULE_INDEX.md`'s existing numbering convention when a submission is first requested for them).
- **`research/evidence_log.md`** remains the single append-only ledger of every intake outcome — this framework does not introduce a second log.
- **`docs/EVIDENCE_MATRIX.md`**'s existing Evidence-Count → Confidence mapping (0/1/2/3-4/5+ → Unknown/Low/Medium/High/Confirmed) is reused unchanged for grading submissions — this framework does not introduce a new confidence scale.

---

## Decision Matrix

| Evidence state after Review | Action |
|---|---|
| **Evidence Complete** — passes every item on `evidence_acceptance_checklist.md` | **Implement** — proceed to Approval (step 5), then Implementation |
| **Evidence Partial** — some usable statements (Confirmed Rule / Worked Example per `EVIDENCE_INTAKE_PROCESS.md` Section 2) exist, but the checklist is not fully met | **Research** — record what's missing specifically (per `evidence_acceptance_checklist.md`'s own gap-statement requirement) and issue a follow-up Request (step 1) targeting exactly that gap |
| **Evidence Missing** — no usable statement was produced, or every statement is a Contradiction/Assumption/fails Section 3 of `EVIDENCE_INTAKE_PROCESS.md` | **Freeze** — record in `research/evidence_log.md` and leave the corresponding `src/interfaces/*.py` stub unchanged; do not re-request until the Product Owner has new material to offer |

This matrix is the same three-way outcome already used across this project's engine-level decisions (Qualification: Freeze: 4 engines this way; Stop Loss/Trailing Stop: Research; Winner/Entry/Target: already Implemented) — this document formalizes it as a standing process rather than a one-off judgment made fresh each time.

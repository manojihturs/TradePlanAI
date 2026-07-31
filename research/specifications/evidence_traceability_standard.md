# Evidence Traceability Standard

**Status:** Documentation only. Defines how every future implemented rule links back to the evidence that justified it, so an engine's correctness can always be traced to a specific, named source rather than to "it seemed right at the time."

---

## The five-link chain

Every implemented business rule must be traceable through all five of the following, in order:

```
1. Evidence document
   The research/incoming/ submission (per evidence_submission_template.md)
   or original source material (transcript, research/specification/ doc)
   that supplied the rule.
        │
        ▼
2. Rule ID
   The stable identifier already used throughout this project
   (e.g. QUAL-009, REVERSAL-001, or a newly assigned ID from
   docs/RULE_INDEX.md's existing numbering convention). Every rule gets
   exactly one ID for its lifetime, even if evidence for it arrives in
   multiple submissions over time.
        │
        ▼
3. Source
   The specification document the rule was written into after passing
   Approval (a file under research/specification/ or
   research/specifications/, e.g. STRATEGY_FUNCTIONAL_SPECIFICATION.md
   §N, or a new *_SPECIFICATION.md for a rule with no existing home).
        │
        ▼
4. Replay validation
   The replay session(s) used to exercise the new engine's real
   behavior post-implementation, plus a record of whether the engine's
   output matched the evidence document's Worked Example /
   Expected Result fields on that data.
        │
        ▼
5. Tests
   The pytest test file(s) covering the new engine, at 100% coverage
   per this project's standing verification gate — with at least one
   test built directly from the evidence document's Worked Example
   (same inputs, same expected output) so the test itself is
   traceable back to link 1, closing the loop.
```

## Where each link is recorded

| Link | Recorded in |
|---|---|
| Evidence document | `research/incoming/<topic>_<date>.md`, referenced by filename |
| Rule ID | `docs/RULE_INDEX.md` (status updated to Confirmed once implemented) |
| Source | The relevant `research/specification*/` document, with the Rule ID cited inline |
| Replay validation | A new row in `research/evidence_log.md` at implementation time, naming the replay session(s) used |
| Tests | The test file's own docstring or a comment citing the Rule ID (not the evidence prose — the code should name the ID, not restate the business justification) |

## Minimum bar for a rule to be considered traceable

A rule is **not** traceable, and should not be marked implemented in `docs/RULE_INDEX.md`, until:

1. Its Rule ID appears in `research/evidence_log.md` with an ACCEPTED (or equivalent Evidence Complete) outcome.
2. Its Rule ID appears in the specification document that was updated at Approval.
3. At least one test exists whose assertion values match the evidence document's Worked Example numbers exactly (not re-derived or approximated).
4. If replay data exists that could exercise the rule, a replay validation record exists in `research/evidence_log.md`; if no such replay data exists yet, this is stated explicitly rather than silently skipped.

## Why this matters for this project specifically

This project has already been burned by the inverse of traceability once: Version 1.0's "Competitor Exit" (`CHANGELOG.md`) was added to the legacy system without a documented source, which is precisely why `INVESTIGATIONS.md` #9 and #11 later had to reconstruct, after the fact, whether that rule was ever actually specified. The five-link chain above exists so that question never has to be asked again about a rule newly implemented under this framework — the chain is built at implementation time, not reconstructed years later from git archaeology.

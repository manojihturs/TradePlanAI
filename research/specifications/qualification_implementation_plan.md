# Qualification Engine — Implementation Recommendation

**Status:** Documentation only. This document makes a recommendation; it does not implement anything.

---

## Recommendation: **C — Blocked Pending Evidence**

`QualificationEngine` (QUAL-001/QUAL-002, the TP High/TP Low sustain tests) should **not** be implemented, not even partially, until the evidence gaps below are closed.

## Why not A (Safe to implement now)

The comparison *logic* of QUAL-001/QUAL-002 is genuinely well-evidenced (HIGH confidence, stated consistently across two independent documents). But logic alone is not runnable code: both tests require a concrete "competitor" value to compare against, and that identity is not evidenced anywhere (QUAL-007). The only competitor mapping this project has ever confirmed (`STRATEGY_FUNCTIONAL_SPECIFICATION.md` Rule 2) is explicitly scoped to a different pipeline stage — the Exit Engine's post-Winner competitor — and the specification itself warns against assuming that pattern transfers to the pre-Winner TP test. Implementing "Safe to implement now" would require guessing at exactly the thing the evidence tells us not to guess at.

## Why not B (Implement partially)

A partial implementation was seriously considered — e.g. building only QUAL-009 (Single Active Trade), which *is* fully evidenced and confirmed. But QUAL-009 is an Entry Engine concern, not a Qualification Engine one; it does not depend on, and does not partially implement, any part of QUAL-001/QUAL-002. Building it under the `QualificationEngine` interface would misrepresent what it actually resolves, and building it under `EntryEngine` instead is a separate, future sprint's decision, not part of this Qualification-specific recommendation. Beyond QUAL-009, every other rule in the catalogue (QUAL-001 through QUAL-008, QUAL-010) is either directly blocked by the same missing competitor identity, or is itself an unresolved architectural/process question (QUAL-006, QUAL-008) rather than a rule with a partial, safely-implementable subset. There is no meaningful partial slice of `QualificationEngine` itself to build.

## What would change this recommendation

Per `research/specifications/QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` §4's Acceptance Criteria (unchanged by this audit, since no new evidence resolving them was found), implementation may begin only once **all** of the following hold:

1. The competitor mapping (strike + level) is uniquely defined for both TP High and TP Low — no ambiguity, no "assume it's the same as Rule 2."
2. The qualification decision is reproducible from stated inputs alone (independent recomputation, the same bar Weekly Future was held to).
3. At least 3 independent worked examples agree with each other.
4. No two examples imply conflicting rules for the same input shape.
5. The TP output shape (price / boolean / both) is resolved.

This audit adds two further open questions worth resolving alongside the above, though they are not blockers for QUAL-001/QUAL-002's own logic:

6. Whether Qualification is a distinct engine from TP at all (QUAL-006) — affects the target module/interface shape, not the rule's correctness.
7. Whether Qualification output is meant to feed Winner Detection (QUAL-008) — affects where the engine's output is wired, not whether it can be built. Current evidence leans toward "no dependency," meaning `QualificationEngine` could plausibly be built as a standalone, unconsumed capability until further evidence says otherwise — worth confirming explicitly rather than assuming either way.

## What is *not* blocked

`QUAL-009` (Single Active Trade) is fully evidenced, confirmed, and independent of every gap above. It is not part of this recommendation's scope (`QualificationEngine`), but it is worth flagging as a ready, low-risk candidate for a future `EntryEngine` sprint, separate from Qualification.

---

## Evidence Summary

- **10 rules catalogued** (QUAL-001–QUAL-010); **1 fully evidenced** (QUAL-009, out of scope for this engine); **5 partially evidenced**; **11 distinct unevidenced gaps** (see `qualification_gap_analysis.md` for the full breakdown).
- This audit corroborates every gap already on record in `research/specifications/QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` and adds two items that document did not carry: the Partial/Complete Disqualification distinction (QUAL-005, `research/analysis/TR-001_ANALYSIS.md` §3.7) and the explicit Qualification→Winner Detection dependency question (QUAL-008, `BUSINESS_WORKFLOW_SPECIFICATION.md`).

## Rule Count

**10** (QUAL-001 through QUAL-010).

## Blocked Rules

**QUAL-001, QUAL-002** (the two rules that together constitute `QualificationEngine` itself) — blocked by **QUAL-007** (competitor identity, unevidenced), plus the cadence and output-shape gaps listed in `qualification_gap_analysis.md`. QUAL-004, QUAL-005, and QUAL-010 are supporting concepts, partially evidenced, and cannot be resolved into implementable rules until their own respective gaps (detection mechanism, second corroborating example, numeric threshold) are closed.

## Recommendation

**C — Blocked pending evidence.** Do not implement `QualificationEngine`, in whole or in part, until the Acceptance Criteria above are met. Update `research/specifications/QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` (already the canonical tracking document for this) if/when new evidence arrives, following its own §5 Evidence Intake Checklist.

# Qualification Engine — Competitor Identity Conflict Matrix

**Status:** Documentation only. Per the forensic prompt's own instruction: "If evidence conflicts: produce a conflict matrix, do not choose a winner." This document reports the result of applying that instruction.

---

## Finding: No conflicting evidence exists

Across every source searched (see `qualification_competitor_analysis.md` for the full list), **no two sources state different, incompatible answers** for the TP-stage competitor's identity. A genuine conflict would look like: Source A says "competitor = Weekly Future," Source B says "competitor = adjacent strike." That shape does not occur anywhere in this repository.

What exists instead is a different, narrower situation, tabulated below for completeness since it is the closest thing to "conflicting" evidence a reader might expect to find.

## Candidate hypotheses vs. evidence

| Candidate | Evidence for | Evidence against |
|---|---|---|
| Exit-stage competitor definition (Rule 2: `PE(S-1)`/`CE(S+1)`) transfers unchanged to the TP-stage test | It is the only "competitor" concept ever defined with a concrete selection rule anywhere in the repository, so it is a natural candidate to reach for | Three independent documents explicitly warn against this transfer: `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7 ("is not stated to use the same S±1 pattern, and this document does not assume it does"), `BUSINESS_ARCHITECTURE.md` §3 ("explicitly not the same... must not be assumed to generalize here"), `REQUIREMENTS_TRACEABILITY_MATRIX.md` (lists the two as separate rows with separate evidence states). No source affirms the transfer. |
| Weekly Future / Top Strike / Bottom Strike / Reference Level / Premium / ORB | None found | Not one source connects any of these concepts to the TP-stage competitor role; see `qualification_competitor_analysis.md` §4 |
| An as-yet-undefined, distinct TP-stage-only competitor concept | Consistent with every source's silence — nothing rules this out | Cannot be evidenced either, since nothing describes it |

This is not a conflict between stated rules — it is **unanimous silence plus one unanimous warning** against the only tempting shortcut (borrowing the Exit-stage definition). Every source that addresses the question at all agrees: the TP-stage competitor is unresolved, and the Exit-stage competitor is not a substitute.

## Explicit non-choice

Per the prompt's instruction, no winner is chosen among the candidates above — including the tempting Exit-stage transfer — because the evidence does not support any of them, and multiple sources explicitly instruct against assuming the one candidate with a concrete definition.

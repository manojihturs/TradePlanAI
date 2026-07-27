# Validation Checklist

The criteria a recovered rule must meet before advancing between
phases of this reconstruction effort, per the project's Business Rules
-> Mathematics -> Code -> Backtesting -> Live Trading ordering. Nothing
advances a phase gate without satisfying the relevant checklist here.

## Status

Draft structure only - specific pass/fail criteria are to be filled in
as the project establishes what "sufficient evidence" concretely means
for this effort. Not yet used to gate any rule, since no rules have
reached a status requiring gating.

## Gate 1 — Evidence Gathered -> Confirmed

Before a rule's status in `RULE_INDEX.md` moves from
`EVIDENCE_GATHERED` to `CONFIRMED`:

- [ ] _Criteria to be defined - e.g. minimum number of independent
      evidence entries, or single-source confidence threshold_
- [ ] No contradicting evidence entry exists (or contradictions have
      been explicitly resolved and documented)
- [ ] The rule is stated in `TRADINGVIEW_STRATEGY_BIBLE.md` with a
      direct citation to its HR-N/RTV-N source(s)

## Gate 2 — Confirmed -> Formalised (Business Rules -> Mathematics)

Before a rule appears in `MATHEMATICAL_SPECIFICATION.md`:

- [ ] Rule status is `CONFIRMED` in `RULE_INDEX.md`
- [ ] The rule can be stated with no remaining ambiguity (boundary
      conditions, field references, ordering all explicit)
- [ ] At least one worked numeric example exists, tied to evidence

## Gate 3 — Formalised -> Implementation Candidate (Mathematics -> Code)

Before a formalised rule becomes a candidate for code changes:

- [ ] Gap Analysis entry exists comparing it to current behaviour
- [ ] Explicit approval obtained from the project owner
- [ ] No implementation work begins without this approval, per
      standing instruction

## Gate 4 — Implementation -> Backtesting

- [ ] _Criteria to be defined once Phase 3 begins_

## Gate 5 — Backtesting -> Live Trading

- [ ] _Criteria to be defined once Phase 4 begins_

## Notes

This checklist itself is a living document and will be refined as the
reconstruction effort clarifies what rigor each gate actually needs -
it is not to be treated as complete or final at this stage.

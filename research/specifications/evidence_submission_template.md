# Evidence Submission Template

**Status:** Documentation only. This is a fill-in-the-blank template — copy it into a new file under `research/incoming/` per submission (e.g. `research/incoming/stop_loss_2026-08-15.md`), named by topic and date, per the existing convention set by `research/incoming/weekly_future_formula_2026-07-30.md`.

**Instructions for the Product Owner:** Fill in every field you can. Leave a field as `UNKNOWN` if you don't have an answer — do not guess or approximate to fill a blank field. An incomplete submission is still valuable; a filled-in-but-guessed field is not, and will be treated as an Assumption (not a Confirmed Rule) per `research/EVIDENCE_INTAKE_PROCESS.md` Section 2.

---

```markdown
## Business Rule Name

(e.g. "Stop Loss Placement Rule" — match an existing gap's name from
docs/RULE_INDEX.md or research/specifications/*_gap_analysis.md if this
submission targets a known gap; otherwise give it a clear, specific name.)

## Purpose

(One or two sentences: what business problem this rule solves, in plain
language — not a restatement of the inputs/outputs below.)

## Inputs

(Every value the rule needs to run. Be concrete — not "the price" but
"the CE premium at the moment of entry, in rupees.")

## Outputs

(What the rule produces. Be concrete about the shape — a price? a
boolean? a percentage?)

## Worked Example

(At least one full, concrete instance: real or realistic numbers, every
intermediate step shown, and the final result. Do not skip steps — a
missing step here becomes an Unknown per the intake process, even if
the final number is given.)

## Counter Example

(An instance where the rule does NOT apply, or produces a different
outcome than the Worked Example — this is what lets the intake process
tell "the rule" apart from "a coincidence in one example." If no
counter example exists yet, write UNKNOWN rather than omitting this
section.)

## Screenshots (optional)

(TradingView chart screenshots, spreadsheet exports, or any visual
evidence. Reference the filename here; place the actual file alongside
this submission in research/incoming/.)

## TradingView Reference

(Indicator name, strategy name, or script reference this rule comes
from, if applicable. UNKNOWN if not applicable.)

## Expected Result

(What a correct implementation should produce, stated independently of
the Worked Example above — this is what a future regression test will
check against.)

## Confidence

(Your own honest rating: High / Medium / Low — how sure are you this
rule is stated completely and correctly, not how important it is.)
```

---

## Field-level notes

- **Worked Example** and **Counter Example** together are what `evidence_acceptance_checklist.md`'s "minimum three worked examples" and "consistent outputs" items are checked against — a submission with only one Worked Example and no Counter Example will not, by itself, pass the checklist; it becomes a candidate for a follow-up Request (see `product_owner_evidence_process.md`'s Decision Matrix, "Evidence Partial → Research").
- Every field maps directly onto `research/EVIDENCE_INTAKE_PROCESS.md` Section 2's classification categories: Worked Example → **Worked Example**; a stated rule with no numbers → **Confirmed Rule** (if unambiguous) or **Assumption** (if hedged); an explicitly blank field → **Unknown**.

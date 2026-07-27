# Mathematical Specification

Formal, unambiguous mathematical definitions for business rules that
have reached sufficient evidence in `TRADINGVIEW_STRATEGY_BIBLE.md`
and [RULE_INDEX.md](RULE_INDEX.md). This is the Phase 2 deliverable
per the project's Business Rules -> Mathematics -> Code -> Backtesting
-> Live Trading ordering - nothing here is written ahead of confirmed
evidence, and nothing here is code.

## Status

Empty - awaiting Phase 1 (Business Rules Recovery) to produce
confirmed rules. No rule is formalised here until its status in
`RULE_INDEX.md` is `CONFIRMED`.

## Format for each formalised rule

Once populated, each rule will be documented as:

- **Rule ID**: cross-referenced to `RULE_INDEX.md`
- **Plain statement**: the business rule in plain language
- **Formal definition**: precise mathematical notation (inputs,
  outputs, conditions) with no ambiguity about ordering, inclusivity
  of boundaries (`>` vs `>=`), or which data field is referenced
- **Worked example**: at least one concrete numeric example, tied to
  its originating evidence
- **Explicit non-goals**: what the rule does NOT cover, to prevent
  scope creep during implementation

## Sections to populate (mirrors the Bible's structure)

### 1. Level Capture Mathematics

### 2. Premium Mapping / Cross-Referencing Mathematics

### 3. Entry Condition Mathematics

### 4. Exit Condition Mathematics

### 5. Position and Risk Mathematics

### 6. Market Structure Condition Mathematics

## Traceability

Every formalised rule here must have a `FORMALISED` status and a
Bible section reference in [RULE_INDEX.md](RULE_INDEX.md).

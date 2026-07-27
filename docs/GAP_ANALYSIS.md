# Gap Analysis

A structured comparison between the reconstructed original strategy
(`TRADINGVIEW_STRATEGY_BIBLE.md` / `MATHEMATICAL_SPECIFICATION.md`)
and the current `strategy/` Python implementation (Version 1.0/1.1).
Produced only once the reconstruction has enough confirmed, formalised
rules to compare against - not before, and not from the code's own
behaviour in isolation.

## Status

Empty - blocked on Phase 1/2 (Business Rules Recovery and
Mathematical Formalisation) producing enough `FORMALISED` rules in
`RULE_INDEX.md` to compare.

## Relationship to existing investigation work

This is distinct from, and will draw on, `INVESTIGATIONS.md`'s
existing findings (repo root) - particularly Investigation #11 (Version
1.1's Competitor Exit interpretation vs. the stated original intent)
and Investigation #13 (the Premium Mapping's Target vs. Competitor
Level are not mathematically equivalent). Those investigations reasoned
from the Python code's own behaviour and regression results; this
document instead starts from the independently-reconstructed original
rules and asks where the code diverges - the reverse direction.

## Format for each identified gap

Once populated, each gap will be documented as:

- **Rule ID**: cross-referenced to `RULE_INDEX.md`
- **Original strategy behaviour**: per the Bible/Mathematical
  Specification
- **Current implementation behaviour**: per the actual `strategy/`
  code, with file/line reference
- **Classification**: `MATCHES` / `MISSING` / `CONTRADICTS` / `PARTIAL`
- **Evidence for the current-code description**: test result, code
  trace, or investigation reference
- **No recommendation is made here** - this document states the gap
  only; deciding what to do about it is a separate step, after this
  phase, requiring explicit approval per the project's phase-gate
  principle (Code third, only after Business Rules and Mathematics)

## Sections to populate (mirrors the Mathematical Specification)

### 1. Level Capture

### 2. Premium Mapping / Cross-Referencing

### 3. Entry Conditions

### 4. Exit Conditions

### 5. Position and Risk Management

### 6. Market Structure Conditions

## Traceability

Every gap listed here must reference a `RULE_INDEX.md` Rule ID with
`FORMALISED` status.

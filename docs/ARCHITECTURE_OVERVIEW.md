# Architecture Overview

Describes how the documents in this reconstruction effort relate to
each other and to the existing repository, and how evidence is
expected to flow from raw source material to eventual implementation.
No code architecture is defined here yet - this describes the
documentation and evidence pipeline only, per the "no code" scope of
this phase.

## Evidence flow

```
Raw evidence                Consolidation              Formalisation         Implementation
-------------                --------------              -------------         --------------
YouTube transcripts    -->   TRADINGVIEW_HIDDEN_RULES.md
TradingView screenshots -->  (repo root, HR-N entries)
Manual backtest notes                |
                                      v
                              TRADINGVIEW_REQUIREMENTS_RECOVERY.md
                              (repo root, RTV-N entries -
                               cross-referenced against current code)
                                      |
                                      v
                              TRADINGVIEW_STRATEGY_BIBLE.md   -->   MATHEMATICAL_SPECIFICATION.md   -->   strategy/ (future)
                              (docs/, consolidated account)         (docs/, formal definitions)            (Phase 3+)
                                      |
                                      v
                              RULE_INDEX.md
                              (docs/, master index + status)
```

## Document responsibilities

- **`TRADINGVIEW_HIDDEN_RULES.md`** (repo root): raw, per-example
  observations. No synthesis, no comparison to code.
- **`TRADINGVIEW_REQUIREMENTS_RECOVERY.md`** (repo root): evidence
  compared against the current Python implementation, classified as
  Already Implemented / Missing Requirement / Contradicts Current
  Specification / Insufficient Evidence.
- **`TRADINGVIEW_STRATEGY_BIBLE.md`** (this directory): the
  consolidated, evidence-backed narrative account of the original
  strategy - synthesises HR-N and RTV-N entries once enough evidence
  exists for a given area of the strategy.
- **`RULE_INDEX.md`** (this directory): a flat, master list of every
  individual recovered rule, each with its evidence source(s), current
  status, and links into the Bible/Mathematical Specification.
- **`STATE_MACHINE.md`** (this directory): the strategy's states
  (e.g. flat, in-position, per-leg states) and the evidenced
  transitions between them - separate from the mathematical detail of
  each transition's trigger condition.
- **`MATHEMATICAL_SPECIFICATION.md`** (this directory): formal,
  unambiguous mathematical definitions for rules that have reached
  sufficient evidence - the Phase 2 deliverable.
- **`GAP_ANALYSIS.md`** (this directory): a structured comparison
  between recovered rules and the current `strategy/` implementation -
  produced only after the Bible/Mathematical Specification reach
  enough maturity to compare against, not before.
- **`VALIDATION_CHECKLIST.md`** (this directory): the criteria a
  recovered rule must meet at each phase gate before advancing.

## Relationship to the existing `strategy/` package

The existing Python package is not touched by this documentation
effort and is not treated as authoritative for what the original
strategy did. It remains a live reference point only for
`GAP_ANALYSIS.md`'s comparisons, once those are appropriate to make.

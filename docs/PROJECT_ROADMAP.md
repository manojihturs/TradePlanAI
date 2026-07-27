# Project Roadmap

Tracks the phases of the TradingView strategy reconstruction effort,
per the five Project Principles in [README.md](README.md): Business
Rules first, Mathematics second, Code third, Backtesting fourth, Live
Trading last. No phase begins until the previous phase's evidence
and traceability requirements are satisfied.

## Phase 1 — Business Rules Recovery

Objective: recover every business rule the original TradingView
strategy actually used, from direct evidence only (YouTube transcript,
chart screenshots, manual backtest notes).

- Status: _to be filled in as evidence is gathered_
- Inputs: TradingView screenshots, YouTube transcript excerpts, manual
  trade logs
- Outputs: entries in `TRADINGVIEW_HIDDEN_RULES.md` and
  `TRADINGVIEW_REQUIREMENTS_RECOVERY.md` (repo root), consolidated into
  [TRADINGVIEW_STRATEGY_BIBLE.md](TRADINGVIEW_STRATEGY_BIBLE.md) and
  indexed in [RULE_INDEX.md](RULE_INDEX.md)
- Exit criteria: _to be defined - see [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)_

## Phase 2 — Mathematical Formalisation

Objective: express each recovered rule as a precise, unambiguous
mathematical definition, tied back to its originating evidence.

- Status: not started
- Depends on: Phase 1 rules reaching sufficient evidence status
- Outputs: [MATHEMATICAL_SPECIFICATION.md](MATHEMATICAL_SPECIFICATION.md)

## Phase 3 — Implementation

Objective: implement the formalised rules in code, only once they are
mathematically unambiguous.

- Status: not started
- Depends on: Phase 2 completion for the rules being implemented
- Relationship to existing code: the current `strategy/` package
  (Version 1.0/1.1) is evaluated against recovered rules in
  [GAP_ANALYSIS.md](GAP_ANALYSIS.md); implementation work here may
  revise, replace, or confirm existing modules - not assumed in
  advance

## Phase 4 — Backtesting

Objective: validate implemented rules against historical data.

- Status: not started
- Depends on: Phase 3 completion for the rules being tested

## Phase 5 — Live Trading

Objective: deploy validated rules to live (paper, then real) trading.

- Status: not started
- Depends on: Phase 4 completion and explicit approval

## Current status

Reconstruction effort just begun. No rules yet reach a status where
Phase 2 can start. See [RULE_INDEX.md](RULE_INDEX.md) for the current
rule-by-rule status.

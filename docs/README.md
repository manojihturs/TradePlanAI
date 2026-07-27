# TradingView Strategy Reconstruction — Documentation

This `/docs` directory is the record of a ground-up reconstruction of
a proprietary TradingView options trading methodology, built from
YouTube transcripts, TradingView chart evidence, and manual
backtesting observations - treated as the sole source of truth. The
existing `strategy/` Python package (Version 1.0/1.1) is treated as
one possible interpretation of that methodology, not as the reference.

## Objective

Not immediate profitability. The first objective is to reconstruct
the original business rules with complete traceability from evidence
to rule to (eventually) implementation.

## Project Principles

1. Business Rules first.
2. Mathematics second.
3. Code third.
4. Backtesting fourth.
5. Live Trading last.

## Ground rules

- Never invent business rules.
- Never assume missing logic.
- Never optimise strategies.
- Never simplify trading logic.
- Everything must be evidence-based.

## Document index

| Document | Purpose |
|---|---|
| [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) | Phases of the reconstruction effort and current status |
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | How the documentation set and eventual implementation relate to each other |
| [TRADINGVIEW_STRATEGY_BIBLE.md](TRADINGVIEW_STRATEGY_BIBLE.md) | The consolidated, evidence-backed account of the original strategy |
| [RULE_INDEX.md](RULE_INDEX.md) | Master index of every recovered business rule, with evidence source and status |
| [TERMINOLOGY.md](TERMINOLOGY.md) | Single definition for every trading term used across the documentation |
| [STATE_MACHINE.md](STATE_MACHINE.md) | The strategy's states and transitions, as evidenced (frozen at v0.1, Draft) |
| [DOMAIN_MODEL.md](DOMAIN_MODEL.md) | Every business entity mentioned in the Strategy Bible - static structure only, no behaviour |
| [EVIDENCE_MATRIX.md](EVIDENCE_MATRIX.md) | Single source of truth tracking every artifact across the project, with confidence and lifecycle status |
| [TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md) | Traces every artifact from origin source through evidence to every related artifact and its implementation lifecycle |
| [MATHEMATICAL_SPECIFICATION.md](MATHEMATICAL_SPECIFICATION.md) | Formal mathematical definitions of recovered rules |
| [GAP_ANALYSIS.md](GAP_ANALYSIS.md) | Where the current Python implementation diverges from recovered rules |
| [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) | Criteria a recovered rule must meet before being trusted |
| [architecture/SOLUTION_STRUCTURE.md](architecture/SOLUTION_STRUCTURE.md) | .NET solution layout, projects, dependencies, layer responsibilities |
| [architecture/DOMAIN_ARCHITECTURE.md](architecture/DOMAIN_ARCHITECTURE.md) | Responsibility of every confirmed/Candidate domain object - no behaviour |
| [architecture/RULE_ENGINE_ARCHITECTURE.md](architecture/RULE_ENGINE_ARCHITECTURE.md) | Rule Registry, Evaluation Pipeline, Session/Market Context, Results, Decisions |
| [architecture/PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md) | Recommended solution folder structure |
| [architecture/IMPLEMENTATION_ROADMAP.md](architecture/IMPLEMENTATION_ROADMAP.md) | Milestones 4.1-4.9 for implementing the architecture |
| [architecture/PYTHON_IMPLEMENTATION_GUIDE.md](architecture/PYTHON_IMPLEMENTATION_GUIDE.md) | Python packaging, dependency, and tooling decisions (Milestone 4.0R technology pivot) |

## Relationship to existing project documents

This effort is distinct from, and does not replace:

- `INVESTIGATIONS.md` (repo root) - the prior investigation log into
  the Version 1.0/1.1 Python implementation's own behaviour.
- `TRADINGVIEW_REQUIREMENTS_RECOVERY.md` (repo root) - evidence
  entries (RTV-N) comparing TradingView evidence against the current
  Python code.
- `TRADINGVIEW_HIDDEN_RULES.md` (repo root) - raw per-example
  documentation (HR-N) of TradingView/manual-backtest observations,
  without reference to the Python code.
- `SPECIFICATION.md` / `CHANGELOG.md` (repo root) - the current
  Python implementation's own specification and version history.

`/docs` is where evidence gathered in those logs gets consolidated,
cross-referenced, and formalised into a complete, traceable account of
the original strategy.

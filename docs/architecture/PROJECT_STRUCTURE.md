# Project Structure

Recommended folder structure for the workspace described in
`SOLUTION_STRUCTURE.md`. Folder names indicate where future
implementation work will go — none of the files listed are created by
this milestone; this is a map, not code.

> **Milestone 4.0R note:** This document originally described a .NET
> solution layout (`.sln`, `.csproj` files). Per the Milestone 4.0R
> pivot, it now describes the equivalent Python package layout. No
> layer, responsibility, Rule ID, or Entity ID reference changed —
> only the file/folder conventions did. See
> `docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md` for the full
> packaging/tooling rationale.

## Placement in this repository

This repository already uses `docs/` and `research/` for the
reconstruction-effort documentation (Phases 1–3), and `strategy/` for
the existing, separate Version 1.0/1.1 Python implementation. The new
engine is placed in its own top-level package, **`trading_engine/`**,
sibling to `strategy/` — not nested inside `docs/`, to avoid any
collision with the existing documentation tree.

```
TradePlan/                          (existing repository root)
│
├── trading_engine/                 (NEW - this architecture's implementation)
│   ├── pyproject.toml
│   ├── README.md
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   └── primitives/             -- generic, trading-agnostic value/result types
│   │       (no trading concepts here)
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── strike.py               -- ENT-001, STRIKE-001
│   │   ├── first_candle.py         -- ENT-002, STRIKE-001
│   │   ├── trend_point.py          -- ENT-003, TREND-001/002/003
│   │   ├── opponent.py             -- ENT-005, OPPONENT-001; OpponentHigh/Low sub-slots ENT-006/007
│   │   ├── market_structure.py     -- ENT-004, TREND-002 (abstract change signal only)
│   │   ├── reversal.py             -- ENT-008, REVERSAL-001
│   │   ├── premium.py              -- ENT-009, REVERSAL-001 (thin)
│   │   ├── edge.py                 -- TREND-003 (condition, not a stored entity - see DOMAIN_ARCHITECTURE.md)
│   │   ├── market_session.py       -- architectural container, no cited Rule/Entity ID
│   │   └── candidates/             -- Milestone 4.0: reserved, inactive, not wired to any rule
│   │       ├── __init__.py
│   │       ├── weekly_future.py    -- ENT-010
│   │       ├── mid_point.py        -- ENT-011
│   │       ├── trigger_point.py    -- ENT-012
│   │       ├── sellers_perspective.py -- ENT-013
│   │       └── opening_range.py    -- ENT-014
│   │       (IVL Level / UNK-001 has NO module - deliberately absent, see DOMAIN_ARCHITECTURE.md)
│   │
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── registry.py             -- keyed by Rule ID, mirrors RULE_INDEX.md
│   │   └── rule_reference.py       -- RuleReference / EvidenceReference value objects
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── evaluation_pipeline.py  -- ordering derived from Depends On/Referenced By
│   │   ├── market_context.py       -- single-step read-only snapshot
│   │   ├── session_state.py        -- accumulating per-MarketSession state, incl. STATE_MACHINE.md's 5 states
│   │   ├── rule_result.py          -- carries Rule ID + Evidence ID(s)
│   │   └── decision.py             -- aggregate of Rule Results per evaluation step
│   │   (no concrete rule mathematics anywhere in these two packages -
│   │   all remain Unknown/Partially Known per TRADINGVIEW_STRATEGY_BIBLE.md)
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   (reserved - no broker/market-data adapters exist yet;
│   │   Milestone 4.9+ per IMPLEMENTATION_ROADMAP.md)
│   │
│   ├── replay/
│   │   ├── __init__.py
│   │   (reserved - Replay Engine; Milestone 4.5+)
│   │
│   ├── backtest/
│   │   ├── __init__.py
│   │   (reserved - Backtest orchestration/reporting; Milestone 4.7+)
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── __main__.py             -- composition root only, wires packages together
│   │   (not a UI package - no UI code per Milestone 4.0 instruction)
│   │
│   └── tests/
│       ├── domain/                 -- exercises domain entities in isolation
│       └── rules_engine/           -- exercises Rule Registry/Pipeline in isolation
│
├── docs/                           (existing - reconstruction documentation, unchanged)
├── research/                       (existing - evidence/analysis/reviews, unchanged)
└── strategy/                       (existing - separate Version 1.0/1.1 Python implementation, unchanged)
```

## Purpose of each package

| Package | Purpose |
|---|---|
| `shared` | Cross-cutting primitives with no trading meaning; the only package every other package may (transitively) import from |
| `domain` | Houses every confirmed and Candidate domain object from `DOMAIN_ARCHITECTURE.md`; the layer the "rules evolve without changing unrelated code" goal protects |
| `rules` + `engine` | Houses the Rule Engine architecture (`RULE_ENGINE_ARCHITECTURE.md`): Registry, Pipeline, Context, Session State, Results, Decisions |
| `infrastructure` | Reserved seam for future broker/market-data/persistence integration — isolated so broker specifics never leak into `domain`/`rules`/`engine` |
| `replay` + `backtest` | Reserved seam for future replay/backtesting, feeding historical data through the same Pipeline `engine` defines |
| `cli` | Composition root only — wires packages together to run the engine; explicitly not a UI |
| `tests` | Unit tests for `domain` and `rules`/`engine`, per the Milestone 4.0 "Unit testing" design goal |

## Naming convention note

Module names under `domain/` and `domain/candidates/` use
`snake_case` (Python convention) of the domain object's
architecture-document name (e.g. `trend_point.py` for `TrendPoint`,
`weekly_future.py` for `WeeklyFuture`) rather than inventing new
terminology — every module name traces directly to a heading in
`DOMAIN_ARCHITECTURE.md`, which in turn traces to an Entity ID/Rule
ID. No module exists for a concept that isn't named in the approved
documentation.

## What is intentionally not shown

No class/function bodies, no type definitions beyond the module-level
grouping above — per Milestone 4.0's "Do NOT write code" instruction
(carried forward unchanged by Milestone 4.0R), this document stops at
folder/module structure. See `docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md`
for packaging, dependency, and tooling decisions that inform *how*
this structure will be built, still without writing any of it yet.

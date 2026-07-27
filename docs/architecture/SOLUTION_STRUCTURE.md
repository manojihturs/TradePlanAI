# Solution Structure

Architecture only — no business logic, no algorithms, no broker code,
no UI code. Every layer described here exists to hold the confirmed
and candidate concepts recorded in `docs/DOMAIN_MODEL.md`,
`docs/TRADINGVIEW_STRATEGY_BIBLE.md`, and
`research/analysis/TR-001_ANALYSIS.md` — nothing here invents what
those concepts do.

> **Milestone 4.0R note:** This document originally described a .NET
> solution (`TradingEngine.sln`, C# projects). Per the Milestone 4.0R
> implementation-technology pivot, all technology-specific references
> below are now Python. **No architectural decision changed** — the
> same layers, the same dependency direction, the same responsibilities
> and boundaries apply; only the language/tooling naming does. See
> `docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md` for the concrete
> packaging, dependency, and tooling decisions this pivot introduces.

## Design goals (from Milestone 4.0's objective)

- Rule traceability (every rule ID in `RULE_INDEX.md` must map to
  exactly one place in code, once implemented)
- Future transcript-driven evolution (new evidence → new/updated
  rules, without touching unrelated code)
- Unit testing
- Replay/backtesting
- Live trading later
- Multiple brokers later
- Multiple instruments later

## Layering approach

A layered ("Clean"/Onion-style) architecture, chosen because the
dependency direction it enforces — outer layers depend on inner
layers, never the reverse — directly serves the "rules evolve without
changing unrelated code" requirement: the Domain layer (the concepts
themselves) never needs to know about backtesting, brokers, or UI, so
changes to those outer concerns cannot ripple inward. A layered
architecture is a language-agnostic idea; enforcing the dependency
direction in Python is a matter of import discipline (and, optionally,
lint rules — see `PYTHON_IMPLEMENTATION_GUIDE.md`) rather than a
project-reference graph, since Python has no build-time equivalent of
a `.csproj`'s `ProjectReference`.

```
trading_engine/                       (single Python package/workspace, not a multi-.sln solution)
│
├── shared/            (innermost — imported by others, imports nothing else in this tree)
├── domain/            → shared
├── rules/ + engine/   → domain, shared      (together: the former "Application" layer)
├── infrastructure/    → rules, engine, domain, shared
├── replay/ + backtest/→ rules, engine, domain, shared
├── cli/               → rules, engine, infrastructure, replay, backtest, domain, shared
└── tests/             (imports whatever it tests; nothing imports tests/)
```

## Layers and dependencies

### shared
No dependency on any other layer in this tree. Holds only
cross-cutting primitives with no trading meaning of their own (e.g.
generic result/error types). Nothing here is described in
`DOMAIN_MODEL.md`, so nothing trading-specific belongs here.

### domain
Depends on: `shared` only.
Holds the confirmed and candidate domain objects from
`docs/DOMAIN_ARCHITECTURE.md` (Strike, TrendPoint, Opponent, Reversal,
Premium, MarketSession, and the marked Candidates). Holds no
evaluation logic, no rule implementations, no I/O. This is the layer
that must remain stable as brokers/backtesting/UI change around it —
per the design goal, this is the layer "rules evolve without changing
unrelated code" is protecting.

### rules + engine (the former "Application" layer)
Depends on: `domain`, `shared`.
Together, `rules/` and `engine/` hold the Rule Engine architecture
described in `docs/RULE_ENGINE_ARCHITECTURE.md`: `rules/` holds the
Rule Registry (keyed by Rule ID) and rule-level traceability; `engine/`
holds the Rule Evaluation Pipeline, Session State, Market Context, Rule
Results, and Decision Objects that orchestrate `domain` objects through
evaluation. Split into two packages (rather than one, as the .NET
version had) because Python's import system makes a registry-of-rules
concern (`rules/`) and an evaluation-orchestration concern (`engine/`)
naturally separable without needing a project-boundary to enforce it —
this mirrors the recommended package layout in
`PYTHON_IMPLEMENTATION_GUIDE.md`. Neither package contains
broker/backtest/UI-specific code or concrete rule mathematics (those
remain Unknown per `TRADINGVIEW_STRATEGY_BIBLE.md`'s Open Questions
until evidenced).

### infrastructure
Depends on: `rules`, `engine`, `domain`, `shared`.
Reserved for future broker/market-data connectivity and persistence.
Per Milestone 4.0's explicit instruction, **no broker API is connected
here yet** — this package exists as the seam where that will happen
later (Milestone 4.9+), kept isolated so broker-specific code never
leaks into `domain` or `rules`/`engine`.

### replay + backtest
Depends on: `rules`, `engine`, `domain`, `shared`.
`replay/` feeds historical data through the same Rule Evaluation
Pipeline `engine/` defines, one step at a time, without any live
broker dependency (Milestone 4.5). `backtest/` orchestrates `replay/`
runs and produces reports (Milestone 4.7). Kept as their own packages
(rather than folded into `cli/`) so backtesting can be run and tested
independently of any live-trading entry point.

### cli
Depends on: `rules`, `engine`, `infrastructure`, `replay`, `backtest`,
`domain`, `shared`.
The composition root — the only package allowed to import from every
other package, since something has to wire them together. Holds no
business logic of its own. Explicitly **not a UI package** — per
instruction, no UI code is created in this milestone or implied by
this structure; `cli/` is a minimal entry point for running the engine
(e.g. against backtest data), not a user interface. (This replaces the
former `TradingEngine.Console` project; a Python console entry point is
a module/script, not a separate compiled executable project.)

### tests
Exercises `domain` and `rules`/`engine` in isolation, per the "Unit
testing" design goal, using the framework and conventions in
`PYTHON_IMPLEMENTATION_GUIDE.md`. No non-test package imports from
`tests/` — tests depend on the code under test, never the reverse.

## Layer responsibility summary

| Layer | Responsibility | Must NOT contain |
|---|---|---|
| shared | Cross-cutting, trading-agnostic primitives | Any trading concept |
| domain | Confirmed/Candidate domain objects (Section: `DOMAIN_ARCHITECTURE.md`) | Rule evaluation logic, I/O, broker/backtest/UI concerns |
| rules + engine | Rule Registry, Pipeline, Session/Market Context, Results, Decisions (Section: `RULE_ENGINE_ARCHITECTURE.md`) | Concrete rule mathematics not yet evidenced; broker/backtest/UI concerns |
| infrastructure | Future broker/market-data/persistence adapters | Domain concepts, rule logic |
| replay + backtest | Future replay/backtest orchestration | Live broker connectivity, UI |
| cli | Composition/wiring only | Business logic |
| tests | Verification of domain/rules/engine behaviour | Production wiring |

## Multi-broker / multi-instrument support

Both requirements are satisfied structurally, not by any concrete
class/function designed here: `infrastructure` is the single seam
where broker-specific code would live, and nothing in `domain` or
`rules`/`engine` references a specific broker or a specific instrument
(NIFTY, or otherwise) by name anywhere in the confirmed evidence
reviewed for this milestone. Multi-instrument support is therefore a
property of keeping `domain` instrument-agnostic from the start, not a
feature to add later — no domain object in
`docs/DOMAIN_ARCHITECTURE.md` is described as NIFTY-specific.

## Traceability note

This structure itself references no Rule ID because it contains no
rule logic. Every subsequent architecture document in this milestone
explicitly cites the Rule IDs / Entity IDs / Analysis sections it is
shaped around.

# trading_engine

The reconstructed TradingView strategy's implementation. See
`../docs/architecture/` for the approved architecture this package
implements, and `../docs/TRADINGVIEW_STRATEGY_BIBLE.md` /
`../docs/RULE_INDEX.md` for the business rules being reconstructed.

## Milestone 4.3A status: Domain layer + Rule Framework + Strategy Engine Skeleton + Calculator Framework

This package currently contains the `domain` subpackage (Milestone
4.1: structural, immutable data models), the `rules` subpackage
(Milestone 4.2: the Rule Framework - contracts, registry, and
evaluation-pipeline scaffolding), the `engine` subpackage (Milestone
4.3: the Strategy Engine Skeleton - orchestration only), and the
`calculators` subpackage (Milestone 4.3A: the Calculator Framework -
contracts, registry, and five placeholder calculators, each of which
raises ``NotImplementedError``). **No trading logic, no rule
mathematics, no strategy decisions, no replay, no backtesting, and no
broker connectivity exist anywhere in this package yet.** See
`../docs/architecture/IMPLEMENTATION_ROADMAP.md` for what follows
(Milestone 4.4 onward).

**Architecture Rule (Milestone 4.3/4.3A):** `StrategyEngine` may
orchestrate. Rules may evaluate. Only future calculator modules may
perform mathematics - and even the calculator modules that exist today
perform none; each placeholder calculator raises
``NotImplementedError``. These responsibilities are never mixed - see
`engine/__init__.py` and `calculators/__init__.py`.

## Package layout

```
trading_engine/
    __init__.py
    domain/
        __init__.py              -- DomainValidationError
        rule_reference.py        -- RuleReference, RuleCategory, RuleStatus, ConfidenceLevel
        evidence_reference.py    -- EvidenceReference, EvidenceLevel
        market_session.py        -- MarketSession
        strike.py                -- Strike
        trend_point.py           -- TrendPoint
        opponent.py               -- Opponent
        premium.py                -- Premium
        market_context.py        -- MarketContext
        session_state.py         -- SessionState, SessionStateType
        decision.py                -- RuleEvaluationResult, Decision
        domain_event.py          -- DomainEvent
    rules/
        __init__.py
        protocols.py              -- Rule (typing.Protocol)
        base.py                   -- AbstractRule (abc.ABC convenience base)
        categories.py             -- RuleCategory (re-export of domain's enum)
        outcome.py                 -- RuleOutcome, RuleExecutionResult
        context.py                 -- RuleExecutionContext
        registry.py                -- RuleRegistry
        exceptions.py               -- RuleFrameworkError, DuplicateRuleError,
                                        RuleRegistrationError, RuleExecutionError
    engine/
        __init__.py
        strategy_engine.py          -- StrategyEngine
        execution_pipeline.py        -- ExecutionPipeline, PipelineOutcome
        execution_report.py          -- ExecutionReport
        execution_summary.py         -- ExecutionSummary
        engine_configuration.py      -- EngineConfiguration
        exceptions.py                 -- EngineError, EngineConfigurationError, PipelineExecutionError
    calculators/
        __init__.py
        protocols.py                  -- Calculator (typing.Protocol)
        base.py                        -- AbstractCalculator (abc.ABC)
        registry.py                    -- CalculatorRegistry
        context.py                     -- CalculationContext
        result.py                       -- CalculationStatus, CalculationResult
        exceptions.py                    -- CalculatorFrameworkError, DuplicateCalculatorError,
                                             CalculatorRegistrationError, CalculationError
        strike_calculator.py             -- StrikeCalculator (placeholder, STRIKE-001)
        trend_calculator.py               -- TrendCalculator (placeholder, TREND-001/002)
        opponent_calculator.py            -- OpponentCalculator (placeholder, OPPONENT-001/002/003)
        reversal_calculator.py            -- ReversalCalculator (placeholder, REVERSAL-001)
        edge_calculator.py                -- EdgeCalculator (placeholder, TREND-003)
    tests/
        domain/                    -- Milestone 4.1A test suite
        rules/                     -- Milestone 4.2 test suite
        engine/                    -- Milestone 4.3 test suite
        calculators/               -- Milestone 4.3A test suite
```

## Design rules this package follows

- Every domain model is an immutable `@dataclass(frozen=True)`.
- Every closed set of values is an `Enum`, never a magic string.
- Every public class has a Google-style docstring citing the Rule
  ID(s)/Entity ID it derives from, per
  `../docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md` Section 10.
- Validation is structural only (non-null identifiers, positive
  prices, non-blank strings) - never a trading rule. Anywhere business
  behaviour is still unresolved, the code says so with a
  `# TODO (<RULE-ID>)` comment rather than guessing.
- `domain/` has **zero third-party dependencies** - standard library
  only (`dataclasses`, `enum`, `typing`, `uuid`, `datetime`, `decimal`,
  `pathlib`).

## What is intentionally NOT here

Per Milestones 4.1/4.2/4.3/4.3A's explicit scope: no trading logic, no
implemented rule or calculator (every rule in `docs/RULE_INDEX.md`
still has Unknown or Partially Known mathematics), no replay, no
backtesting, no broker APIs, no market calculations, and no Weekly
Future / Mid Point / Trigger Point / Opening Range / Seller
Perspective calculations. Every one of the five placeholder
calculators (`calculators/strike_calculator.py`,
`trend_calculator.py`, `opponent_calculator.py`,
`reversal_calculator.py`, `edge_calculator.py`) compiles, registers,
and exposes correct identity/traceability metadata, but its
`calculate()` unconditionally raises `NotImplementedError` citing the
Rule ID it awaits evidence for. `rules/registry.py`'s
`execution_order()` currently returns registration order only - not
the dependency-graph-respecting order `docs/RULE_INDEX.md`'s "Depends
On" data implies. `engine/execution_pipeline.py` never applies a
resulting Session State update (Rule Evaluation Pipeline step 5 in
`docs/architecture/RULE_ENGINE_ARCHITECTURE.md`) and never reads
`engine_configuration.py`'s `logging_enabled` field - no logging
format is evidenced anywhere. `calculators/registry.py` performs no
execution ordering at all (explicit Milestone 4.3A scope limit). See
each module's `# TODO (<RULE-ID>)` / `# TODO (RULE_ENGINE_ARCHITECTURE)`
comments for exactly what remains unresolved and why.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

or, without an editable install:

```bash
pip install -r requirements-dev.txt
```

## Running checks

```bash
mypy --strict trading_engine/domain trading_engine/rules trading_engine/engine trading_engine/calculators
ruff check trading_engine
black --check trading_engine
pytest trading_engine/tests --cov=trading_engine.domain --cov=trading_engine.rules --cov=trading_engine.engine --cov=trading_engine.calculators --cov-report=term-missing
```

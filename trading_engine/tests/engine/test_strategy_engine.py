"""Tests for StrategyEngine."""

from __future__ import annotations

import pytest

from trading_engine.engine.engine_configuration import EngineConfiguration
from trading_engine.engine.exceptions import EngineConfigurationError, PipelineExecutionError
from trading_engine.engine.execution_report import ExecutionReport
from trading_engine.engine.strategy_engine import StrategyEngine
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.outcome import RuleOutcome
from trading_engine.rules.registry import RuleRegistry

from ..rules.conftest import make_rule_reference
from .conftest import FrameworkExceptionRule


class TestConstructorValidation:
    def test_valid_construction_with_default_configuration(
        self, populated_registry: RuleRegistry
    ) -> None:
        engine = StrategyEngine(populated_registry)
        assert engine.registry is populated_registry
        assert engine.configuration == EngineConfiguration()

    def test_valid_construction_with_explicit_configuration(
        self, populated_registry: RuleRegistry
    ) -> None:
        config = EngineConfiguration(dry_run=True)
        engine = StrategyEngine(populated_registry, config)
        assert engine.configuration is config


class TestInvalidConstructorValues:
    def test_none_registry_raises(self) -> None:
        with pytest.raises(EngineConfigurationError, match="registry must not be None"):
            StrategyEngine(None)  # type: ignore[arg-type]


class TestRun:
    def test_run_returns_execution_report(
        self, populated_registry: RuleRegistry, sample_execution_context: RuleExecutionContext
    ) -> None:
        engine = StrategyEngine(populated_registry)
        report = engine.run(sample_execution_context)
        assert isinstance(report, ExecutionReport)
        assert report.rules_executed == ("STRIKE-001", "TREND-001", "REVERSAL-001")
        assert len(report.results) == 3
        assert {r.outcome for r in report.results} == {
            RuleOutcome.PASS,
            RuleOutcome.UNKNOWN,
            RuleOutcome.FAIL,
        }

    def test_run_end_time_not_before_start_time(
        self, populated_registry: RuleRegistry, sample_execution_context: RuleExecutionContext
    ) -> None:
        engine = StrategyEngine(populated_registry)
        report = engine.run(sample_execution_context)
        assert report.end_time >= report.start_time

    def test_run_with_empty_registry_produces_empty_report(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        engine = StrategyEngine(RuleRegistry())
        report = engine.run(sample_execution_context)
        assert report.rules_executed == ()
        assert report.results == ()

    def test_run_none_context_raises(self, populated_registry: RuleRegistry) -> None:
        engine = StrategyEngine(populated_registry)
        with pytest.raises(PipelineExecutionError, match="context.*must not be None"):
            engine.run(None)  # type: ignore[arg-type]

    def test_run_propagates_fatal_framework_error_into_report_errors(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        registry = RuleRegistry()
        registry.register(FrameworkExceptionRule(make_rule_reference("STRIKE-001")))
        engine = StrategyEngine(registry)
        report = engine.run(sample_execution_context)
        assert report.results == ()
        assert len(report.errors) == 1

    def test_run_respects_maximum_rule_count(
        self, populated_registry: RuleRegistry, sample_execution_context: RuleExecutionContext
    ) -> None:
        engine = StrategyEngine(populated_registry, EngineConfiguration(maximum_rule_count=1))
        report = engine.run(sample_execution_context)
        assert len(report.results) == 1
        assert len(report.warnings) == 1

    def test_run_does_not_contain_business_logic_branches(self) -> None:
        # Structural guard, not a behavioural test: StrategyEngine's
        # executable code (not its prose docstrings) must never branch
        # on a domain concept by name - it orchestrates the generic
        # Rule contract only.
        import ast
        import inspect
        import textwrap

        source = textwrap.dedent(inspect.getsource(StrategyEngine))
        tree = ast.parse(source)
        code_only = "\n".join(
            ast.unparse(node)
            for node in ast.walk(tree)
            if not isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.Expr, ast.Constant)
            )
        )
        for forbidden in ("Strike", "TrendPoint", "Opponent", "Edge", "Reversal"):
            assert forbidden not in code_only


class TestEdgeCases:
    def test_two_engines_sharing_a_registry_do_not_interfere(
        self, populated_registry: RuleRegistry, sample_execution_context: RuleExecutionContext
    ) -> None:
        engine_a = StrategyEngine(populated_registry)
        engine_b = StrategyEngine(populated_registry, EngineConfiguration(maximum_rule_count=1))
        report_a = engine_a.run(sample_execution_context)
        report_b = engine_b.run(sample_execution_context)
        assert len(report_a.results) == 3
        assert len(report_b.results) == 1

"""Tests for ExecutionPipeline and PipelineOutcome."""

from __future__ import annotations

import pytest

from trading_engine.engine.engine_configuration import EngineConfiguration
from trading_engine.engine.exceptions import PipelineExecutionError
from trading_engine.engine.execution_pipeline import ExecutionPipeline, PipelineOutcome
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.outcome import RuleOutcome

from ..rules.conftest import FakeRule, make_rule_reference
from .conftest import BuggyRule, FrameworkExceptionRule


class TestPipelineOutcome:
    def test_defaults_are_empty_tuples(self) -> None:
        outcome = PipelineOutcome()
        assert outcome.rules_executed == ()
        assert outcome.results == ()
        assert outcome.warnings == ()
        assert outcome.errors == ()


class TestBasicIteration:
    def test_collects_one_result_per_rule(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (
            FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS),
            FakeRule(make_rule_reference("TREND-001"), outcome=RuleOutcome.FAIL),
        )
        outcome = ExecutionPipeline().run(rules, sample_execution_context, EngineConfiguration())
        assert outcome.rules_executed == ("STRIKE-001", "TREND-001")
        assert [r.outcome for r in outcome.results] == [RuleOutcome.PASS, RuleOutcome.FAIL]
        assert outcome.warnings == ()
        assert outcome.errors == ()

    def test_empty_rule_sequence_produces_empty_outcome(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        outcome = ExecutionPipeline().run((), sample_execution_context, EngineConfiguration())
        assert outcome == PipelineOutcome()


class TestMaximumRuleCount:
    def test_stops_after_limit_and_records_warning(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (
            FakeRule(make_rule_reference("STRIKE-001")),
            FakeRule(make_rule_reference("TREND-001")),
            FakeRule(make_rule_reference("REVERSAL-001")),
        )
        config = EngineConfiguration(maximum_rule_count=2)
        outcome = ExecutionPipeline().run(rules, sample_execution_context, config)
        assert outcome.rules_executed == ("STRIKE-001", "TREND-001")
        assert len(outcome.results) == 2
        assert len(outcome.warnings) == 1
        assert "Maximum rule count" in outcome.warnings[0]

    def test_limit_greater_than_rule_count_evaluates_all(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (FakeRule(make_rule_reference("STRIKE-001")),)
        config = EngineConfiguration(maximum_rule_count=100)
        outcome = ExecutionPipeline().run(rules, sample_execution_context, config)
        assert len(outcome.results) == 1
        assert outcome.warnings == ()


class TestDryRun:
    def test_dry_run_produces_no_results(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (FakeRule(make_rule_reference("STRIKE-001")),)
        config = EngineConfiguration(dry_run=True)
        outcome = ExecutionPipeline().run(rules, sample_execution_context, config)
        assert outcome.rules_executed == ("STRIKE-001",)
        assert outcome.results == ()
        assert len(outcome.warnings) == 1
        assert "Dry run" in outcome.warnings[0]


class TestFatalFrameworkExceptions:
    def test_framework_exception_stops_iteration_and_records_error(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (
            FakeRule(make_rule_reference("STRIKE-001")),
            FrameworkExceptionRule(make_rule_reference("TREND-001")),
            FakeRule(make_rule_reference("REVERSAL-001")),
        )
        outcome = ExecutionPipeline().run(rules, sample_execution_context, EngineConfiguration())
        # STRIKE-001 evaluated successfully, TREND-001's exception
        # stopped iteration - REVERSAL-001 never reached.
        assert outcome.rules_executed == ("STRIKE-001", "TREND-001")
        assert len(outcome.results) == 1
        assert len(outcome.errors) == 1
        assert "Fatal framework exception" in outcome.errors[0]

    def test_framework_exception_stops_regardless_of_continue_on_error(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (
            FrameworkExceptionRule(make_rule_reference("STRIKE-001")),
            FakeRule(make_rule_reference("TREND-001")),
        )
        config = EngineConfiguration(fail_fast=False, continue_on_error=True)
        outcome = ExecutionPipeline().run(rules, sample_execution_context, config)
        assert outcome.rules_executed == ("STRIKE-001",)
        assert outcome.results == ()


class TestUnexpectedExceptions:
    def test_fail_fast_raises_pipeline_execution_error(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (BuggyRule(make_rule_reference("STRIKE-001")),)
        config = EngineConfiguration(fail_fast=True, continue_on_error=False)
        with pytest.raises(PipelineExecutionError, match="Unexpected exception"):
            ExecutionPipeline().run(rules, sample_execution_context, config)

    def test_continue_on_error_records_and_continues(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (
            BuggyRule(make_rule_reference("STRIKE-001")),
            FakeRule(make_rule_reference("TREND-001"), outcome=RuleOutcome.PASS),
        )
        config = EngineConfiguration(fail_fast=False, continue_on_error=True)
        outcome = ExecutionPipeline().run(rules, sample_execution_context, config)
        assert outcome.rules_executed == ("STRIKE-001", "TREND-001")
        assert len(outcome.results) == 1
        assert outcome.results[0].outcome is RuleOutcome.PASS
        assert len(outcome.errors) == 1

    def test_neither_fail_fast_nor_continue_on_error_stops_without_raising(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = (
            BuggyRule(make_rule_reference("STRIKE-001")),
            FakeRule(make_rule_reference("TREND-001")),
        )
        config = EngineConfiguration(fail_fast=False, continue_on_error=False)
        outcome = ExecutionPipeline().run(rules, sample_execution_context, config)
        assert outcome.rules_executed == ("STRIKE-001",)
        assert outcome.results == ()
        assert len(outcome.errors) == 1


class TestEdgeCases:
    def test_all_rules_producing_results_leaves_no_errors_or_warnings(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        rules = tuple(FakeRule(make_rule_reference(f"STRIKE-{i:03d}")) for i in range(1, 4))
        outcome = ExecutionPipeline().run(rules, sample_execution_context, EngineConfiguration())
        assert len(outcome.results) == 3
        assert outcome.warnings == ()
        assert outcome.errors == ()

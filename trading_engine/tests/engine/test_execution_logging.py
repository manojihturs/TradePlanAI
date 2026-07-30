"""Tests for execution-time diagnostic event emission (Milestone 6.4).

Covers both :class:`ExecutionPipeline.run` and
:class:`StrategyEngine.run`. A dedicated file - no existing test file
is modified to add this.
"""

from __future__ import annotations

import pytest

from trading_engine.diagnostics.events import (
    DependencyResolved,
    ExecutionFailed,
    ExecutionSummaryLogged,
    RuleFinished,
    RuleSkipped,
    RuleStarted,
)
from trading_engine.diagnostics.sink import InMemoryDiagnosticsSink
from trading_engine.engine.engine_configuration import EngineConfiguration
from trading_engine.engine.execution_pipeline import ExecutionPipeline
from trading_engine.engine.strategy_engine import StrategyEngine
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.outcome import RuleOutcome
from trading_engine.rules.registry import RuleRegistry

from ..rules.conftest import FakeRule, make_rule_reference
from .conftest import BuggyRule, FrameworkExceptionRule


class TestLoggingDisabled:
    def test_pipeline_emits_nothing_when_logging_disabled(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        rules = (FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS),)
        config = EngineConfiguration(logging_enabled=False)

        ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        assert len(sink) == 0

    def test_strategy_engine_emits_nothing_when_logging_disabled(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))
        config = EngineConfiguration(logging_enabled=False, diagnostics_sink=sink)
        engine = StrategyEngine(registry, config)

        engine.run(sample_execution_context)

        assert len(sink) == 0

    def test_disabled_ignores_a_sink_passed_directly_to_the_pipeline(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        # Even if a caller passes a real sink directly to
        # ExecutionPipeline.run(), logging_enabled=False must still
        # win - this is the "no-op regardless of what was passed"
        # guarantee documented on ExecutionPipeline.run().
        sink = InMemoryDiagnosticsSink()
        rules = (FakeRule(make_rule_reference("STRIKE-001")),)
        config = EngineConfiguration(logging_enabled=False)

        ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        assert len(sink) == 0


class TestLoggingEnabled:
    def test_pipeline_emits_started_and_finished_for_a_successful_rule(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        rules = (FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS),)
        config = EngineConfiguration(logging_enabled=True)

        ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 2
        assert isinstance(events[0], RuleStarted)
        assert isinstance(events[1], RuleFinished)
        assert events[0].rule_id == "STRIKE-001"
        assert events[1].rule_id == "STRIKE-001"
        assert events[1].outcome_name == "PASS"

    def test_strategy_engine_emits_dependency_resolved_and_summary(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS))
        config = EngineConfiguration(logging_enabled=True, diagnostics_sink=sink)
        engine = StrategyEngine(registry, config)

        report = engine.run(sample_execution_context)

        events = sink.events()
        assert isinstance(events[0], DependencyResolved)
        assert isinstance(events[-1], ExecutionSummaryLogged)
        assert events[-1].execution_id == report.execution_id
        assert events[-1].total_rules == 1
        assert events[-1].pass_count == 1

    def test_default_sink_is_standard_logging_when_none_configured(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        # No diagnostics_sink set on the configuration - StrategyEngine
        # falls back to StandardLoggingDiagnosticsSink rather than
        # silently doing nothing, per _resolve_diagnostics_sink().
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))
        config = EngineConfiguration(logging_enabled=True)
        engine = StrategyEngine(registry, config)

        # Should not raise - StandardLoggingDiagnosticsSink.emit()
        # just forwards to the stdlib logging module.
        engine.run(sample_execution_context)


class TestEventOrdering:
    def test_started_always_precedes_finished_for_the_same_rule(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        rules = (
            FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS),
            FakeRule(make_rule_reference("TREND-001"), outcome=RuleOutcome.UNKNOWN),
        )
        config = EngineConfiguration(logging_enabled=True)

        ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        events = sink.events()
        assert [type(event).__name__ for event in events] == [
            "RuleStarted",
            "RuleFinished",
            "RuleStarted",
            "RuleFinished",
        ]
        assert events[0].rule_id == "STRIKE-001"
        assert events[1].rule_id == "STRIKE-001"
        assert events[2].rule_id == "TREND-001"
        assert events[3].rule_id == "TREND-001"

    def test_skip_events_appear_in_place_of_started_finished(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        rules = (FakeRule(make_rule_reference("STRIKE-001")),)
        config = EngineConfiguration(logging_enabled=True, dry_run=True)

        ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 1
        assert isinstance(events[0], RuleSkipped)
        assert events[0].reason == "dry run"

    def test_maximum_rule_count_emits_skip_for_the_stopping_rule(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        rules = (
            FakeRule(make_rule_reference("STRIKE-001")),
            FakeRule(make_rule_reference("TREND-001")),
        )
        config = EngineConfiguration(logging_enabled=True, maximum_rule_count=1)

        ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        events = sink.events()
        # STRIKE-001: started + finished; TREND-001: skipped (limit reached).
        assert [type(event).__name__ for event in events] == [
            "RuleStarted",
            "RuleFinished",
            "RuleSkipped",
        ]
        assert events[2].rule_id == "TREND-001"
        assert events[2].reason == "maximum rule count reached"


class TestExceptionLogging:
    def test_framework_exception_emits_fatal_execution_failed(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        rules = (FrameworkExceptionRule(make_rule_reference("STRIKE-001")),)
        config = EngineConfiguration(logging_enabled=True)

        ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 2
        assert isinstance(events[0], RuleStarted)
        assert isinstance(events[1], ExecutionFailed)
        assert events[1].fatal is True
        assert events[1].rule_id == "STRIKE-001"

    def test_unexpected_exception_with_fail_fast_emits_fatal_before_raising(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        from trading_engine.engine.exceptions import PipelineExecutionError

        sink = InMemoryDiagnosticsSink()
        rules = (BuggyRule(make_rule_reference("STRIKE-001")),)
        config = EngineConfiguration(logging_enabled=True, fail_fast=True, continue_on_error=False)

        with pytest.raises(PipelineExecutionError):
            ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 2
        assert isinstance(events[1], ExecutionFailed)
        assert events[1].fatal is True
        assert events[1].exception_type == "ValueError"

    def test_unexpected_exception_with_continue_on_error_emits_non_fatal(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        rules = (
            BuggyRule(make_rule_reference("STRIKE-001")),
            FakeRule(make_rule_reference("TREND-001"), outcome=RuleOutcome.PASS),
        )
        config = EngineConfiguration(logging_enabled=True, fail_fast=False, continue_on_error=True)

        ExecutionPipeline().run(rules, sample_execution_context, config, diagnostics_sink=sink)

        events = sink.events()
        failure_events = [event for event in events if isinstance(event, ExecutionFailed)]
        assert len(failure_events) == 1
        assert failure_events[0].fatal is False


class TestDeterministicOutput:
    def test_repeated_runs_over_identical_input_produce_identically_shaped_event_sequences(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        def make_rules() -> tuple[FakeRule, ...]:
            return (
                FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS),
                FakeRule(make_rule_reference("TREND-001"), outcome=RuleOutcome.UNKNOWN),
            )

        config = EngineConfiguration(logging_enabled=True)

        first_sink = InMemoryDiagnosticsSink()
        ExecutionPipeline().run(
            make_rules(), sample_execution_context, config, diagnostics_sink=first_sink
        )

        second_sink = InMemoryDiagnosticsSink()
        ExecutionPipeline().run(
            make_rules(), sample_execution_context, config, diagnostics_sink=second_sink
        )

        first_shape = [
            (type(event).__name__, getattr(event, "rule_id", None)) for event in first_sink.events()
        ]
        second_shape = [
            (type(event).__name__, getattr(event, "rule_id", None))
            for event in second_sink.events()
        ]
        assert first_shape == second_shape

    def test_strategy_engine_execution_order_event_is_deterministic_across_runs(
        self, sample_execution_context: RuleExecutionContext
    ) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("TREND-002")))
        registry.register(FakeRule(make_rule_reference("TREND-001")))

        first_sink = InMemoryDiagnosticsSink()
        StrategyEngine(
            registry, EngineConfiguration(logging_enabled=True, diagnostics_sink=first_sink)
        ).run(sample_execution_context)

        second_sink = InMemoryDiagnosticsSink()
        StrategyEngine(
            registry, EngineConfiguration(logging_enabled=True, diagnostics_sink=second_sink)
        ).run(sample_execution_context)

        first_order = next(
            e for e in first_sink.events() if isinstance(e, DependencyResolved)
        ).execution_order
        second_order = next(
            e for e in second_sink.events() if isinstance(e, DependencyResolved)
        ).execution_order
        assert first_order == second_order == ("TREND-001", "TREND-002")

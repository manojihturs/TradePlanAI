"""Tests for RuleRegistry's diagnostic event emission (Milestone 6.4).

A dedicated file, separate from ``test_registry.py`` and
``test_dependency_ordering.py``. No existing test file is modified to
add this.
"""

from __future__ import annotations

import pytest

from trading_engine.diagnostics.events import DependencyMissing, DependencyResolved, RuleRegistered
from trading_engine.diagnostics.sink import InMemoryDiagnosticsSink
from trading_engine.rules.exceptions import CircularDependencyError, UnresolvedDependencyError
from trading_engine.rules.registry import RuleRegistry

from .conftest import FakeRule, make_rule_reference


class TestRegistrationEmitsNoEventByDefault:
    def test_register_without_sink_emits_nothing_observable(self) -> None:
        # No sink passed -> internally routed to NullDiagnosticsSink;
        # nothing to assert except that registration itself still
        # succeeds normally.
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))
        assert "STRIKE-001" in registry


class TestRegistrationEmitsRuleRegistered:
    def test_single_registration_emits_one_event(self) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")), diagnostics_sink=sink)

        assert len(sink) == 1
        event = sink.events()[0]
        assert isinstance(event, RuleRegistered)
        assert event.rule_id == "STRIKE-001"
        assert event.total_registered == 1

    def test_total_registered_increments_across_calls(self) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")), diagnostics_sink=sink)
        registry.register(FakeRule(make_rule_reference("TREND-001")), diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 2
        assert events[0].total_registered == 1
        assert events[1].total_registered == 2

    def test_failed_registration_emits_no_event(self) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")), diagnostics_sink=sink)
        assert len(sink) == 1

        from trading_engine.rules.exceptions import DuplicateRuleError

        with pytest.raises(DuplicateRuleError):
            registry.register(FakeRule(make_rule_reference("STRIKE-001")), diagnostics_sink=sink)

        # Still just the one successful registration's event.
        assert len(sink) == 1


class TestExecutionOrderEmitsDependencyResolved:
    def test_success_emits_one_event_with_the_resolved_order(self) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("TREND-002")))
        registry.register(FakeRule(make_rule_reference("TREND-001")))

        registry.execution_order(diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 1
        assert isinstance(events[0], DependencyResolved)
        assert events[0].execution_order == ("TREND-001", "TREND-002")

    def test_no_sink_means_no_event_but_still_computes_order(self) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))
        order = registry.execution_order()
        assert len(order) == 1


class TestExecutionOrderEmitsDependencyMissing:
    def test_unsupported_dependency_emits_event_before_raising(self) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))

        def resolver(rule_id: str) -> tuple[str, ...]:
            return ("not-a-valid-id",) if rule_id == "STRIKE-001" else ()

        with pytest.raises(UnresolvedDependencyError):
            registry.execution_order(dependency_resolver=resolver, diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 1
        assert isinstance(events[0], DependencyMissing)
        assert events[0].reason == "unsupported dependency"
        assert events[0].rule_id == "STRIKE-001"
        assert events[0].dependency_id == "not-a-valid-id"

    def test_missing_dependency_emits_event_before_raising(self) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("TREND-002")))

        with pytest.raises(UnresolvedDependencyError):
            registry.execution_order(diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 1
        assert isinstance(events[0], DependencyMissing)
        assert events[0].reason == "missing dependency"
        assert events[0].dependency_id == "TREND-001"

    def test_circular_dependency_emits_one_event_per_cyclic_rule(self) -> None:
        sink = InMemoryDiagnosticsSink()
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))
        registry.register(FakeRule(make_rule_reference("TREND-001")))

        def resolver(rule_id: str) -> tuple[str, ...]:
            return {"STRIKE-001": ("TREND-001",), "TREND-001": ("STRIKE-001",)}.get(rule_id, ())

        with pytest.raises(CircularDependencyError):
            registry.execution_order(dependency_resolver=resolver, diagnostics_sink=sink)

        events = sink.events()
        assert len(events) == 2
        assert all(isinstance(event, DependencyMissing) for event in events)
        assert all(event.reason == "circular dependency" for event in events)

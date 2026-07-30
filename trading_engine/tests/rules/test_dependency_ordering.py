"""Tests for RuleRegistry.execution_order()'s dependency-aware ordering.

A dedicated file, separate from ``test_registry.py``, covering the
Milestone 6.3 dependency-ordering scenarios specifically. No existing
test file is modified to add this.
"""

from __future__ import annotations

import pytest

from trading_engine.rules.exceptions import CircularDependencyError, UnresolvedDependencyError
from trading_engine.rules.registry import RuleRegistry

from .conftest import FakeRule, make_rule_reference


class TestEmptyRegistry:
    def test_execution_order_of_empty_registry_is_empty(self) -> None:
        assert RuleRegistry().execution_order() == ()


class TestSingleRule:
    def test_single_rule_with_no_dependencies(self) -> None:
        registry = RuleRegistry()
        rule = FakeRule(make_rule_reference("STRIKE-001"))
        registry.register(rule)
        assert registry.execution_order() == (rule,)


class TestMultipleIndependentRules:
    def test_independent_rules_keep_registration_order(self) -> None:
        # STRIKE-001, REVERSAL-001, OPPONENT-002 have no dependencies
        # on each other per docs/RULE_INDEX.md.
        registry = RuleRegistry()
        strike = FakeRule(make_rule_reference("STRIKE-001"))
        reversal = FakeRule(make_rule_reference("REVERSAL-001"))
        opponent_002 = FakeRule(make_rule_reference("OPPONENT-002"))
        registry.register(strike)
        registry.register(reversal)
        registry.register(opponent_002)
        assert registry.execution_order() == (strike, reversal, opponent_002)


class TestSimpleDependencyChain:
    def test_trend_002_is_ordered_after_trend_001(self) -> None:
        # docs/RULE_INDEX.md: TREND-002 Depends On: TREND-001.
        registry = RuleRegistry()
        trend_002 = FakeRule(make_rule_reference("TREND-002"))
        trend_001 = FakeRule(make_rule_reference("TREND-001"))
        # Registered out of dependency order deliberately.
        registry.register(trend_002)
        registry.register(trend_001)
        order = registry.execution_order()
        assert order.index(trend_001) < order.index(trend_002)


class TestBranchingDependencies:
    def test_opponent_001_ordered_after_all_three_of_its_dependencies(self) -> None:
        # docs/RULE_INDEX.md: OPPONENT-001 Depends On: TREND-001,
        # OPPONENT-002, OPPONENT-003.
        registry = RuleRegistry()
        opponent_001 = FakeRule(make_rule_reference("OPPONENT-001"))
        trend_001 = FakeRule(make_rule_reference("TREND-001"))
        opponent_002 = FakeRule(make_rule_reference("OPPONENT-002"))
        opponent_003 = FakeRule(make_rule_reference("OPPONENT-003"))
        registry.register(opponent_001)
        registry.register(trend_001)
        registry.register(opponent_002)
        registry.register(opponent_003)
        order = registry.execution_order()
        assert order.index(trend_001) < order.index(opponent_001)
        assert order.index(opponent_002) < order.index(opponent_001)
        assert order.index(opponent_003) < order.index(opponent_001)

    def test_trend_003_ordered_after_trend_001_and_opponent_001(self) -> None:
        # docs/RULE_INDEX.md: TREND-003 Depends On: TREND-001, OPPONENT-001.
        # OPPONENT-001 itself further depends on TREND-001,
        # OPPONENT-002, OPPONENT-003 - the full evidenced graph.
        registry = RuleRegistry()
        for rule_id in (
            "TREND-003",
            "OPPONENT-001",
            "TREND-001",
            "OPPONENT-002",
            "OPPONENT-003",
        ):
            registry.register(FakeRule(make_rule_reference(rule_id)))

        order = registry.execution_order()
        index_of = {rule.id(): position for position, rule in enumerate(order)}
        assert index_of["TREND-001"] < index_of["TREND-003"]
        assert index_of["OPPONENT-001"] < index_of["TREND-003"]
        assert index_of["TREND-001"] < index_of["OPPONENT-001"]
        assert index_of["OPPONENT-002"] < index_of["OPPONENT-001"]
        assert index_of["OPPONENT-003"] < index_of["OPPONENT-001"]


class TestDuplicateRegistration:
    def test_duplicate_rule_id_registration_still_rejected(self) -> None:
        # Re-confirms Milestone 4.2's existing DuplicateRuleError
        # behaviour is unaffected by this milestone's changes.
        from trading_engine.rules.exceptions import DuplicateRuleError

        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))
        with pytest.raises(DuplicateRuleError):
            registry.register(FakeRule(make_rule_reference("STRIKE-001")))

    def test_duplicate_entries_within_one_rules_own_dependency_list_are_deduplicated(self) -> None:
        registry = RuleRegistry()
        dependent = FakeRule(make_rule_reference("TREND-002"))
        dependency = FakeRule(make_rule_reference("TREND-001"))
        registry.register(dependent)
        registry.register(dependency)

        def resolver(rule_id: str) -> tuple[str, ...]:
            if rule_id == "TREND-002":
                return ("TREND-001", "TREND-001", "TREND-001")
            return ()

        order = registry.execution_order(dependency_resolver=resolver)
        assert order == (dependency, dependent)


class TestCircularDependencyDetection:
    def test_two_rule_cycle_raises(self) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))
        registry.register(FakeRule(make_rule_reference("TREND-001")))

        def resolver(rule_id: str) -> tuple[str, ...]:
            return {"STRIKE-001": ("TREND-001",), "TREND-001": ("STRIKE-001",)}.get(rule_id, ())

        with pytest.raises(CircularDependencyError):
            registry.execution_order(dependency_resolver=resolver)

    def test_self_referencing_rule_raises(self) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))

        def resolver(rule_id: str) -> tuple[str, ...]:
            return ("STRIKE-001",) if rule_id == "STRIKE-001" else ()

        with pytest.raises(CircularDependencyError, match="STRIKE-001"):
            registry.execution_order(dependency_resolver=resolver)

    def test_three_rule_cycle_lists_all_cyclic_ids(self) -> None:
        registry = RuleRegistry()
        for rule_id in ("STRIKE-001", "TREND-001", "REVERSAL-001"):
            registry.register(FakeRule(make_rule_reference(rule_id)))

        cycle = {
            "STRIKE-001": ("TREND-001",),
            "TREND-001": ("REVERSAL-001",),
            "REVERSAL-001": ("STRIKE-001",),
        }

        with pytest.raises(CircularDependencyError) as excinfo:
            registry.execution_order(dependency_resolver=lambda rid: cycle.get(rid, ()))
        for rule_id in ("STRIKE-001", "TREND-001", "REVERSAL-001"):
            assert rule_id in str(excinfo.value)


class TestDeterministicOrdering:
    def test_repeated_calls_return_identical_order(self) -> None:
        registry = RuleRegistry()
        for rule_id in ("TREND-003", "OPPONENT-001", "TREND-001", "OPPONENT-002", "OPPONENT-003"):
            registry.register(FakeRule(make_rule_reference(rule_id)))

        first = registry.execution_order()
        second = registry.execution_order()
        third = registry.execution_order()
        assert first == second == third

    def test_ties_break_by_registration_order(self) -> None:
        # REVERSAL-001 and OPPONENT-003 are both dependency-free and
        # therefore tied for "ready first" - registration order must
        # decide, deterministically, every time.
        registry = RuleRegistry()
        opponent_003 = FakeRule(make_rule_reference("OPPONENT-003"))
        reversal = FakeRule(make_rule_reference("REVERSAL-001"))
        registry.register(opponent_003)
        registry.register(reversal)
        order = registry.execution_order()
        assert order.index(opponent_003) < order.index(reversal)


class TestUnsupportedDependency:
    def test_malformed_dependency_id_raises(self) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))

        def resolver(rule_id: str) -> tuple[str, ...]:
            return ("not-a-valid-rule-id",) if rule_id == "STRIKE-001" else ()

        with pytest.raises(UnresolvedDependencyError, match="unsupported dependency"):
            registry.execution_order(dependency_resolver=resolver)


class TestMissingDependency:
    def test_well_formed_but_unregistered_dependency_raises(self) -> None:
        # TREND-002 depends on TREND-001 per docs/RULE_INDEX.md, but
        # only TREND-002 is registered here.
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("TREND-002")))
        with pytest.raises(UnresolvedDependencyError, match="missing dependency"):
            registry.execution_order()

    def test_error_message_names_both_the_dependent_and_the_dependency(self) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("TREND-002")))
        with pytest.raises(UnresolvedDependencyError) as excinfo:
            registry.execution_order()
        assert "TREND-002" in str(excinfo.value)
        assert "TREND-001" in str(excinfo.value)


class TestDefaultResolverUsesRealRuleIndexData:
    def test_default_resolver_reflects_docs_rule_index(self) -> None:
        # Registering all 8 confirmed Rule IDs with no custom resolver
        # must succeed and respect every evidenced edge, using the
        # real trading_engine.rules.dependencies.depends_on default.
        registry = RuleRegistry()
        for rule_id in (
            "STRIKE-001",
            "TREND-001",
            "TREND-002",
            "TREND-003",
            "OPPONENT-001",
            "OPPONENT-002",
            "OPPONENT-003",
            "REVERSAL-001",
        ):
            registry.register(FakeRule(make_rule_reference(rule_id)))

        order = registry.execution_order()
        index_of = {rule.id(): position for position, rule in enumerate(order)}
        assert len(order) == 8
        assert index_of["TREND-001"] < index_of["TREND-002"]
        assert index_of["TREND-001"] < index_of["TREND-003"]
        assert index_of["OPPONENT-001"] < index_of["TREND-003"]
        assert index_of["TREND-001"] < index_of["OPPONENT-001"]
        assert index_of["OPPONENT-002"] < index_of["OPPONENT-001"]
        assert index_of["OPPONENT-003"] < index_of["OPPONENT-001"]

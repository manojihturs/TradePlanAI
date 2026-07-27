"""Tests for RuleRegistry, RuleExecutionContext, and the Rule Framework exceptions."""

from __future__ import annotations

from datetime import datetime

import pytest

from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.rule_reference import RuleCategory, RuleReference
from trading_engine.domain.session_state import SessionState
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.exceptions import (
    DuplicateRuleError,
    RuleExecutionError,
    RuleFrameworkError,
    RuleRegistrationError,
)
from trading_engine.rules.registry import RuleRegistry

from .conftest import FakeRule, NonConformingRule, make_rule_reference


class TestExceptionHierarchy:
    def test_all_three_are_rule_framework_errors(self) -> None:
        assert issubclass(DuplicateRuleError, RuleFrameworkError)
        assert issubclass(RuleRegistrationError, RuleFrameworkError)
        assert issubclass(RuleExecutionError, RuleFrameworkError)

    def test_rule_framework_error_is_an_exception(self) -> None:
        assert issubclass(RuleFrameworkError, Exception)

    def test_each_is_raisable_and_catchable_by_base(self) -> None:
        for exc_type in (DuplicateRuleError, RuleRegistrationError, RuleExecutionError):
            with pytest.raises(RuleFrameworkError):
                raise exc_type("message")


class TestRegistryRegistration:
    def test_register_then_get_roundtrips(self, fake_rule: FakeRule) -> None:
        registry = RuleRegistry()
        registry.register(fake_rule)
        assert registry.get("STRIKE-001") is fake_rule

    def test_register_none_raises(self) -> None:
        registry = RuleRegistry()
        with pytest.raises(RuleRegistrationError, match="None"):
            registry.register(None)  # type: ignore[arg-type]

    def test_register_non_conforming_object_raises(self) -> None:
        registry = RuleRegistry()
        with pytest.raises(RuleRegistrationError, match="does not satisfy the Rule protocol"):
            registry.register(NonConformingRule())  # type: ignore[arg-type]

    def test_register_duplicate_rule_id_raises(self, fake_rule: FakeRule) -> None:
        registry = RuleRegistry()
        registry.register(fake_rule)
        duplicate = FakeRule(make_rule_reference("STRIKE-001"))
        with pytest.raises(DuplicateRuleError, match="STRIKE-001"):
            registry.register(duplicate)

    def test_register_different_ids_both_succeed(self) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001")))
        registry.register(FakeRule(make_rule_reference("TREND-001")))
        assert len(registry) == 2


class TestRegistryLookup:
    def test_get_unknown_rule_id_raises(self) -> None:
        registry = RuleRegistry()
        with pytest.raises(RuleRegistrationError, match="No rule is registered"):
            registry.get("TREND-999")

    def test_contains_reflects_registration(self, fake_rule: FakeRule) -> None:
        registry = RuleRegistry()
        assert "STRIKE-001" not in registry
        registry.register(fake_rule)
        assert "STRIKE-001" in registry

    def test_by_category_filters_correctly(self) -> None:
        registry = RuleRegistry()
        strike_rule = FakeRule(make_rule_reference("STRIKE-001"))
        trend_reference = RuleReference(
            rule_id="TREND-001",
            category=RuleCategory.TREND,
            status=strike_rule.reference.status,
            confidence=strike_rule.reference.confidence,
            evidence_count=2,
        )
        trend_rule = FakeRule(trend_reference)
        registry.register(strike_rule)
        registry.register(trend_rule)

        assert registry.by_category(RuleCategory.STRIKE) == (strike_rule,)
        assert registry.by_category(RuleCategory.TREND) == (trend_rule,)
        assert registry.by_category(RuleCategory.OPPONENT) == ()

    def test_all_rules_returns_every_registered_rule(self, fake_rule: FakeRule) -> None:
        registry = RuleRegistry()
        registry.register(fake_rule)
        assert registry.all_rules() == (fake_rule,)


class TestRegistryExecutionOrder:
    def test_execution_order_returns_registration_order(self) -> None:
        registry = RuleRegistry()
        rule_a = FakeRule(make_rule_reference("STRIKE-001"))
        rule_b = FakeRule(make_rule_reference("TREND-001"))
        registry.register(rule_a)
        registry.register(rule_b)
        assert registry.execution_order() == (rule_a, rule_b)

    def test_execution_order_does_not_evaluate_anything(self, fake_rule: FakeRule) -> None:
        registry = RuleRegistry()
        registry.register(fake_rule)
        # No RuleExecutionContext is supplied or required - the
        # registry performs no evaluation, only ordering/lookup.
        result = registry.execution_order()
        assert result == (fake_rule,)


class TestRegistryEdgeCases:
    def test_empty_registry_has_zero_length(self) -> None:
        assert len(RuleRegistry()) == 0

    def test_register_blank_id_raises(self, sample_rule_reference: RuleReference) -> None:
        class BlankIdRule(FakeRule):
            def id(self) -> str:
                return "   "

        registry = RuleRegistry()
        with pytest.raises(RuleRegistrationError, match="must not be blank"):
            registry.register(BlankIdRule(sample_rule_reference))


class TestRuleExecutionContext:
    def test_valid_construction(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        context = RuleExecutionContext(sample_market_context, sample_session_state)
        assert context.market_context is sample_market_context
        assert context.session_state is sample_session_state
        assert context.configuration == {}

    def test_configuration_can_be_supplied(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        context = RuleExecutionContext(
            sample_market_context, sample_session_state, configuration={"lookback": 3}
        )
        assert context.configuration == {"lookback": 3}

    def test_default_clock_returns_a_datetime(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        context = RuleExecutionContext(sample_market_context, sample_session_state)
        assert isinstance(context.clock(), datetime)

    def test_clock_can_be_overridden(
        self,
        sample_market_context: MarketContext,
        sample_session_state: SessionState,
        valid_datetime: datetime,
    ) -> None:
        context = RuleExecutionContext(
            sample_market_context, sample_session_state, clock=lambda: valid_datetime
        )
        assert context.clock() == valid_datetime

    def test_none_market_context_raises(self, sample_session_state: SessionState) -> None:
        with pytest.raises(RuleExecutionError, match="market_context must not be None"):
            RuleExecutionContext(None, sample_session_state)  # type: ignore[arg-type]

    def test_none_session_state_raises(self, sample_market_context: MarketContext) -> None:
        with pytest.raises(RuleExecutionError, match="session_state must not be None"):
            RuleExecutionContext(sample_market_context, None)  # type: ignore[arg-type]

    def test_is_hashable_is_not_required_but_frozen_prevents_reassignment(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        import dataclasses

        context = RuleExecutionContext(sample_market_context, sample_session_state)
        with pytest.raises(dataclasses.FrozenInstanceError):
            context.configuration = {}  # type: ignore[misc]

"""Tests for the Rule protocol and its AbstractRule base."""

from __future__ import annotations

import uuid
from abc import ABC

import pytest

from trading_engine.domain.evidence_reference import EvidenceReference
from trading_engine.domain.rule_reference import RuleReference
from trading_engine.rules.base import AbstractRule
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.exceptions import RuleRegistrationError
from trading_engine.rules.outcome import RuleExecutionResult, RuleOutcome
from trading_engine.rules.protocols import Rule

from .conftest import FakeRule, NonConformingRule, make_rule_reference


class TestRuleProtocolConformance:
    def test_fake_rule_satisfies_protocol(self, fake_rule: FakeRule) -> None:
        assert isinstance(fake_rule, Rule)

    def test_non_conforming_object_does_not_satisfy_protocol(self) -> None:
        assert not isinstance(NonConformingRule(), Rule)

    def test_protocol_checks_method_presence_only(self, fake_rule: FakeRule) -> None:
        # runtime_checkable does not check signatures - only presence.
        assert callable(fake_rule.id)
        assert callable(fake_rule.name)
        assert callable(fake_rule.category)
        assert callable(fake_rule.description)
        assert callable(fake_rule.required_evidence)
        assert callable(fake_rule.evaluate)


class TestAbstractRuleIsAbstract:
    def test_cannot_instantiate_directly(self, sample_rule_reference: RuleReference) -> None:
        assert issubclass(AbstractRule, ABC)
        with pytest.raises(TypeError):
            AbstractRule(sample_rule_reference, "name", "description")  # type: ignore[abstract]


class TestAbstractRuleIdentityMethods:
    def test_id_returns_reference_rule_id(self, fake_rule: FakeRule) -> None:
        assert fake_rule.id() == "STRIKE-001"

    def test_name_returns_supplied_name(self, sample_rule_reference: RuleReference) -> None:
        rule = FakeRule(sample_rule_reference, name="My Rule")
        assert rule.name() == "My Rule"

    def test_category_returns_reference_category(
        self, fake_rule: FakeRule, sample_rule_reference: RuleReference
    ) -> None:
        assert fake_rule.category() == sample_rule_reference.category

    def test_description_returns_supplied_description(
        self, sample_rule_reference: RuleReference
    ) -> None:
        rule = FakeRule(sample_rule_reference, description="Does a thing.")
        assert rule.description() == "Does a thing."

    def test_required_evidence_defaults_to_empty_tuple(self, fake_rule: FakeRule) -> None:
        assert fake_rule.required_evidence() == ()

    def test_required_evidence_can_be_supplied(
        self, sample_rule_reference: RuleReference, sample_evidence_reference: EvidenceReference
    ) -> None:
        class RuleWithEvidence(AbstractRule):
            def evaluate(self, context: RuleExecutionContext) -> RuleExecutionResult:
                return RuleExecutionResult(uuid.uuid4(), self.reference, RuleOutcome.UNKNOWN, "x")

        rule = RuleWithEvidence(
            sample_rule_reference, "n", "d", required_evidence=(sample_evidence_reference,)
        )
        assert rule.required_evidence() == (sample_evidence_reference,)


class TestAbstractRuleInvalidConstructorValues:
    def test_none_reference_raises(self) -> None:
        with pytest.raises(RuleRegistrationError, match="reference must not be None"):
            FakeRule(reference=None, name="n", description="d")  # type: ignore[arg-type]

    def test_blank_name_raises(self, sample_rule_reference: RuleReference) -> None:
        with pytest.raises(RuleRegistrationError, match="name must not be blank"):
            FakeRule(sample_rule_reference, name="   ")

    def test_blank_description_raises(self, sample_rule_reference: RuleReference) -> None:
        with pytest.raises(RuleRegistrationError, match="description must not be blank"):
            FakeRule(sample_rule_reference, description="")


class TestAbstractRuleEvaluate:
    def test_evaluate_returns_execution_result(
        self, fake_rule: FakeRule, sample_execution_context: RuleExecutionContext
    ) -> None:
        result = fake_rule.evaluate(sample_execution_context)
        assert isinstance(result, RuleExecutionResult)
        assert result.rule is fake_rule.reference

    def test_evaluate_outcome_is_configurable(
        self, sample_rule_reference: RuleReference, sample_execution_context: RuleExecutionContext
    ) -> None:
        rule = FakeRule(sample_rule_reference, outcome=RuleOutcome.PASS)
        assert rule.evaluate(sample_execution_context).outcome is RuleOutcome.PASS


class TestEdgeCases:
    def test_two_fake_rules_with_different_ids_are_independent(self) -> None:
        rule_a = FakeRule(make_rule_reference("STRIKE-001"))
        rule_b = FakeRule(make_rule_reference("TREND-001"))
        assert rule_a.id() != rule_b.id()

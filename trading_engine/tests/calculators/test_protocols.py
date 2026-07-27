"""Tests for the Calculator protocol, AbstractCalculator, and the five placeholder calculators."""

from __future__ import annotations

from abc import ABC

import pytest

from trading_engine.calculators.base import AbstractCalculator
from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.edge_calculator import EdgeCalculator
from trading_engine.calculators.exceptions import CalculatorRegistrationError
from trading_engine.calculators.opponent_calculator import OpponentCalculator
from trading_engine.calculators.protocols import Calculator
from trading_engine.calculators.reversal_calculator import ReversalCalculator
from trading_engine.calculators.strike_calculator import StrikeCalculator
from trading_engine.calculators.trend_calculator import TrendCalculator
from trading_engine.domain.rule_reference import RuleReference

from .conftest import FakeCalculator, NonConformingCalculator

_PLACEHOLDER_CALCULATORS = (
    (StrikeCalculator, "STRIKE-001-CALCULATOR", "STRIKE-001"),
    (TrendCalculator, "TREND-001-CALCULATOR", "TREND-001"),
    (OpponentCalculator, "OPPONENT-001-CALCULATOR", "OPPONENT-001"),
    (ReversalCalculator, "REVERSAL-001-CALCULATOR", "REVERSAL-001"),
    (EdgeCalculator, "TREND-003-CALCULATOR", "TREND-003"),
)


class TestCalculatorProtocolConformance:
    def test_fake_calculator_satisfies_protocol(self) -> None:
        assert isinstance(FakeCalculator(), Calculator)

    def test_non_conforming_object_does_not_satisfy_protocol(self) -> None:
        assert not isinstance(NonConformingCalculator(), Calculator)

    def test_every_placeholder_calculator_satisfies_protocol(self) -> None:
        for calculator_cls, _, _ in _PLACEHOLDER_CALCULATORS:
            assert isinstance(calculator_cls(), Calculator)


class TestAbstractCalculatorIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        assert issubclass(AbstractCalculator, ABC)
        with pytest.raises(TypeError):
            AbstractCalculator("X", "name", "description")  # type: ignore[abstract]


class TestAbstractCalculatorIdentityMethods:
    def test_id_returns_calculator_id(self) -> None:
        calculator = FakeCalculator(calculator_id="ABC-123")
        assert calculator.id() == "ABC-123"

    def test_name_returns_supplied_name(self) -> None:
        calculator = FakeCalculator(name="My Calculator")
        assert calculator.name() == "My Calculator"

    def test_description_returns_supplied_description(self) -> None:
        calculator = FakeCalculator(description="Does a thing.")
        assert calculator.description() == "Does a thing."

    def test_supported_rules_defaults_to_empty_tuple(self) -> None:
        assert FakeCalculator().supported_rules() == ()


class TestAbstractCalculatorInvalidConstructorValues:
    def test_blank_calculator_id_raises(self) -> None:
        with pytest.raises(CalculatorRegistrationError, match="calculator_id must not be blank"):
            FakeCalculator(calculator_id="   ")

    def test_blank_name_raises(self) -> None:
        with pytest.raises(CalculatorRegistrationError, match="name must not be blank"):
            FakeCalculator(name="")

    def test_blank_description_raises(self) -> None:
        with pytest.raises(CalculatorRegistrationError, match="description must not be blank"):
            FakeCalculator(description="   ")


class TestFakeCalculatorCalculate:
    def test_calculate_returns_result(self, sample_calculation_context: CalculationContext) -> None:
        result = FakeCalculator().calculate(sample_calculation_context)
        assert result.calculator_id == "FAKE-CALCULATOR"


class TestPlaceholderCalculators:
    @pytest.mark.parametrize("calculator_cls,calculator_id,rule_id", _PLACEHOLDER_CALCULATORS)
    def test_identity_methods(
        self, calculator_cls: type[AbstractCalculator], calculator_id: str, rule_id: str
    ) -> None:
        calculator = calculator_cls()
        assert calculator.id() == calculator_id
        assert calculator.name()
        assert calculator.description()

    @pytest.mark.parametrize("calculator_cls,calculator_id,rule_id", _PLACEHOLDER_CALCULATORS)
    def test_supported_rules_cite_the_expected_rule_id(
        self, calculator_cls: type[AbstractCalculator], calculator_id: str, rule_id: str
    ) -> None:
        calculator = calculator_cls()
        rule_ids = {reference.rule_id for reference in calculator.supported_rules()}
        assert rule_id in rule_ids
        for reference in calculator.supported_rules():
            assert isinstance(reference, RuleReference)

    @pytest.mark.parametrize("calculator_cls,calculator_id,rule_id", _PLACEHOLDER_CALCULATORS)
    def test_calculate_raises_not_implemented_referencing_rule_id(
        self,
        calculator_cls: type[AbstractCalculator],
        calculator_id: str,
        rule_id: str,
        sample_calculation_context: CalculationContext,
    ) -> None:
        calculator = calculator_cls()
        with pytest.raises(NotImplementedError, match=rule_id):
            calculator.calculate(sample_calculation_context)


class TestEdgeCases:
    def test_two_placeholder_calculators_have_distinct_ids(self) -> None:
        ids = {calculator_cls().id() for calculator_cls, _, _ in _PLACEHOLDER_CALCULATORS}
        assert len(ids) == len(_PLACEHOLDER_CALCULATORS)

"""Tests for StrikeCalculator.

A dedicated file, matching the structure established for
``test_weekly_future_calculator.py`` (Milestone 6.1), added because
Milestone 6.2's consistency review found this calculator - like the
other four pre-existing placeholders - was previously covered only by
``test_protocols.py``'s generic parametrized checks, with no
calculator-specific registration/duplicate-registration/never-returns
coverage. No existing test file is modified to add this.
"""

from __future__ import annotations

import pytest

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.exceptions import DuplicateCalculatorError
from trading_engine.calculators.protocols import Calculator
from trading_engine.calculators.registry import CalculatorRegistry
from trading_engine.calculators.strike_calculator import StrikeCalculator
from trading_engine.domain.rule_reference import RuleReference


class TestProtocolConformance:
    def test_satisfies_calculator_protocol(self) -> None:
        assert isinstance(StrikeCalculator(), Calculator)


class TestIdentityMethods:
    def test_id(self) -> None:
        assert StrikeCalculator().id() == "STRIKE-001-CALCULATOR"

    def test_name(self) -> None:
        assert StrikeCalculator().name() == "Strike Calculator"

    def test_description_is_non_blank(self) -> None:
        assert StrikeCalculator().description()

    def test_supported_rules_cites_strike_001(self) -> None:
        references = StrikeCalculator().supported_rules()
        rule_ids = {reference.rule_id for reference in references}
        assert rule_ids == {"STRIKE-001"}
        for reference in references:
            assert isinstance(reference, RuleReference)


class TestRegistration:
    def test_registers_successfully(self) -> None:
        registry = CalculatorRegistry()
        registry.register(StrikeCalculator())
        assert "STRIKE-001-CALCULATOR" in registry
        assert len(registry) == 1

    def test_get_returns_the_registered_instance(self) -> None:
        registry = CalculatorRegistry()
        calculator = StrikeCalculator()
        registry.register(calculator)
        assert registry.get("STRIKE-001-CALCULATOR") is calculator

    def test_duplicate_registration_raises(self) -> None:
        registry = CalculatorRegistry()
        registry.register(StrikeCalculator())
        with pytest.raises(DuplicateCalculatorError, match="STRIKE-001-CALCULATOR"):
            registry.register(StrikeCalculator())


class TestConstruction:
    def test_construction_requires_no_arguments(self) -> None:
        calculator = StrikeCalculator()
        assert calculator is not None

    def test_two_instances_are_independent_but_equal_in_identity(self) -> None:
        a = StrikeCalculator()
        b = StrikeCalculator()
        assert a is not b
        assert a.id() == b.id()


class TestCalculateRaisesNotImplemented:
    def test_calculate_raises_not_implemented_error(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError):
            StrikeCalculator().calculate(sample_calculation_context)

    def test_not_implemented_error_references_strike_001(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError, match="STRIKE-001"):
            StrikeCalculator().calculate(sample_calculation_context)

    def test_calculate_performs_no_business_mathematics(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        calculator = StrikeCalculator()
        try:
            calculator.calculate(sample_calculation_context)
        except NotImplementedError:
            pass
        else:
            pytest.fail("calculate() must raise NotImplementedError, not return a result.")

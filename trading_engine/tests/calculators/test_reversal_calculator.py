"""Tests for ReversalCalculator.

See ``test_strike_calculator.py``'s module docstring for why this
dedicated file exists (Milestone 6.2 consistency review).
"""

from __future__ import annotations

import pytest

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.exceptions import DuplicateCalculatorError
from trading_engine.calculators.protocols import Calculator
from trading_engine.calculators.registry import CalculatorRegistry
from trading_engine.calculators.reversal_calculator import ReversalCalculator
from trading_engine.domain.rule_reference import RuleReference


class TestProtocolConformance:
    def test_satisfies_calculator_protocol(self) -> None:
        assert isinstance(ReversalCalculator(), Calculator)


class TestIdentityMethods:
    def test_id(self) -> None:
        assert ReversalCalculator().id() == "REVERSAL-001-CALCULATOR"

    def test_name(self) -> None:
        assert ReversalCalculator().name() == "Reversal Calculator"

    def test_description_is_non_blank(self) -> None:
        assert ReversalCalculator().description()

    def test_supported_rules_cites_reversal_001(self) -> None:
        references = ReversalCalculator().supported_rules()
        rule_ids = {reference.rule_id for reference in references}
        assert rule_ids == {"REVERSAL-001"}
        for reference in references:
            assert isinstance(reference, RuleReference)


class TestRegistration:
    def test_registers_successfully(self) -> None:
        registry = CalculatorRegistry()
        registry.register(ReversalCalculator())
        assert "REVERSAL-001-CALCULATOR" in registry
        assert len(registry) == 1

    def test_get_returns_the_registered_instance(self) -> None:
        registry = CalculatorRegistry()
        calculator = ReversalCalculator()
        registry.register(calculator)
        assert registry.get("REVERSAL-001-CALCULATOR") is calculator

    def test_duplicate_registration_raises(self) -> None:
        registry = CalculatorRegistry()
        registry.register(ReversalCalculator())
        with pytest.raises(DuplicateCalculatorError, match="REVERSAL-001-CALCULATOR"):
            registry.register(ReversalCalculator())


class TestConstruction:
    def test_construction_requires_no_arguments(self) -> None:
        calculator = ReversalCalculator()
        assert calculator is not None

    def test_two_instances_are_independent_but_equal_in_identity(self) -> None:
        a = ReversalCalculator()
        b = ReversalCalculator()
        assert a is not b
        assert a.id() == b.id()


class TestCalculateRaisesNotImplemented:
    def test_calculate_raises_not_implemented_error(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError):
            ReversalCalculator().calculate(sample_calculation_context)

    def test_not_implemented_error_references_reversal_001(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError, match="REVERSAL-001"):
            ReversalCalculator().calculate(sample_calculation_context)

    def test_calculate_performs_no_business_mathematics(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        calculator = ReversalCalculator()
        try:
            calculator.calculate(sample_calculation_context)
        except NotImplementedError:
            pass
        else:
            pytest.fail("calculate() must raise NotImplementedError, not return a result.")

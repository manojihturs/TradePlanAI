"""Tests for TrendCalculator.

See ``test_strike_calculator.py``'s module docstring for why this
dedicated file exists (Milestone 6.2 consistency review).
"""

from __future__ import annotations

import pytest

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.exceptions import DuplicateCalculatorError
from trading_engine.calculators.protocols import Calculator
from trading_engine.calculators.registry import CalculatorRegistry
from trading_engine.calculators.trend_calculator import TrendCalculator
from trading_engine.domain.rule_reference import RuleReference


class TestProtocolConformance:
    def test_satisfies_calculator_protocol(self) -> None:
        assert isinstance(TrendCalculator(), Calculator)


class TestIdentityMethods:
    def test_id(self) -> None:
        assert TrendCalculator().id() == "TREND-001-CALCULATOR"

    def test_name(self) -> None:
        assert TrendCalculator().name() == "Trend Calculator"

    def test_description_is_non_blank(self) -> None:
        assert TrendCalculator().description()

    def test_supported_rules_cites_trend_001_and_002(self) -> None:
        references = TrendCalculator().supported_rules()
        rule_ids = {reference.rule_id for reference in references}
        assert rule_ids == {"TREND-001", "TREND-002"}
        for reference in references:
            assert isinstance(reference, RuleReference)


class TestRegistration:
    def test_registers_successfully(self) -> None:
        registry = CalculatorRegistry()
        registry.register(TrendCalculator())
        assert "TREND-001-CALCULATOR" in registry
        assert len(registry) == 1

    def test_get_returns_the_registered_instance(self) -> None:
        registry = CalculatorRegistry()
        calculator = TrendCalculator()
        registry.register(calculator)
        assert registry.get("TREND-001-CALCULATOR") is calculator

    def test_duplicate_registration_raises(self) -> None:
        registry = CalculatorRegistry()
        registry.register(TrendCalculator())
        with pytest.raises(DuplicateCalculatorError, match="TREND-001-CALCULATOR"):
            registry.register(TrendCalculator())


class TestConstruction:
    def test_construction_requires_no_arguments(self) -> None:
        calculator = TrendCalculator()
        assert calculator is not None

    def test_two_instances_are_independent_but_equal_in_identity(self) -> None:
        a = TrendCalculator()
        b = TrendCalculator()
        assert a is not b
        assert a.id() == b.id()


class TestCalculateRaisesNotImplemented:
    def test_calculate_raises_not_implemented_error(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError):
            TrendCalculator().calculate(sample_calculation_context)

    def test_not_implemented_error_references_trend_001(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError, match="TREND-001"):
            TrendCalculator().calculate(sample_calculation_context)

    def test_calculate_performs_no_business_mathematics(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        calculator = TrendCalculator()
        try:
            calculator.calculate(sample_calculation_context)
        except NotImplementedError:
            pass
        else:
            pytest.fail("calculate() must raise NotImplementedError, not return a result.")

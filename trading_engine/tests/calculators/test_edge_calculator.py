"""Tests for EdgeCalculator.

See ``test_strike_calculator.py``'s module docstring for why this
dedicated file exists (Milestone 6.2 consistency review).
"""

from __future__ import annotations

import pytest

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.edge_calculator import EdgeCalculator
from trading_engine.calculators.exceptions import DuplicateCalculatorError
from trading_engine.calculators.protocols import Calculator
from trading_engine.calculators.registry import CalculatorRegistry
from trading_engine.domain.rule_reference import RuleReference


class TestProtocolConformance:
    def test_satisfies_calculator_protocol(self) -> None:
        assert isinstance(EdgeCalculator(), Calculator)


class TestIdentityMethods:
    def test_id(self) -> None:
        assert EdgeCalculator().id() == "TREND-003-CALCULATOR"

    def test_name(self) -> None:
        assert EdgeCalculator().name() == "Edge Calculator"

    def test_description_is_non_blank(self) -> None:
        assert EdgeCalculator().description()

    def test_supported_rules_cites_trend_003(self) -> None:
        references = EdgeCalculator().supported_rules()
        rule_ids = {reference.rule_id for reference in references}
        assert rule_ids == {"TREND-003"}
        for reference in references:
            assert isinstance(reference, RuleReference)


class TestRegistration:
    def test_registers_successfully(self) -> None:
        registry = CalculatorRegistry()
        registry.register(EdgeCalculator())
        assert "TREND-003-CALCULATOR" in registry
        assert len(registry) == 1

    def test_get_returns_the_registered_instance(self) -> None:
        registry = CalculatorRegistry()
        calculator = EdgeCalculator()
        registry.register(calculator)
        assert registry.get("TREND-003-CALCULATOR") is calculator

    def test_duplicate_registration_raises(self) -> None:
        registry = CalculatorRegistry()
        registry.register(EdgeCalculator())
        with pytest.raises(DuplicateCalculatorError, match="TREND-003-CALCULATOR"):
            registry.register(EdgeCalculator())


class TestConstruction:
    def test_construction_requires_no_arguments(self) -> None:
        calculator = EdgeCalculator()
        assert calculator is not None

    def test_two_instances_are_independent_but_equal_in_identity(self) -> None:
        a = EdgeCalculator()
        b = EdgeCalculator()
        assert a is not b
        assert a.id() == b.id()


class TestCalculateRaisesNotImplemented:
    def test_calculate_raises_not_implemented_error(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError):
            EdgeCalculator().calculate(sample_calculation_context)

    def test_not_implemented_error_references_trend_003(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError, match="TREND-003"):
            EdgeCalculator().calculate(sample_calculation_context)

    def test_calculate_performs_no_business_mathematics(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        calculator = EdgeCalculator()
        try:
            calculator.calculate(sample_calculation_context)
        except NotImplementedError:
            pass
        else:
            pytest.fail("calculate() must raise NotImplementedError, not return a result.")


class TestEdgeCases:
    def test_calculator_id_reflects_supported_rule_not_edge_itself(self) -> None:
        # Per docs/architecture/DOMAIN_ARCHITECTURE.md, Edge is
        # modeled as a condition over two TrendPoints, not a
        # standalone entity/rule - this calculator's ID cites the
        # rule it supports (TREND-003), not an "EDGE-*" identifier.
        assert EdgeCalculator().id() == "TREND-003-CALCULATOR"
        assert "EDGE" not in EdgeCalculator().id()

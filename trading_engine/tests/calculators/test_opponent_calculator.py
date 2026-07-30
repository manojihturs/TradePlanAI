"""Tests for OpponentCalculator.

See ``test_strike_calculator.py``'s module docstring for why this
dedicated file exists (Milestone 6.2 consistency review).
"""

from __future__ import annotations

import pytest

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.exceptions import DuplicateCalculatorError
from trading_engine.calculators.opponent_calculator import OpponentCalculator
from trading_engine.calculators.protocols import Calculator
from trading_engine.calculators.registry import CalculatorRegistry
from trading_engine.domain.rule_reference import RuleReference


class TestProtocolConformance:
    def test_satisfies_calculator_protocol(self) -> None:
        assert isinstance(OpponentCalculator(), Calculator)


class TestIdentityMethods:
    def test_id(self) -> None:
        assert OpponentCalculator().id() == "OPPONENT-001-CALCULATOR"

    def test_name(self) -> None:
        assert OpponentCalculator().name() == "Opponent Calculator"

    def test_description_is_non_blank(self) -> None:
        assert OpponentCalculator().description()

    def test_supported_rules_cites_all_three_opponent_rules(self) -> None:
        references = OpponentCalculator().supported_rules()
        rule_ids = {reference.rule_id for reference in references}
        assert rule_ids == {"OPPONENT-001", "OPPONENT-002", "OPPONENT-003"}
        for reference in references:
            assert isinstance(reference, RuleReference)


class TestRegistration:
    def test_registers_successfully(self) -> None:
        registry = CalculatorRegistry()
        registry.register(OpponentCalculator())
        assert "OPPONENT-001-CALCULATOR" in registry
        assert len(registry) == 1

    def test_get_returns_the_registered_instance(self) -> None:
        registry = CalculatorRegistry()
        calculator = OpponentCalculator()
        registry.register(calculator)
        assert registry.get("OPPONENT-001-CALCULATOR") is calculator

    def test_duplicate_registration_raises(self) -> None:
        registry = CalculatorRegistry()
        registry.register(OpponentCalculator())
        with pytest.raises(DuplicateCalculatorError, match="OPPONENT-001-CALCULATOR"):
            registry.register(OpponentCalculator())


class TestConstruction:
    def test_construction_requires_no_arguments(self) -> None:
        calculator = OpponentCalculator()
        assert calculator is not None

    def test_two_instances_are_independent_but_equal_in_identity(self) -> None:
        a = OpponentCalculator()
        b = OpponentCalculator()
        assert a is not b
        assert a.id() == b.id()


class TestCalculateRaisesNotImplemented:
    def test_calculate_raises_not_implemented_error(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError):
            OpponentCalculator().calculate(sample_calculation_context)

    def test_not_implemented_error_references_opponent_001(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError, match="OPPONENT-001"):
            OpponentCalculator().calculate(sample_calculation_context)

    def test_calculate_performs_no_business_mathematics(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        calculator = OpponentCalculator()
        try:
            calculator.calculate(sample_calculation_context)
        except NotImplementedError:
            pass
        else:
            pytest.fail("calculate() must raise NotImplementedError, not return a result.")


class TestEdgeCases:
    def test_includes_awaiting_evidence_placeholder_rules(self) -> None:
        # OPPONENT-002/003 are Awaiting-Evidence placeholders (Evidence
        # Count 0) per docs/RULE_INDEX.md - this calculator's
        # supported_rules() still cites them as co-dependencies of
        # OPPONENT-001, without asserting they have any resolved
        # behaviour.
        references = OpponentCalculator().supported_rules()
        by_id = {reference.rule_id: reference for reference in references}
        assert by_id["OPPONENT-002"].evidence_count == 0
        assert by_id["OPPONENT-003"].evidence_count == 0

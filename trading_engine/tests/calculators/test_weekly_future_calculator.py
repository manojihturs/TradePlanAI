"""Tests for WeeklyFutureCalculator.

A dedicated file rather than an addition to ``test_protocols.py``'s
existing ``_PLACEHOLDER_CALCULATORS`` parametrization, so that no
existing test file needs modification for this milestone.
"""

from __future__ import annotations

import pytest

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.protocols import Calculator
from trading_engine.calculators.registry import CalculatorRegistry
from trading_engine.calculators.weekly_future_calculator import WeeklyFutureCalculator
from trading_engine.domain.rule_reference import RuleReference


class TestProtocolConformance:
    def test_satisfies_calculator_protocol(self) -> None:
        assert isinstance(WeeklyFutureCalculator(), Calculator)


class TestIdentityMethods:
    def test_id(self) -> None:
        assert WeeklyFutureCalculator().id() == "WEEKLY-FUTURE-CALCULATOR"

    def test_name(self) -> None:
        assert WeeklyFutureCalculator().name() == "Weekly Future Calculator"

    def test_description_is_non_blank(self) -> None:
        assert WeeklyFutureCalculator().description()

    def test_supported_rules_cites_strike_001(self) -> None:
        references = WeeklyFutureCalculator().supported_rules()
        rule_ids = {reference.rule_id for reference in references}
        assert rule_ids == {"STRIKE-001"}
        for reference in references:
            assert isinstance(reference, RuleReference)


class TestRegistration:
    def test_registers_successfully_without_conflicting_with_existing_calculators(self) -> None:
        # Distinct calculator_id from StrikeCalculator's
        # "STRIKE-001-CALCULATOR", even though both cite STRIKE-001 as
        # a supported rule - registration keys on calculator_id, not
        # supported_rules, so no DuplicateCalculatorError should occur.
        registry = CalculatorRegistry()
        registry.register(WeeklyFutureCalculator())
        assert "WEEKLY-FUTURE-CALCULATOR" in registry
        assert len(registry) == 1

    def test_get_returns_the_registered_instance(self) -> None:
        registry = CalculatorRegistry()
        calculator = WeeklyFutureCalculator()
        registry.register(calculator)
        assert registry.get("WEEKLY-FUTURE-CALCULATOR") is calculator


class TestConstruction:
    def test_construction_requires_no_arguments(self) -> None:
        # Unlike FakeCalculator (a test double with configurable
        # fields), every real placeholder calculator - including this
        # one - takes no constructor arguments, per the pattern
        # established in Milestone 4.3A.
        calculator = WeeklyFutureCalculator()
        assert calculator is not None

    def test_two_instances_are_independent_but_equal_in_identity(self) -> None:
        a = WeeklyFutureCalculator()
        b = WeeklyFutureCalculator()
        assert a is not b
        assert a.id() == b.id()


class TestCalculateRaisesNotImplemented:
    def test_calculate_raises_not_implemented_error(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError):
            WeeklyFutureCalculator().calculate(sample_calculation_context)

    def test_not_implemented_error_references_strike_001(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError, match="STRIKE-001"):
            WeeklyFutureCalculator().calculate(sample_calculation_context)

    def test_not_implemented_error_mentions_weekly_future(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        with pytest.raises(NotImplementedError, match="Weekly Future"):
            WeeklyFutureCalculator().calculate(sample_calculation_context)

    def test_calculate_performs_no_business_mathematics(
        self, sample_calculation_context: CalculationContext
    ) -> None:
        # Structural guard: calculate() must not return a
        # CalculationResult at all in this milestone - it must always
        # raise, never silently succeed with a guessed value.
        calculator = WeeklyFutureCalculator()
        try:
            calculator.calculate(sample_calculation_context)
        except NotImplementedError:
            pass
        else:
            pytest.fail("calculate() must raise NotImplementedError, not return a result.")


class TestEdgeCases:
    def test_calculator_id_distinct_from_strike_calculator_id(self) -> None:
        # Both calculators cite STRIKE-001 as a supported rule, but
        # must have distinct Calculator IDs (registry identity is
        # calculator_id, not supported_rules).
        assert WeeklyFutureCalculator().id() != "STRIKE-001-CALCULATOR"

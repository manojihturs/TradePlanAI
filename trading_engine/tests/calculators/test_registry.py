"""Tests for CalculatorRegistry and the Calculator Framework exceptions."""

from __future__ import annotations

import pytest

from trading_engine.calculators.exceptions import (
    CalculationError,
    CalculatorFrameworkError,
    CalculatorRegistrationError,
    DuplicateCalculatorError,
)
from trading_engine.calculators.registry import CalculatorRegistry

from .conftest import FakeCalculator, NonConformingCalculator


class TestExceptionHierarchy:
    def test_all_three_are_calculator_framework_errors(self) -> None:
        assert issubclass(DuplicateCalculatorError, CalculatorFrameworkError)
        assert issubclass(CalculatorRegistrationError, CalculatorFrameworkError)
        assert issubclass(CalculationError, CalculatorFrameworkError)

    def test_calculator_framework_error_is_an_exception(self) -> None:
        assert issubclass(CalculatorFrameworkError, Exception)

    def test_each_is_raisable_and_catchable_by_base(self) -> None:
        for exc_type in (DuplicateCalculatorError, CalculatorRegistrationError, CalculationError):
            with pytest.raises(CalculatorFrameworkError):
                raise exc_type("message")


class TestRegistration:
    def test_register_then_get_roundtrips(self) -> None:
        registry = CalculatorRegistry()
        calculator = FakeCalculator(calculator_id="X")
        registry.register(calculator)
        assert registry.get("X") is calculator

    def test_register_none_raises(self) -> None:
        registry = CalculatorRegistry()
        with pytest.raises(CalculatorRegistrationError, match="None"):
            registry.register(None)  # type: ignore[arg-type]

    def test_register_non_conforming_object_raises(self) -> None:
        registry = CalculatorRegistry()
        with pytest.raises(
            CalculatorRegistrationError, match="does not satisfy the Calculator protocol"
        ):
            registry.register(NonConformingCalculator())  # type: ignore[arg-type]

    def test_register_duplicate_id_raises(self) -> None:
        registry = CalculatorRegistry()
        registry.register(FakeCalculator(calculator_id="X"))
        with pytest.raises(DuplicateCalculatorError, match="X"):
            registry.register(FakeCalculator(calculator_id="X"))

    def test_register_different_ids_both_succeed(self) -> None:
        registry = CalculatorRegistry()
        registry.register(FakeCalculator(calculator_id="A"))
        registry.register(FakeCalculator(calculator_id="B"))
        assert len(registry) == 2

    def test_register_blank_id_raises(self) -> None:
        class BlankIdCalculator(FakeCalculator):
            def id(self) -> str:
                return "   "

        registry = CalculatorRegistry()
        with pytest.raises(CalculatorRegistrationError, match="must not be blank"):
            registry.register(BlankIdCalculator())


class TestLookup:
    def test_get_unknown_id_raises(self) -> None:
        registry = CalculatorRegistry()
        with pytest.raises(CalculatorRegistrationError, match="No calculator is registered"):
            registry.get("UNKNOWN")

    def test_contains_reflects_registration(self) -> None:
        registry = CalculatorRegistry()
        assert "X" not in registry
        registry.register(FakeCalculator(calculator_id="X"))
        assert "X" in registry


class TestListCalculators:
    def test_list_calculators_returns_every_registered_calculator(self) -> None:
        registry = CalculatorRegistry()
        a = FakeCalculator(calculator_id="A")
        b = FakeCalculator(calculator_id="B")
        registry.register(a)
        registry.register(b)
        assert registry.list_calculators() == (a, b)

    def test_empty_registry_lists_nothing(self) -> None:
        assert CalculatorRegistry().list_calculators() == ()


class TestEdgeCases:
    def test_empty_registry_has_zero_length(self) -> None:
        assert len(CalculatorRegistry()) == 0

    def test_registry_has_no_execution_ordering_method(self) -> None:
        # Explicit per Milestone 4.3A: "No execution ordering." -
        # unlike RuleRegistry, CalculatorRegistry defines no
        # execution_order()/similar method.
        assert not hasattr(CalculatorRegistry(), "execution_order")

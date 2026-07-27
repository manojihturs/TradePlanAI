"""CalculatorRegistry: the Calculator ID -> calculator implementation lookup.

Traceability notes
-------------------
Mirrors :class:`trading_engine.rules.registry.RuleRegistry` at the
mathematical layer, minus execution ordering - per the Milestone 4.3A
instruction, the Calculator Registry's responsibilities are strictly
"Register calculators / Reject duplicate IDs / Lookup calculators /
List calculators. No execution ordering." Nothing about *when* or in
what sequence calculators run is decided here, unlike
``RuleRegistry.execution_order()`` - no such ordering concept exists
for calculators in this milestone.
"""

from __future__ import annotations

from trading_engine.calculators.exceptions import (
    CalculatorRegistrationError,
    DuplicateCalculatorError,
)
from trading_engine.calculators.protocols import Calculator


class CalculatorRegistry:
    """A Calculator ID -> Calculator lookup, with duplicate-ID
    rejection.

    Rule References
        None directly - a generic container for any object satisfying
        :class:`~trading_engine.calculators.protocols.Calculator`.
    """

    def __init__(self) -> None:
        self._calculators: dict[str, Calculator] = {}

    def register(self, calculator: Calculator) -> None:
        """Register a calculator under its own ``id()``.

        Raises:
            CalculatorRegistrationError: if ``calculator`` is ``None``,
                does not structurally satisfy
                :class:`~trading_engine.calculators.protocols.Calculator`,
                or its ``id()`` is blank.
            DuplicateCalculatorError: if a calculator is already
                registered under the same Calculator ID.
        """
        if calculator is None:
            raise CalculatorRegistrationError("Cannot register a calculator that is None.")

        if not isinstance(calculator, Calculator):
            raise CalculatorRegistrationError(
                f"{calculator!r} does not satisfy the Calculator protocol "
                "(missing one or more required methods)."
            )

        calculator_id = calculator.id()
        if not calculator_id or not calculator_id.strip():
            raise CalculatorRegistrationError("A calculator's id() must not be blank.")

        if calculator_id in self._calculators:
            raise DuplicateCalculatorError(
                f"Calculator ID {calculator_id!r} is already registered."
            )

        self._calculators[calculator_id] = calculator

    def get(self, calculator_id: str) -> Calculator:
        """Look up a registered calculator by its exact Calculator ID.

        Raises:
            CalculatorRegistrationError: if no calculator is registered
                under ``calculator_id``.
        """
        try:
            return self._calculators[calculator_id]
        except KeyError as exc:
            raise CalculatorRegistrationError(
                f"No calculator is registered under Calculator ID {calculator_id!r}."
            ) from exc

    def list_calculators(self) -> tuple[Calculator, ...]:
        """Return every registered calculator, in registration order."""
        return tuple(self._calculators.values())

    def __len__(self) -> int:
        return len(self._calculators)

    def __contains__(self, calculator_id: str) -> bool:
        return calculator_id in self._calculators

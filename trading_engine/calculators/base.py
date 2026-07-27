"""AbstractCalculator: an optional shared base for concrete calculators.

Traceability notes
-------------------
Mirrors :mod:`trading_engine.rules.base`'s ``AbstractRule`` at the
mathematical layer: :class:`~trading_engine.calculators.protocols.Calculator`
alone is a sufficient contract, but offers no shared implementation -
this class removes the identity-method boilerplate every placeholder
calculator in this milestone would otherwise repeat. Not required by
the framework - a class satisfying
:class:`~trading_engine.calculators.protocols.Calculator` structurally,
without inheriting from ``AbstractCalculator``, is equally valid.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.exceptions import CalculatorRegistrationError
from trading_engine.calculators.result import CalculationResult
from trading_engine.domain.rule_reference import RuleReference


class AbstractCalculator(ABC):
    """A convenience base class implementing the identity portion of
    the :class:`~trading_engine.calculators.protocols.Calculator`
    contract.

    Stores a caller-supplied ``calculator_id``/``name``/``description``
    and the RuleReference(s) this calculator's (future) output would
    support. Subclasses need only implement :meth:`calculate`.

    Rule References
        None directly - a generic base usable by any calculator. See
        each concrete subclass (e.g.
        :class:`~trading_engine.calculators.strike_calculator.StrikeCalculator`)
        for its own Rule References.

    Attributes:
        calculator_id: This calculator's unique identifier.
    """

    def __init__(
        self,
        calculator_id: str,
        name: str,
        description: str,
        supported_rules: tuple[RuleReference, ...] = (),
    ) -> None:
        if not calculator_id or not calculator_id.strip():
            raise CalculatorRegistrationError("AbstractCalculator.calculator_id must not be blank.")

        if not name or not name.strip():
            raise CalculatorRegistrationError("AbstractCalculator.name must not be blank.")

        if not description or not description.strip():
            raise CalculatorRegistrationError("AbstractCalculator.description must not be blank.")

        self.calculator_id = calculator_id
        self._name = name
        self._description = description
        self._supported_rules = supported_rules

    def id(self) -> str:
        """Return this calculator's Calculator ID."""
        return self.calculator_id

    def name(self) -> str:
        """Return this calculator's caller-supplied short name."""
        return self._name

    def description(self) -> str:
        """Return this calculator's caller-supplied description."""
        return self._description

    def supported_rules(self) -> tuple[RuleReference, ...]:
        """Return the RuleReference(s) this calculator supports."""
        return self._supported_rules

    @abstractmethod
    def calculate(self, context: CalculationContext) -> CalculationResult:
        """Perform this calculator's calculation.

        Left abstract deliberately - see each concrete subclass for
        its own ``# TODO (<RULE-ID>)`` and ``NotImplementedError``.
        """
        ...

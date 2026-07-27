"""The Calculator contract: the structural protocol every calculator satisfies.

Traceability notes
-------------------
Mirrors :mod:`trading_engine.rules.protocols` at the mathematical
layer: a ``typing.Protocol`` so any object with the right methods can
be treated as a Calculator without a forced inheritance relationship.
Per the Milestone 4.3A instruction, "No calculator shall know about
the Strategy Engine" - nothing in this protocol references
:mod:`trading_engine.engine` in any way, and a calculator's only input
is a :class:`~trading_engine.calculators.context.CalculationContext`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.result import CalculationResult
from trading_engine.domain.rule_reference import RuleReference


@runtime_checkable
class Calculator(Protocol):
    """The structural contract every calculator implementation must
    satisfy.

    ``@runtime_checkable`` allows :func:`isinstance` checks against
    this protocol (used by
    :class:`~trading_engine.calculators.registry.CalculatorRegistry` to
    reject objects that do not structurally satisfy it) - per
    ``typing`` semantics this checks method *presence* only, not
    parameter/return types or behaviour.
    """

    def id(self) -> str:
        """Return this calculator's unique Calculator ID."""
        ...

    def name(self) -> str:
        """Return a short, human-readable name for this calculator."""
        ...

    def description(self) -> str:
        """Return a short, human-readable description of what this
        calculator computes."""
        ...

    def supported_rules(self) -> tuple[RuleReference, ...]:
        """Return the RuleReference(s) this calculator's output is
        intended to support, per ``docs/RULE_INDEX.md``."""
        ...

    def calculate(self, context: CalculationContext) -> CalculationResult:
        """Perform this calculator's calculation against the supplied
        context and return exactly one result.

        No default/expected behaviour is specified here - every
        calculator in this milestone raises ``NotImplementedError``,
        since no rule in ``docs/RULE_INDEX.md`` has known mathematics
        yet.
        """
        ...

"""CalculationStatus and CalculationResult: the shape of one calculator's output.

Traceability notes
-------------------
The Calculator Framework counterpart of
:class:`trading_engine.rules.outcome.RuleExecutionResult`. No entry in
``docs/RULE_INDEX.md``/``docs/architecture/`` specifies a calculation
result's shape - it is defined here purely as generic infrastructure,
same rationale as :class:`trading_engine.rules.outcome.RuleOutcome`.
``computed_values`` is a generic mapping, not a typed value, since no
calculator's evidenced mathematics exists yet to determine what shape
a real result would take. Per the Milestone 4.3A instruction: "Do NOT
include trading signals."
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from trading_engine.calculators.exceptions import CalculationError


class CalculationStatus(Enum):
    """The possible statuses of one calculator's execution.

    Distinct from the boolean ``success`` flag on
    :class:`CalculationResult`: ``NOT_IMPLEMENTED`` is a real, expected
    status today (every placeholder calculator in this milestone
    raises ``NotImplementedError``), and is not the same thing as a
    calculation that ran and failed.
    """

    #: The calculation completed and produced a value.
    SUCCESS = auto()

    #: The calculation ran but did not complete successfully.
    FAILURE = auto()

    #: The calculator's mathematics does not exist yet (the expected
    #: status for every placeholder calculator in this milestone).
    NOT_IMPLEMENTED = auto()

    #: The supplied CalculationContext was not valid for this
    #: calculator.
    INVALID_CONTEXT = auto()


@dataclass(frozen=True)
class CalculationResult:
    """The outcome of one calculator's ``calculate()`` call.

    Rule References
        None directly - a structural container referencing whichever
        calculator produced it via :attr:`calculator_id`.

    Attributes:
        calculation_id: Unique identifier for this result.
        calculator_id: The Calculator ID that produced this result.
        success: Whether the calculation completed successfully.
        status: Which of the four :class:`CalculationStatus` values
            this execution reached.
        metadata: Free-form, generic metadata about how the
            calculation ran (e.g. timing detail). Untyped, empty by
            default.
        warnings: Non-fatal notices recorded during this calculation.
        errors: Problems encountered during this calculation.
        computed_values: The calculation's output, as a generic
            mapping - deliberately untyped (see module docstring). No
            trading signal belongs here.
    """

    calculation_id: uuid.UUID
    calculator_id: str
    success: bool
    status: CalculationStatus
    metadata: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    computed_values: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.calculation_id is None:
            raise CalculationError("CalculationResult.calculation_id must not be None.")

        if not self.calculator_id or not self.calculator_id.strip():
            raise CalculationError("CalculationResult.calculator_id must not be blank.")

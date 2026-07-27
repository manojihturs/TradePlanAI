"""ReversalCalculator: placeholder for REVERSAL-001's mathematics.

Traceability notes
-------------------
Per ``docs/RULE_INDEX.md``, REVERSAL-001 ("A reversal must be
identified through premium behaviour, never assumed") has
``Mathematical Definition: Unknown`` - which specific premium
behaviour constitutes identifying a reversal is not evidenced (see
``trading_engine/domain/premium.py``'s own ``# TODO (REVERSAL-001)``).
This calculator exists only as a registered, discoverable extension
point - it performs no calculation.
"""

from __future__ import annotations

from trading_engine.calculators.base import AbstractCalculator
from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.result import CalculationResult
from trading_engine.domain.rule_reference import (
    ConfidenceLevel,
    RuleCategory,
    RuleReference,
    RuleStatus,
)

_REVERSAL_001 = RuleReference(
    rule_id="REVERSAL-001",
    category=RuleCategory.REVERSAL,
    status=RuleStatus.DRAFT,
    confidence=ConfidenceLevel.MEDIUM,
    evidence_count=2,
)


class ReversalCalculator(AbstractCalculator):
    """Placeholder calculator for REVERSAL-001 (reversal
    identification via premium behaviour).

    Rule References
        REVERSAL-001

    Entity
        ENT-008 (Reversal), ENT-009 (:class:`trading_engine.domain.premium.Premium`)
    """

    def __init__(self) -> None:
        super().__init__(
            calculator_id="REVERSAL-001-CALCULATOR",
            name="Reversal Calculator",
            description="Placeholder for reversal-identification mathematics (REVERSAL-001).",
            supported_rules=(_REVERSAL_001,),
        )

    def calculate(self, context: CalculationContext) -> CalculationResult:
        # TODO (REVERSAL-001): Reversal mathematics awaiting evidence.
        # Which specific premium behaviour identifies a reversal is
        # Unknown.
        raise NotImplementedError("TODO (REVERSAL-001): Reversal mathematics awaiting evidence.")

"""EdgeCalculator: placeholder for TREND-003's ("Edge") mathematics.

Traceability notes
-------------------
Per ``docs/architecture/DOMAIN_ARCHITECTURE.md``, Edge is "modeled as
a condition evaluated over two TrendPoints," not a standalone entity -
it is the subject of TREND-003 ("Both current and opponent TP Lows
staying well below the strike reduces probability of price moving
below it"), which per ``docs/RULE_INDEX.md`` has ``Mathematical
Definition: Unknown``. This calculator exists only as a registered,
discoverable extension point - it performs no calculation.
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

_TREND_003 = RuleReference(
    rule_id="TREND-003",
    category=RuleCategory.TREND,
    status=RuleStatus.DRAFT,
    confidence=ConfidenceLevel.MEDIUM,
    evidence_count=2,
)


class EdgeCalculator(AbstractCalculator):
    """Placeholder calculator for TREND-003 (the "Edge" condition over
    two TrendPoints).

    Rule References
        TREND-003

    Entity
        None directly - per ``docs/architecture/DOMAIN_ARCHITECTURE.md``,
        Edge is a condition, not a standalone entity.
    """

    def __init__(self) -> None:
        super().__init__(
            calculator_id="TREND-003-CALCULATOR",
            name="Edge Calculator",
            description="Placeholder for the Edge condition mathematics over two TrendPoints (TREND-003).",
            supported_rules=(_TREND_003,),
        )

    def calculate(self, context: CalculationContext) -> CalculationResult:
        # TODO (TREND-003): Edge mathematics awaiting evidence. How
        # "staying well below the strike" is quantified, for either
        # TrendPoint, is Unknown.
        raise NotImplementedError("TODO (TREND-003): Edge mathematics awaiting evidence.")

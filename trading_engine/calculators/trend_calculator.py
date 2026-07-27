"""TrendCalculator: placeholder for TREND-001/002/003's mathematics.

Traceability notes
-------------------
Per ``docs/RULE_INDEX.md``, TREND-001 ("Every analysed strike
maintains a dynamically-updated Trend Point Low") and TREND-002 ("TP
Low is not static - converts to a new value when market structure
changes") both have ``Mathematical Definition: Unknown``. This
calculator exists only as a registered, discoverable extension point -
it performs no calculation.
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

_TREND_001 = RuleReference(
    rule_id="TREND-001",
    category=RuleCategory.TREND,
    status=RuleStatus.DRAFT,
    confidence=ConfidenceLevel.MEDIUM,
    evidence_count=2,
)

_TREND_002 = RuleReference(
    rule_id="TREND-002",
    category=RuleCategory.TREND,
    status=RuleStatus.DRAFT,
    confidence=ConfidenceLevel.MEDIUM,
    evidence_count=2,
)


class TrendCalculator(AbstractCalculator):
    """Placeholder calculator for TREND-001/TREND-002 (Trend Point Low
    tracking and updates).

    Rule References
        TREND-001, TREND-002

    Entity
        ENT-003 (:class:`trading_engine.domain.trend_point.TrendPoint`)
    """

    def __init__(self) -> None:
        super().__init__(
            calculator_id="TREND-001-CALCULATOR",
            name="Trend Calculator",
            description="Placeholder for Trend Point Low tracking/update mathematics (TREND-001, TREND-002).",
            supported_rules=(_TREND_001, _TREND_002),
        )

    def calculate(self, context: CalculationContext) -> CalculationResult:
        # TODO (TREND-001): Trend mathematics awaiting evidence. How a
        # Trend Point Low is computed, and how TREND-002's "market
        # structure change" is detected, are both Unknown.
        raise NotImplementedError("TODO (TREND-001): Trend mathematics awaiting evidence.")

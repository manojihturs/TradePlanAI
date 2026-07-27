"""StrikeCalculator: placeholder for STRIKE-001's mathematics.

Traceability notes
-------------------
Per ``docs/RULE_INDEX.md``, STRIKE-001 ("Initial strike selection is
based on the first candle") has ``Mathematical Definition: Unknown``
(see ``docs/TRADINGVIEW_STRATEGY_BIBLE.md`` Open Questions: "selected
based on the first candle" - selected *how*?). This calculator exists
only as a registered, discoverable extension point - it performs no
calculation.
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

_STRIKE_001 = RuleReference(
    rule_id="STRIKE-001",
    category=RuleCategory.STRIKE,
    status=RuleStatus.DRAFT,
    confidence=ConfidenceLevel.MEDIUM,
    evidence_count=2,
)


class StrikeCalculator(AbstractCalculator):
    """Placeholder calculator for STRIKE-001 (initial strike
    selection).

    Rule References
        STRIKE-001

    Entity
        ENT-001 (:class:`trading_engine.domain.strike.Strike`)
    """

    def __init__(self) -> None:
        super().__init__(
            calculator_id="STRIKE-001-CALCULATOR",
            name="Strike Calculator",
            description="Placeholder for initial strike selection mathematics (STRIKE-001).",
            supported_rules=(_STRIKE_001,),
        )

    def calculate(self, context: CalculationContext) -> CalculationResult:
        # TODO (STRIKE-001): Strike mathematics awaiting evidence. The
        # calculation connecting a session's First Candle to the
        # resulting selected Strike is not yet known.
        raise NotImplementedError("TODO (STRIKE-001): Strike mathematics awaiting evidence.")

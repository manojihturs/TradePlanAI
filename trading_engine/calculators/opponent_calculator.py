"""OpponentCalculator: placeholder for OPPONENT-001's mathematics.

Traceability notes
-------------------
Per ``docs/RULE_INDEX.md``, OPPONENT-001 ("A strike progresses only
after defeating the next opponent") has ``Mathematical Definition:
Unknown``, and depends on OPPONENT-002/OPPONENT-003 (Opponent
High/Low), both ``Awaiting Evidence`` with zero recorded behaviour.
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

_OPPONENT_001 = RuleReference(
    rule_id="OPPONENT-001",
    category=RuleCategory.OPPONENT,
    status=RuleStatus.DRAFT,
    confidence=ConfidenceLevel.MEDIUM,
    evidence_count=2,
)

_OPPONENT_002 = RuleReference(
    rule_id="OPPONENT-002",
    category=RuleCategory.OPPONENT,
    status=RuleStatus.AWAITING_EVIDENCE,
    confidence=ConfidenceLevel.UNKNOWN,
    evidence_count=0,
)

_OPPONENT_003 = RuleReference(
    rule_id="OPPONENT-003",
    category=RuleCategory.OPPONENT,
    status=RuleStatus.AWAITING_EVIDENCE,
    confidence=ConfidenceLevel.UNKNOWN,
    evidence_count=0,
)


class OpponentCalculator(AbstractCalculator):
    """Placeholder calculator for OPPONENT-001 (opponent-defeat
    progression), and its Awaiting-Evidence dependencies
    OPPONENT-002/003 (Opponent High/Low).

    Rule References
        OPPONENT-001, OPPONENT-002, OPPONENT-003

    Entity
        ENT-005 (:class:`trading_engine.domain.opponent.Opponent`),
        ENT-006/007 (Opponent High/Low - attribute slots only)
    """

    def __init__(self) -> None:
        super().__init__(
            calculator_id="OPPONENT-001-CALCULATOR",
            name="Opponent Calculator",
            description="Placeholder for opponent-defeat progression mathematics (OPPONENT-001).",
            supported_rules=(_OPPONENT_001, _OPPONENT_002, _OPPONENT_003),
        )

    def calculate(self, context: CalculationContext) -> CalculationResult:
        # TODO (OPPONENT-001): Opponent mathematics awaiting evidence.
        # What constitutes "defeating" an opponent, and how Opponent
        # High/Low (OPPONENT-002/003) are computed, are both Unknown.
        raise NotImplementedError("TODO (OPPONENT-001): Opponent mathematics awaiting evidence.")

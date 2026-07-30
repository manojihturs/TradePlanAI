"""WeeklyFutureCalculator: placeholder for the Weekly Future High/Low mathematics.

Traceability notes
-------------------
Weekly Future (ENT-010) has no Rule ID of its own in ``docs/RULE_INDEX.md``
- it is a Candidate Entity, not a confirmed business rule. Per
``docs/architecture/DOMAIN_ARCHITECTURE.md``'s Candidate treatment and
mirroring :class:`~trading_engine.calculators.edge_calculator.EdgeCalculator`'s
precedent (Edge likewise has no Rule ID of its own and cites the rule
it supports, TREND-003), this calculator's ``supported_rules()`` cites
**STRIKE-001**: ``research/analysis/RULE_DEPENDENCY_GRAPH.md`` and
``research/analysis/REPOSITORY_CHANGE_PROPOSAL.md`` establish that
STRIKE-001's strike selection depends on a Weekly Future first-candle
High/Low (unverified against ``docs/RULE_INDEX.md``'s own ledger, which
still reads "Depends On: none yet" - see those two documents for the
flagged documentation-lag discrepancy). Weekly Future mathematics exist
only to serve STRIKE-001; there is no independent Weekly-Future rule to
cite instead.

Per ``research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md``, the
transcript evidence names the required inputs (Call option first-candle
High/Low, Put option first-candle High/Low, ATM strike) and states the
combination rule's general shape in natural language, but the one
worked example in the source transcript is internally inconsistent (a
subtraction self-corrected on camera from 91 to 81 to 82; a Low value
stated as both "268" and "26168" for the same candle; a Low that
numerically exceeds the High it was computed alongside) and the
speaker twice refers viewers to a separate "Weekly Future Calculation"
/ "Complete Calculation Video" that is not present anywhere in this
repository (confirmed again in
``research/analysis/NEW_EVIDENCE_REPORT.md``, Milestone 6.0). This
calculator therefore performs no calculation.
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


class WeeklyFutureCalculator(AbstractCalculator):
    """Placeholder calculator for the Weekly Future High/Low
    computation that STRIKE-001's strike selection depends on.

    Rule References
        STRIKE-001 (the rule this calculator's future output would
        serve - see module docstring for why Weekly Future itself has
        no Rule ID to cite)

    Entity
        ENT-010 (Weekly Future - Candidate, per
        ``docs/architecture/DOMAIN_ARCHITECTURE.md``)
    """

    def __init__(self) -> None:
        super().__init__(
            calculator_id="WEEKLY-FUTURE-CALCULATOR",
            name="Weekly Future Calculator",
            description=(
                "Placeholder for Weekly Future High/Low mathematics "
                "(ENT-010), the upstream input STRIKE-001's strike "
                "selection depends on."
            ),
            supported_rules=(_STRIKE_001,),
        )

    def calculate(self, context: CalculationContext) -> CalculationResult:
        # TODO (STRIKE-001): Weekly Future mathematics awaiting evidence.
        # research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md documents
        # the specific blockers: the transcript's Call/Put-option-derived
        # High/Low arithmetic is self-contradictory (a subtraction
        # self-corrected from 91 to 81 to 82; a Low value stated as both
        # "268" and "26168" for the same candle; a Low that numerically
        # exceeds the High computed alongside it), and the speaker's own
        # referenced "Weekly Future Calculation" / "Complete Calculation
        # Video" is not present in this repository (confirmed again by
        # research/analysis/NEW_EVIDENCE_REPORT.md, Milestone 6.0).
        raise NotImplementedError("TODO (STRIKE-001): Weekly Future mathematics awaiting evidence.")

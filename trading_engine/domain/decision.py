"""RuleEvaluationResult and Decision: rule evaluation outcomes and their aggregate.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule Results"
and "Decision Objects"). A RuleEvaluationResult's ``outcome`` is
deliberately left generic (``typing.Any``) since different rules'
outcomes are not yet evidenced to share a shape (e.g. STRIKE-001
"produces a strike," TREND-003 "evaluates a condition" are not
interchangeable result types by current evidence). Decision performs
no synthesis across results - no combination rule (e.g. "if TREND-003
holds AND REVERSAL-001 fires, then...") is evidenced anywhere.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from trading_engine.domain import DomainValidationError
from trading_engine.domain.evidence_reference import EvidenceReference
from trading_engine.domain.rule_reference import RuleReference


@dataclass(frozen=True)
class RuleEvaluationResult:
    """The outcome of one rule's evaluation at one MarketContext.

    Carries the Rule ID and Evidence ID(s) that produced it, so
    downstream consumers can weight or filter results by evidentiary
    strength without the Rule Engine itself making that judgment call.

    Rule References
        None directly - a structural container referencing whichever
        rule produced it via :attr:`rule`.

    Attributes:
        result_id: Unique identifier for this result.
        rule: The RuleReference this result was produced by.
        evidence: The EvidenceReference(s) backing that rule.
        outcome_description: A short human-readable description of
            what this evaluation concluded. Must not be blank.
        outcome_value: The evaluation's outcome value, deliberately
            untyped (see module docstring). ``None`` if the rule
            produced no distinct value beyond its description.
        evaluated_at: When this evaluation occurred.
    """

    result_id: uuid.UUID
    rule: RuleReference
    evidence: tuple[EvidenceReference, ...]
    outcome_description: str
    evaluated_at: datetime
    outcome_value: Any | None = None

    def __post_init__(self) -> None:
        if self.result_id is None:
            raise DomainValidationError("RuleEvaluationResult.result_id must not be None.")

        if not self.outcome_description or not self.outcome_description.strip():
            raise DomainValidationError(
                "RuleEvaluationResult.outcome_description must not be blank."
            )

    # TODO (RULE_ENGINE_ARCHITECTURE): No rule in RULE_INDEX.md has an
    # implemented evaluation function yet (Milestone 4.4+). This type
    # only defines the shape a result would have.


@dataclass(frozen=True)
class Decision:
    """The aggregate of RuleEvaluationResults from one evaluation
    step.

    Represents "what the engine currently believes," without itself
    constituting a trading decision - no entry/exit logic exists in
    confirmed evidence (``docs/TRADINGVIEW_STRATEGY_BIBLE.md``'s
    ``ENTRY`` and ``EXIT`` categories are both empty).

    Rule References
        None directly - see the individual results in :attr:`results`
        for their own Rule References.

    Attributes:
        decision_id: Unique identifier for this Decision.
        session_id: The MarketSession this Decision was produced within.
        results: The RuleEvaluationResult(s) aggregated into this Decision.
        created_at: When this Decision was assembled.
    """

    decision_id: uuid.UUID
    session_id: uuid.UUID
    results: tuple[RuleEvaluationResult, ...] = field(default_factory=tuple)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.decision_id is None:
            raise DomainValidationError("Decision.decision_id must not be None.")

        if self.session_id is None:
            raise DomainValidationError("Decision.session_id must not be None.")

    # TODO (RULE_ENGINE_ARCHITECTURE): No synthesis/combination logic
    # across multiple RuleEvaluationResults is evidenced anywhere in
    # the reviewed documents. This type is a plain collection only.

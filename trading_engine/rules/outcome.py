"""RuleOutcome and RuleExecutionResult: the shape of one rule's evaluation.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule
Results"). That document deliberately leaves a rule's outcome value
"generic ... not typed as boolean/numeric/etc." at the *domain* layer
(see :class:`trading_engine.domain.decision.RuleEvaluationResult`).
:class:`RuleOutcome` is the Milestone 4.2 framework-level refinement of
that same idea: a plain boolean cannot represent a rule that could not
be evaluated at all (missing evidence, or Unknown mathematics - the
case for every one of the 6 confirmed rules in ``docs/RULE_INDEX.md``
today) versus one that evaluated cleanly to a negative result - these
are real, distinct states. This enum exists to make that distinction
explicit at the framework boundary, without asserting what any
specific rule's outcome *means*.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from trading_engine.domain.evidence_reference import EvidenceReference
from trading_engine.domain.rule_reference import RuleReference
from trading_engine.rules.exceptions import RuleExecutionError


class RuleOutcome(Enum):
    """The possible outcomes of one rule's evaluation.

    Deliberately not a ``bool``: a rule whose mathematics is Unknown
    (per ``docs/RULE_INDEX.md``, currently true for every confirmed
    rule) cannot honestly report only "true" or "false" - it may be
    unable to reach a conclusion at all, or may not apply to the
    current Market Context/Session State.
    """

    #: The rule evaluated and its condition held.
    PASS = auto()

    #: The rule evaluated and its condition did not hold.
    FAIL = auto()

    #: The rule could not reach a conclusion for a reason other than
    #: missing evidence (e.g. its mathematics is Unknown per the Rule
    #: Bible - the common case for every confirmed rule today).
    UNKNOWN = auto()

    #: The rule requires evidence (data) that was not present in the
    #: supplied RuleExecutionContext.
    INSUFFICIENT_EVIDENCE = auto()

    #: The rule does not apply given the current Market
    #: Context/Session State (e.g. a placeholder rule such as
    #: OPPONENT-002/003, per ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``'s
    #: "registered but inactive" treatment).
    NOT_APPLICABLE = auto()


@dataclass(frozen=True)
class RuleExecutionResult:
    """The outcome of evaluating exactly one rule against exactly one
    :class:`~trading_engine.rules.context.RuleExecutionContext`.

    The Rule Framework counterpart to
    :class:`trading_engine.domain.decision.RuleEvaluationResult`,
    typed against :class:`RuleOutcome` instead of a generic value - see
    module docstring. No calculation happens here; this is a result
    *shape* only, produced by whatever rule implementation eventually
    exists (Milestone 4.3+).

    Rule References
        None directly - a structural container referencing whichever
        rule produced it via :attr:`rule`.

    Attributes:
        result_id: Unique identifier for this result.
        rule: The RuleReference this result was produced by.
        outcome: Which of the five :class:`RuleOutcome` values this
            evaluation reached.
        reason: A short, human-readable explanation of why this
            outcome was reached. Must not be blank.
        evidence_used: The EvidenceReference(s) that were actually
            consulted to reach this outcome (a subset of, or equal to,
            the rule's ``required_evidence()``).
        executed_at: When this evaluation occurred.
    """

    result_id: uuid.UUID
    rule: RuleReference
    outcome: RuleOutcome
    reason: str
    evidence_used: tuple[EvidenceReference, ...] = field(default_factory=tuple)
    executed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.result_id is None:
            raise RuleExecutionError("RuleExecutionResult.result_id must not be None.")

        if self.rule is None:
            raise RuleExecutionError("RuleExecutionResult.rule must not be None.")

        if not self.reason or not self.reason.strip():
            raise RuleExecutionError("RuleExecutionResult.reason must not be blank.")

    # TODO (RULE_ENGINE_ARCHITECTURE): No rule in docs/RULE_INDEX.md has
    # an implemented evaluation function yet (Milestone 4.3+). This
    # type only defines the shape a result would have; nothing here
    # decides what outcome any specific rule should reach.

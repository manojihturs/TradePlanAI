"""Rule identity and traceability value object.

Traceability
------------
Mirrors ``docs/RULE_INDEX.md`` and the "Category Taxonomy (fixed)" /
"Rule lifecycle fields" sections of
``docs/TRADINGVIEW_STRATEGY_BIBLE.md`` exactly. Do not add an enum
member here without first adding it to those documents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto

from trading_engine.domain import DomainValidationError

_RULE_ID_PATTERN = re.compile(r"^[A-Z_]+-\d{3}$")


class RuleCategory(Enum):
    """The fixed rule-category taxonomy from
    ``docs/TRADINGVIEW_STRATEGY_BIBLE.md`` ("Category Taxonomy
    (fixed)"). Every recovered business rule belongs to exactly one of
    these, or ``UNKNOWN`` until enough evidence exists to classify it.
    """

    CORE = auto()
    PHILOSOPHY = auto()
    WEEKLY_FUTURE = auto()
    FIRST_CANDLE = auto()
    STRIKE = auto()
    TREND = auto()
    STATE = auto()
    CONTROL_ZONE = auto()
    FLOW = auto()
    OPPONENT = auto()
    ENTRY = auto()
    EXIT = auto()
    REVERSAL = auto()
    DECAY = auto()
    PREMIUM = auto()
    RISK = auto()
    VALIDATION = auto()
    MATH = auto()
    UNKNOWN = auto()


class RuleStatus(Enum):
    """Rule lifecycle status values from ``docs/RULE_INDEX.md``
    ("Status values (rule lifecycle)").
    """

    #: Placeholder only - referenced as a dependency by another rule,
    #: but no evidence yet defines its own behaviour (e.g.
    #: OPPONENT-002, OPPONENT-003).
    AWAITING_EVIDENCE = auto()

    #: Recorded from evidence, not yet cross-checked or reviewed.
    DRAFT = auto()

    #: Being actively cross-checked against additional evidence.
    UNDER_REVIEW = auto()

    #: Confirmed consistent across sufficient independent evidence.
    VALIDATED = auto()

    #: Replaced by a later, corrected rule ID - kept for history, not deleted.
    SUPERSEDED = auto()


class ConfidenceLevel(Enum):
    """Confidence labels from the Confidence Policy in
    ``docs/EVIDENCE_MATRIX.md`` (Evidence Count 0 -> UNKNOWN, 1 -> LOW,
    2 -> MEDIUM, 3-4 -> HIGH, 5+ -> CONFIRMED).

    This enum represents the resulting label only. It does **not**
    compute a level from an evidence count anywhere in this module -
    that mapping is a documentation policy applied by whoever records
    a rule's confidence, not a domain calculation. Encoding it as
    executable logic here would risk silent divergence from future
    edits to the policy in ``docs/EVIDENCE_MATRIX.md``.
    """

    UNKNOWN = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CONFIRMED = auto()


@dataclass(frozen=True)
class RuleReference:
    """An immutable pointer to exactly one rule row in
    ``docs/RULE_INDEX.md`` / ``docs/TRADINGVIEW_STRATEGY_BIBLE.md``
    (e.g. ``STRIKE-001``, ``TREND-003``, ``OPPONENT-002``).

    Carries the same lifecycle fields those documents track, so a
    domain object referencing a rule can be checked for drift against
    its documentation source. This value object does not evaluate the
    rule it refers to - see
    ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` for where
    evaluation lives (a future ``rules``/``engine`` package concern,
    out of scope for this Milestone 4.1 Domain layer).

    Rule References
        This type itself is not evidence for a business rule - it is
        the traceability mechanism other domain models use to cite
        Rule IDs such as STRIKE-001, TREND-001.

    Attributes:
        rule_id: The rule identifier, in ``<CATEGORY>-<NNN>`` form
            exactly as assigned in ``docs/RULE_INDEX.md`` (e.g.
            ``"STRIKE-001"``). Permanent once assigned - never
            renumbered, per that document's Rule ID convention.
        category: The fixed category this rule belongs to.
        status: The rule's current lifecycle status.
        confidence: The rule's current confidence, per the Confidence
            Policy.
        evidence_count: The number of independent evidence sources
            currently supporting this rule (not the number of other
            artifacts that reference it - see
            ``docs/EVIDENCE_MATRIX.md``'s Confidence Policy for that
            distinction).
    """

    rule_id: str
    category: RuleCategory
    status: RuleStatus
    confidence: ConfidenceLevel
    evidence_count: int = field(default=0)

    def __post_init__(self) -> None:
        if not self.rule_id or not self.rule_id.strip():
            raise DomainValidationError("RuleReference.rule_id must not be blank.")

        if not _RULE_ID_PATTERN.match(self.rule_id):
            raise DomainValidationError(
                f"RuleReference.rule_id {self.rule_id!r} does not match the "
                "<CATEGORY>-<NNN> convention defined in docs/RULE_INDEX.md."
            )

        if self.evidence_count < 0:
            raise DomainValidationError("RuleReference.evidence_count must not be negative.")

"""Evidence identity and traceability value object.

Traceability
------------
Mirrors ``docs/TRACEABILITY_MATRIX.md`` (its "Source Evidence" table
and Evidence ID assignment) and ``research/KNOWLEDGE_SOURCES.md``
(the Evidence Level hierarchy) exactly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from trading_engine.domain import DomainValidationError


class EvidenceLevel(Enum):
    """The evidence-level hierarchy from
    ``research/KNOWLEDGE_SOURCES.md`` ("Evidence levels"). Higher
    numbered levels do not override lower-numbered ones - an
    ``EXISTING_IMPLEMENTATION`` observation never establishes what the
    original strategy did; it only describes what one prior
    implementation attempt did.
    """

    #: LEVEL 1 - Original YouTube transcript. Highest confidence.
    ORIGINAL_TRANSCRIPT = 1

    #: LEVEL 2 - User manual observations, including TradingView
    #: screenshots and manual trade logs.
    MANUAL_OBSERVATION = 2

    #: LEVEL 3 - The existing ``strategy/`` Python implementation.
    #: Reference only - a prior interpretation, not original source
    #: material.
    EXISTING_IMPLEMENTATION = 3

    #: LEVEL 4 - A pattern noticed or inferred, not yet confirmed
    #: against any direct source.
    HYPOTHESIS = 4


@dataclass(frozen=True)
class EvidenceReference:
    """An immutable pointer to exactly one evidence row in
    ``docs/TRACEABILITY_MATRIX.md`` (e.g. ``EVID-001``, ``EVID-007``).

    Distinct from :class:`~trading_engine.domain.rule_reference.RuleReference`:
    an evidence reference points at the source that justifies a rule or
    entity, not at the rule/entity itself.

    Evidence
        This type is the traceability mechanism for citing Evidence
        IDs such as EVID-001 from other domain models.

    Attributes:
        evidence_id: The evidence identifier exactly as assigned in
            ``docs/TRACEABILITY_MATRIX.md`` (e.g. ``"EVID-007"``).
        level: How trustworthy this evidence source is, per
            ``research/KNOWLEDGE_SOURCES.md``.
        description: A short human-readable description of the
            evidence content, mirrored from
            ``docs/TRACEABILITY_MATRIX.md``'s "Content" column (e.g.
            the quoted statement it points to).
        source_path: The repository-relative path to the saved source
            file, if one exists (e.g.
            ``Path("research/transcripts/TR-001.md")``). ``None`` for
            evidence that only exists as an unsaved conversational
            statement (e.g. EVID-001 through EVID-006, per
            ``docs/TRACEABILITY_MATRIX.md``) - this is a legitimate,
            documented state, not a missing value that indicates an
            error.
    """

    evidence_id: str
    level: EvidenceLevel
    description: str
    source_path: Path | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.evidence_id.strip():
            raise DomainValidationError("EvidenceReference.evidence_id must not be blank.")

        if not self.description or not self.description.strip():
            raise DomainValidationError("EvidenceReference.description must not be blank.")

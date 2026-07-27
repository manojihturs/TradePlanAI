"""DomainEvent: the generic base shape for a discrete occurrence.

Traceability notes
-------------------
No confirmed Rule ID or Entity ID names a concrete event type.
``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` and
``docs/EVIDENCE_MATRIX.md`` both record the "Event" artifact type as
currently empty ("No artifact in the project has yet been classified
as a discrete Event distinct from a State"). The closest candidate for
a future concrete event is SM-004 (``OPPONENT_DEFEATED``) in
``docs/STATE_MACHINE.md``, which is itself explicitly a hypothesis,
not a confirmed state - so no concrete event subtype is defined in
this milestone. This module defines only the generic base shape a
future event would share.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from trading_engine.domain import DomainValidationError


@dataclass(frozen=True)
class DomainEvent:
    """A generic, minimal shape for a discrete occurrence within the
    domain.

    Deliberately generic and concrete (not abstract) at this
    milestone: no subclass is defined because no specific event type
    is evidenced (see module docstring). This type can be instantiated
    directly to represent "some event occurred," pending evidence of
    what specific events matter.

    Rule References
        None - see module docstring.

    Attributes:
        event_id: Unique identifier for this event instance.
        occurred_at: When this event occurred.
        description: A short human-readable description of what
            occurred. Must not be blank.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    description: str

    def __post_init__(self) -> None:
        if self.event_id is None:
            raise DomainValidationError("DomainEvent.event_id must not be None.")

        if not self.description or not self.description.strip():
            raise DomainValidationError("DomainEvent.description must not be blank.")

    # TODO (STATE_MACHINE / SM-004): "Opponent Defeated" is the
    # closest hypothesised concrete event in the current evidence, but
    # remains a hypothesis, not a confirmed state or event
    # (docs/STATE_MACHINE.md). No concrete DomainEvent subclass is
    # defined until a specific event type is evidenced.

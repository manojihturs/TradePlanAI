"""ReferenceRepository: in-memory storage for a session's reference ladder.

Traceability
------------
Pure infrastructure - no business rule. In-memory only (no database,
per this sprint's own instruction); a session's ladder is built once
(Specification Section 6) and read many times by downstream engines.
"""

from __future__ import annotations

import uuid

from models.reference_level import ReferenceLevel


class ReferenceRepository:
    """Stores each session's built reference ladder, keyed by session
    id.

    No global state - each instance owns its own private store,
    constructor-injectable into any collaborator that needs to read a
    previously-built ladder.
    """

    def __init__(self) -> None:
        self._ladders: dict[uuid.UUID, tuple[ReferenceLevel, ...]] = {}

    def save(self, session_id: uuid.UUID, levels: tuple[ReferenceLevel, ...]) -> None:
        """Store ``levels`` as the reference ladder for
        ``session_id``, overwriting any previously-stored ladder for
        the same session."""
        self._ladders[session_id] = levels

    def get(self, session_id: uuid.UUID) -> tuple[ReferenceLevel, ...] | None:
        """The reference ladder for ``session_id``, or ``None`` if
        none has been saved."""
        return self._ladders.get(session_id)

    def clear(self) -> None:
        """Discard every stored ladder."""
        self._ladders = {}

"""Opponent: the entity a Strike must "defeat" to progress.

Traceability notes
-------------------
Whether "Opponent" is the same concept as "competitor" already
implemented elsewhere in this repository (``strategy/exit_signal.py``'s
Competitor Exit) is explicitly unconfirmed
(``docs/TERMINOLOGY.md``). This module does **not** assume they are
the same - Opponent is designed as its own concept, not wired to or
modeled after the existing Python ``strategy/`` package's competitor
logic, even though both are now implemented in the same language.
Proximity of language is not evidence of conceptual equivalence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from trading_engine.domain import DomainValidationError


@dataclass(frozen=True)
class Opponent:
    """An entity associated with a Strike that must be "defeated" for
    that Strike to progress.

    ``high`` and ``low`` are reserved attribute slots only, per
    ``docs/architecture/DOMAIN_ARCHITECTURE.md`` ("Opponent High /
    Opponent Low - Awaiting Evidence"): OPPONENT-002 and OPPONENT-003
    have zero recorded behaviour, so no computation or cross-field
    invariant (e.g. requiring ``high >= low``) is enforced here -
    doing so would mean guessing at structure the evidence does not
    yet support.

    Rule References
        OPPONENT-001
        TREND-003

    Entity
        ENT-005

    Attributes:
        opponent_id: Unique identifier for this Opponent instance.
        strike_id: The Strike this Opponent is associated with.
        own_trend_point_id: The identifier of this Opponent's own
            TrendPoint, if one has been established. ``None`` until
            then.
        high: Reserved attribute slot for "Opponent High"
            (OPPONENT-002, Awaiting Evidence). ``None`` until defined.
        low: Reserved attribute slot for "Opponent Low" (OPPONENT-003,
            Awaiting Evidence). ``None`` until defined.
    """

    opponent_id: uuid.UUID
    strike_id: uuid.UUID
    own_trend_point_id: uuid.UUID | None = None
    high: Decimal | None = None
    low: Decimal | None = None

    def __post_init__(self) -> None:
        if self.opponent_id is None:
            raise DomainValidationError("Opponent.opponent_id must not be None.")

        if self.strike_id is None:
            raise DomainValidationError("Opponent.strike_id must not be None.")

    # TODO (OPPONENT-001): What mathematically constitutes one
    # Strike/side "defeating" its Opponent is Unknown (Bible Open
    # Questions). No defeat-evaluation function exists on this type.
    # TODO (OPPONENT-002): "Opponent High" has zero recorded behaviour
    # - the `high` attribute is a reserved slot only.
    # TODO (OPPONENT-003): "Opponent Low" has zero recorded behaviour
    # - the `low` attribute is a reserved slot only.

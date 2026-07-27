"""MarketSession: the per-trading-day analysis scope.

Traceability notes
-------------------
No Rule ID or Entity ID directly names "MarketSession." It is included
as an architectural necessity - see
``docs/architecture/DOMAIN_ARCHITECTURE.md`` ("MarketSession -
Architectural container"): ``STRIKE_SELECTED`` is described in
``docs/STATE_MACHINE.md`` as "the earliest state implied by any
current rule," and TR-001's own structure is ~11 independent daily
analyses, implying every confirmed rule and state operates within a
session scope that resets daily.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from trading_engine.domain import DomainValidationError


@dataclass(frozen=True)
class MarketSession:
    """One trading day's analysis scope.

    Holds only identity and the date it represents.
    ``docs/STATE_MACHINE.md`` does not evidence session lifecycle
    rules (start/end triggers, reset rules) beyond the implication
    that one exists, so none is implemented here.

    Rule References
        None directly - see module docstring.

    Attributes:
        session_id: Unique identifier for this session instance.
        session_date: The trading date this session represents.
    """

    session_id: uuid.UUID
    session_date: date

    def __post_init__(self) -> None:
        if self.session_id is None:
            raise DomainValidationError("MarketSession.session_id must not be None.")

    # TODO (STATE_MACHINE): Session start/end triggers and reset rules
    # are not evidenced anywhere in docs/STATE_MACHINE.md ("What is
    # needed to complete this document"). No lifecycle method is added
    # here until they are.

"""TradeSignal: the Entry Signal raised immediately after a Winner.

Traceability
------------
``research/architecture/DATA_DICTIONARY.md`` Section 8;
Specification Section 10 ("Winner immediately generates Entry
Signal"). ``accepted`` reflects Specification Rule 4: ``False`` when
a trade was already active at signal time (the signal is discarded,
never queued).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from core.enums import TradeDirection
from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class TradeSignal:
    """One Entry Signal, raised immediately after a Winner.

    Attributes:
        signal_id: This signal's own identifier.
        winner_event_id: The originating Winner event's identifier.
        side: The winning side (CE or PE).
        strike: The winning strike. Must be positive.
        raised_at: When the signal was raised.
        accepted: Whether this signal resulted in a trade - ``False``
            if a trade was already active (Specification Rule 4).
    """

    signal_id: uuid.UUID
    winner_event_id: uuid.UUID
    side: TradeDirection
    strike: Decimal
    raised_at: datetime
    accepted: bool = False

    def __post_init__(self) -> None:
        if self.signal_id is None:
            raise ValidationError("TradeSignal.signal_id must not be None.")
        if self.winner_event_id is None:
            raise ValidationError("TradeSignal.winner_event_id must not be None.")
        if self.strike <= 0:
            raise ValidationError("TradeSignal.strike must be greater than 0.")
        if self.raised_at is None:
            raise ValidationError("TradeSignal.raised_at must not be None.")

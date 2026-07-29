"""StrikeSelection: the session's Top Strike and Bottom Strike.

Traceability
------------
``research/architecture/DATA_DICTIONARY.md`` Section 3. The ATM
selection rule is MISSING INFORMATION (Specification Section 20 item
2, Critical) - this model only carries whatever values an eventual
``interfaces.strike_selector.StrikeSelector`` implementation
produces. Whether ``top_strike`` can equal ``bottom_strike`` is
unconfirmed, so that case is not rejected here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class StrikeSelection:
    """The session's Top Strike and Bottom Strike (both "ATM").

    Attributes:
        session_id: The trading session this belongs to.
        top_strike: The selected Top Strike. Must be positive.
        bottom_strike: The selected Bottom Strike. Must be positive.
        selected_at: When the selection was made.
    """

    session_id: uuid.UUID
    top_strike: Decimal
    bottom_strike: Decimal
    selected_at: datetime

    def __post_init__(self) -> None:
        if self.session_id is None:
            raise ValidationError("StrikeSelection.session_id must not be None.")
        if self.top_strike <= 0:
            raise ValidationError("StrikeSelection.top_strike must be greater than 0.")
        if self.bottom_strike <= 0:
            raise ValidationError("StrikeSelection.bottom_strike must be greater than 0.")
        if self.selected_at is None:
            raise ValidationError("StrikeSelection.selected_at must not be None.")

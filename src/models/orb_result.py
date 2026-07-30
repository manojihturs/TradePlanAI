"""ORBResult: one strike/side's Opening Range Breakout calculation.

Traceability
------------
Sprint: "ORB Engine" (Business Implementation Mode). Opening
High/Low are the same first-5-minute-candle CE/PE values already
carried by ``models.reference_level.ReferenceLevel`` (Specification
Rule 1, CONFIRMED) - this model does not recompute them, only
restates the relevant side's pair plus the derived Range and
Breakout Status. See ``orb_engine.orb_engine.ORBEngine`` for how
``status`` is determined - a standard, industry-generic definition,
not a proprietary business rule requiring transcript evidence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from core.enums import OptionType, ORBStatus
from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class ORBResult:
    """One strike/side's Opening Range Breakout calculation.

    Attributes:
        orb_result_id: This value's own identifier.
        session_id: The trading session this belongs to.
        strike: The strike price this ORB calculation concerns.
        side: Which contract type (CE/PE) this concerns.
        opening_high: The opening range's high (first 5-minute candle).
        opening_low: The opening range's low (first 5-minute candle).
        range: ``opening_high - opening_low``.
        status: Whether/how the opening range has been broken.
        calculated_at: When this was computed.
    """

    orb_result_id: uuid.UUID
    session_id: uuid.UUID
    strike: Decimal
    side: OptionType
    opening_high: Decimal
    opening_low: Decimal
    range: Decimal
    status: ORBStatus
    calculated_at: datetime

    def __post_init__(self) -> None:
        if self.orb_result_id is None:
            raise ValidationError("ORBResult.orb_result_id must not be None.")
        if self.session_id is None:
            raise ValidationError("ORBResult.session_id must not be None.")
        if self.strike <= 0:
            raise ValidationError("ORBResult.strike must be greater than 0.")
        if self.opening_high < self.opening_low:
            raise ValidationError(
                f"ORBResult.opening_high ({self.opening_high}) is less than "
                f"opening_low ({self.opening_low})."
            )
        if self.range != self.opening_high - self.opening_low:
            raise ValidationError("ORBResult.range must equal opening_high - opening_low.")
        if self.calculated_at is None:
            raise ValidationError("ORBResult.calculated_at must not be None.")

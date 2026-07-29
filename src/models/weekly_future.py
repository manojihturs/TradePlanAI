"""WeeklyFuture: the session's Weekly Future High/Low.

Traceability
------------
``research/architecture/DATA_DICTIONARY.md`` Section 2. The formula
for ``high``/``low`` is MISSING INFORMATION (Specification Section 20
item 1, Critical) - this model only carries whatever values an
eventual ``interfaces.weekly_future_calculator.WeeklyFutureCalculator``
implementation produces. No ``high >= low`` invariant is enforced,
since a prior evidence source in this repository
(``research/analysis/WEEKLY_FUTURE_VERIFICATION.md``) found a
different Weekly Future worked example where Low exceeded High -
that invariant must not be assumed here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class WeeklyFuture:
    """The session's Weekly Future High and Low.

    Attributes:
        weekly_future_id: This value's own identifier.
        session_id: The trading session this belongs to.
        high: Weekly Future High. Formula is MISSING INFORMATION.
        low: Weekly Future Low. Formula is MISSING INFORMATION.
        calculated_at: When this was computed - confirmed to be the
            first 5-minute candle's completion, 09:20 (Specification
            Rule 1).
    """

    weekly_future_id: uuid.UUID
    session_id: uuid.UUID
    high: Decimal
    low: Decimal
    calculated_at: datetime

    def __post_init__(self) -> None:
        if self.weekly_future_id is None:
            raise ValidationError("WeeklyFuture.weekly_future_id must not be None.")
        if self.session_id is None:
            raise ValidationError("WeeklyFuture.session_id must not be None.")
        if self.calculated_at is None:
            raise ValidationError("WeeklyFuture.calculated_at must not be None.")

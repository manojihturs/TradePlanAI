"""Premium: the basis for identifying a Reversal.

Traceability notes
-------------------
Referenced only indirectly, as the basis for identifying a Reversal
(REVERSAL-001). No rule defines Premium as a first-class concept yet
(which contract, CE/PE/both - see ``docs/DOMAIN_MODEL.md``). Modeled
as a minimal value holder only - deliberately thin, since adding
CE/PE-specific structure now would be inventing attributes the
evidence doesn't yet support.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_engine.domain import DomainValidationError


@dataclass(frozen=True)
class Premium:
    """A single observed premium value.

    Rule References
        REVERSAL-001

    Entity
        ENT-009

    Attributes:
        premium_id: Unique identifier for this Premium observation.
        value: The observed premium value. Must be positive.
        observed_at: When this value was observed.
    """

    premium_id: uuid.UUID
    value: Decimal
    observed_at: datetime

    def __post_init__(self) -> None:
        if self.premium_id is None:
            raise DomainValidationError("Premium.premium_id must not be None.")

        if self.value <= 0:
            raise DomainValidationError("Premium.value must be greater than 0.")

    # TODO (REVERSAL-001): Which specific premium behaviour
    # constitutes identifying a Reversal is Unknown. No identification
    # function exists on this type.

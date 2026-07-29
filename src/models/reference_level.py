"""ReferenceLevel: one strike-ladder level's CE/PE High/Low.

Traceability
------------
``research/architecture/DATA_DICTIONARY.md`` Section 4. CE/PE
High/Low source is CONFIRMED (Specification Rule 1): the first
5-minute candle (09:15-09:20), per contract. Ladder step size and
centering remain MISSING INFORMATION (Specification Section 20 items
14, 17) - this model represents a single level; the 13-level ladder
itself is assembled by an eventual ``reference_builder``
implementation, out of Sprint 1's scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class ReferenceLevel:
    """One strike's CE/PE High/Low reference values.

    Attributes:
        strike: The strike price. Must be positive.
        ce_high: CE contract's High over the first 5-minute candle.
        ce_low: CE contract's Low over the first 5-minute candle.
        pe_high: PE contract's High over the first 5-minute candle.
        pe_low: PE contract's Low over the first 5-minute candle.
    """

    strike: Decimal
    ce_high: Decimal
    ce_low: Decimal
    pe_high: Decimal
    pe_low: Decimal

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValidationError("ReferenceLevel.strike must be greater than 0.")
        if self.ce_high < self.ce_low:
            raise ValidationError(
                f"ReferenceLevel.ce_high ({self.ce_high}) is less than ce_low ({self.ce_low})."
            )
        if self.pe_high < self.pe_low:
            raise ValidationError(
                f"ReferenceLevel.pe_high ({self.pe_high}) is less than pe_low ({self.pe_low})."
            )

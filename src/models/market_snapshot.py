"""MarketSnapshot: one point-in-time market data observation.

Traceability
------------
``research/architecture/DATA_DICTIONARY.md`` Section 1. Candle vs.
tick cadence for post-09:21 evaluation is MISSING INFORMATION
(Specification Section 20 item 7), so this model supports both: OHLC
fields are optional and, if present, must all be present together
(candle mode); if absent, only ``underlying_price`` is required (tick
mode).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """One observed market data point - a candle (if OHLC fields are
    given) or a tick (if not).

    Attributes:
        timestamp: When this observation was made.
        underlying_price: The underlying's price at this observation.
            Must be positive.
        open: Candle open, if this is a candle-mode snapshot.
        high: Candle high, if this is a candle-mode snapshot.
        low: Candle low, if this is a candle-mode snapshot.
        close: Candle close, if this is a candle-mode snapshot.
        volume: Traded volume, if known. Must not be negative.
    """

    timestamp: datetime
    underlying_price: Decimal
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    volume: int | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            raise ValidationError("MarketSnapshot.timestamp must not be None.")
        if self.underlying_price <= 0:
            raise ValidationError("MarketSnapshot.underlying_price must be greater than 0.")
        if self.volume is not None and self.volume < 0:
            raise ValidationError("MarketSnapshot.volume must not be negative.")

        ohlc = (self.open, self.high, self.low, self.close)
        if any(value is not None for value in ohlc) and not all(
            value is not None for value in ohlc
        ):
            raise ValidationError(
                "MarketSnapshot open/high/low/close must be all present (candle mode) "
                "or all absent (tick mode)."
            )
        if self.high is not None and self.low is not None:
            if self.high < self.low:
                raise ValidationError(
                    f"MarketSnapshot high ({self.high}) is less than low ({self.low})."
                )
            if self.open is not None and not (self.low <= self.open <= self.high):
                raise ValidationError(
                    f"MarketSnapshot open ({self.open}) is outside "
                    f"[low, high] = [{self.low}, {self.high}]."
                )
            if self.close is not None and not (self.low <= self.close <= self.high):
                raise ValidationError(
                    f"MarketSnapshot close ({self.close}) is outside "
                    f"[low, high] = [{self.low}, {self.high}]."
                )

    def is_candle(self) -> bool:
        """Whether this snapshot carries full OHLC data."""
        return self.open is not None

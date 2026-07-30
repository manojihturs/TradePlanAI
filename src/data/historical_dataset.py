"""HistoricalDataset: an immutable, validated historical market-data set.

Traceability
------------
Field set matches this sprint's own instruction (symbol, timeframe,
date range, ordered snapshot collection, metadata). Only ever
constructed by :class:`~data.historical_data_provider.HistoricalDataProvider`
after successful validation - see that module for how "ordered" and
"validated" are guaranteed before this object exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot


@dataclass(frozen=True, slots=True)
class HistoricalDataset:
    """An immutable, chronologically-ordered set of historical
    :class:`~models.market_snapshot.MarketSnapshot` candles.

    Attributes:
        symbol: The instrument symbol this dataset covers.
        timeframe: The candle timeframe label (e.g. ``"5m"``) -
            structural only, not interpreted by this package.
        date_range_start: The earliest date covered, derived from the
            snapshots themselves.
        date_range_end: The latest date covered, derived from the
            snapshots themselves.
        snapshots: Every candle, in chronological order. Never empty.
        metadata: Free-form provenance notes (e.g. row count, source
            path) - not interpreted by this package.
    """

    symbol: str
    timeframe: str
    date_range_start: date
    date_range_end: date
    snapshots: tuple[MarketSnapshot, ...]
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValidationError("HistoricalDataset.symbol must not be blank.")
        if not self.timeframe or not self.timeframe.strip():
            raise ValidationError("HistoricalDataset.timeframe must not be blank.")
        if self.date_range_end < self.date_range_start:
            raise ValidationError(
                "HistoricalDataset.date_range_end must not be before date_range_start."
            )
        if not self.snapshots:
            raise ValidationError("HistoricalDataset.snapshots must not be empty.")
        for earlier, later in zip(self.snapshots, self.snapshots[1:]):
            if later.timestamp < earlier.timestamp:
                raise ValidationError("HistoricalDataset.snapshots must be in chronological order.")

    @property
    def key(self) -> str:
        """The unique, versioned identity of this dataset -
        ``"<symbol>@<timeframe>"`` - suitable as a dataset identifier
        for a replay session."""
        return f"{self.symbol}@{self.timeframe}"

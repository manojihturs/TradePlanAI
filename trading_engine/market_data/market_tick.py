"""MarketTick: one immutable, structurally-validated live price update.

Traceability notes
-------------------
Per ``research/implementation/DATA_MODEL_BLUEPRINT.md``, ``MarketTick``
is a net-new model, distinct from
:class:`trading_engine.replay.history_loader.Candle` (which represents
one already-closed historical OHLC bar) - a tick represents a single
live price observation, with no open/high/low/close aggregation. No
document evidences the real field set a broker's tick message carries;
this model contains only the fields Milestone I1's own Task ("Tick
model: Timestamp, Instrument, LTP, Volume, OI, Bid, Ask") specifies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_engine.market_data.exceptions import MarketDataValidationError
from trading_engine.market_data.instrument_resolver import InstrumentKey


@dataclass(frozen=True)
class MarketTick:
    """One live price observation for one instrument.

    Attributes:
        timestamp: When this tick was observed.
        instrument: The instrument this tick is for.
        last_traded_price: The most recent traded price. Must be
            positive.
        volume: Cumulative traded volume. Must not be negative.
        open_interest: Open interest at the time of this tick. Must
            not be negative.
        bid: The best bid price, if available.
        ask: The best ask price, if available. If both ``bid`` and
            ``ask`` are given, ``bid`` must not exceed ``ask``.
    """

    timestamp: datetime
    instrument: InstrumentKey
    last_traded_price: Decimal
    volume: int
    open_interest: int
    bid: Decimal | None = None
    ask: Decimal | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            raise MarketDataValidationError("MarketTick.timestamp must not be None.")

        if self.instrument is None:
            raise MarketDataValidationError("MarketTick.instrument must not be None.")

        if self.last_traded_price <= 0:
            raise MarketDataValidationError("MarketTick.last_traded_price must be greater than 0.")

        if self.volume < 0:
            raise MarketDataValidationError("MarketTick.volume must not be negative.")

        if self.open_interest < 0:
            raise MarketDataValidationError("MarketTick.open_interest must not be negative.")

        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise MarketDataValidationError(
                f"MarketTick.bid ({self.bid}) must not exceed ask ({self.ask})."
            )

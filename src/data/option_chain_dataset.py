"""OptionChainCandle / OptionChainDataset: multi-strike CE/PE candle series.

Traceability
------------
Backtest harness plumbing only - not a business rule.
``data.historical_data_provider.HistoricalDataProvider`` loads a
single instrument's plain OHLC series, with no strike/option-chain
dimension at all (see that module's own docstring on why). Running
the confirmed src/ pipeline end to end (Weekly Future through Exit)
needs, for every candle, every reference-ladder strike's CE and PE
observation simultaneously - this module is that shape, immutable and
chronologically ordered, mirroring
``data.historical_dataset.HistoricalDataset``'s own validation
conventions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from core.exceptions import ValidationError
from models.strike_chain_snapshot import StrikeChainSnapshot


@dataclass(frozen=True, slots=True)
class OptionChainCandle:
    """Every reference-ladder strike's CE/PE snapshot for one candle
    timestamp.

    Attributes:
        timestamp: The candle timestamp all ``strikes`` entries share.
        strikes: One :class:`~models.strike_chain_snapshot.StrikeChainSnapshot`
            per strike in the reference ladder, for this timestamp.
            Never empty.
    """

    timestamp: datetime
    strikes: tuple[StrikeChainSnapshot, ...]

    def __post_init__(self) -> None:
        if self.timestamp is None:
            raise ValidationError("OptionChainCandle.timestamp must not be None.")
        if not self.strikes:
            raise ValidationError("OptionChainCandle.strikes must not be empty.")
        for pair in self.strikes:
            if pair.ce.timestamp != self.timestamp:
                raise ValidationError(
                    f"OptionChainCandle.timestamp ({self.timestamp}) does not match "
                    f"strike {pair.strike}'s own snapshot timestamp ({pair.ce.timestamp})."
                )
        seen_strikes = {pair.strike for pair in self.strikes}
        if len(seen_strikes) != len(self.strikes):
            raise ValidationError("OptionChainCandle.strikes must not repeat a strike.")


@dataclass(frozen=True, slots=True)
class OptionChainDataset:
    """An immutable, chronologically-ordered set of
    :class:`OptionChainCandle`, for one trading session.

    Attributes:
        session_date: The trading day this dataset covers.
        candles: Every candle, in chronological order. Never empty.
    """

    session_date: date
    candles: tuple[OptionChainCandle, ...]

    def __post_init__(self) -> None:
        if self.session_date is None:
            raise ValidationError("OptionChainDataset.session_date must not be None.")
        if not self.candles:
            raise ValidationError("OptionChainDataset.candles must not be empty.")
        for earlier, later in zip(self.candles, self.candles[1:]):
            if later.timestamp < earlier.timestamp:
                raise ValidationError("OptionChainDataset.candles must be in chronological order.")

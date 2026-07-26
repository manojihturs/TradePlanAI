"""Module 3: Entry Signal.

Single responsibility: detect a confirmed entry from a Module 2
``PremiumMapping`` and the current 5-minute CE/PE candles. This module
contains NO exit, target, or stop-loss logic - those belong to later
modules.

Per specification, a trade is confirmed only when BOTH premiums
confirm within the SAME 5-minute candle:

    BUY CE:
        Condition 1: current CE premium crosses ABOVE its mapped CE level.
        Condition 2: current PE premium crosses BELOW its mapped PE level.

    BUY PE (the mirror):
        Condition 1: current PE premium crosses ABOVE its mapped PE level.
        Condition 2: current CE premium crosses BELOW its mapped CE level.

Both conditions must be true in the same candle, evaluated against
candle HIGH/LOW (intrabar touch), not candle close - confirmed
elsewhere in this session as the correct basis. A signal only fires on
a FRESH cross - i.e. the combined condition must transition from not-
satisfied to satisfied between consecutive candles, not merely still
be satisfied - also confirmed elsewhere in this session, not invented
here.

This is checked independently for the TOP mapping (CE<-PE Low,
PE<-CE High) and the BOTTOM mapping (CE<-PE High, PE<-CE Low), and
independently for every captured strike - both mappings use the exact
same crossing rule, mirrored onto their own pair of ladders.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Tuple

from strategy.premium_mapping import PremiumMapping

logger = logging.getLogger(__name__)


class EntrySignalError(Exception):
    """Raised when entry-signal detection cannot proceed.

    Distinguished from generic exceptions so callers can catch
    detection failures specifically without swallowing unrelated bugs.
    """


class TradeSide(Enum):
    """Which contract a confirmed entry signal is for."""

    CE = "CE"
    PE = "PE"


class MappingAnchor(Enum):
    """Which of Module 2's two independent anchors produced a signal."""

    TOP = "TOP"
    BOTTOM = "BOTTOM"


@dataclass(frozen=True)
class Candle:
    """A single 5-minute OHLC candle for one option contract.

    Attributes:
        open: Candle open price.
        high: Candle high price.
        low: Candle low price.
        close: Candle close price.
    """

    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        """Validate basic OHLC consistency.

        Raises:
            EntrySignalError: if high is below low, or open/close fall
                outside the [low, high] range - that indicates corrupt
                source data, not a valid candle.
        """
        if self.high < self.low:
            raise EntrySignalError(f"candle high ({self.high}) is below low ({self.low})")
        if not (self.low <= self.open <= self.high):
            raise EntrySignalError(
                f"candle open ({self.open}) is outside [low={self.low}, high={self.high}]"
            )
        if not (self.low <= self.close <= self.high):
            raise EntrySignalError(
                f"candle close ({self.close}) is outside [low={self.low}, high={self.high}]"
            )


@dataclass(frozen=True)
class EntrySignal:
    """A single confirmed entry, per specification.

    Attributes:
        timestamp: The candle timestamp the signal fired on.
        strike: The strike whose mapped levels confirmed the signal.
        side: TradeSide.CE or TradeSide.PE - which contract to buy.
        anchor: Which mapping (TOP or BOTTOM) produced this signal.
        ce_level: The mapped CE-chart level that was crossed.
        pe_level: The mapped PE-chart level that was crossed.
    """

    timestamp: datetime
    strike: int
    side: TradeSide
    anchor: MappingAnchor
    ce_level: float
    pe_level: float


def _raw_condition(
    ce_candle: Candle, pe_candle: Candle, ce_level: float, pe_level: float, side: TradeSide,
) -> bool:
    """The two-condition check for one side, one candle, one level pair.

    Args:
        ce_candle: This candle's CE OHLC.
        pe_candle: This candle's PE OHLC.
        ce_level: The mapped CE-chart level for this strike/anchor.
        pe_level: The mapped PE-chart level for this strike/anchor.
        side: TradeSide.CE checks the BUY CE condition pair; TradeSide.PE
            checks the BUY PE (mirror) condition pair.

    Returns:
        True if both conditions for ``side`` are satisfied by these
        candles (intrabar high/low touch basis), independent of
        whether this is a fresh cross or a still-standing one.
    """
    if side is TradeSide.CE:
        return ce_candle.high > ce_level and pe_candle.low < pe_level
    return pe_candle.high > pe_level and ce_candle.low < ce_level


class EntrySignalDetector:
    """Stateful fresh-cross detector for one session's Premium Mapping.

    Holds only the minimum state needed to tell a fresh cross from a
    still-standing one: the previous candle's raw (non-fresh) condition
    for every (strike, anchor, side) combination. Nothing about
    exits, targets, or stop-losses is tracked here.
    """

    def __init__(self, mapping: PremiumMapping) -> None:
        """Initialize the detector for a session's Premium Mapping.

        Args:
            mapping: The frozen ``PremiumMapping`` (Module 2 output)
                this detector evaluates candles against.
        """
        self._mapping = mapping
        self._prev_raw: Dict[Tuple[int, MappingAnchor, TradeSide], bool] = {}
        logger.info("EntrySignalDetector initialized for %s", mapping.session_date)

    @property
    def session_date(self) -> date:
        """The trading date this detector was built for."""
        return self._mapping.session_date

    def process_candle(
        self, timestamp: datetime, ce_candles: Dict[int, Candle], pe_candles: Dict[int, Candle],
    ) -> List[EntrySignal]:
        """Evaluate one 5-minute candle across every strike and anchor.

        Args:
            timestamp: The timestamp of this (already-closed) candle.
            ce_candles: strike -> this candle's CE OHLC, for every
                strike present in the Premium Mapping that has data
                this candle.
            pe_candles: strike -> this candle's PE OHLC, for every
                strike present in the Premium Mapping that has data
                this candle.

        Returns:
            A list of ``EntrySignal`` for every (strike, anchor, side)
            combination that produced a FRESH confirmed entry this
            candle. Empty if nothing confirmed - "otherwise NO TRADE"
            per specification, so an empty list is the normal case,
            not an error.
        """
        signals: List[EntrySignal] = []

        ladder_pairs = (
            (MappingAnchor.TOP, self._mapping.top_ce_ladder, self._mapping.top_pe_ladder),
            (MappingAnchor.BOTTOM, self._mapping.bottom_ce_ladder, self._mapping.bottom_pe_ladder),
        )

        for anchor, ce_ladder, pe_ladder in ladder_pairs:
            for strike in ce_ladder:
                if strike not in pe_ladder:
                    continue   # both ladders always share strikes in practice; skip defensively
                ce_candle = ce_candles.get(strike)
                pe_candle = pe_candles.get(strike)
                if ce_candle is None or pe_candle is None:
                    logger.debug("Skipping strike %d at %s: candle data missing", strike, timestamp)
                    continue

                ce_level = ce_ladder[strike]
                pe_level = pe_ladder[strike]

                for side in (TradeSide.CE, TradeSide.PE):
                    key = (strike, anchor, side)
                    raw = _raw_condition(ce_candle, pe_candle, ce_level, pe_level, side)
                    fresh = raw and not self._prev_raw.get(key, False)
                    if fresh:
                        signal = EntrySignal(
                            timestamp=timestamp, strike=strike, side=side, anchor=anchor,
                            ce_level=ce_level, pe_level=pe_level,
                        )
                        signals.append(signal)
                        logger.info(
                            "Entry signal: BUY %s at strike %d (%s anchor) - "
                            "ce_level=%.2f pe_level=%.2f, timestamp=%s",
                            side.value, strike, anchor.value, ce_level, pe_level, timestamp,
                        )
                    self._prev_raw[key] = raw

        return signals

"""Module 4: Exit Signal.

Single responsibility: given a confirmed entry (Module 3) and the
Premium Mapping (Module 2), determine Target and Mapped Stop Loss, and
detect which one occurs first. This module contains NO trailing stop,
competitor-movement, OI, synthetic-future, indicator, or time-based
exit logic - out of scope by specification unless explicitly requested.
It does not modify or depend on any internal state of
``strategy.entry_signal`` - it only reads the ``EntrySignal`` value
that module produces.

Exit priority, per specification:
    1. Target
    2. Mapped Stop Loss
    Whichever occurs first. If both occur in the same candle, Target
    takes priority (checked first).

Target and Mapped Stop Loss are derived from the SAME field ladder
that produced the entry price (confirmed elsewhere in this session):
the entry price is one value in one of Module 2's four ladders
(top_ce_ladder, top_pe_ladder, bottom_ce_ladder, bottom_pe_ladder),
sorted by strike. Sorted instead BY VALUE (not by strike position -
these ladders do not move monotonically with strike in the same
direction, confirmed elsewhere in this session), Target is the next-
higher value and Mapped Stop Loss is the next-lower value.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping, Optional, Tuple

from strategy.entry_signal import Candle, EntrySignal, MappingAnchor, TradeSide
from strategy.premium_mapping import PremiumMapping

logger = logging.getLogger(__name__)


class ExitSignalError(Exception):
    """Raised when exit-signal detection cannot proceed.

    Distinguished from generic exceptions so callers can catch
    detection failures specifically without swallowing unrelated bugs.
    """


class ExitReason(Enum):
    """Which of the two (and only two) supported exits fired."""

    TARGET = "TARGET"
    STOP_LOSS = "STOP_LOSS"


@dataclass(frozen=True)
class ExitLevels:
    """The Target and Mapped Stop Loss for one open position.

    Attributes:
        target: The next-higher value in the entry's own field ladder.
        stop_loss: The next-lower value in the entry's own field ladder.
    """

    target: float
    stop_loss: float

    def __post_init__(self) -> None:
        """Validate Target is above Stop Loss.

        Raises:
            ExitSignalError: if target <= stop_loss - that would mean
                the position has no room between entry and either exit,
                which indicates a broken ladder lookup, not a valid
                trade.
        """
        if self.target <= self.stop_loss:
            raise ExitSignalError(
                f"target ({self.target}) must be above stop_loss ({self.stop_loss})"
            )


@dataclass(frozen=True)
class ExitSignal:
    """A single confirmed exit.

    Attributes:
        timestamp: The candle timestamp the exit fired on.
        reason: ExitReason.TARGET or ExitReason.STOP_LOSS.
        exit_price: The Target or Stop Loss value that was hit.
    """

    timestamp: datetime
    reason: ExitReason
    exit_price: float


def _ladder_for_entry(entry: EntrySignal, mapping: PremiumMapping) -> Mapping[int, float]:
    """Select the single field ladder that produced ``entry``'s price.

    Args:
        entry: The confirmed entry to look up.
        mapping: The Premium Mapping (Module 2) the entry was detected
            against.

    Returns:
        The one ladder (of the mapping's four) whose value at
        ``entry.strike`` equals the entry price.
    """
    if entry.anchor is MappingAnchor.TOP:
        return mapping.top_ce_ladder if entry.side is TradeSide.CE else mapping.top_pe_ladder
    return mapping.bottom_ce_ladder if entry.side is TradeSide.CE else mapping.bottom_pe_ladder


def compute_exit_levels(entry: EntrySignal, mapping: PremiumMapping) -> ExitLevels:
    """Compute Target and Mapped Stop Loss for a confirmed entry.

    Target is the next-higher value, and Mapped Stop Loss the next-
    lower value, in the SAME field ladder that produced the entry
    price - ordered by VALUE, not by strike position (see module
    docstring).

    Args:
        entry: The confirmed entry (Module 3 output) to compute levels for.
        mapping: The Premium Mapping (Module 2) the entry was detected
            against.

    Returns:
        The ``ExitLevels`` (target, stop_loss) for this entry.

    Raises:
        ExitSignalError: if the entry's strike is not the ladder's
            lowest or highest value AND has no adjacent rung on the
            required side (i.e. there is no strike captured far enough
            beyond it to supply a Target or a Stop Loss).
    """
    ladder = _ladder_for_entry(entry, mapping)
    entry_price = entry.ce_level if entry.side is TradeSide.CE else entry.pe_level

    values_by_strike = sorted(ladder.items(), key=lambda kv: kv[1])
    index = next((i for i, (strike, _value) in enumerate(values_by_strike)
                  if strike == entry.strike), None)
    if index is None:
        raise ExitSignalError(
            f"entry strike {entry.strike} is not present in its own ladder - "
            f"cannot compute exit levels"
        )

    if index == 0:
        raise ExitSignalError(
            f"strike {entry.strike} is already the lowest value in its ladder "
            f"({entry_price}) - no lower rung available for a Mapped Stop Loss"
        )
    if index == len(values_by_strike) - 1:
        raise ExitSignalError(
            f"strike {entry.strike} is already the highest value in its ladder "
            f"({entry_price}) - no higher rung available for a Target"
        )

    stop_loss = values_by_strike[index - 1][1]
    target = values_by_strike[index + 1][1]

    logger.info(
        "Exit levels for %s entry at strike %d (%s anchor): entry=%.2f "
        "target=%.2f stop_loss=%.2f",
        entry.side.value, entry.strike, entry.anchor.value, entry_price, target, stop_loss,
    )
    return ExitLevels(target=target, stop_loss=stop_loss)


def check_exit(
    timestamp: datetime, candle: Candle, levels: ExitLevels,
) -> Optional[ExitSignal]:
    """Check whether Target or Mapped Stop Loss occurred on this candle.

    Priority: Target is checked first, Mapped Stop Loss second -
    whichever occurs first per specification. Both are checked against
    intrabar high/low (the same touch basis used for entries elsewhere
    in this session, not close), so a single candle whose range covers
    both will resolve to Target, matching the stated priority.

    Args:
        timestamp: The timestamp of this (already-closed) candle.
        candle: The traded contract's own OHLC candle for this timestamp.
        levels: The ``ExitLevels`` (target, stop_loss) for the open position.

    Returns:
        An ``ExitSignal`` if either level was reached this candle,
        else ``None`` - no exit is the normal case for most candles,
        not an error.
    """
    if candle.high >= levels.target:
        logger.info("Exit: TARGET hit at %.2f (candle high %.2f) at %s",
                    levels.target, candle.high, timestamp)
        return ExitSignal(timestamp=timestamp, reason=ExitReason.TARGET,
                           exit_price=levels.target)
    if candle.low <= levels.stop_loss:
        logger.info("Exit: STOP_LOSS hit at %.2f (candle low %.2f) at %s",
                    levels.stop_loss, candle.low, timestamp)
        return ExitSignal(timestamp=timestamp, reason=ExitReason.STOP_LOSS,
                           exit_price=levels.stop_loss)
    return None

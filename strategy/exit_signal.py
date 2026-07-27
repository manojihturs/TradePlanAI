"""Module 4: Exit Signal.

Single responsibility: given a confirmed entry (Module 3) and the
Premium Mapping (Module 2), determine Target, Mapped Stop Loss, and
(as of Version 1.1) Competitor Exit, and detect which occurs first.
This module contains NO trailing stop, OI, synthetic-future,
indicator, or time-based exit logic - out of scope by specification
unless explicitly requested. It does not modify or depend on any
internal state of ``strategy.entry_signal`` - it only reads the
``EntrySignal`` value that module produces.

Exit priority, per specification (Version 1.1):
    1. Competitor Exit
    2. Target
    3. Mapped Stop Loss
    Whichever occurs first. If multiple occur in the same candle,
    Competitor Exit takes priority over Target, which takes priority
    over Stop Loss.

Target and Mapped Stop Loss are derived from the SAME field ladder
that produced the entry price (confirmed elsewhere in this session):
the entry price is one value in one of Module 2's four ladders
(top_ce_ladder, top_pe_ladder, bottom_ce_ladder, bottom_pe_ladder),
sorted by strike. Sorted instead BY VALUE (not by strike position -
these ladders do not move monotonically with strike in the same
direction, confirmed elsewhere in this session), Target is the next-
higher value and Mapped Stop Loss is the next-lower value.

Competitor Exit (Version 1.1, deliberate strategy enhancement - see
CHANGELOG.md - NOT a defect correction) is derived from the SAME-
anchor, OPPOSITE-side ladder (e.g. a TOP CE entry's competitor ladder
is ``top_pe_ladder``): the threshold is the next-LOWER value (same
adjacent-rung-by-value convention as Stop Loss) below the level
already stored on the entry itself (``entry.pe_level`` for a CE entry,
``entry.ce_level`` for a PE entry - never recalculated). The contract
actually monitored against that threshold is always the SAME strike as
the open position, opposite side (the "competitor" contract, in this
project's existing terminology from Investigations #6 and #9) - see
``compute_competitor_exit_level`` and ``check_exit_with_competitor``.
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
    """Which of the three supported exits fired (Version 1.1 adds
    COMPETITOR_EXIT to the original TARGET/STOP_LOSS)."""

    TARGET = "TARGET"
    STOP_LOSS = "STOP_LOSS"
    COMPETITOR_EXIT = "COMPETITOR_EXIT"


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
        reason: ExitReason.TARGET, ExitReason.STOP_LOSS, or (Version
            1.1) ExitReason.COMPETITOR_EXIT.
        exit_price: The realized exit price on the TRADED contract's
            own side. For TARGET/STOP_LOSS this is the ladder rung
            value that was hit. For COMPETITOR_EXIT there is no ladder
            rung on the traded contract's own side (the trigger comes
            entirely from the competitor contract), so this is the
            traded contract's own trigger-candle OPEN price - see
            ``pricing_method``.
        competitor_ladder: (Version 1.1, COMPETITOR_EXIT only) Which of
            the mapping's four ladders supplied the trigger threshold
            ("TOP_PE", "TOP_CE", "BOTTOM_PE", "BOTTOM_CE"). ``None``
            for TARGET/STOP_LOSS.
        competitor_strike: (Version 1.1, COMPETITOR_EXIT only) The
            strike whose ladder entry supplied ``competitor_trigger_level``
            - NOT the strike of the contract that was actually
            monitored (that is always the position's own strike,
            opposite side). ``None`` for TARGET/STOP_LOSS.
        competitor_trigger_level: (Version 1.1, COMPETITOR_EXIT only)
            The threshold value the competitor candle's low reached or
            fell below. ``None`` for TARGET/STOP_LOSS.
        competitor_trigger_price: (Version 1.1, COMPETITOR_EXIT only)
            The competitor candle's actual low that triggered the
            exit. ``None`` for TARGET/STOP_LOSS.
        pricing_method: (Version 1.1, COMPETITOR_EXIT only)
            "CANDLE_APPROXIMATION" - this system only ever delivers
            already-closed 5-minute OHLC candles (no tick feed exists
            anywhere in this project), so ``exit_price`` is approximated
            from the traded contract's own trigger-candle OPEN rather
            than a true live tick. "LIVE_TICK" is reserved for a future
            tick-level feed this system does not currently have.
            ``None`` for TARGET/STOP_LOSS.
    """

    timestamp: datetime
    reason: ExitReason
    exit_price: float
    competitor_ladder: Optional[str] = None
    competitor_strike: Optional[int] = None
    competitor_trigger_level: Optional[float] = None
    competitor_trigger_price: Optional[float] = None
    pricing_method: Optional[str] = None


@dataclass(frozen=True)
class CompetitorLevel:
    """The Competitor Exit threshold for one open position (Version 1.1).

    Computed once, at position-open time, from the SAME-anchor,
    OPPOSITE-side ladder (see ``_competitor_ladder_for_entry``) - the
    ladder rung one position below (by VALUE) the level already stored
    on the entry itself. Reuses the existing ladder; computes nothing
    new about premiums or mapping.

    Attributes:
        ladder_name: Which of the mapping's four ladders produced this
            threshold ("TOP_PE", "TOP_CE", "BOTTOM_PE", "BOTTOM_CE") -
            for reporting only.
        source_strike: The strike whose ladder entry supplied
            ``trigger_level`` - for reporting only; NOT the contract
            being monitored (the competitor contract watched is always
            the position's own strike, opposite side).
        trigger_level: The threshold value - the competitor candle's
            LOW reaching this value or below fires the exit.
    """

    ladder_name: str
    source_strike: int
    trigger_level: float


def _competitor_ladder_for_entry(
    entry: EntrySignal, mapping: PremiumMapping,
) -> Tuple[str, Mapping[int, float]]:
    """Select the SAME-anchor, OPPOSITE-side ladder for Competitor Exit.

    TOP CE -> top_pe_ladder; TOP PE -> top_ce_ladder;
    BOTTOM CE -> bottom_pe_ladder; BOTTOM PE -> bottom_ce_ladder.
    Per specification (Version 1.1) - not inferred.

    Args:
        entry: The confirmed entry to select a competitor ladder for.
        mapping: The Premium Mapping the entry was detected against.

    Returns:
        A tuple of (ladder name, the ladder itself).
    """
    if entry.anchor is MappingAnchor.TOP:
        if entry.side is TradeSide.CE:
            return "TOP_PE", mapping.top_pe_ladder
        return "TOP_CE", mapping.top_ce_ladder
    if entry.side is TradeSide.CE:
        return "BOTTOM_PE", mapping.bottom_pe_ladder
    return "BOTTOM_CE", mapping.bottom_ce_ladder


def compute_competitor_exit_level(
    entry: EntrySignal, mapping: PremiumMapping,
) -> Optional[CompetitorLevel]:
    """Compute the Competitor Exit threshold for a confirmed entry (Version 1.1).

    Per specification: uses the SAME-anchor, opposite-side ladder; the
    "current mapped level" is the level already stored on ``entry``
    itself (``entry.pe_level`` for a CE entry, ``entry.ce_level`` for a
    PE entry - never recalculated); the threshold is the next LOWER
    rung by VALUE in that ladder (same adjacent-rung convention already
    used for Target/Stop Loss).

    Args:
        entry: The confirmed entry to compute a Competitor Exit
            threshold for.
        mapping: The Premium Mapping the entry was detected against.

    Returns:
        The ``CompetitorLevel`` to monitor, or ``None`` if the entry's
        own level is already the lowest value in the competitor ladder
        (no lower rung exists) - Competitor Exit simply does not apply
        to this trade in that case; this is not an error.
    """
    ladder_name, ladder = _competitor_ladder_for_entry(entry, mapping)
    current_level = entry.pe_level if entry.side is TradeSide.CE else entry.ce_level

    items = sorted(ladder.items(), key=lambda kv: kv[1])
    index = next((i for i, (strike, _value) in enumerate(items) if strike == entry.strike), None)
    if index is None or index == 0:
        logger.info(
            "No Competitor Exit level for %s entry at strike %d (%s anchor): "
            "no lower rung in %s ladder (current_level=%.2f)",
            entry.side.value, entry.strike, entry.anchor.value, ladder_name, current_level,
        )
        return None

    source_strike, trigger_level = items[index - 1]
    logger.info(
        "Competitor Exit level for %s entry at strike %d (%s anchor): "
        "ladder=%s source_strike=%d trigger_level=%.2f",
        entry.side.value, entry.strike, entry.anchor.value,
        ladder_name, source_strike, trigger_level,
    )
    return CompetitorLevel(ladder_name=ladder_name, source_strike=source_strike, trigger_level=trigger_level)


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


# ---------------------------------------------------------------------------
# Version 1.1 - Competitor Exit (deliberate strategy enhancement, see
# CHANGELOG.md - NOT a defect correction). Additive only: check_exit()
# above is untouched and still implements Target/Stop Loss exactly as
# before. This wraps it with a higher-priority Competitor Exit check.
# ---------------------------------------------------------------------------

def check_exit_with_competitor(
    timestamp: datetime,
    own_candle: Candle,
    competitor_candle: Optional[Candle],
    levels: ExitLevels,
    competitor: Optional[CompetitorLevel],
) -> Optional[ExitSignal]:
    """Check Competitor Exit, then Target, then Stop Loss, in that order.

    Competitor Exit has the highest priority per specification: if it
    fires on this candle, Target and Stop Loss are not evaluated at all
    for this candle, even if either would also have fired (verified by
    ``strategy/tests/test_exit_signal.py``'s simultaneous-trigger tests).

    Pricing: Competitor Exit is event-driven, like Target/Stop Loss,
    but has no ladder rung on the TRADED contract's own side - the
    trigger comes entirely from the competitor contract. This system
    only ever delivers already-closed 5-minute OHLC candles (no tick
    feed exists anywhere in this project), so the traded contract's
    exit price is approximated using its own trigger-candle OPEN (the
    earliest own-side price point available from OHLC alone), per
    instruction - never the CLOSE. ``pricing_method`` is always
    recorded as "CANDLE_APPROXIMATION" for this reason; "LIVE_TICK" is
    reserved for a future tick-level feed this system does not
    currently have, so historical and live results stay comparable
    under the same approximation.

    Args:
        timestamp: The timestamp of this (already-closed) candle.
        own_candle: The traded contract's own OHLC candle for this
            timestamp.
        competitor_candle: The competitor contract's (same strike,
            opposite side) OHLC candle for this timestamp, if
            available this candle - ``None`` if data is missing, in
            which case Competitor Exit is simply not evaluated this
            candle (falls through to Target/Stop Loss).
        levels: The Target/Stop Loss ``ExitLevels`` for this position.
        competitor: The ``CompetitorLevel`` threshold for this
            position, or ``None`` if Competitor Exit does not apply to
            it at all (see ``compute_competitor_exit_level``).

    Returns:
        An ``ExitSignal`` if Competitor Exit, Target, or Stop Loss
        fired this candle (in that priority order), else ``None``.
    """
    if competitor is not None and competitor_candle is not None:
        if competitor_candle.low <= competitor.trigger_level:
            exit_price = own_candle.open
            logger.info(
                "Exit: COMPETITOR_EXIT - competitor low %.2f <= trigger %.2f "
                "(ladder=%s source_strike=%d) at %s - own exit_price=%.2f (CANDLE_APPROXIMATION)",
                competitor_candle.low, competitor.trigger_level,
                competitor.ladder_name, competitor.source_strike, timestamp, exit_price,
            )
            return ExitSignal(
                timestamp=timestamp, reason=ExitReason.COMPETITOR_EXIT, exit_price=exit_price,
                competitor_ladder=competitor.ladder_name,
                competitor_strike=competitor.source_strike,
                competitor_trigger_level=competitor.trigger_level,
                competitor_trigger_price=competitor_candle.low,
                pricing_method="CANDLE_APPROXIMATION",
            )
    return check_exit(timestamp, own_candle, levels)

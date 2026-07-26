"""Module 5: Position Manager.

Single responsibility: track open/flat state across the Entry Engine
(Module 3) and Exit Engine (Module 4). This module computes NOTHING
itself - it does not detect entries and does not decide exits. It only:

    1. Accepts an already-confirmed ``EntrySignal`` (Module 3 output)
       and opens a position, delegating Target/Stop Loss computation
       to ``exit_signal.compute_exit_levels`` (Module 4).
    2. While a position is open, feeds each new candle to
       ``exit_signal.check_exit`` (Module 4) and closes the position
       if it fires.
    3. Refuses to open a second position while one is already open,
       and refuses to process an exit candle while flat.

Neither ``entry_signal.py`` nor ``exit_signal.py`` is modified by, or
needs to change for, this module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from strategy.entry_signal import Candle, EntrySignal
from strategy.exit_signal import ExitLevels, ExitSignal, check_exit, compute_exit_levels
from strategy.premium_mapping import PremiumMapping

logger = logging.getLogger(__name__)


class PositionManagerError(Exception):
    """Raised when a state transition is invalid.

    Distinguished from generic exceptions so callers can catch
    invalid-transition failures specifically (e.g. a caller bug that
    tries to open two positions at once) without swallowing unrelated
    bugs.
    """


class PositionState(Enum):
    """The Position Manager's only two states."""

    FLAT = "FLAT"
    OPEN = "OPEN"


@dataclass(frozen=True)
class Position:
    """An open position: the entry that created it and its exit levels.

    Attributes:
        entry: The ``EntrySignal`` (Module 3) that opened this position.
        exit_levels: The ``ExitLevels`` (Module 4) - Target and Mapped
            Stop Loss - this position exits on.
    """

    entry: EntrySignal
    exit_levels: ExitLevels


@dataclass(frozen=True)
class ClosedTrade:
    """A completed round trip: the entry that opened it, the exit that
    closed it.

    Attributes:
        entry: The ``EntrySignal`` (Module 3) that opened the position.
        exit: The ``ExitSignal`` (Module 4) that closed it.
    """

    entry: EntrySignal
    exit: ExitSignal


class PositionManager:
    """Holds at most one open position at a time and tracks its state.

    This class performs no entry detection and no exit decision-making
    of its own - see module docstring. It is intentionally minimal:
    two states (FLAT, OPEN), one position slot.
    """

    def __init__(self) -> None:
        """Initialize the manager in the FLAT state, with no position."""
        self._position: Optional[Position] = None
        logger.info("PositionManager initialized: FLAT")

    @property
    def state(self) -> PositionState:
        """The manager's current state."""
        return PositionState.OPEN if self._position is not None else PositionState.FLAT

    @property
    def is_flat(self) -> bool:
        """True if there is no open position."""
        return self._position is None

    @property
    def is_open(self) -> bool:
        """True if a position is currently open."""
        return self._position is not None

    @property
    def current_position(self) -> Optional[Position]:
        """The currently open ``Position``, or ``None`` if flat."""
        return self._position

    def open(self, entry: EntrySignal, mapping: PremiumMapping) -> Position:
        """Open a position from a confirmed entry signal.

        Args:
            entry: The confirmed ``EntrySignal`` (Module 3) to open a
                position from.
            mapping: The ``PremiumMapping`` (Module 2) the entry was
                detected against - passed through to Module 4's
                ``compute_exit_levels`` to derive Target/Stop Loss.

        Returns:
            The newly opened ``Position``.

        Raises:
            PositionManagerError: if a position is already open - only
                one position is held at a time, and the caller must
                wait for it to close (see ``process_candle``) before
                opening another.
        """
        if self.is_open:
            raise PositionManagerError(
                f"cannot open a new position while one is already open "
                f"(current: {self._position.entry.side.value} at strike "
                f"{self._position.entry.strike})"
            )
        exit_levels = compute_exit_levels(entry, mapping)
        self._position = Position(entry=entry, exit_levels=exit_levels)
        logger.info(
            "Position OPENED: %s at strike %d (%s anchor), target=%.2f stop_loss=%.2f",
            entry.side.value, entry.strike, entry.anchor.value,
            exit_levels.target, exit_levels.stop_loss,
        )
        return self._position

    def process_candle(self, timestamp: datetime, candle: Candle) -> Optional[ClosedTrade]:
        """Check the open position's exit levels against one candle.

        Args:
            timestamp: The timestamp of this (already-closed) candle.
            candle: The traded contract's own OHLC candle for this timestamp.

        Returns:
            A ``ClosedTrade`` if this candle closed the position
            (Target or Stop Loss hit), else ``None`` - no exit is the
            normal case for most candles, not an error. Always
            ``None`` while flat.

        Raises:
            PositionManagerError: never raised for being flat - calling
                this while flat is a harmless no-op, since a caller
                driving a candle stream forward doesn't need to track
                the manager's state itself between candles.
        """
        if self.is_flat:
            return None

        exit_signal = check_exit(timestamp, candle, self._position.exit_levels)
        if exit_signal is None:
            return None

        closed = ClosedTrade(entry=self._position.entry, exit=exit_signal)
        logger.info(
            "Position CLOSED: %s at strike %d - %s @ %.2f",
            closed.entry.side.value, closed.entry.strike,
            exit_signal.reason.value, exit_signal.exit_price,
        )
        self._position = None
        return closed

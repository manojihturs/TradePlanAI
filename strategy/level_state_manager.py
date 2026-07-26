"""Module 9: Level State Manager.

Single responsibility: track each mapped level's own state
(ACTIVE / USED / DISABLED), independent of the strategy engine
(Modules 3-8). This module contains NO entry, exit, or position logic
- it only answers "can a trade open from this level?" and records
"this level has now completed a trade."

Per specification, the state belongs to the MAPPED LEVEL ITSELF - not
to the strike, and not to the premium value. A single strike has four
independent mapped levels (its TOP-CE, TOP-PE, BOTTOM-CE, and
BOTTOM-PE ladder entries), each tracked separately. A level's identity
is therefore the triple (strike, anchor, side) that produced it -
exactly the same triple ``EntrySignal`` already carries.

Rules, exactly as specified:
    1. At the start of a trading day, after the premium map is built,
       every mapped level starts ACTIVE.
    2. A trade can only be opened from an ACTIVE level.
    3. When a trade from that level completes (Target or Stop Loss),
       that level becomes USED.
    4. USED levels cannot generate another entry during the same
       trading day.
    5. At the next trading day's map, the previous map (and all its
       level states) is discarded; the new map's levels all start
       ACTIVE again.
    Levels are never reactivated intraday.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet

from strategy.entry_signal import EntrySignal, MappingAnchor, TradeSide
from strategy.premium_mapping import PremiumMapping

logger = logging.getLogger(__name__)


class LevelStateError(Exception):
    """Raised when a level-state operation is invalid.

    Distinguished from generic exceptions so callers can catch
    invalid-transition failures specifically (e.g. marking a level
    USED that was never ACTIVE) without swallowing unrelated bugs.
    """


class LevelState(Enum):
    """The only three states a mapped level can be in."""

    ACTIVE = "ACTIVE"
    USED = "USED"
    DISABLED = "DISABLED"


@dataclass(frozen=True)
class LevelKey:
    """The identity of a single mapped level.

    Per specification, this identity is the level ITSELF - not the
    strike alone (a strike has four independent mapped levels) and not
    the premium value alone (two different strikes can coincidentally
    share a value, and would still be different levels).

    Attributes:
        strike: The strike that produced this mapped level.
        anchor: MappingAnchor.TOP or MappingAnchor.BOTTOM.
        side: TradeSide.CE or TradeSide.PE - which ladder this level
            belongs to (e.g. TOP+CE = the TOP anchor's CE-entry field,
            which is PE-Low at this strike).
    """

    strike: int
    anchor: MappingAnchor
    side: TradeSide


def level_key_from_entry(entry: EntrySignal) -> LevelKey:
    """Derive a ``LevelKey`` from a confirmed entry signal.

    Args:
        entry: The ``EntrySignal`` (Module 3) to derive a key from.

    Returns:
        The ``LevelKey`` identifying the mapped level this entry came from.
    """
    return LevelKey(strike=entry.strike, anchor=entry.anchor, side=entry.side)


def _all_level_keys(mapping: PremiumMapping) -> FrozenSet[LevelKey]:
    """Enumerate every mapped level present in a Premium Mapping.

    Args:
        mapping: The ``PremiumMapping`` (Module 2) to enumerate.

    Returns:
        A frozen set of every (strike, anchor, side) triple present
        across all four of the mapping's ladders.
    """
    keys = set()
    for strike in mapping.top_ce_ladder:
        keys.add(LevelKey(strike, MappingAnchor.TOP, TradeSide.CE))
    for strike in mapping.top_pe_ladder:
        keys.add(LevelKey(strike, MappingAnchor.TOP, TradeSide.PE))
    for strike in mapping.bottom_ce_ladder:
        keys.add(LevelKey(strike, MappingAnchor.BOTTOM, TradeSide.CE))
    for strike in mapping.bottom_pe_ladder:
        keys.add(LevelKey(strike, MappingAnchor.BOTTOM, TradeSide.PE))
    return frozenset(keys)


class LevelStateManager:
    """Tracks ACTIVE / USED / DISABLED state for every mapped level.

    Holds no reference to any strategy-engine object (Modules 3-8) -
    only ``LevelKey -> LevelState``. Callers (typically the Replay
    Engine or a live runner) are responsible for calling
    ``can_open()`` before opening a position and ``mark_used()`` after
    one closes.
    """

    def __init__(self) -> None:
        """Initialize with no levels tracked (call ``initialize_day`` first)."""
        self._states: Dict[LevelKey, LevelState] = {}

    def initialize_day(self, mapping: PremiumMapping) -> None:
        """Discard all prior state and set every level in ``mapping`` to ACTIVE.

        Per specification, this is the ONLY way levels ever become
        ACTIVE again after being USED - called once per trading day,
        after that day's premium map is built. A level's state from a
        prior day's map is never carried over or reused, since a new
        day's map is a completely new set of levels.

        Args:
            mapping: The new day's ``PremiumMapping`` (Module 2).
        """
        self._states = {key: LevelState.ACTIVE for key in _all_level_keys(mapping)}
        logger.info("LevelStateManager: initialized %d levels as ACTIVE for %s",
                    len(self._states), mapping.session_date)

    def register_level(self, key: LevelKey) -> None:
        """Register a level not present in the original day's map as ACTIVE.

        Needed because Module 8 (Ladder Expansion) can introduce new
        strikes - and therefore new mapped levels - intraday, after
        ``initialize_day`` has already run. A newly expanded level has
        never been touched, so it starts ACTIVE like every other level
        did at the start of the day. This is a no-op if the level is
        already tracked (its current state, whatever it is, is left
        alone - registering never resets an existing level).

        Args:
            key: The ``LevelKey`` to register.
        """
        if key not in self._states:
            self._states[key] = LevelState.ACTIVE
            logger.info("LevelStateManager: registered new level %s as ACTIVE (ladder expansion)", key)

    def get_state(self, key: LevelKey) -> LevelState:
        """Look up a level's current state.

        Args:
            key: The ``LevelKey`` to look up.

        Returns:
            The level's current ``LevelState``.

        Raises:
            LevelStateError: if ``key`` has never been registered
                (neither ``initialize_day`` nor ``register_level`` has
                seen it).
        """
        try:
            return self._states[key]
        except KeyError as exc:
            raise LevelStateError(f"level {key} has never been initialized") from exc

    def can_open(self, key: LevelKey) -> bool:
        """True only if ``key`` is currently ACTIVE - per rule 2.

        Args:
            key: The ``LevelKey`` to check.

        Returns:
            True if a trade may open from this level right now.

        Raises:
            LevelStateError: if ``key`` has never been registered.
        """
        return self.get_state(key) is LevelState.ACTIVE

    def mark_used(self, key: LevelKey) -> None:
        """Transition a level from ACTIVE to USED - per rule 3.

        Args:
            key: The ``LevelKey`` whose trade just completed (Target
                or Stop Loss - either exit reason marks the level USED,
                per specification: "when a trade from that level
                completes").

        Raises:
            LevelStateError: if ``key`` is not currently ACTIVE - a
                trade should never complete from a level that wasn't
                ACTIVE when it opened, so this indicates a caller bug,
                not a normal outcome.
        """
        current = self.get_state(key)
        if current is not LevelState.ACTIVE:
            raise LevelStateError(
                f"cannot mark level {key} USED - its current state is "
                f"{current.value}, not ACTIVE"
            )
        self._states[key] = LevelState.USED
        logger.info("LevelStateManager: level %s marked USED", key)

    def disable(self, key: LevelKey) -> None:
        """Manually set a level to DISABLED (not driven by any rule here).

        No specified rule currently sets DISABLED automatically - this
        exists only so an external caller (e.g. a manual override, or a
        future rule) has a way to disable a level without inventing a
        state transition inside this module.

        Args:
            key: The ``LevelKey`` to disable.
        """
        self._states[key] = LevelState.DISABLED
        logger.info("LevelStateManager: level %s manually DISABLED", key)

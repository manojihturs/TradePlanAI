"""Module 8: Ladder Expansion.

Single responsibility: when a confirmed entry occurs at the edge of
the currently captured strike range and the Exit Engine (Module 4)
cannot find an adjacent rung for a Mapped Stop Loss or Target, fetch
one more strike and extend the ladder - never skip the trade for this
reason. Per instruction:

    "The +/-6 strike range is only the initial data collection window,
    not a hard trading boundary... dynamically fetch the next required
    strike from Upstox and extend the premium ladder... Never skip a
    valid signal because of missing ladder data. Only skip a trade if
    the required historical premium data cannot be retrieved from the
    broker API."

This module contains NO network code itself - fetching is injected via
the same ``FirstCandleFetcher`` callback Module 1 already uses, so it
has no direct broker dependency. It does not modify Modules 1, 2, or 4
- it only calls their existing (Module 1/2) or new additive (Module 1's
``extend_capture``, Module 2's ``extend_mapping``) functions in a loop
until ``exit_signal.compute_exit_levels`` succeeds.
"""

from __future__ import annotations

import logging
from typing import Mapping, Tuple

from strategy.entry_signal import EntrySignal, MappingAnchor, TradeSide
from strategy.exit_signal import ExitLevels, compute_exit_levels
from strategy.level_capture import FirstCandleFetcher, LevelCapture, extend_capture
from strategy.premium_mapping import PremiumMapping, extend_mapping

logger = logging.getLogger(__name__)

#: Safety cap on how many strikes a single entry may trigger fetching -
#: only one more rung is ever needed in practice (one for SL, one for
#: Target, at most 2 per entry); this guards against an unexpected
#: infinite loop if the broker API keeps returning unusable data,
#: without ever refusing a trade purely because of a range boundary.
_MAX_EXPANSIONS_PER_ENTRY = 10


class LadderExpansionError(Exception):
    """Raised only when the required data could not be retrieved.

    Per instruction, this is the ONLY reason a valid signal is
    allowed to be skipped - never because a strike was outside the
    originally captured range.
    """


def _determine_expansion_strike(
    ladder: Mapping[int, float], strike_gap: int, need_lower: bool,
) -> int:
    """Work out which new strike would extend a ladder in the needed direction.

    A ladder's value does not necessarily increase with strike - CE
    High decreases as strike rises while PE Low increases, for example
    (confirmed elsewhere in this session). This is determined directly
    from the ladder's OWN existing data (comparing its lowest and
    highest captured strike's values), not assumed for any particular
    field, so it works generically for all four of Module 2's ladders.

    Args:
        ladder: The field ladder (strike -> value) that is missing a rung.
        strike_gap: The distance between adjacent tradable strikes.
        need_lower: True if a LOWER value is needed (Mapped Stop Loss
            missing), False if a HIGHER value is needed (Target missing).

    Returns:
        The new strike to fetch and add to the ladder.
    """
    strikes = sorted(ladder)
    lowest_strike, highest_strike = strikes[0], strikes[-1]
    value_increases_with_strike = ladder[highest_strike] > ladder[lowest_strike]

    if need_lower:
        return (lowest_strike - strike_gap) if value_increases_with_strike \
            else (highest_strike + strike_gap)
    return (highest_strike + strike_gap) if value_increases_with_strike \
        else (lowest_strike - strike_gap)


def _ladder_for_entry(entry: EntrySignal, mapping: PremiumMapping):
    """Same selection rule as exit_signal._ladder_for_entry (Module 4) -
    duplicated here as a read-only lookup rather than importing a
    private function across module boundaries."""
    if entry.anchor is MappingAnchor.TOP:
        return mapping.top_ce_ladder if entry.side is TradeSide.CE else mapping.top_pe_ladder
    return mapping.bottom_ce_ladder if entry.side is TradeSide.CE else mapping.bottom_pe_ladder


def ensure_exit_levels(
    entry: EntrySignal, capture: LevelCapture, mapping: PremiumMapping,
    strike_gap: int, fetch_first_candle: FirstCandleFetcher,
) -> Tuple[ExitLevels, LevelCapture, PremiumMapping]:
    """Compute exit levels for an entry, expanding the ladder as needed.

    Tries ``exit_signal.compute_exit_levels`` first. If it fails
    because the entry's strike is at the edge of the currently
    captured ladder, fetches one more strike (in the correct value
    direction, determined from the ladder's own data), extends both
    the capture and the mapping, and retries - repeating until it
    succeeds or the safety cap is hit.

    Args:
        entry: The confirmed entry to compute exit levels for.
        capture: The current ``LevelCapture`` (Module 1) - possibly
            already extended from a prior call.
        mapping: The current ``PremiumMapping`` (Module 2) - possibly
            already extended from a prior call.
        strike_gap: The distance between adjacent tradable strikes.
        fetch_first_candle: The same callback shape Module 1 uses to
            fetch a strike's first-5-minute candle.

    Returns:
        A tuple of (exit_levels, capture, mapping) - capture and
        mapping are returned because they may have been extended
        (new objects; the originals are untouched, per their
        immutability) and the caller should keep using the returned
        versions for any further lookups this session.

    Raises:
        LadderExpansionError: if the required strike's data cannot be
            retrieved from the broker API, or if more than
            ``_MAX_EXPANSIONS_PER_ENTRY`` expansions are attempted
            without success - the only permitted reasons to give up on
            an otherwise-valid signal, per instruction.
    """
    for attempt in range(_MAX_EXPANSIONS_PER_ENTRY):
        ladder = _ladder_for_entry(entry, mapping)
        values_by_strike = sorted(ladder.items(), key=lambda kv: kv[1])
        index = next((i for i, (strike, _v) in enumerate(values_by_strike)
                      if strike == entry.strike), None)

        # index is None (entry's strike not yet in this ladder) or both
        # neighbours already exist: not an edge case this module handles -
        # let Module 4 compute (and, if truly unresolvable, raise) normally.
        if index is None or (0 < index < len(values_by_strike) - 1):
            return compute_exit_levels(entry, mapping), capture, mapping

        needs_lower_rung = index == 0
        new_strike = _determine_expansion_strike(ladder, strike_gap, need_lower=needs_lower_rung)
        logger.info(
            "Ladder expansion needed for %s at strike %d (%s anchor): "
            "fetching strike %d (attempt %d)",
            entry.side.value, entry.strike, entry.anchor.value, new_strike, attempt + 1,
        )
        try:
            capture = extend_capture(capture, new_strike, fetch_first_candle)
            mapping = extend_mapping(mapping, capture, new_strike)
        except Exception as fetch_exc:
            raise LadderExpansionError(
                f"could not retrieve strike {new_strike} from the broker API "
                f"to extend the ladder for {entry.side.value} at strike "
                f"{entry.strike}: {fetch_exc}"
            ) from fetch_exc

    raise LadderExpansionError(
        f"exceeded {_MAX_EXPANSIONS_PER_ENTRY} ladder expansion attempts for "
        f"{entry.side.value} at strike {entry.strike} without finding a usable rung"
    )

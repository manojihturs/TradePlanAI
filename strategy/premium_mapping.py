"""Module 2: Premium Mapping.

Single responsibility: from Module 1's frozen ``LevelCapture``, build
the four cross-plotted premium ladders the strategy trades off of.
This module performs NO entry, exit, target, or stop-loss logic -
that is out of scope by specification and belongs to later modules.

Per specification, there is no shared "ATM" concept here - the Top
strike and Bottom strike are two independent anchors, each rounded to
the nearest tradable strike, each with its own field pairing:

    TOP anchor (round(Top strike)):
        CE chart <- PE Low   (PE's Low, at every captured strike, is the
                               reference ladder plotted on the CE chart)
        PE chart <- CE High  (CE's High, at every captured strike, is the
                               reference ladder plotted on the PE chart)

    BOTTOM anchor (round(Bottom strike)):
        CE chart <- PE High
        PE chart <- CE Low

The rounding itself reuses ``level_capture.compute_atm_strike`` (round
to the nearest strike_gap) since that is exactly the rounding rule
confirmed for Top/Bottom - it is not duplicated here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Mapping

from strategy.level_capture import LevelCapture, LevelCaptureError, compute_atm_strike

logger = logging.getLogger(__name__)


class PremiumMappingError(Exception):
    """Raised when the premium mapping cannot be built.

    Distinguished from generic exceptions so callers can catch mapping
    failures specifically without accidentally swallowing unrelated bugs.
    """


@dataclass(frozen=True)
class PremiumMapping:
    """The complete, frozen output of Module 2 for one session.

    Attributes:
        session_date: The trading date this mapping belongs to.
        top_strike_rounded: The Top strike (from Module 1), rounded to
            the nearest tradable strike - the TOP anchor.
        bottom_strike_rounded: The Bottom strike (from Module 1),
            rounded to the nearest tradable strike - the BOTTOM anchor.
        top_ce_ladder: strike -> PE Low, for every captured strike -
            the reference ladder plotted on the CE chart under the TOP
            anchor.
        top_pe_ladder: strike -> CE High, for every captured strike -
            the reference ladder plotted on the PE chart under the TOP
            anchor.
        bottom_ce_ladder: strike -> PE High, for every captured strike -
            the reference ladder plotted on the CE chart under the
            BOTTOM anchor.
        bottom_pe_ladder: strike -> CE Low, for every captured strike -
            the reference ladder plotted on the PE chart under the
            BOTTOM anchor.
    """

    session_date: date
    top_strike_rounded: int
    bottom_strike_rounded: int
    top_ce_ladder: Mapping[int, float]
    top_pe_ladder: Mapping[int, float]
    bottom_ce_ladder: Mapping[int, float]
    bottom_pe_ladder: Mapping[int, float]

    def top_ce_level(self, strike: int) -> float:
        """PE Low at ``strike`` - the TOP-anchor CE-chart reference level.

        Args:
            strike: The strike to look up.

        Returns:
            The PE Low value captured at ``strike``.

        Raises:
            PremiumMappingError: if ``strike`` was not captured.
        """
        return self._lookup(self.top_ce_ladder, strike)

    def top_pe_level(self, strike: int) -> float:
        """CE High at ``strike`` - the TOP-anchor PE-chart reference level.

        Args:
            strike: The strike to look up.

        Returns:
            The CE High value captured at ``strike``.

        Raises:
            PremiumMappingError: if ``strike`` was not captured.
        """
        return self._lookup(self.top_pe_ladder, strike)

    def bottom_ce_level(self, strike: int) -> float:
        """PE High at ``strike`` - the BOTTOM-anchor CE-chart reference level.

        Args:
            strike: The strike to look up.

        Returns:
            The PE High value captured at ``strike``.

        Raises:
            PremiumMappingError: if ``strike`` was not captured.
        """
        return self._lookup(self.bottom_ce_ladder, strike)

    def bottom_pe_level(self, strike: int) -> float:
        """CE Low at ``strike`` - the BOTTOM-anchor PE-chart reference level.

        Args:
            strike: The strike to look up.

        Returns:
            The CE Low value captured at ``strike``.

        Raises:
            PremiumMappingError: if ``strike`` was not captured.
        """
        return self._lookup(self.bottom_pe_ladder, strike)

    @staticmethod
    def _lookup(ladder: Mapping[int, float], strike: int) -> float:
        try:
            return ladder[strike]
        except KeyError as exc:
            raise PremiumMappingError(
                f"strike {strike} is not in this ladder "
                f"(captured strikes: {sorted(ladder)})"
            ) from exc


def build_premium_mapping(capture: LevelCapture, strike_gap: int) -> PremiumMapping:
    """Build the four premium ladders from a frozen Module 1 capture.

    Args:
        capture: The frozen ``LevelCapture`` produced by
            ``level_capture.capture_levels`` (Module 1).
        strike_gap: The distance between adjacent tradable strikes,
            used only to round the Top/Bottom strikes to a tradable
            strike (reuses ``compute_atm_strike``'s rounding rule).

    Returns:
        A frozen ``PremiumMapping`` for the session.

    Raises:
        PremiumMappingError: if the rounded Top or Bottom anchor falls
            outside the strikes captured by Module 1 - the ladders
            cannot be built without that anchor's own data.
    """
    top_strike_rounded = compute_atm_strike(capture.top_strike, strike_gap)
    bottom_strike_rounded = compute_atm_strike(capture.bottom_strike, strike_gap)

    logger.info(
        "Building premium mapping for %s: top=%.2f->%d bottom=%.2f->%d",
        capture.session_date, capture.top_strike, top_strike_rounded,
        capture.bottom_strike, bottom_strike_rounded,
    )

    for anchor_name, anchor in (("Top", top_strike_rounded), ("Bottom", bottom_strike_rounded)):
        try:
            capture.get_levels(anchor)
        except LevelCaptureError as exc:
            raise PremiumMappingError(
                f"{anchor_name} anchor strike {anchor} was not captured by "
                f"Module 1 for {capture.session_date}: {exc}"
            ) from exc

    top_ce_ladder = {strike: levels.pe_low for strike, levels in capture.levels.items()}
    top_pe_ladder = {strike: levels.ce_high for strike, levels in capture.levels.items()}
    bottom_ce_ladder = {strike: levels.pe_high for strike, levels in capture.levels.items()}
    bottom_pe_ladder = {strike: levels.ce_low for strike, levels in capture.levels.items()}

    logger.info("Premium mapping complete for %s: %d strikes per ladder",
                capture.session_date, len(top_ce_ladder))

    return PremiumMapping(
        session_date=capture.session_date,
        top_strike_rounded=top_strike_rounded,
        bottom_strike_rounded=bottom_strike_rounded,
        top_ce_ladder=top_ce_ladder,
        top_pe_ladder=top_pe_ladder,
        bottom_ce_ladder=bottom_ce_ladder,
        bottom_pe_ladder=bottom_pe_ladder,
    )


# ---------------------------------------------------------------------------
# Additive extension (2026-07-27) - mirrors level_capture.extend_capture().
# Does not change build_premium_mapping() or any existing behavior - only
# adds the ability to grow an existing, already-frozen PremiumMapping with
# one more strike's levels, once an extended LevelCapture has that strike
# (see strategy/ladder_expansion.py, Module 8). PremiumMapping remains
# immutable: this returns a NEW PremiumMapping, leaving the original
# untouched.
def extend_mapping(mapping: PremiumMapping, capture: LevelCapture, new_strike: int) -> PremiumMapping:
    """Return a new PremiumMapping with one additional strike added to
    all four ladders.

    Args:
        mapping: The existing, already-frozen ``PremiumMapping`` to extend.
        capture: A ``LevelCapture`` that already contains ``new_strike``
            (typically the result of ``level_capture.extend_capture``).
        new_strike: The additional strike to add to every ladder.

    Returns:
        A new ``PremiumMapping`` identical to ``mapping`` except with
        ``new_strike`` present in all four ladders. top_strike_rounded
        and bottom_strike_rounded are unchanged.

    Raises:
        PremiumMappingError: if ``new_strike`` is not present in ``capture``.
    """
    if new_strike in mapping.top_ce_ladder:
        logger.debug("extend_mapping: strike %d already present, no-op", new_strike)
        return mapping

    try:
        levels = capture.get_levels(new_strike)
    except LevelCaptureError as exc:
        raise PremiumMappingError(
            f"cannot extend mapping to strike {new_strike}: not present in "
            f"the supplied capture: {exc}"
        ) from exc

    new_top_ce = dict(mapping.top_ce_ladder); new_top_ce[new_strike] = levels.pe_low
    new_top_pe = dict(mapping.top_pe_ladder); new_top_pe[new_strike] = levels.ce_high
    new_bottom_ce = dict(mapping.bottom_ce_ladder); new_bottom_ce[new_strike] = levels.pe_high
    new_bottom_pe = dict(mapping.bottom_pe_ladder); new_bottom_pe[new_strike] = levels.ce_low

    logger.info("Ladder expansion: strike %d added to premium mapping for %s",
                new_strike, mapping.session_date)

    return PremiumMapping(
        session_date=mapping.session_date,
        top_strike_rounded=mapping.top_strike_rounded,
        bottom_strike_rounded=mapping.bottom_strike_rounded,
        top_ce_ladder=new_top_ce,
        top_pe_ladder=new_top_pe,
        bottom_ce_ladder=new_bottom_ce,
        bottom_pe_ladder=new_bottom_pe,
    )

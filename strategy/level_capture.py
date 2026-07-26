"""Module 1: Level Capture.

Single responsibility: freeze the first 5-minute candle of the trading
session and derive the immutable set of strike-level data the rest of
the strategy is built on.

This module implements ONLY the following, per specification:

    1. Freeze the first 5-minute candle (09:15-09:20) of the underlying
       spot index and of every option contract in the strike range.
    2. Compute the ATM strike from the spot's 09:20 open price.
    3. Compute the Top strike:    Top    = Open + (CE_High(ATM) - PE_Low(ATM))
    4. Compute the Bottom strike: Bottom = Open - (PE_High(ATM) - CE_Low(ATM))
       Top and Bottom are left UNROUNDED - they are not snapped to the
       nearest tradable strike.
    5. Generate the strike range ATM +/- ``num_strikes``.
    6. Fetch the first 5-minute CE High/Low and PE High/Low for every
       strike in that range.
    7. Freeze the result permanently (the returned object is immutable).

This module contains NO entry, exit, target, stop-loss, or premium-
mapping logic - that is out of scope by specification and belongs to
later modules. It also contains no network/HTTP code: fetching the
underlying candle data is injected via the ``FirstCandleFetcher``
protocol so this module can be unit tested with no network access and
compiles independently of any specific market-data provider.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Dict, Mapping, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

#: (open, high, low, close) of one 5-minute candle.
OHLC = Tuple[float, float, float, float]

#: Callback the caller supplies to fetch a first-5-minute candle for a
#: given (strike, side). ``side`` is the literal string "CE" or "PE".
#: This module never performs I/O itself - see module docstring.
FirstCandleFetcher = Callable[[int, str], OHLC]


class LevelCaptureError(Exception):
    """Raised when level capture cannot be completed.

    Distinguished from generic exceptions so callers can catch capture
    failures specifically (e.g. to retry or alert) without accidentally
    swallowing unrelated bugs.
    """


@dataclass(frozen=True)
class StrikeLevels:
    """Frozen first-5-minute CE/PE High/Low for a single strike.

    Attributes:
        strike: The option strike price.
        ce_high: First-5-minute high of the CE (call) contract at this strike.
        ce_low: First-5-minute low of the CE (call) contract at this strike.
        pe_high: First-5-minute high of the PE (put) contract at this strike.
        pe_low: First-5-minute low of the PE (put) contract at this strike.
    """

    strike: int
    ce_high: float
    ce_low: float
    pe_high: float
    pe_low: float

    def __post_init__(self) -> None:
        """Validate the captured levels are internally consistent.

        Raises:
            LevelCaptureError: if a High is below its own Low for either
                side - that would indicate corrupt/misread source data,
                not a valid market state.
        """
        if self.ce_high < self.ce_low:
            raise LevelCaptureError(
                f"strike {self.strike}: CE high ({self.ce_high}) is below "
                f"CE low ({self.ce_low})"
            )
        if self.pe_high < self.pe_low:
            raise LevelCaptureError(
                f"strike {self.strike}: PE high ({self.pe_high}) is below "
                f"PE low ({self.pe_low})"
            )


@dataclass(frozen=True)
class LevelCapture:
    """The complete, permanently-frozen output of Module 1 for one session.

    Attributes:
        session_date: The trading date this capture belongs to.
        spot_open: The underlying spot index's 09:20 open price.
        atm: The at-the-money strike, derived from ``spot_open``.
        top_strike: Open + (CE_High(atm) - PE_Low(atm)). Unrounded.
        bottom_strike: Open - (PE_High(atm) - CE_Low(atm)). Unrounded.
        levels: Immutable mapping of strike -> StrikeLevels, covering
            atm +/- num_strikes.
    """

    session_date: date
    spot_open: float
    atm: int
    top_strike: float
    bottom_strike: float
    levels: Mapping[int, StrikeLevels] = field(repr=False)

    def get_levels(self, strike: int) -> StrikeLevels:
        """Look up the frozen levels for one strike.

        Args:
            strike: The strike price to look up.

        Returns:
            The ``StrikeLevels`` captured for that strike.

        Raises:
            LevelCaptureError: if ``strike`` was not captured (outside
                the +/- num_strikes range, or missing source data).
        """
        try:
            return self.levels[strike]
        except KeyError as exc:
            raise LevelCaptureError(
                f"strike {strike} was not captured for {self.session_date} "
                f"(captured strikes: {sorted(self.levels)})"
            ) from exc


# ---------------------------------------------------------------------------
# Pure calculation functions (no I/O - fully unit-testable)
# ---------------------------------------------------------------------------

def compute_atm_strike(spot_open: float, strike_gap: int) -> int:
    """Round the spot's open price to the nearest tradable strike.

    Args:
        spot_open: The underlying spot index's 09:20 open price.
        strike_gap: The distance between adjacent tradable strikes
            (e.g. 50 for NIFTY).

    Returns:
        The nearest strike to ``spot_open``, as an int.

    Raises:
        LevelCaptureError: if ``strike_gap`` is not a positive integer.
    """
    if strike_gap <= 0:
        raise LevelCaptureError(f"strike_gap must be positive, got {strike_gap}")
    return int(round(spot_open / strike_gap) * strike_gap)


def compute_top_strike(spot_open: float, ce_high_atm: float, pe_low_atm: float) -> float:
    """Top = Open + (CE_High(ATM) - PE_Low(ATM)). Unrounded, per specification.

    Args:
        spot_open: The underlying spot index's 09:20 open price.
        ce_high_atm: First-5-minute CE high at the ATM strike.
        pe_low_atm: First-5-minute PE low at the ATM strike.

    Returns:
        The raw (unrounded) Top strike value.
    """
    return spot_open + (ce_high_atm - pe_low_atm)


def compute_bottom_strike(spot_open: float, pe_high_atm: float, ce_low_atm: float) -> float:
    """Bottom = Open - (PE_High(ATM) - CE_Low(ATM)). Unrounded, per specification.

    Args:
        spot_open: The underlying spot index's 09:20 open price.
        pe_high_atm: First-5-minute PE high at the ATM strike.
        ce_low_atm: First-5-minute CE low at the ATM strike.

    Returns:
        The raw (unrounded) Bottom strike value.
    """
    return spot_open - (pe_high_atm - ce_low_atm)


def generate_strike_range(atm: int, strike_gap: int, num_strikes: int) -> Tuple[int, ...]:
    """Generate the strike range ATM +/- ``num_strikes``, inclusive of ATM.

    Args:
        atm: The at-the-money strike.
        strike_gap: The distance between adjacent tradable strikes.
        num_strikes: How many strikes to include on each side of ATM.

    Returns:
        A tuple of strikes, ascending, e.g. for atm=24150, strike_gap=50,
        num_strikes=6: (23850, 23900, ..., 24150, ..., 24450).

    Raises:
        LevelCaptureError: if ``strike_gap`` is not positive or
            ``num_strikes`` is negative.
    """
    if strike_gap <= 0:
        raise LevelCaptureError(f"strike_gap must be positive, got {strike_gap}")
    if num_strikes < 0:
        raise LevelCaptureError(f"num_strikes must be non-negative, got {num_strikes}")
    return tuple(atm + i * strike_gap for i in range(-num_strikes, num_strikes + 1))


# ---------------------------------------------------------------------------
# Orchestration (the only function in this module that performs I/O,
# and only via the injected fetcher callbacks - see module docstring)
# ---------------------------------------------------------------------------

def capture_levels(
    session_date: date,
    spot_open: float,
    strike_gap: int,
    num_strikes: int,
    fetch_first_candle: FirstCandleFetcher,
) -> LevelCapture:
    """Run the full Module 1 workflow and return the frozen result.

    Steps (per specification): compute ATM from ``spot_open`` -> fetch
    the ATM contract's own first-5-minute candle to compute Top/Bottom
    -> generate the ATM +/- ``num_strikes`` strike range -> fetch every
    strike's first-5-minute CE/PE High/Low -> freeze.

    Args:
        session_date: The trading date being captured.
        spot_open: The underlying spot index's 09:20 open price.
        strike_gap: The distance between adjacent tradable strikes.
        num_strikes: How many strikes to include on each side of ATM.
        fetch_first_candle: Callback of the form
            ``fetch_first_candle(strike, side) -> (open, high, low, close)``
            returning the first-5-minute candle for a given strike/side.
            Injected so this module has no direct network dependency.

    Returns:
        A frozen ``LevelCapture`` for the session.

    Raises:
        LevelCaptureError: if any required strike/side candle could not
            be fetched, or if the fetched data fails internal
            consistency checks (see ``StrikeLevels.__post_init__``).
    """
    atm = compute_atm_strike(spot_open, strike_gap)
    logger.info("Level capture starting for %s: spot_open=%.2f atm=%d",
                session_date, spot_open, atm)

    strikes = generate_strike_range(atm, strike_gap, num_strikes)

    captured: Dict[int, StrikeLevels] = {}
    for strike in strikes:
        try:
            _, ce_high, ce_low, _ = fetch_first_candle(strike, "CE")
            _, pe_high, pe_low, _ = fetch_first_candle(strike, "PE")
        except Exception as exc:
            raise LevelCaptureError(
                f"failed to fetch first-5-minute candle for strike {strike} "
                f"on {session_date}: {exc}"
            ) from exc
        captured[strike] = StrikeLevels(
            strike=strike, ce_high=ce_high, ce_low=ce_low,
            pe_high=pe_high, pe_low=pe_low,
        )
        logger.debug("Captured strike %d: CE(H=%.2f L=%.2f) PE(H=%.2f L=%.2f)",
                     strike, ce_high, ce_low, pe_high, pe_low)

    if atm not in captured:
        # Cannot happen given generate_strike_range always includes atm,
        # but checked explicitly since Top/Bottom depend on it - fail
        # loudly rather than let a KeyError surface from deep inside.
        raise LevelCaptureError(f"ATM strike {atm} missing from captured levels")

    atm_levels = captured[atm]
    top_strike = compute_top_strike(spot_open, atm_levels.ce_high, atm_levels.pe_low)
    bottom_strike = compute_bottom_strike(spot_open, atm_levels.pe_high, atm_levels.ce_low)

    logger.info("Level capture complete for %s: top=%.2f bottom=%.2f (%d strikes)",
                session_date, top_strike, bottom_strike, len(captured))

    return LevelCapture(
        session_date=session_date,
        spot_open=spot_open,
        atm=atm,
        top_strike=top_strike,
        bottom_strike=bottom_strike,
        levels=captured,
    )


# ---------------------------------------------------------------------------
# Additive extension (2026-07-27) - per instruction, the +/- num_strikes
# range from capture_levels() is only the INITIAL data collection window,
# not a hard trading boundary. This does not change capture_levels() or
# any existing behavior - it only adds the ability to grow an existing,
# already-frozen LevelCapture with one more strike's data on demand
# (e.g. when an entry occurs at the current edge and a Mapped Stop Loss
# or Target needs one more adjacent rung - see strategy/ladder_expansion.py,
# Module 8). LevelCapture itself remains immutable: this returns a NEW
# LevelCapture, leaving the original untouched.
def extend_capture(
    capture: LevelCapture, new_strike: int, fetch_first_candle: FirstCandleFetcher,
) -> LevelCapture:
    """Return a new LevelCapture with one additional strike's levels added.

    Args:
        capture: The existing, already-frozen ``LevelCapture`` to extend.
        new_strike: The additional strike to capture. If already present
            in ``capture``, this is a no-op (the original is returned).
        fetch_first_candle: Same callback shape as ``capture_levels`` -
            ``fetch_first_candle(strike, side) -> (open, high, low, close)``.

    Returns:
        A new ``LevelCapture`` identical to ``capture`` except with
        ``new_strike`` added to ``levels``. Top/Bottom/ATM/spot_open are
        unchanged - they depend only on the original ATM strike's own
        candle, already captured.

    Raises:
        LevelCaptureError: if ``new_strike``'s candle data could not be
            fetched, or fails internal consistency checks.
    """
    if new_strike in capture.levels:
        logger.debug("extend_capture: strike %d already captured, no-op", new_strike)
        return capture

    try:
        _, ce_high, ce_low, _ = fetch_first_candle(new_strike, "CE")
        _, pe_high, pe_low, _ = fetch_first_candle(new_strike, "PE")
    except Exception as exc:
        raise LevelCaptureError(
            f"failed to fetch first-5-minute candle for strike {new_strike} "
            f"on {capture.session_date} (ladder expansion): {exc}"
        ) from exc

    new_levels = dict(capture.levels)
    new_levels[new_strike] = StrikeLevels(
        strike=new_strike, ce_high=ce_high, ce_low=ce_low, pe_high=pe_high, pe_low=pe_low,
    )
    logger.info("Ladder expansion: strike %d added to capture for %s",
                new_strike, capture.session_date)

    return LevelCapture(
        session_date=capture.session_date,
        spot_open=capture.spot_open,
        atm=capture.atm,
        top_strike=capture.top_strike,
        bottom_strike=capture.bottom_strike,
        levels=new_levels,
    )

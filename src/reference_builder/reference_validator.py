"""ReferenceValidator: structural validation for the reference ladder.

Traceability
------------
Specification Section 6: "Generate 13 strike levels: ATM, 6 ITM, 6
OTM." The ladder *size* (13) and *strike uniqueness* are CONFIRMED
structural facts; ladder *spacing* (50-point in the one example vs.
some other step) is explicitly MISSING INFORMATION (Specification
Section 20 item 14) and is never assumed or enforced here - this
validator accepts whatever strike values the caller supplies, in
whatever spacing, and only checks that there are exactly 13 distinct
ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel

#: CONFIRMED (Specification Section 6): 6 ITM + 1 ATM + 6 OTM.
EXPECTED_LADDER_SIZE = 13


@dataclass(frozen=True, slots=True)
class StrikeCandleInput:
    """One strike's first-5-minute-candle CE/PE input data
    (Specification Rule 1, CONFIRMED source).

    Attributes:
        strike: The strike price.
        ce_candle: The CE contract's first 5-minute candle
            (09:15-09:20). Must be candle-mode (OHLC present).
        pe_candle: The PE contract's first 5-minute candle. Must be
            candle-mode.
    """

    strike: Decimal
    ce_candle: MarketSnapshot
    pe_candle: MarketSnapshot


class ReferenceValidator:
    """Validates reference-ladder inputs and outputs.

    Stateless - a plain, injectable collaborator (per this project's
    dependency-injection convention), not a global/singleton.
    """

    def validate_inputs(self, inputs: tuple[StrikeCandleInput, ...]) -> None:
        """Validate a caller-supplied strike ladder before building.

        Raises:
            ValidationError: if the ladder is not exactly
                :data:`EXPECTED_LADDER_SIZE` strikes, contains
                duplicate strikes, or any CE/PE candle is not
                candle-mode (no OHLC).
        """
        if len(inputs) != EXPECTED_LADDER_SIZE:
            raise ValidationError(
                f"Expected exactly {EXPECTED_LADDER_SIZE} strikes in the reference ladder, "
                f"got {len(inputs)}."
            )

        strikes = [item.strike for item in inputs]
        if len(set(strikes)) != len(strikes):
            raise ValidationError("Reference ladder input contains duplicate strikes.")

        for item in inputs:
            if not item.ce_candle.is_candle():
                raise ValidationError(
                    f"CE candle for strike {item.strike} is not candle-mode (OHLC required)."
                )
            if not item.pe_candle.is_candle():
                raise ValidationError(
                    f"PE candle for strike {item.strike} is not candle-mode (OHLC required)."
                )

    def validate_levels(self, levels: tuple[ReferenceLevel, ...]) -> None:
        """Validate an already-built reference ladder.

        Raises:
            ValidationError: if the ladder is not exactly
                :data:`EXPECTED_LADDER_SIZE` levels, or contains
                duplicate strikes.
        """
        if len(levels) != EXPECTED_LADDER_SIZE:
            raise ValidationError(
                f"Expected exactly {EXPECTED_LADDER_SIZE} levels in the reference ladder, "
                f"got {len(levels)}."
            )

        strikes = [level.strike for level in levels]
        if len(set(strikes)) != len(strikes):
            raise ValidationError("Reference ladder contains duplicate strikes.")

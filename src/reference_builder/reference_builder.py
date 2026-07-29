"""ReferenceBuilder: builds the strike reference ladder.

Traceability
------------
Specification Rule 1 (v1.1, CONFIRMED): CE High/CE Low/PE High/PE Low
are taken from the first 5-minute candle (09:15-09:20) - for each
strike's CE contract, CE High/Low are that contract's own High/Low
over that one candle; PE High/Low are the PE contract's High/Low over
the same candle. That is the entire computation this module performs
- a direct field copy from an already-observed candle, no formula,
no threshold, no invented business rule.

This module does not select which strikes belong in the ladder
(Strike Selection remains MISSING INFORMATION, Specification Section
20 item 2) and does not assume any particular strike spacing
(Section 20 item 14) - it only accepts whatever 13-strike ladder,
with whatever CE/PE first-candle data, the caller supplies.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from models.reference_level import ReferenceLevel
from reference_builder.reference_repository import ReferenceRepository
from reference_builder.reference_validator import ReferenceValidator, StrikeCandleInput


class ReferenceBuilder:
    """Builds a 13-level :class:`~models.reference_level.ReferenceLevel`
    ladder from caller-supplied first-5-minute-candle CE/PE data.

    Constructor-injected dependencies only - no globals, no
    singletons. ``repository`` is optional: if supplied, every built
    ladder is also saved there under its session id.
    """

    def __init__(
        self,
        validator: ReferenceValidator | None = None,
        repository: ReferenceRepository | None = None,
    ) -> None:
        self._validator = validator if validator is not None else ReferenceValidator()
        self._repository = repository

    def build(
        self, session_id: uuid.UUID, inputs: tuple[StrikeCandleInput, ...]
    ) -> tuple[ReferenceLevel, ...]:
        """Build the reference ladder for ``session_id`` from
        ``inputs``.

        Raises:
            core.exceptions.ValidationError: if ``inputs`` (or the
                resulting ladder) fails
                :class:`~reference_builder.reference_validator.ReferenceValidator`'s
                checks.
        """
        self._validator.validate_inputs(inputs)

        levels = tuple(self._build_level(item) for item in inputs)

        self._validator.validate_levels(levels)

        if self._repository is not None:
            self._repository.save(session_id, levels)

        return levels

    @staticmethod
    def _build_level(item: StrikeCandleInput) -> ReferenceLevel:
        ce_high, ce_low = _high_low(item.ce_candle.high, item.ce_candle.low)
        pe_high, pe_low = _high_low(item.pe_candle.high, item.pe_candle.low)
        return ReferenceLevel(
            strike=item.strike,
            ce_high=ce_high,
            ce_low=ce_low,
            pe_high=pe_high,
            pe_low=pe_low,
        )


def _high_low(high: Decimal | None, low: Decimal | None) -> tuple[Decimal, Decimal]:
    # Guaranteed non-None by ReferenceValidator.validate_inputs()'s
    # is_candle() check, which runs before this is ever called.
    assert high is not None
    assert low is not None
    return high, low

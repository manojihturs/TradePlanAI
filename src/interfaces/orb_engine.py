"""ORBEngine: interface only.

Traceability
------------
Sprint: "ORB Engine" (Business Implementation Mode). Opening Range is
evidenced (Medium confidence) as a Spot-chart concept distinct from
the Weekly Future/Trend Point system in
``research/analysis/TR-001_ANALYSIS.md`` Section 5. This engine
reuses the already-CONFIRMED first-5-minute CE/PE High/Low
(``models.reference_level.ReferenceLevel``, Specification Rule 1)
rather than re-deriving the opening candle from raw data - the same
"first candle" input this codebase's other engines already rely on.

Breakout/breakdown classification against the opening range is a
standard, industry-generic definition (see
``core.enums.ORBStatus``'s own docstring) - not a proprietary
interpretation requiring further transcript evidence.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol, runtime_checkable

from core.enums import OptionType
from models.market_snapshot import MarketSnapshot
from models.orb_result import ORBResult
from models.reference_level import ReferenceLevel


@runtime_checkable
class ORBEngine(Protocol):
    """Computes one strike/side's Opening Range Breakout classification
    from its already-known opening candle plus subsequent candles."""

    def calculate(
        self,
        session_id: uuid.UUID,
        level: ReferenceLevel,
        side: OptionType,
        candles: tuple[MarketSnapshot, ...],
        calculated_at: datetime,
    ) -> ORBResult:
        """Compute Opening High/Low/Range/Breakout Status for
        ``side`` at ``level.strike``.

        Args:
            level: The strike's already-built first-5-minute CE/PE
                reference values - the opening range itself.
            side: Which contract type (CE/PE) to calculate for.
            candles: Every candle observed *after* the opening range,
                in chronological order, used only to classify
                breakout/breakdown - never to recompute the opening
                range itself. May be empty (yields ``ORBStatus.NONE``).
        """
        ...  # pragma: no cover

"""WeeklyFutureCalculator: computes Weekly Future High/Low.

Traceability
------------
Formula confirmed by 3 independent Product Owner-supplied worked
examples, 2026-07-30 - 6/6 data points independently recomputed and
matched exactly, zero contradictions. See
``research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md``
v1.0 §2-3 for the full derivation and
``research/specifications/WEEKLY_FUTURE_CALCULATION_EXAMPLES.md`` for
the verified arithmetic on every example.

The formula is a single signed subtraction on each side - no
ordering-dependent special case is needed (this resolves the
sign-flip ambiguity that made ``research/transcripts/TR-001.md``'s
own worked example self-contradictory; see the specification's §3
note).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from core.protocols import IdFactory
from models.reference_level import ReferenceLevel
from models.weekly_future import WeeklyFuture


class WeeklyFutureCalculator:
    """Computes the session's Weekly Future High/Low from the anchor
    strike's first-5-minute CE/PE reference values.

    Constructor-injected ID factory only - no globals, no singletons,
    matching every other engine in this codebase.
    """

    def __init__(self, id_factory: IdFactory = uuid.uuid4) -> None:
        self._id_factory = id_factory

    def calculate(
        self, session_id: uuid.UUID, level: ReferenceLevel, calculated_at: datetime
    ) -> WeeklyFuture:
        """Compute Weekly Future High/Low from ``level``.

        ``High = level.strike + (level.ce_high - level.pe_low)``
        ``Low = level.strike - (level.pe_high - level.ce_low)``
        """
        high = level.strike + (level.ce_high - level.pe_low)
        low = level.strike - (level.pe_high - level.ce_low)
        return WeeklyFuture(
            weekly_future_id=self._id_factory(),
            session_id=session_id,
            high=high,
            low=low,
            calculated_at=calculated_at,
        )

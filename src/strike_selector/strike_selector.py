"""StrikeSelector: selects Top Strike and Bottom Strike.

Traceability
------------
Rounding rule confirmed by 3 independent Product Owner-supplied
worked examples, 2026-07-30 - all 6 Top/Bottom Strike values
independently recomputed and matched exactly. See
``research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md``
v1.0 §4-5.

Exact tie-break behaviour at the midpoint between two multiples of 50
is UNRESOLVED - Awaiting Strategy Evidence (no worked example
demonstrates it); this implementation uses ``ROUND_HALF_UP`` as a
documented engineering default, per
``research/specifications/WEEKLY_FUTURE_TEST_CASES.md`` TC-EDGE-3 -
not a confirmed business rule.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture

_ROUNDING_STEP = Decimal(50)


class StrikeSelector:
    """Selects Top Strike (from Weekly Future High) and Bottom Strike
    (from Weekly Future Low), each rounded to the nearest multiple of
    50.

    Stateless - no constructor dependencies.
    """

    def select(
        self, session_id: uuid.UUID, weekly_future: WeeklyFuture, selected_at: datetime
    ) -> StrikeSelection:
        return StrikeSelection(
            session_id=session_id,
            top_strike=self._round_to_nearest_50(weekly_future.high),
            bottom_strike=self._round_to_nearest_50(weekly_future.low),
            selected_at=selected_at,
        )

    @staticmethod
    def _round_to_nearest_50(value: Decimal) -> Decimal:
        steps = (value / _ROUNDING_STEP).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        return steps * _ROUNDING_STEP

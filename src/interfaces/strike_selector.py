"""StrikeSelector: interface only.

Traceability
------------
Specification Section 5, Section 20 item 2 (Critical) — RESOLVED
2026-07-30, Product Owner-supplied worked examples, see
``research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md``
v1.0 §4-5 (AUTHORITATIVE). Rounding rule: nearest multiple of 50,
confirmed by 3 independent worked examples (TC-1/2/3). See the
concrete implementation at ``strike_selector.strike_selector.StrikeSelector``.

Exact tie-break behaviour at the midpoint between two multiples of 50
remains UNRESOLVED - Awaiting Strategy Evidence (no worked example
demonstrates it); the concrete implementation uses ``ROUND_HALF_UP``
as a documented engineering default, per
``research/specifications/WEEKLY_FUTURE_TEST_CASES.md`` TC-EDGE-3 -
not a confirmed business rule.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol, runtime_checkable

from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture


@runtime_checkable
class StrikeSelector(Protocol):
    """Selects the session's Top Strike and Bottom Strike (both
    "ATM") from the session's :class:`~models.weekly_future.WeeklyFuture`,
    each rounded to the nearest multiple of 50 (Specification Section
    5, confirmed by ``WEEKLY_FUTURE_FORMULA_SPECIFICATION.md`` v1.0 §4-5)."""

    def select(
        self, session_id: uuid.UUID, weekly_future: WeeklyFuture, selected_at: datetime
    ) -> StrikeSelection:
        """Select Top Strike (from Weekly Future High) and Bottom
        Strike (from Weekly Future Low), each rounded to the nearest
        multiple of 50. See
        ``research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md``
        v1.0 §4-5.
        """
        ...  # pragma: no cover

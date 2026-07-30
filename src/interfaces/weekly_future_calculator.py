"""WeeklyFutureCalculator: interface only.

Traceability
------------
Specification Section 4, Section 20 item 1 (Critical) — RESOLVED
2026-07-30, Product Owner-supplied worked examples, see
``research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md``
v1.0 (AUTHORITATIVE) and ``WEEKLY_FUTURE_BLOCKER_REPORT.md``'s
"Resolution (2026-07-30)" section.

Signature change from the original stub: the confirmed formula needs
the anchor strike's own CE/PE first-5-minute High/Low
(``models.reference_level.ReferenceLevel`` — already built, Sprint 4
``reference_builder``), not a raw ``models.market_snapshot.MarketSnapshot``.
The original stub's signature was itself a guess (no evidence existed
yet to know what the real input shape was) — this revision replaces
that guess with the shape the actual formula requires, per real
evidence, not speculation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol, runtime_checkable

from models.reference_level import ReferenceLevel
from models.weekly_future import WeeklyFuture


@runtime_checkable
class WeeklyFutureCalculator(Protocol):
    """Computes the session's Weekly Future High/Low from the anchor
    strike's first-5-minute CE/PE reference values (Specification
    Rule 1 confirms *which* candle; the formula itself is confirmed
    by ``WEEKLY_FUTURE_FORMULA_SPECIFICATION.md`` v1.0)."""

    def calculate(
        self, session_id: uuid.UUID, level: ReferenceLevel, calculated_at: datetime
    ) -> WeeklyFuture:
        """Compute the Weekly Future High/Low from ``level`` (the
        anchor strike's own CE/PE first-5-minute High/Low).

        Formula: ``High = level.strike + (level.ce_high - level.pe_low)``;
        ``Low = level.strike - (level.pe_high - level.ce_low)``. See
        ``WEEKLY_FUTURE_FORMULA_SPECIFICATION.md`` v1.0 §2-3.
        """
        ...  # pragma: no cover

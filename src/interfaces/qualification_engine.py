"""QualificationEngine: interface only.

Traceability
------------
Specification Sections 7-8, Section 20 item 3 (Critical) - RESOLVED
2026-08-01, Product Owner-supplied evidence, see
``research/incoming/qualification_session1_intake_2026-07-31.md``
(AUTHORITATIVE) and
``research/specifications/qualification_engine_scoring_2026-08-01.md``
(Evidence Complete, 6/6 ``evidence_acceptance_checklist.md`` items).

Signature change from the original stub: the confirmed mechanism
needs the anchor role, the injected trend direction, the full marked-
level ladder, and the anchor's own CE/PE candle snapshots - not a
single opaque ``tp_state: object``. The original stub's signature was
itself a guess (no evidence existed yet to know what the real input
shape was); this revision replaces that guess with the shape the
actual mechanism requires, per real evidence, not speculation. See
``qualification_engine.qualification_engine.QualificationEngine`` for
the concrete implementation.

External-invalidation handling (news/budget/war/natural disaster,
Section 7) remains UNRESOLVED - no detection mechanism has been
supplied by any evidence session so far; this interface/implementation
does not attempt to model it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from core.enums import AnchorRole, TrendDirection
from models.market_snapshot import MarketSnapshot
from models.qualification_signal import QualificationSignal
from models.reference_level import ReferenceLevel


@runtime_checkable
class QualificationEngine(Protocol):
    """Detects a confirmed dual-crossover qualification event for one
    candle, and computes its Target/Stop Loss/Competitor Exit levels
    (Specification Sections 7-8, resolved 2026-08-01)."""

    def evaluate(
        self,
        anchor_role: AnchorRole,
        trend: TrendDirection,
        reference_levels: tuple[ReferenceLevel, ...],
        own_ce_snapshot: MarketSnapshot,
        own_pe_snapshot: MarketSnapshot,
        candle_timestamp: datetime,
    ) -> QualificationSignal | None:
        """Return a :class:`~models.qualification_signal.QualificationSignal`
        if a dual crossover is confirmed on this candle for the
        trend-implied side, else ``None``.

        See ``qualification_engine.qualification_engine.QualificationEngine``
        for the full mechanism and its evidence trail.
        """
        ...  # pragma: no cover

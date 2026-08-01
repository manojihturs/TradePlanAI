"""QualificationSignal: a confirmed dual-crossover qualification event.

Traceability
------------
``research/incoming/qualification_session1_intake_2026-07-31.md`` -
General Rule Statement, Entry Trigger Rule, Entry/Target/SL/TSL
Clarification, 4 dated worked examples (22/29/30/31-July-2026).
Formally scored Evidence Complete,
``research/specifications/qualification_engine_scoring_2026-08-01.md``.

Target/Stop Loss are the adjacent value, in the SAME reference column
as the entry crossing, one rung favourable/unfavourable respectively.
Competitor Exit is the confirming leg's own crossed value, fixed for
the life of the trade (Product Owner confirmed 2026-08-01: "Yes, it
stays fixed") - it does not recompute as price moves, unlike
Target/SL which are determined once at qualification time from the
ladder position actually crossed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from core.enums import AnchorRole, TradeDirection
from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class QualificationSignal:
    """A confirmed simultaneous dual-crossover qualification event.

    Attributes:
        signal_id: This signal's own identifier.
        anchor_role: TOP or BOTTOM - which boundary strike's ladder
            produced this signal.
        side: CE or PE - which side qualified (determined by the
            trend gate, then confirmed by the dual crossover).
        entry_strike: The strike whose own value, in the entry-side
            reference column, was crossed - not necessarily the
            anchor strike itself (Product Owner confirmed, 30-July
            Row 2: the entry level can belong to a strike other than
            the anchor).
        entry_level: The entry-side reference column's value at
            ``entry_strike`` - the premium level crossed.
        target_level: The next value, in the same reference column,
            one rung favourable from ``entry_level``.
        stop_loss_level: The next value, in the same reference
            column, one rung unfavourable from ``entry_level``.
        competitor_exit_level: The confirming leg's own crossed
            value (opposite reference column) - fixed for this
            trade's lifetime, confirmed not to move as price moves.
        qualified_at: When this signal was produced.
    """

    signal_id: uuid.UUID
    anchor_role: AnchorRole
    side: TradeDirection
    entry_strike: Decimal
    entry_level: Decimal
    target_level: Decimal
    stop_loss_level: Decimal
    competitor_exit_level: Decimal
    qualified_at: datetime

    def __post_init__(self) -> None:
        if self.signal_id is None:
            raise ValidationError("QualificationSignal.signal_id must not be None.")
        if self.entry_strike <= 0:
            raise ValidationError("QualificationSignal.entry_strike must be greater than 0.")
        for name, value in (
            ("entry_level", self.entry_level),
            ("target_level", self.target_level),
            ("stop_loss_level", self.stop_loss_level),
            ("competitor_exit_level", self.competitor_exit_level),
        ):
            if value <= 0:
                raise ValidationError(f"QualificationSignal.{name} must be greater than 0.")
        if self.qualified_at is None:
            raise ValidationError("QualificationSignal.qualified_at must not be None.")

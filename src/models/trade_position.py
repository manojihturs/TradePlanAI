"""TradePosition: the single active (or most recently closed) trade.

Traceability
------------
``research/architecture/DATA_DICTIONARY.md`` Section 9. Target,
Support, and Competitor Monitor Strike are CONFIRMED (Specification
Rule 2) as a function of entry strike S: Target = CE(S+1)/PE(S-1),
Support = CE(S-1)/PE(S+1), Competitor Monitor Strike = PE(S-1)/CE(S+1),
depending on ``entry_side``. Entry price, Stop Loss level, and
Trailing Stop state are MISSING INFORMATION and are deliberately
omitted from this model (Specification Section 20 items 4, 9-10) -
adding placeholder fields for them would misrepresent them as known.

Immutable by design, matching every other model in this package:
:meth:`TradePosition.close` returns a new, closed instance rather
than mutating the open one in place.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from core.enums import ExitReason, TradeDirection, TradeState
from core.exceptions import ValidationError

#: The only two states a TradePosition may be in - a narrower subset
#: of core.enums.TradeState, which also includes IDLE/READY for the
#: session-level state machine.
_POSITION_STATES = frozenset({TradeState.TRADE_ACTIVE, TradeState.TRADE_CLOSED})


@dataclass(frozen=True, slots=True)
class TradePosition:
    """The single active (or most recently closed) trade.

    Attributes:
        trade_id: This trade's own identifier.
        entry_strike: The strike entered (= winning strike S).
        entry_side: CE or PE.
        target_level: CE(S+1) if CE, PE(S-1) if PE (Specification
            Rule 2, CONFIRMED).
        support_level: CE(S-1) if CE, PE(S+1) if PE (CONFIRMED).
        competitor_monitor_strike: PE(S-1) if CE, CE(S+1) if PE
            (CONFIRMED).
        status: TRADE_ACTIVE or TRADE_CLOSED.
        exit_reason: Set only when ``status`` is TRADE_CLOSED.
        opened_at: When the trade was opened.
        closed_at: Set only when ``status`` is TRADE_CLOSED.
    """

    trade_id: uuid.UUID
    entry_strike: Decimal
    entry_side: TradeDirection
    target_level: Decimal
    support_level: Decimal
    competitor_monitor_strike: Decimal
    opened_at: datetime
    status: TradeState = TradeState.TRADE_ACTIVE
    exit_reason: ExitReason | None = None
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.trade_id is None:
            raise ValidationError("TradePosition.trade_id must not be None.")
        if self.entry_strike <= 0:
            raise ValidationError("TradePosition.entry_strike must be greater than 0.")
        if self.opened_at is None:
            raise ValidationError("TradePosition.opened_at must not be None.")
        if self.status not in _POSITION_STATES:
            raise ValidationError(
                f"TradePosition.status must be TRADE_ACTIVE or TRADE_CLOSED, got {self.status}."
            )
        if self.status is TradeState.TRADE_ACTIVE:
            if self.exit_reason is not None:
                raise ValidationError("An active TradePosition must not have an exit_reason.")
            if self.closed_at is not None:
                raise ValidationError("An active TradePosition must not have a closed_at.")
        else:
            if self.exit_reason is None:
                raise ValidationError("A closed TradePosition must have an exit_reason.")
            if self.closed_at is None:
                raise ValidationError("A closed TradePosition must have a closed_at.")

    def is_active(self) -> bool:
        """Whether this position is still open."""
        return self.status is TradeState.TRADE_ACTIVE

    def close(self, reason: ExitReason, closed_at: datetime) -> TradePosition:
        """Return a new, closed copy of this position.

        Raises:
            ValidationError: if this position is already closed.
        """
        if not self.is_active():
            raise ValidationError(f"TradePosition {self.trade_id} is already closed.")
        return replace(
            self, status=TradeState.TRADE_CLOSED, exit_reason=reason, closed_at=closed_at
        )

"""QualifiedPosition: the single active (or most recently closed)
Qualification-Engine-derived trade.

Traceability
------------
Sprint 11 - ongoing exit monitoring for the confirmed
``qualification_engine.qualification_engine.QualificationEngine``
mechanism (see that module's own docstring for the full evidence
trail). Unlike :class:`~models.trade_position.TradePosition` (Rule 2,
adjacent-strike model), this position's Target/Stop Loss/Competitor
Exit are already concrete premium *values* computed at qualification
time by :class:`~models.qualification_signal.QualificationSignal`,
not strikes to be re-looked-up later - so no reference-level lookup
is needed to evaluate a touch against them.

Immutable by design, matching every other model in this package:
:meth:`QualifiedPosition.close` returns a new, closed instance rather
than mutating the open one in place.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from core.enums import AnchorRole, ExitReason, TradeDirection, TradeState
from core.exceptions import ValidationError

#: The only two states a QualifiedPosition may be in - mirrors
#: models.trade_position.TradePosition's own convention.
_POSITION_STATES = frozenset({TradeState.TRADE_ACTIVE, TradeState.TRADE_CLOSED})


@dataclass(frozen=True, slots=True)
class QualifiedPosition:
    """The single active (or most recently closed) Qualification-
    Engine-derived trade.

    Attributes:
        position_id: This position's own identifier.
        anchor_role: TOP or BOTTOM - which ladder produced the
            qualifying signal.
        side: CE or PE.
        entry_strike: The strike whose own value, in the entry-side
            reference column, was crossed (not necessarily the
            anchor strike itself).
        entry_level: The premium level at which this position opened.
        target_level: The confirmed Target premium level.
        stop_loss_level: The confirmed Stop Loss premium level
            (= Rule 2's Support level, Product Owner confirmed both
            sides, 2026-08-01).
        competitor_exit_level: The confirmed Competitor Exit premium
            level - fixed for this position's lifetime.
        status: TRADE_ACTIVE or TRADE_CLOSED.
        exit_reason: Set only when ``status`` is TRADE_CLOSED.
        opened_at: When the position was opened.
        closed_at: Set only when ``status`` is TRADE_CLOSED.
        exit_price: The actual premium level this position closed at,
            set only when ``status`` is TRADE_CLOSED (2026-08-02).
            For TARGET_HIT/STOP_LOSS/COMPETITOR_HIT this always equals
            one of ``target_level``/``stop_loss_level``/
            ``competitor_exit_level`` (fixed levels, known at
            qualification time); for TRAILING_STOP it is the dynamic
            trail level at the moment of exit, which is NOT any of
            those fixed levels and was previously not recorded
            anywhere on this model. ``None`` for a SESSION_END forced
            close - no real fill occurred, only ``closed_at`` marks
            when the session ended.
    """

    position_id: uuid.UUID
    anchor_role: AnchorRole
    side: TradeDirection
    entry_strike: Decimal
    entry_level: Decimal
    target_level: Decimal
    stop_loss_level: Decimal
    competitor_exit_level: Decimal
    opened_at: datetime
    status: TradeState = TradeState.TRADE_ACTIVE
    exit_reason: ExitReason | None = None
    closed_at: datetime | None = None
    exit_price: Decimal | None = None

    def __post_init__(self) -> None:
        if self.position_id is None:
            raise ValidationError("QualifiedPosition.position_id must not be None.")
        if self.entry_strike <= 0:
            raise ValidationError("QualifiedPosition.entry_strike must be greater than 0.")
        for name, value in (
            ("entry_level", self.entry_level),
            ("target_level", self.target_level),
            ("stop_loss_level", self.stop_loss_level),
            ("competitor_exit_level", self.competitor_exit_level),
        ):
            if value <= 0:
                raise ValidationError(f"QualifiedPosition.{name} must be greater than 0.")
        if self.opened_at is None:
            raise ValidationError("QualifiedPosition.opened_at must not be None.")
        if self.status not in _POSITION_STATES:
            raise ValidationError(
                f"QualifiedPosition.status must be TRADE_ACTIVE or TRADE_CLOSED, got {self.status}."
            )
        if self.status is TradeState.TRADE_ACTIVE:
            if self.exit_reason is not None:
                raise ValidationError("An active QualifiedPosition must not have an exit_reason.")
            if self.closed_at is not None:
                raise ValidationError("An active QualifiedPosition must not have a closed_at.")
            if self.exit_price is not None:
                raise ValidationError("An active QualifiedPosition must not have an exit_price.")
        else:
            if self.exit_reason is None:
                raise ValidationError("A closed QualifiedPosition must have an exit_reason.")
            if self.closed_at is None:
                raise ValidationError("A closed QualifiedPosition must have a closed_at.")
            if self.exit_reason is ExitReason.SESSION_END:
                if self.exit_price is not None:
                    raise ValidationError(
                        "A SESSION_END QualifiedPosition must not have an exit_price - "
                        "no real fill occurred."
                    )
            elif self.exit_price is None:
                raise ValidationError(
                    "A closed QualifiedPosition must have an exit_price, unless "
                    "exit_reason is SESSION_END."
                )
            elif self.exit_price <= 0:
                raise ValidationError("QualifiedPosition.exit_price must be greater than 0.")

    def is_active(self) -> bool:
        """Whether this position is still open."""
        return self.status is TradeState.TRADE_ACTIVE

    def close(
        self, reason: ExitReason, closed_at: datetime, exit_price: Decimal | None = None
    ) -> QualifiedPosition:
        """Return a new, closed copy of this position.

        Args:
            reason: Why this position closed.
            closed_at: When it closed.
            exit_price: The actual premium level closed at - required
                unless ``reason`` is ``SESSION_END`` (see this class's
                own docstring for ``exit_price``).

        Raises:
            ValidationError: if this position is already closed, or
                ``exit_price``'s presence doesn't match what ``reason``
                requires (see ``__post_init__``).
        """
        if not self.is_active():
            raise ValidationError(f"QualifiedPosition {self.position_id} is already closed.")
        return replace(
            self,
            status=TradeState.TRADE_CLOSED,
            exit_reason=reason,
            closed_at=closed_at,
            exit_price=exit_price,
        )

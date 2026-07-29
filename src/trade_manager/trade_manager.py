"""TradeManager: enforces the single-active-trade business rule.

Traceability
------------
Specification Section 10: "Only ONE trade may remain active. Never
take another trade until current trade exits." Rule 4 (v1.1):
"Ignore all new entry signals until the active trade exits" - a
rejected :meth:`TradeManager.open` call returns ``None`` and publishes
no event; it does not queue, retry, or raise.

This module does not compute Target/Support/Competitor-monitor-strike
(Specification Rule 2) - that is an Entry Engine responsibility
(Sprint 2, out of this sprint's scope). ``TradeManager`` only accepts
an already-built :class:`~models.trade_position.TradePosition` and
enforces the one-trade-at-a-time gate around it.
"""

from __future__ import annotations

import uuid

from core.enums import ExitReason
from core.events import TradeClosedEvent, TradeOpenedEvent
from core.exceptions import TradeManagerError, ValidationError
from core.protocols import Clock, EventBusProtocol, IdFactory, utc_now
from models.trade_position import TradePosition


class TradeManager:
    """Owns the single active :class:`TradePosition`, if any.

    Every other module that needs to know "is a trade active" should
    query this class rather than tracking its own copy of that state,
    per ``research/architecture/MODULE_ARCHITECTURE.md`` Section
    3.10.
    """

    def __init__(
        self,
        bus: EventBusProtocol | None = None,
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._active: TradePosition | None = None
        self._bus = bus
        self._clock: Clock = clock if clock is not None else utc_now
        self._id_factory: IdFactory = id_factory if id_factory is not None else uuid.uuid4

    def active_position(self) -> TradePosition | None:
        """The currently active position, or ``None`` if none is
        open."""
        return self._active

    def is_trade_active(self) -> bool:
        """Whether a trade is currently active."""
        return self._active is not None

    def open(self, position: TradePosition) -> TradePosition | None:
        """Open ``position`` as the active trade.

        Returns ``position`` if it was accepted, or ``None`` if a
        trade was already active - in which case ``position`` is
        discarded outright (Specification Rule 4), no event is
        published, and no exception is raised.

        Raises:
            ValidationError: if ``position`` is not itself in the
                ``TRADE_ACTIVE`` status.
        """
        if not position.is_active():
            raise ValidationError("TradeManager.open() requires a position that is active.")
        if self._active is not None:
            return None

        self._active = position
        if self._bus is not None:
            self._bus.publish(
                TradeOpenedEvent(
                    event_id=self._id_factory(),
                    occurred_at=self._clock(),
                    trade_id=position.trade_id,
                    entry_strike=position.entry_strike,
                    entry_side=position.entry_side,
                    target_level=position.target_level,
                    support_level=position.support_level,
                    competitor_monitor_strike=position.competitor_monitor_strike,
                )
            )
        return position

    def close(self, reason: ExitReason) -> TradePosition:
        """Close the active trade.

        Returns:
            The now-closed :class:`TradePosition`.

        Raises:
            TradeManagerError: if no trade is currently active.
        """
        if self._active is None:
            raise TradeManagerError("No active trade to close.")

        closed = self._active.close(reason, self._clock())
        self._active = None
        if self._bus is not None:
            self._bus.publish(
                TradeClosedEvent(
                    event_id=self._id_factory(),
                    occurred_at=self._clock(),
                    trade_id=closed.trade_id,
                    exit_reason=reason,
                )
            )
        return closed

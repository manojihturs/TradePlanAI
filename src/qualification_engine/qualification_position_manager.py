"""QualificationPositionManager: enforces the single-active-trade
business rule for Qualification-Engine-derived positions.

Traceability
------------
Sprint 11 - ongoing exit monitoring for the confirmed
``qualification_engine.qualification_engine.QualificationEngine``
mechanism. Mirrors ``trade_manager.trade_manager.TradeManager``'s
shape and its own Rule 4 (v1.1, CONFIRMED, already reused for
QUAL-009 - "Only ONE trade may remain active. Never take another
trade until current trade exits") - a rejected
:meth:`QualificationPositionManager.open` call returns ``None`` and
publishes no event; it does not queue, retry, or raise.

Also owns QUAL-011's end-of-session forced close
(``research/specifications/qualification_rule_catalog.md``) via
:meth:`force_close_session_end` - a real, confirmed event ("market
closed, No level touched") scoped as session-boundary orchestration,
not a per-candle exit condition.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from core.enums import ExitReason
from core.events import QualificationClosedEvent, QualificationOpenedEvent
from core.exceptions import TradeManagerError
from core.protocols import Clock, EventBusProtocol, IdFactory, utc_now
from models.qualification_signal import QualificationSignal
from models.qualified_position import QualifiedPosition


class QualificationPositionManager:
    """Owns the single active :class:`~models.qualified_position.QualifiedPosition`,
    if any."""

    def __init__(
        self,
        bus: EventBusProtocol | None = None,
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._active: QualifiedPosition | None = None
        self._bus = bus
        self._clock: Clock = clock if clock is not None else utc_now
        self._id_factory: IdFactory = id_factory if id_factory is not None else uuid.uuid4

    def active_position(self) -> QualifiedPosition | None:
        """The currently active position, or ``None`` if none is
        open."""
        return self._active

    def is_trade_active(self) -> bool:
        """Whether a trade is currently active."""
        return self._active is not None

    def open(self, signal: QualificationSignal) -> QualifiedPosition | None:
        """Open a new :class:`~models.qualified_position.QualifiedPosition`
        from ``signal``.

        Returns the opened position, or ``None`` if a trade was
        already active - in which case ``signal`` is discarded
        outright (Rule 4), no event is published, and no exception is
        raised.
        """
        if self._active is not None:
            return None

        position = QualifiedPosition(
            position_id=self._id_factory(),
            anchor_role=signal.anchor_role,
            side=signal.side,
            entry_strike=signal.entry_strike,
            entry_level=signal.entry_level,
            target_level=signal.target_level,
            stop_loss_level=signal.stop_loss_level,
            competitor_exit_level=signal.competitor_exit_level,
            opened_at=signal.qualified_at,
        )
        self._active = position
        if self._bus is not None:
            self._bus.publish(
                QualificationOpenedEvent(
                    event_id=self._id_factory(),
                    occurred_at=self._clock(),
                    position_id=position.position_id,
                    entry_strike=position.entry_strike,
                    entry_side=position.side,
                    entry_level=position.entry_level,
                    target_level=position.target_level,
                    stop_loss_level=position.stop_loss_level,
                    competitor_exit_level=position.competitor_exit_level,
                )
            )
        return position

    def close(self, reason: ExitReason, exit_price: Decimal | None = None) -> QualifiedPosition:
        """Close the active trade.

        Args:
            reason: Why the trade closed.
            exit_price: The actual premium level closed at - required
                unless ``reason`` is ``SESSION_END`` (see
                :meth:`~models.qualified_position.QualifiedPosition.close`).

        Returns:
            The now-closed :class:`~models.qualified_position.QualifiedPosition`.

        Raises:
            core.exceptions.TradeManagerError: if no trade is
                currently active.
        """
        if self._active is None:
            raise TradeManagerError("No active qualified trade to close.")

        closed = self._active.close(reason, self._clock(), exit_price)
        self._active = None
        if self._bus is not None:
            self._bus.publish(
                QualificationClosedEvent(
                    event_id=self._id_factory(),
                    occurred_at=self._clock(),
                    position_id=closed.position_id,
                    exit_reason=reason,
                )
            )
        return closed

    def force_close_session_end(self) -> QualifiedPosition | None:
        """QUAL-011: close the active trade with
        :attr:`~core.enums.ExitReason.SESSION_END`, if one is open.

        Returns the now-closed position, or ``None`` if no trade was
        active - unlike :meth:`close`, this does not raise, since the
        caller (a session-boundary orchestrator) does not know in
        advance whether a trade is open.
        """
        if self._active is None:
            return None
        return self.close(ExitReason.SESSION_END)

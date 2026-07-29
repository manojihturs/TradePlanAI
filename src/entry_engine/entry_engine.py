"""EntryEngine: subscribes to WinnerDetectedEvent and opens a trade.

Traceability
------------
Specification Section 10: "Immediately after Winner. Only ONE trade
may remain active. Never take another trade until current trade
exits." Rule 4 (v1.1, CONFIRMED): a rejected attempt is discarded
outright, not queued or retried - this engine reflects that by
setting :attr:`~models.trade_signal.TradeSignal.accepted` to
``False`` and taking no further action, never raising.

Entry price/order-type basis is MISSING INFORMATION (Specification
Section 11) and is not represented anywhere in this module.

The reference-level ladder needed to compute Target/Support/
Competitor-Exit (Specification Rule 2) is injected at construction -
Sprint 2 does not implement the Reference Level Builder, so the
ladder is assumed to be supplied externally for the session, matching
this sprint's own "do not implement TP/Qualification/Weekly
Future/Strike Selection" boundary.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from core.events import WinnerDetectedEvent
from core.protocols import Clock, EventBusProtocol, IdFactory
from models.reference_level import ReferenceLevel
from models.trade_signal import TradeSignal
from position_manager.position_manager import PositionManager


class EntryEngine:
    """Reacts to :class:`~core.events.WinnerDetectedEvent` by
    building a :class:`~models.trade_signal.TradeSignal` and
    attempting to open a trade via an injected
    :class:`~position_manager.position_manager.PositionManager`.

    Constructor-injected dependencies only - no globals, no
    singletons. Subscribes itself to ``bus`` for
    ``WinnerDetectedEvent`` on construction, so wiring an
    ``EntryEngine`` into a running pipeline is a single call.
    """

    def __init__(
        self,
        bus: EventBusProtocol,
        position_manager: PositionManager,
        reference_levels: tuple[ReferenceLevel, ...],
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._bus = bus
        self._position_manager = position_manager
        self._reference_levels = reference_levels
        self._clock: Clock = clock if clock is not None else datetime.now
        self._id_factory: IdFactory = id_factory if id_factory is not None else uuid.uuid4
        self._bus.subscribe(WinnerDetectedEvent, self._on_winner_detected)  # type: ignore[arg-type]

    def handle_winner_detected(self, event: WinnerDetectedEvent) -> TradeSignal:
        """Build a :class:`TradeSignal` for ``event`` and attempt to
        open a trade.

        Returns the resulting signal, with ``accepted`` reflecting
        whether a trade was actually opened (``False`` if one was
        already active - Specification Rule 4).

        Exposed as a public method (in addition to being wired to
        the event bus in the constructor) so it can be exercised
        directly in tests without requiring bus plumbing.
        """
        signal = TradeSignal(
            signal_id=self._id_factory(),
            winner_event_id=event.event_id,
            side=event.winning_side,
            strike=event.winning_strike,
            raised_at=self._clock(),
        )
        position = self._position_manager.open_position(
            trade_id=self._id_factory(),
            entry_strike=signal.strike,
            entry_side=signal.side,
            opened_at=signal.raised_at,
            reference_levels=self._reference_levels,
        )
        accepted = position is not None
        return TradeSignal(
            signal_id=signal.signal_id,
            winner_event_id=signal.winner_event_id,
            side=signal.side,
            strike=signal.strike,
            raised_at=signal.raised_at,
            accepted=accepted,
        )

    def _on_winner_detected(self, event: WinnerDetectedEvent) -> None:
        self.handle_winner_detected(event)

"""EventRecorder: captures every event published on an injected bus.

Traceability
------------
Pure infrastructure - no business rule. Supports Replay, Timeline,
Diagnostics, Debugging, Backtesting, and Explainability by keeping an
immutable, chronologically-ordered record of every domain event, for
later inspection.

Uses ``events.event_bus.EventBus``'s Sprint 3 wildcard subscription
(:meth:`~core.protocols.EventBusProtocol.subscribe_all`) to capture
every event type automatically, without needing an exhaustive,
fragile list of every concrete event class.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from core.events import Event
from core.protocols import EventBusProtocol


class EventRecorder:
    """Records every event published on an injected event bus.

    Constructor-injected dependency, no globals/singletons - each
    instance owns its own private event list. Recorded events are
    never mutated (every ``core.events.Event`` implementation is
    already an immutable, frozen dataclass) and are never copied -
    the same instances that were published are the ones returned by
    every query method here.
    """

    def __init__(self, bus: EventBusProtocol) -> None:
        self._bus = bus
        self._events: list[Event] = []
        self._bus.subscribe_all(self._on_event)

    def record(self, event: Event) -> None:
        """Append ``event`` to the record.

        This is the same method wired to the bus in the constructor
        (exposed publicly so it can be exercised directly in tests,
        or used to record an event that did not arrive via the bus).
        """
        self._events.append(event)

    def get_events(self) -> tuple[Event, ...]:
        """Every recorded event, in chronological order (by
        ``occurred_at``; ties keep their original recording order)."""
        return self._ordered()

    def clear(self) -> None:
        """Discard every recorded event."""
        self._events = []

    def filter_by_type(self, event_type: type[Event]) -> tuple[Event, ...]:
        """Every recorded event that is an instance of ``event_type``,
        in chronological order."""
        return tuple(event for event in self._ordered() if isinstance(event, event_type))

    def filter_by_trade(self, trade_id: uuid.UUID) -> tuple[Event, ...]:
        """Every recorded event whose ``trade_id`` attribute equals
        ``trade_id``, in chronological order.

        Events with no ``trade_id`` attribute (e.g.
        ``MarketOpenEvent``) are never matched.
        """
        return tuple(
            event for event in self._ordered() if getattr(event, "trade_id", None) == trade_id
        )

    def filter_by_time_range(self, start: datetime, end: datetime) -> tuple[Event, ...]:
        """Every recorded event whose ``occurred_at`` falls within
        ``[start, end]`` inclusive, in chronological order."""
        return tuple(event for event in self._ordered() if start <= event.occurred_at <= end)

    def _ordered(self) -> tuple[Event, ...]:
        return tuple(sorted(self._events, key=lambda event: event.occurred_at))

    def _on_event(self, event: Event) -> None:
        self.record(event)

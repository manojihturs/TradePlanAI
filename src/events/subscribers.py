"""EventSubscriber: a structural handler contract and bulk-subscribe helper.

Traceability
------------
Pure infrastructure. ``EventSubscriber`` lets a class group multiple
event handlers into one object with a single ``handle`` entry point
(useful for a module that reacts to more than one event type);
``subscribe_all``/``unsubscribe_all`` register/deregister several
event-type-to-handler pairs in one call.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.events import Event
from core.protocols import EventBusProtocol, EventHandler


@runtime_checkable
class EventSubscriber(Protocol):
    """The structural contract an event handler object satisfies."""

    def handle(self, event: Event) -> None:
        """React to one dispatched event."""
        ...  # pragma: no cover


def subscribe_all(bus: EventBusProtocol, subscriptions: dict[type[Event], EventHandler]) -> None:
    """Register every ``(event_type, handler)`` pair in
    ``subscriptions`` on ``bus``."""
    for event_type, handler in subscriptions.items():
        bus.subscribe(event_type, handler)


def unsubscribe_all(bus: EventBusProtocol, subscriptions: dict[type[Event], EventHandler]) -> None:
    """Remove every ``(event_type, handler)`` pair in
    ``subscriptions`` from ``bus``."""
    for event_type, handler in subscriptions.items():
        bus.unsubscribe(event_type, handler)

"""EventBus: the in-process publish/subscribe/unsubscribe implementation.

Traceability
------------
Pure infrastructure - dispatches already-constructed
``core.events.Event`` instances to handlers registered for their
exact concrete type. No business rule; matches this sprint's own
instruction ("Support publish(), subscribe(), unsubscribe()").
"""

from __future__ import annotations

from collections import defaultdict

from core.events import Event
from core.exceptions import EventBusError
from core.protocols import EventHandler


class EventBus:
    """A synchronous, in-process event bus.

    Not thread-safe - matches this project's synchronous,
    single-pipeline design (no concurrent execution is assumed
    anywhere in Sprint 1).
    """

    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[EventHandler]] = defaultdict(list)

    def publish(self, event: Event) -> None:
        """Dispatch ``event`` to every handler subscribed to its
        exact concrete type, in subscription order.

        A concrete type with no subscribers is a no-op, not an
        error.
        """
        for handler in list(self._handlers.get(type(event), ())):
            handler(event)

    def subscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """Register ``handler`` to be called for every future
        ``event_type`` published.

        Subscribing the same handler twice for the same
        ``event_type`` registers it twice - it will be called twice
        per publish. Use :meth:`unsubscribe` to remove one
        registration at a time.
        """
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """Remove one previously-registered ``handler`` for
        ``event_type``.

        Raises:
            EventBusError: if ``handler`` was never subscribed for
                ``event_type``.
        """
        handlers = self._handlers.get(event_type, [])
        try:
            handlers.remove(handler)
        except ValueError as exc:
            raise EventBusError(
                f"Handler {handler!r} was never subscribed for {event_type.__name__}."
            ) from exc

    def handler_count(self, event_type: type[Event]) -> int:
        """How many handlers are currently subscribed for
        ``event_type`` - a read-only introspection helper, useful for
        tests."""
        return len(self._handlers.get(event_type, ()))

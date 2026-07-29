"""EventBus: the in-process publish/subscribe/unsubscribe implementation.

Traceability
------------
Pure infrastructure - dispatches already-constructed
``core.events.Event`` instances to handlers registered for their
exact concrete type. No business rule; matches this sprint's own
instruction ("Support publish(), subscribe(), unsubscribe()").

Sprint 3 addition: :meth:`subscribe_all`/:meth:`unsubscribe_all`, a
wildcard registration used by ``event_recorder.event_recorder.EventRecorder``
to capture every published event regardless of concrete type, without
requiring an exhaustive, fragile list of every event class (which
would silently miss any future event type). This is the one Sprint
1/2 module touched this sprint, per Sprint 3's own "unless
integration requires it" allowance - existing ``publish``/``subscribe``/
``unsubscribe`` behavior is unchanged, only additive.
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
        self._global_handlers: list[EventHandler] = []

    def publish(self, event: Event) -> None:
        """Dispatch ``event`` to every handler subscribed to its
        exact concrete type, in subscription order, then to every
        wildcard handler registered via :meth:`subscribe_all`.

        A concrete type with no subscribers is a no-op, not an
        error.
        """
        for handler in list(self._handlers.get(type(event), ())):
            handler(event)
        for global_handler in list(self._global_handlers):
            global_handler(event)

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

    def subscribe_all(self, handler: EventHandler) -> None:
        """Register ``handler`` to be called for every future event,
        regardless of concrete type."""
        self._global_handlers.append(handler)

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Remove one previously-registered wildcard ``handler``.

        Raises:
            EventBusError: if ``handler`` was never subscribed via
                :meth:`subscribe_all`.
        """
        try:
            self._global_handlers.remove(handler)
        except ValueError as exc:
            raise EventBusError(f"Handler {handler!r} was never subscribed to all events.") from exc

    def handler_count(self, event_type: type[Event]) -> int:
        """How many handlers are currently subscribed for
        ``event_type`` - a read-only introspection helper, useful for
        tests."""
        return len(self._handlers.get(event_type, ()))

    def global_handler_count(self) -> int:
        """How many wildcard handlers are currently subscribed via
        :meth:`subscribe_all` - a read-only introspection helper,
        useful for tests."""
        return len(self._global_handlers)

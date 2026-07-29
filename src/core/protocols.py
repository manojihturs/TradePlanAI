"""Structural interfaces (``typing.Protocol``) shared across packages.

Traceability
------------
Pure infrastructure/dependency-injection contracts (clock, ID
factory, event bus shape) - no business rule. Kept in ``core`` so
that ``events``/``trade_manager``/``replay`` can depend on the
*shape* of an event bus without necessarily importing the concrete
``events.event_bus.EventBus`` implementation, matching this
repository's established clock/sink-injection convention (see
``trading_engine.rules.protocols.Rule``,
``trading_engine.diagnostics.sink.DiagnosticsSink``).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Protocol, runtime_checkable

from core.events import Event

#: A handler as stored/invoked by the event bus - generic over the
#: ``Event`` protocol rather than one specific concrete event type,
#: since the bus itself is not generic on any single event class.
EventHandler = Callable[[Event], None]

#: Injectable wall-clock source - matches this repository's
#: established ``clock: Callable[[], datetime] = datetime.now``
#: pattern used throughout ``trading_engine``.
Clock = Callable[[], datetime]

#: Injectable UUID source, for deterministic testing.
IdFactory = Callable[[], uuid.UUID]


@runtime_checkable
class EventBusProtocol(Protocol):
    """The structural contract every event bus implementation
    satisfies."""

    def publish(self, event: Event) -> None:
        """Dispatch ``event`` to every handler subscribed to its
        concrete type."""
        ...  # pragma: no cover

    def subscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """Register ``handler`` to be called for every future
        ``event_type`` published."""
        ...  # pragma: no cover

    def unsubscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """Remove a previously-registered ``handler`` for
        ``event_type``."""
        ...  # pragma: no cover

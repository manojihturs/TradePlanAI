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
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from core.events import Event

#: A handler as stored/invoked by the event bus - generic over the
#: ``Event`` protocol rather than one specific concrete event type,
#: since the bus itself is not generic on any single event class.
EventHandler = Callable[[Event], None]

#: Injectable wall-clock source.
Clock = Callable[[], datetime]

#: Injectable UUID source, for deterministic testing.
IdFactory = Callable[[], uuid.UUID]


def utc_now() -> datetime:
    """The default :data:`Clock` implementation for every class in
    this codebase that accepts an injectable clock.

    Traceability
    ------------
    ``ARCHITECTURE_REVIEW.md`` Finding 1 (High): several classes
    previously defaulted their uninjected clock to the bare
    ``datetime.now`` builtin, which returns a *naive* (timezone-less)
    datetime. Every timestamp elsewhere in this codebase - every test
    fixture, and any real market-data feed - is timezone-aware, so an
    uninjected default clock would eventually be subtracted from or
    compared against an aware datetime and raise ``TypeError: can't
    subtract offset-naive and offset-aware datetimes``. This already
    happened once, during Sprint 3 development, and was fixed only in
    the affected test fixture, not at the source. This function is
    the single, shared, timezone-aware default every class should use
    instead of calling ``datetime.now`` directly.
    """
    return datetime.now(UTC)


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

    def subscribe_all(self, handler: EventHandler) -> None:
        """Register ``handler`` to be called for every future event,
        regardless of concrete type. Added in Sprint 3 for
        ``event_recorder.event_recorder.EventRecorder``."""
        ...  # pragma: no cover

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Remove a previously-registered wildcard ``handler``."""
        ...  # pragma: no cover

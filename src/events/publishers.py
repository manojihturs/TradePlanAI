"""EventPublisher: a thin, injectable wrapper for publishing events.

Traceability
------------
Pure infrastructure. Modules that need to publish events (e.g.
``trade_manager``, ``replay``) depend on the injected
``core.protocols.EventBusProtocol`` shape via this small composition
helper, rather than importing ``events.event_bus.EventBus`` directly
- keeping them decoupled from the concrete bus implementation, per
this project's stated dependency-injection convention.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.events import Event
from core.protocols import EventBusProtocol


@dataclass(slots=True)
class EventPublisher:
    """Wraps an injected :class:`~core.protocols.EventBusProtocol`
    and exposes a single ``publish`` method."""

    bus: EventBusProtocol

    def publish(self, event: Event) -> None:
        """Publish ``event`` via the wrapped bus."""
        self.bus.publish(event)

"""Tests for core.protocols."""

from __future__ import annotations

import uuid
from datetime import datetime

from core.events import Event
from core.protocols import EventBusProtocol


class _FakeBus:
    def __init__(self) -> None:
        self.published: list[Event] = []

    def publish(self, event: Event) -> None:
        self.published.append(event)

    def subscribe(self, event_type: type, handler: object) -> None:
        return None

    def unsubscribe(self, event_type: type, handler: object) -> None:
        return None

    def subscribe_all(self, handler: object) -> None:
        return None

    def unsubscribe_all(self, handler: object) -> None:
        return None


def test_fake_bus_satisfies_event_bus_protocol() -> None:
    bus = _FakeBus()
    assert isinstance(bus, EventBusProtocol)


def test_object_without_required_methods_does_not_satisfy_protocol() -> None:
    class NotABus:
        pass

    assert not isinstance(NotABus(), EventBusProtocol)


def test_clock_and_id_factory_type_aliases_are_usable() -> None:
    from core.protocols import Clock, IdFactory

    clock: Clock = datetime.now
    id_factory: IdFactory = uuid.uuid4

    assert isinstance(clock(), datetime)
    assert isinstance(id_factory(), uuid.UUID)

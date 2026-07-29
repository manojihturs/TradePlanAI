"""Tests for events.publishers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from core.events import Event, MarketOpenEvent
from events.event_bus import EventBus
from events.publishers import EventPublisher


def test_publisher_forwards_to_bus() -> None:
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]

    publisher = EventPublisher(bus=bus)
    event = MarketOpenEvent(uuid.uuid4(), datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC), uuid.uuid4())
    publisher.publish(event)

    assert received == [event]

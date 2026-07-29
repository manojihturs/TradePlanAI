"""Tests for events.subscribers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from core.events import Event, MarketCloseEvent, MarketOpenEvent
from events.event_bus import EventBus
from events.subscribers import EventSubscriber, subscribe_all, unsubscribe_all


class _Recorder:
    def __init__(self) -> None:
        self.received: list[Event] = []

    def handle(self, event: Event) -> None:
        self.received.append(event)


def test_recorder_satisfies_event_subscriber_protocol() -> None:
    assert isinstance(_Recorder(), EventSubscriber)


def test_object_without_handle_does_not_satisfy_protocol() -> None:
    class NotASubscriber:
        pass

    assert not isinstance(NotASubscriber(), EventSubscriber)


def test_subscribe_all_registers_every_pair() -> None:
    bus = EventBus()
    recorder = _Recorder()

    subscribe_all(bus, {MarketOpenEvent: recorder.handle, MarketCloseEvent: recorder.handle})  # type: ignore[dict-item]

    open_event = MarketOpenEvent(
        uuid.uuid4(), datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC), uuid.uuid4()
    )
    close_event = MarketCloseEvent(
        uuid.uuid4(), datetime(2026, 7, 30, 15, 30, 0, tzinfo=UTC), uuid.uuid4()
    )
    bus.publish(open_event)
    bus.publish(close_event)

    assert recorder.received == [open_event, close_event]


def test_unsubscribe_all_removes_every_pair() -> None:
    bus = EventBus()
    recorder = _Recorder()
    subscriptions = {
        MarketOpenEvent: recorder.handle,
        MarketCloseEvent: recorder.handle,
    }
    subscribe_all(bus, subscriptions)  # type: ignore[arg-type]

    unsubscribe_all(bus, subscriptions)  # type: ignore[arg-type]

    open_event = MarketOpenEvent(
        uuid.uuid4(), datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC), uuid.uuid4()
    )
    bus.publish(open_event)

    assert recorder.received == []

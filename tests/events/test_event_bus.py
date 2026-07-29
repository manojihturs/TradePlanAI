"""Tests for events.event_bus."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from core.events import MarketCloseEvent, MarketOpenEvent
from core.exceptions import EventBusError
from events.event_bus import EventBus


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def open_event() -> MarketOpenEvent:
    return MarketOpenEvent(uuid.uuid4(), datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC), uuid.uuid4())


class TestSubscribeAndPublish:
    def test_subscribed_handler_is_called(self, bus: EventBus, open_event: MarketOpenEvent) -> None:
        received: list[MarketOpenEvent] = []
        bus.subscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]

        bus.publish(open_event)

        assert received == [open_event]

    def test_multiple_handlers_all_called_in_order(
        self, bus: EventBus, open_event: MarketOpenEvent
    ) -> None:
        order: list[str] = []
        bus.subscribe(MarketOpenEvent, lambda _: order.append("first"))  # type: ignore[arg-type]
        bus.subscribe(MarketOpenEvent, lambda _: order.append("second"))  # type: ignore[arg-type]

        bus.publish(open_event)

        assert order == ["first", "second"]

    def test_publish_with_no_subscribers_is_a_no_op(
        self, bus: EventBus, open_event: MarketOpenEvent
    ) -> None:
        bus.publish(open_event)  # must not raise

    def test_handler_only_receives_its_own_event_type(self, bus: EventBus) -> None:
        received: list[object] = []
        bus.subscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]

        close_event = MarketCloseEvent(
            uuid.uuid4(), datetime(2026, 7, 30, 15, 30, 0, tzinfo=UTC), uuid.uuid4()
        )
        bus.publish(close_event)

        assert received == []

    def test_same_handler_subscribed_twice_is_called_twice(
        self, bus: EventBus, open_event: MarketOpenEvent
    ) -> None:
        calls: list[MarketOpenEvent] = []

        def handler(event: MarketOpenEvent) -> None:
            calls.append(event)

        bus.subscribe(MarketOpenEvent, handler)  # type: ignore[arg-type]
        bus.subscribe(MarketOpenEvent, handler)  # type: ignore[arg-type]
        bus.publish(open_event)

        assert calls == [open_event, open_event]


class TestUnsubscribe:
    def test_unsubscribed_handler_is_not_called(
        self, bus: EventBus, open_event: MarketOpenEvent
    ) -> None:
        received: list[MarketOpenEvent] = []
        bus.subscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]
        bus.unsubscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]

        bus.publish(open_event)

        assert received == []

    def test_unsubscribing_unregistered_handler_raises(self, bus: EventBus) -> None:
        with pytest.raises(EventBusError, match="was never subscribed"):
            bus.unsubscribe(MarketOpenEvent, lambda _: None)  # type: ignore[arg-type]

    def test_unsubscribe_removes_only_one_registration(
        self, bus: EventBus, open_event: MarketOpenEvent
    ) -> None:
        calls: list[MarketOpenEvent] = []

        def handler(event: MarketOpenEvent) -> None:
            calls.append(event)

        bus.subscribe(MarketOpenEvent, handler)  # type: ignore[arg-type]
        bus.subscribe(MarketOpenEvent, handler)  # type: ignore[arg-type]
        bus.unsubscribe(MarketOpenEvent, handler)  # type: ignore[arg-type]

        bus.publish(open_event)

        assert calls == [open_event]


class TestHandlerCount:
    def test_zero_for_unknown_type(self, bus: EventBus) -> None:
        assert bus.handler_count(MarketOpenEvent) == 0

    def test_reflects_subscriptions(self, bus: EventBus) -> None:
        bus.subscribe(MarketOpenEvent, lambda _: None)  # type: ignore[arg-type]
        assert bus.handler_count(MarketOpenEvent) == 1


class TestSubscribeAll:
    def test_wildcard_handler_receives_every_event_type(
        self, bus: EventBus, open_event: MarketOpenEvent
    ) -> None:
        received: list[object] = []
        bus.subscribe_all(received.append)  # type: ignore[arg-type]

        close_event = MarketCloseEvent(
            uuid.uuid4(), datetime(2026, 7, 30, 15, 30, 0, tzinfo=UTC), uuid.uuid4()
        )
        bus.publish(open_event)
        bus.publish(close_event)

        assert received == [open_event, close_event]

    def test_wildcard_handlers_run_after_type_specific_handlers(
        self, bus: EventBus, open_event: MarketOpenEvent
    ) -> None:
        order: list[str] = []
        bus.subscribe(MarketOpenEvent, lambda _: order.append("specific"))  # type: ignore[arg-type]
        bus.subscribe_all(lambda _: order.append("wildcard"))  # type: ignore[arg-type]

        bus.publish(open_event)

        assert order == ["specific", "wildcard"]

    def test_unsubscribe_all_removes_handler(
        self, bus: EventBus, open_event: MarketOpenEvent
    ) -> None:
        received: list[object] = []
        bus.subscribe_all(received.append)  # type: ignore[arg-type]
        bus.unsubscribe_all(received.append)  # type: ignore[arg-type]

        bus.publish(open_event)

        assert received == []

    def test_unsubscribe_all_unregistered_handler_raises(self, bus: EventBus) -> None:
        with pytest.raises(EventBusError, match="was never subscribed to all events"):
            bus.unsubscribe_all(lambda _: None)  # type: ignore[arg-type]


class TestGlobalHandlerCount:
    def test_zero_when_none_registered(self, bus: EventBus) -> None:
        assert bus.global_handler_count() == 0

    def test_reflects_subscriptions(self, bus: EventBus) -> None:
        bus.subscribe_all(lambda _: None)  # type: ignore[arg-type]
        assert bus.global_handler_count() == 1

"""Tests for event_recorder.event_recorder."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from core.enums import ExitReason
from core.events import MarketCloseEvent, MarketOpenEvent, TradeClosedEvent, TradeOpenedEvent
from event_recorder.event_recorder import EventRecorder
from events.event_bus import EventBus


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def recorder(bus: EventBus) -> EventRecorder:
    return EventRecorder(bus=bus)


def _open_event(when: datetime, session_id: uuid.UUID | None = None) -> MarketOpenEvent:
    return MarketOpenEvent(uuid.uuid4(), when, session_id or uuid.uuid4())


def _close_event(when: datetime, session_id: uuid.UUID | None = None) -> MarketCloseEvent:
    return MarketCloseEvent(uuid.uuid4(), when, session_id or uuid.uuid4())


def _trade_opened(when: datetime, trade_id: uuid.UUID) -> TradeOpenedEvent:
    from decimal import Decimal

    from core.enums import TradeDirection

    return TradeOpenedEvent(
        event_id=uuid.uuid4(),
        occurred_at=when,
        trade_id=trade_id,
        entry_strike=Decimal(24000),
        entry_side=TradeDirection.CE,
        target_level=Decimal(24050),
        support_level=Decimal(23950),
        competitor_monitor_strike=Decimal(23950),
    )


def _trade_closed(when: datetime, trade_id: uuid.UUID) -> TradeClosedEvent:
    return TradeClosedEvent(uuid.uuid4(), when, trade_id, ExitReason.TARGET_HIT)


class TestAutomaticCapture:
    def test_events_published_on_bus_are_recorded(
        self, bus: EventBus, recorder: EventRecorder
    ) -> None:
        event = _open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC))
        bus.publish(event)

        assert recorder.get_events() == (event,)

    def test_multiple_event_types_all_captured(
        self, bus: EventBus, recorder: EventRecorder
    ) -> None:
        open_event = _open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC))
        close_event = _close_event(datetime(2026, 7, 30, 15, 30, 0, tzinfo=UTC))
        bus.publish(open_event)
        bus.publish(close_event)

        assert recorder.get_events() == (open_event, close_event)


class TestDirectRecord:
    def test_record_appends_without_bus(self, recorder: EventRecorder) -> None:
        event = _open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC))
        recorder.record(event)

        assert recorder.get_events() == (event,)


class TestChronologicalOrdering:
    def test_events_recorded_out_of_order_are_returned_sorted(
        self, recorder: EventRecorder
    ) -> None:
        later = _open_event(datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC))
        earlier = _open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC))
        recorder.record(later)
        recorder.record(earlier)

        assert recorder.get_events() == (earlier, later)

    def test_ties_preserve_recording_order(self, recorder: EventRecorder) -> None:
        same_time = datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)
        first = _open_event(same_time)
        second = _close_event(same_time)
        recorder.record(first)
        recorder.record(second)

        assert recorder.get_events() == (first, second)


class TestClear:
    def test_clear_removes_every_event(self, recorder: EventRecorder) -> None:
        recorder.record(_open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)))
        recorder.clear()

        assert recorder.get_events() == ()


class TestFilterByType:
    def test_returns_only_matching_type(self, recorder: EventRecorder) -> None:
        open_event = _open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC))
        close_event = _close_event(datetime(2026, 7, 30, 15, 30, 0, tzinfo=UTC))
        recorder.record(open_event)
        recorder.record(close_event)

        assert recorder.filter_by_type(MarketOpenEvent) == (open_event,)

    def test_returns_empty_when_no_match(self, recorder: EventRecorder) -> None:
        recorder.record(_open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)))
        assert recorder.filter_by_type(MarketCloseEvent) == ()


class TestFilterByTrade:
    def test_returns_only_events_for_that_trade(self, recorder: EventRecorder) -> None:
        trade_id = uuid.uuid4()
        other_trade_id = uuid.uuid4()
        opened = _trade_opened(datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC), trade_id)
        closed = _trade_closed(datetime(2026, 7, 30, 9, 45, 0, tzinfo=UTC), trade_id)
        other = _trade_opened(datetime(2026, 7, 30, 9, 50, 0, tzinfo=UTC), other_trade_id)
        recorder.record(opened)
        recorder.record(closed)
        recorder.record(other)

        assert recorder.filter_by_trade(trade_id) == (opened, closed)

    def test_events_without_trade_id_never_match(self, recorder: EventRecorder) -> None:
        recorder.record(_open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)))
        assert recorder.filter_by_trade(uuid.uuid4()) == ()


class TestFilterByTimeRange:
    def test_returns_only_events_within_range_inclusive(self, recorder: EventRecorder) -> None:
        before = _open_event(datetime(2026, 7, 30, 9, 0, 0, tzinfo=UTC))
        start_boundary = _open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC))
        inside = _open_event(datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC))
        end_boundary = _open_event(datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC))
        after = _open_event(datetime(2026, 7, 30, 9, 45, 0, tzinfo=UTC))
        for event in (before, start_boundary, inside, end_boundary, after):
            recorder.record(event)

        result = recorder.filter_by_time_range(
            datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC), datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)
        )

        assert result == (start_boundary, inside, end_boundary)


class TestImmutability:
    def test_recorded_events_are_frozen_dataclasses(self, recorder: EventRecorder) -> None:
        event = _open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC))
        recorder.record(event)

        with pytest.raises(AttributeError):
            event.session_id = uuid.uuid4()  # type: ignore[misc]

    def test_get_events_returns_same_instances(self, recorder: EventRecorder) -> None:
        event = _open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC))
        recorder.record(event)

        assert recorder.get_events()[0] is event


class TestNoGlobalState:
    def test_two_recorders_are_independent(self) -> None:
        bus_one = EventBus()
        bus_two = EventBus()
        recorder_one = EventRecorder(bus=bus_one)
        recorder_two = EventRecorder(bus=bus_two)

        bus_one.publish(_open_event(datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)))

        assert len(recorder_one.get_events()) == 1
        assert len(recorder_two.get_events()) == 0

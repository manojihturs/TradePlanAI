"""Tests for trade_manager.trade_manager."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import ExitReason, TradeDirection
from core.events import TradeClosedEvent, TradeOpenedEvent
from core.exceptions import TradeManagerError, ValidationError
from events.event_bus import EventBus
from models.trade_position import TradePosition
from trade_manager.trade_manager import TradeManager


def _make_position(**overrides: object) -> TradePosition:
    fields: dict[str, object] = {
        "trade_id": uuid.uuid4(),
        "entry_strike": Decimal(24100),
        "entry_side": TradeDirection.CE,
        "target_level": Decimal(24150),
        "support_level": Decimal(24050),
        "competitor_monitor_strike": Decimal(24050),
        "opened_at": datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
    }
    fields.update(overrides)
    return TradePosition(**fields)  # type: ignore[arg-type]


class TestOpen:
    def test_open_when_no_active_trade_succeeds(self) -> None:
        manager = TradeManager()
        position = _make_position()

        result = manager.open(position)

        assert result is position
        assert manager.active_position() is position
        assert manager.is_trade_active() is True

    def test_open_while_trade_active_is_rejected(self) -> None:
        manager = TradeManager()
        first = _make_position()
        second = _make_position(trade_id=uuid.uuid4())
        manager.open(first)

        result = manager.open(second)

        assert result is None
        assert manager.active_position() is first

    def test_open_with_non_active_position_raises(self) -> None:
        manager = TradeManager()
        closed = _make_position().close(
            ExitReason.TARGET_HIT, datetime(2026, 7, 30, 9, 45, 0, tzinfo=UTC)
        )

        with pytest.raises(ValidationError, match="requires a position that is active"):
            manager.open(closed)

    def test_open_publishes_trade_opened_event(self) -> None:
        bus = EventBus()
        received: list[TradeOpenedEvent] = []
        bus.subscribe(TradeOpenedEvent, received.append)  # type: ignore[arg-type]
        manager = TradeManager(bus=bus)
        position = _make_position()

        manager.open(position)

        assert len(received) == 1
        assert received[0].trade_id == position.trade_id
        assert received[0].entry_strike == position.entry_strike
        assert received[0].target_level == position.target_level

    def test_rejected_open_publishes_nothing(self) -> None:
        bus = EventBus()
        received: list[TradeOpenedEvent] = []
        bus.subscribe(TradeOpenedEvent, received.append)  # type: ignore[arg-type]
        manager = TradeManager(bus=bus)
        manager.open(_make_position())
        received.clear()

        manager.open(_make_position(trade_id=uuid.uuid4()))

        assert received == []

    def test_open_without_bus_does_not_raise(self) -> None:
        manager = TradeManager(bus=None)
        manager.open(_make_position())  # must not raise


class TestClose:
    def test_close_active_trade_succeeds(self) -> None:
        manager = TradeManager()
        position = _make_position()
        manager.open(position)

        closed = manager.close(ExitReason.TARGET_HIT)

        assert closed.trade_id == position.trade_id
        assert closed.is_active() is False
        assert closed.exit_reason == ExitReason.TARGET_HIT
        assert manager.active_position() is None
        assert manager.is_trade_active() is False

    def test_close_without_active_trade_raises(self) -> None:
        manager = TradeManager()
        with pytest.raises(TradeManagerError, match="No active trade to close"):
            manager.close(ExitReason.TARGET_HIT)

    def test_close_publishes_trade_closed_event(self) -> None:
        bus = EventBus()
        received: list[TradeClosedEvent] = []
        bus.subscribe(TradeClosedEvent, received.append)  # type: ignore[arg-type]
        manager = TradeManager(bus=bus)
        position = _make_position()
        manager.open(position)

        manager.close(ExitReason.STOP_LOSS)

        assert len(received) == 1
        assert received[0].trade_id == position.trade_id
        assert received[0].exit_reason == ExitReason.STOP_LOSS

    def test_close_without_bus_does_not_raise(self) -> None:
        manager = TradeManager(bus=None)
        manager.open(_make_position())
        manager.close(ExitReason.TARGET_HIT)  # must not raise


class TestNextTradeAfterClose:
    def test_new_trade_allowed_after_close(self) -> None:
        manager = TradeManager()
        manager.open(_make_position())
        manager.close(ExitReason.TARGET_HIT)

        second = _make_position(trade_id=uuid.uuid4())
        result = manager.open(second)

        assert result is second
        assert manager.active_position() is second


class TestInjectedClockAndIdFactory:
    def test_injected_clock_used_for_close_timestamp(self) -> None:
        fixed_time = datetime(2026, 7, 30, 10, 0, 0, tzinfo=UTC)
        manager = TradeManager(clock=lambda: fixed_time)
        manager.open(_make_position())

        closed = manager.close(ExitReason.TARGET_HIT)

        assert closed.closed_at == fixed_time

    def test_injected_id_factory_used_for_event_ids(self) -> None:
        fixed_id = uuid.uuid4()
        bus = EventBus()
        received: list[TradeOpenedEvent] = []
        bus.subscribe(TradeOpenedEvent, received.append)  # type: ignore[arg-type]
        manager = TradeManager(bus=bus, id_factory=lambda: fixed_id)

        manager.open(_make_position())

        assert received[0].event_id == fixed_id

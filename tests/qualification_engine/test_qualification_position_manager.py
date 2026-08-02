"""Tests for qualification_engine.qualification_position_manager."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import AnchorRole, ExitReason, TradeDirection
from core.events import QualificationClosedEvent, QualificationOpenedEvent
from core.exceptions import TradeManagerError
from events.event_bus import EventBus
from models.qualification_signal import QualificationSignal
from qualification_engine.qualification_position_manager import QualificationPositionManager


def _make_signal(**overrides: object) -> QualificationSignal:
    fields: dict[str, object] = {
        "signal_id": uuid.uuid4(),
        "anchor_role": AnchorRole.TOP,
        "side": TradeDirection.CE,
        "entry_strike": Decimal(24250),
        "entry_level": Decimal("120.1"),
        "target_level": Decimal("145.2"),
        "stop_loss_level": Decimal("98.3"),
        "competitor_exit_level": Decimal("121.5"),
        "qualified_at": datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
    }
    fields.update(overrides)
    return QualificationSignal(**fields)  # type: ignore[arg-type]


class TestOpen:
    def test_open_when_no_active_trade_succeeds(self) -> None:
        manager = QualificationPositionManager()
        signal = _make_signal()

        position = manager.open(signal)

        assert position is not None
        assert position.entry_strike == signal.entry_strike
        assert manager.active_position() is position
        assert manager.is_trade_active() is True

    def test_open_while_trade_active_is_rejected(self) -> None:
        manager = QualificationPositionManager()
        manager.open(_make_signal())

        result = manager.open(_make_signal(signal_id=uuid.uuid4()))

        assert result is None

    def test_open_publishes_qualification_opened_event(self) -> None:
        bus = EventBus()
        received: list[QualificationOpenedEvent] = []
        bus.subscribe(QualificationOpenedEvent, received.append)  # type: ignore[arg-type]
        manager = QualificationPositionManager(bus=bus)
        signal = _make_signal()

        position = manager.open(signal)

        assert position is not None
        assert len(received) == 1
        assert received[0].position_id == position.position_id
        assert received[0].entry_strike == signal.entry_strike
        assert received[0].target_level == signal.target_level

    def test_rejected_open_publishes_nothing(self) -> None:
        bus = EventBus()
        received: list[QualificationOpenedEvent] = []
        bus.subscribe(QualificationOpenedEvent, received.append)  # type: ignore[arg-type]
        manager = QualificationPositionManager(bus=bus)
        manager.open(_make_signal())
        received.clear()

        manager.open(_make_signal(signal_id=uuid.uuid4()))

        assert received == []

    def test_open_without_bus_does_not_raise(self) -> None:
        manager = QualificationPositionManager(bus=None)
        manager.open(_make_signal())  # must not raise


class TestClose:
    def test_close_active_trade_succeeds(self) -> None:
        manager = QualificationPositionManager()
        position = manager.open(_make_signal())
        assert position is not None

        closed = manager.close(ExitReason.TARGET_HIT, Decimal("145.2"))

        assert closed.position_id == position.position_id
        assert closed.is_active() is False
        assert closed.exit_reason == ExitReason.TARGET_HIT
        assert manager.active_position() is None
        assert manager.is_trade_active() is False

    def test_close_without_active_trade_raises(self) -> None:
        manager = QualificationPositionManager()
        with pytest.raises(TradeManagerError, match="No active qualified trade to close"):
            manager.close(ExitReason.TARGET_HIT, Decimal("145.2"))

    def test_close_publishes_qualification_closed_event(self) -> None:
        bus = EventBus()
        received: list[QualificationClosedEvent] = []
        bus.subscribe(QualificationClosedEvent, received.append)  # type: ignore[arg-type]
        manager = QualificationPositionManager(bus=bus)
        position = manager.open(_make_signal())
        assert position is not None

        manager.close(ExitReason.STOP_LOSS, Decimal("98.3"))

        assert len(received) == 1
        assert received[0].position_id == position.position_id
        assert received[0].exit_reason == ExitReason.STOP_LOSS

    def test_close_without_bus_does_not_raise(self) -> None:
        manager = QualificationPositionManager(bus=None)
        manager.open(_make_signal())
        manager.close(ExitReason.TARGET_HIT, Decimal("145.2"))  # must not raise


class TestNextTradeAfterClose:
    def test_new_trade_allowed_after_close(self) -> None:
        manager = QualificationPositionManager()
        manager.open(_make_signal())
        manager.close(ExitReason.TARGET_HIT, Decimal("145.2"))

        second = manager.open(_make_signal(signal_id=uuid.uuid4()))

        assert second is not None
        assert manager.active_position() is second


class TestForceCloseSessionEnd:
    def test_closes_active_trade_with_session_end_reason(self) -> None:
        manager = QualificationPositionManager()
        position = manager.open(_make_signal())
        assert position is not None

        closed = manager.force_close_session_end()

        assert closed is not None
        assert closed.exit_reason == ExitReason.SESSION_END
        assert manager.active_position() is None

    def test_no_active_trade_returns_none(self) -> None:
        manager = QualificationPositionManager()
        assert manager.force_close_session_end() is None


class TestInjectedClockAndIdFactory:
    def test_injected_clock_used_for_close_timestamp(self) -> None:
        fixed_time = datetime(2026, 7, 30, 10, 0, 0, tzinfo=UTC)
        manager = QualificationPositionManager(clock=lambda: fixed_time)
        manager.open(_make_signal())

        closed = manager.close(ExitReason.TARGET_HIT, Decimal("145.2"))

        assert closed.closed_at == fixed_time

    def test_injected_id_factory_used_for_event_ids(self) -> None:
        fixed_id = uuid.uuid4()
        bus = EventBus()
        received: list[QualificationOpenedEvent] = []
        bus.subscribe(QualificationOpenedEvent, received.append)  # type: ignore[arg-type]
        manager = QualificationPositionManager(bus=bus, id_factory=lambda: fixed_id)

        manager.open(_make_signal())

        assert received[0].event_id == fixed_id

"""Tests for entry_engine.entry_engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import TradeDirection
from core.events import TradeOpenedEvent, WinnerDetectedEvent
from entry_engine.entry_engine import EntryEngine
from events.event_bus import EventBus
from models.reference_level import ReferenceLevel
from position_manager.position_manager import PositionManager
from trade_manager.trade_manager import TradeManager


def _level(strike: int) -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(strike),
        ce_high=Decimal(110),
        ce_low=Decimal(90),
        pe_high=Decimal(105),
        pe_low=Decimal(85),
    )


LADDER = tuple(_level(s) for s in (23900, 23950, 24000, 24050, 24100))


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def position_manager(bus: EventBus) -> PositionManager:
    return PositionManager(TradeManager(bus=bus))


@pytest.fixture
def engine(bus: EventBus, position_manager: PositionManager) -> EntryEngine:
    return EntryEngine(bus=bus, position_manager=position_manager, reference_levels=LADDER)


def _winner_event(
    side: TradeDirection = TradeDirection.CE, strike: int = 24000
) -> WinnerDetectedEvent:
    now = datetime(2026, 7, 30, 9, 40, 0, tzinfo=UTC)
    return WinnerDetectedEvent(
        event_id=uuid.uuid4(),
        occurred_at=now,
        session_id=uuid.uuid4(),
        candle_timestamp=now,
        winning_side=side,
        winning_strike=Decimal(strike),
    )


class TestHandleWinnerDetectedDirect:
    def test_ce_winner_opens_position_with_confirmed_mapping(
        self, engine: EntryEngine, position_manager: PositionManager
    ) -> None:
        event = _winner_event(TradeDirection.CE, 24000)

        signal = engine.handle_winner_detected(event)

        assert signal.accepted is True
        assert signal.side == TradeDirection.CE
        assert signal.strike == Decimal(24000)
        assert signal.winner_event_id == event.event_id

        position = position_manager.current_position()
        assert position is not None
        assert position.entry_strike == Decimal(24000)
        assert position.target_level == Decimal(24050)
        assert position.support_level == Decimal(23950)
        assert position.competitor_monitor_strike == Decimal(23950)

    def test_pe_winner_opens_position_with_confirmed_mapping(
        self, engine: EntryEngine, position_manager: PositionManager
    ) -> None:
        event = _winner_event(TradeDirection.PE, 24000)

        signal = engine.handle_winner_detected(event)

        assert signal.accepted is True
        position = position_manager.current_position()
        assert position is not None
        assert position.target_level == Decimal(23950)
        assert position.support_level == Decimal(24050)
        assert position.competitor_monitor_strike == Decimal(24050)

    def test_second_winner_while_active_is_rejected(
        self, engine: EntryEngine, position_manager: PositionManager
    ) -> None:
        first = engine.handle_winner_detected(_winner_event(TradeDirection.CE, 24000))
        assert first.accepted is True

        second_event = _winner_event(TradeDirection.PE, 24050)
        second = engine.handle_winner_detected(second_event)

        assert second.accepted is False
        assert second.winner_event_id == second_event.event_id
        # original position untouched
        position = position_manager.current_position()
        assert position is not None
        assert position.entry_strike == Decimal(24000)


class TestBusWiring:
    def test_publishing_winner_detected_triggers_entry(
        self, bus: EventBus, position_manager: PositionManager
    ) -> None:
        EntryEngine(bus=bus, position_manager=position_manager, reference_levels=LADDER)
        received: list[TradeOpenedEvent] = []
        bus.subscribe(TradeOpenedEvent, received.append)  # type: ignore[arg-type]

        bus.publish(_winner_event(TradeDirection.CE, 24000))

        assert len(received) == 1
        assert received[0].entry_strike == Decimal(24000)
        assert position_manager.current_position() is not None

    def test_rejected_signal_via_bus_publishes_no_trade_opened(
        self, bus: EventBus, position_manager: PositionManager
    ) -> None:
        EntryEngine(bus=bus, position_manager=position_manager, reference_levels=LADDER)
        received: list[TradeOpenedEvent] = []
        bus.subscribe(TradeOpenedEvent, received.append)  # type: ignore[arg-type]

        bus.publish(_winner_event(TradeDirection.CE, 24000))
        bus.publish(_winner_event(TradeDirection.PE, 24050))

        assert len(received) == 1  # only the first was accepted


class TestInjectedClockAndIdFactory:
    def test_injected_clock_and_id_factory_used(
        self, bus: EventBus, position_manager: PositionManager
    ) -> None:
        fixed_time = datetime(2026, 7, 30, 9, 45, 0, tzinfo=UTC)
        fixed_signal_id = uuid.uuid4()
        engine = EntryEngine(
            bus=bus,
            position_manager=position_manager,
            reference_levels=LADDER,
            clock=lambda: fixed_time,
            id_factory=lambda: fixed_signal_id,
        )

        signal = engine.handle_winner_detected(_winner_event(TradeDirection.CE, 24000))

        assert signal.raised_at == fixed_time
        assert signal.signal_id == fixed_signal_id

"""Tests for winner_engine.winner_engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import TradeDirection
from core.events import WinnerDetectedEvent
from core.exceptions import AmbiguousWinnerError, ValidationError
from events.event_bus import EventBus
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from winner_engine.winner_engine import WinnerEngine


@pytest.fixture
def level() -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(24000),
        ce_high=Decimal(110),
        ce_low=Decimal(90),
        pe_high=Decimal(105),
        pe_low=Decimal(85),
    )


@pytest.fixture
def candle_timestamp() -> datetime:
    return datetime(2026, 7, 30, 9, 40, 0, tzinfo=UTC)


def _candle(low: str, high: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 40, 0, tzinfo=UTC),
        underlying_price=Decimal(24000),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _tick(price: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 40, 0, tzinfo=UTC), underlying_price=Decimal(price)
    )


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def engine(bus: EventBus) -> WinnerEngine:
    return WinnerEngine(bus=bus)


@pytest.fixture
def session_id() -> uuid.UUID:
    return uuid.uuid4()


class TestCeWins:
    def test_ce_touches_high_declares_ce_winner(
        self,
        engine: WinnerEngine,
        bus: EventBus,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        received: list[WinnerDetectedEvent] = []
        bus.subscribe(WinnerDetectedEvent, received.append)  # type: ignore[arg-type]

        ce = _candle("105", "115")  # range includes ce_high=110
        pe = _candle("50", "60")  # no pe level touched

        event = engine.evaluate(session_id, candle_timestamp, Decimal(24000), level, ce, pe)

        assert event is not None
        assert event.winning_side == TradeDirection.CE
        assert event.winning_strike == Decimal(24000)
        assert received == [event]

    def test_ce_touches_low_declares_ce_winner(
        self,
        engine: WinnerEngine,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        ce = _candle("85", "95")  # range includes ce_low=90
        pe = _candle("50", "60")

        event = engine.evaluate(session_id, candle_timestamp, Decimal(24000), level, ce, pe)

        assert event is not None
        assert event.winning_side == TradeDirection.CE


class TestPeWins:
    def test_pe_touches_high_declares_pe_winner(
        self,
        engine: WinnerEngine,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        ce = _candle("200", "210")  # no ce level touched
        pe = _candle("100", "110")  # range includes pe_high=105

        event = engine.evaluate(session_id, candle_timestamp, Decimal(24000), level, ce, pe)

        assert event is not None
        assert event.winning_side == TradeDirection.PE

    def test_pe_touches_low_declares_pe_winner(
        self,
        engine: WinnerEngine,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        ce = _candle("200", "210")
        pe = _candle("80", "90")  # range includes pe_low=85

        event = engine.evaluate(session_id, candle_timestamp, Decimal(24000), level, ce, pe)

        assert event is not None
        assert event.winning_side == TradeDirection.PE


class TestNoWinner:
    def test_neither_side_touches_returns_none(
        self,
        engine: WinnerEngine,
        bus: EventBus,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        received: list[WinnerDetectedEvent] = []
        bus.subscribe(WinnerDetectedEvent, received.append)  # type: ignore[arg-type]

        ce = _candle("200", "210")
        pe = _candle("50", "60")

        event = engine.evaluate(session_id, candle_timestamp, Decimal(24000), level, ce, pe)

        assert event is None
        assert received == []


class TestAmbiguousWinner:
    def test_both_touching_raises(
        self,
        engine: WinnerEngine,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        ce = _candle("105", "115")  # touches ce_high
        pe = _candle("100", "110")  # touches pe_high

        with pytest.raises(AmbiguousWinnerError, match="does not occur"):
            engine.evaluate(session_id, candle_timestamp, Decimal(24000), level, ce, pe)


class TestTickModeRejected:
    def test_ce_tick_snapshot_raises(
        self,
        engine: WinnerEngine,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        with pytest.raises(ValidationError, match="requires candle-mode snapshots"):
            engine.evaluate(
                session_id,
                candle_timestamp,
                Decimal(24000),
                level,
                _tick("100"),
                _candle("50", "60"),
            )

    def test_pe_tick_snapshot_raises(
        self,
        engine: WinnerEngine,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        with pytest.raises(ValidationError, match="requires candle-mode snapshots"):
            engine.evaluate(
                session_id,
                candle_timestamp,
                Decimal(24000),
                level,
                _candle("200", "210"),
                _tick("100"),
            )


class TestInjectedClockAndIdFactory:
    def test_injected_clock_and_id_factory_used(
        self,
        bus: EventBus,
        level: ReferenceLevel,
        candle_timestamp: datetime,
        session_id: uuid.UUID,
    ) -> None:
        fixed_time = datetime(2026, 7, 30, 10, 0, 0, tzinfo=UTC)
        fixed_id = uuid.uuid4()
        engine = WinnerEngine(bus=bus, clock=lambda: fixed_time, id_factory=lambda: fixed_id)

        ce = _candle("105", "115")
        pe = _candle("50", "60")
        event = engine.evaluate(session_id, candle_timestamp, Decimal(24000), level, ce, pe)

        assert event is not None
        assert event.occurred_at == fixed_time
        assert event.event_id == fixed_id

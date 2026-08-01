"""Tests for core.events."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from core.enums import EventPriority, ExitReason, TradeDirection
from core.events import (
    CompetitorHitEvent,
    Event,
    MarketCloseEvent,
    MarketOpenEvent,
    QualificationClosedEvent,
    QualificationOpenedEvent,
    StrikeSelectedEvent,
    TargetHitEvent,
    TradeClosedEvent,
    TradeOpenedEvent,
    WeeklyFutureCalculatedEvent,
    WinnerDetectedEvent,
)
from core.exceptions import ValidationError


@pytest.fixture
def event_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def occurred_at() -> datetime:
    return datetime(2026, 7, 30, 9, 20, 0)  # noqa: DTZ001


@pytest.fixture
def session_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def trade_id() -> uuid.UUID:
    return uuid.uuid4()


class TestMarketOpenEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, session_id: uuid.UUID
    ) -> None:
        event = MarketOpenEvent(event_id, occurred_at, session_id)
        assert event.session_id == session_id
        assert event.priority == EventPriority.NORMAL
        assert isinstance(event, Event)

    def test_none_event_id_raises(self, occurred_at: datetime, session_id: uuid.UUID) -> None:
        with pytest.raises(ValidationError, match="event_id must not be None"):
            MarketOpenEvent(None, occurred_at, session_id)  # type: ignore[arg-type]

    def test_none_occurred_at_raises(self, event_id: uuid.UUID, session_id: uuid.UUID) -> None:
        with pytest.raises(ValidationError, match="occurred_at must not be None"):
            MarketOpenEvent(event_id, None, session_id)  # type: ignore[arg-type]

    def test_none_session_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="session_id must not be None"):
            MarketOpenEvent(event_id, occurred_at, None)  # type: ignore[arg-type]

    def test_is_frozen(
        self, event_id: uuid.UUID, occurred_at: datetime, session_id: uuid.UUID
    ) -> None:
        event = MarketOpenEvent(event_id, occurred_at, session_id)
        with pytest.raises(AttributeError):
            event.session_id = uuid.uuid4()  # type: ignore[misc]


class TestMarketCloseEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, session_id: uuid.UUID
    ) -> None:
        event = MarketCloseEvent(event_id, occurred_at, session_id)
        assert event.session_id == session_id

    def test_none_session_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="session_id must not be None"):
            MarketCloseEvent(event_id, occurred_at, None)  # type: ignore[arg-type]


class TestWeeklyFutureCalculatedEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, session_id: uuid.UUID
    ) -> None:
        event = WeeklyFutureCalculatedEvent(
            event_id, occurred_at, session_id, Decimal(24500), Decimal(24000)
        )
        assert event.weekly_future_high == Decimal(24500)
        assert event.weekly_future_low == Decimal(24000)

    def test_none_session_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="session_id must not be None"):
            WeeklyFutureCalculatedEvent(
                event_id, occurred_at, None, Decimal(1), Decimal(1)  # type: ignore[arg-type]
            )


class TestStrikeSelectedEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, session_id: uuid.UUID
    ) -> None:
        event = StrikeSelectedEvent(
            event_id, occurred_at, session_id, Decimal(24100), Decimal(23900)
        )
        assert event.top_strike == Decimal(24100)
        assert event.bottom_strike == Decimal(23900)

    def test_none_session_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="session_id must not be None"):
            StrikeSelectedEvent(
                event_id, occurred_at, None, Decimal(1), Decimal(1)  # type: ignore[arg-type]
            )


class TestWinnerDetectedEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, session_id: uuid.UUID
    ) -> None:
        event = WinnerDetectedEvent(
            event_id, occurred_at, session_id, occurred_at, TradeDirection.CE, Decimal(24100)
        )
        assert event.winning_side == TradeDirection.CE
        assert event.priority == EventPriority.HIGH

    def test_none_session_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="session_id must not be None"):
            WinnerDetectedEvent(
                event_id,
                occurred_at,
                None,  # type: ignore[arg-type]
                occurred_at,
                TradeDirection.CE,
                Decimal(1),
            )


class TestTradeOpenedEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, trade_id: uuid.UUID
    ) -> None:
        event = TradeOpenedEvent(
            event_id,
            occurred_at,
            trade_id,
            Decimal(24100),
            TradeDirection.CE,
            Decimal(24150),
            Decimal(24050),
            Decimal(24050),
        )
        assert event.entry_strike == Decimal(24100)
        assert event.target_level == Decimal(24150)
        assert event.support_level == Decimal(24050)
        assert event.competitor_monitor_strike == Decimal(24050)

    def test_none_trade_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="trade_id must not be None"):
            TradeOpenedEvent(
                event_id,
                occurred_at,
                None,  # type: ignore[arg-type]
                Decimal(1),
                TradeDirection.CE,
                Decimal(1),
                Decimal(1),
                Decimal(1),
            )


class TestTradeClosedEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, trade_id: uuid.UUID
    ) -> None:
        event = TradeClosedEvent(event_id, occurred_at, trade_id, ExitReason.TARGET_HIT)
        assert event.exit_reason == ExitReason.TARGET_HIT

    def test_none_trade_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="trade_id must not be None"):
            TradeClosedEvent(event_id, occurred_at, None, ExitReason.TARGET_HIT)  # type: ignore[arg-type]


class TestQualificationOpenedEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, trade_id: uuid.UUID
    ) -> None:
        event = QualificationOpenedEvent(
            event_id,
            occurred_at,
            trade_id,
            Decimal(24250),
            TradeDirection.CE,
            Decimal("120.1"),
            Decimal("145.2"),
            Decimal("98.3"),
            Decimal("121.5"),
        )
        assert event.entry_strike == Decimal(24250)
        assert event.entry_level == Decimal("120.1")
        assert event.target_level == Decimal("145.2")
        assert event.stop_loss_level == Decimal("98.3")
        assert event.competitor_exit_level == Decimal("121.5")

    def test_none_position_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="position_id must not be None"):
            QualificationOpenedEvent(
                event_id,
                occurred_at,
                None,  # type: ignore[arg-type]
                Decimal(1),
                TradeDirection.CE,
                Decimal(1),
                Decimal(1),
                Decimal(1),
                Decimal(1),
            )


class TestQualificationClosedEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, trade_id: uuid.UUID
    ) -> None:
        event = QualificationClosedEvent(event_id, occurred_at, trade_id, ExitReason.TARGET_HIT)
        assert event.exit_reason == ExitReason.TARGET_HIT

    def test_none_position_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="position_id must not be None"):
            QualificationClosedEvent(
                event_id, occurred_at, None, ExitReason.TARGET_HIT  # type: ignore[arg-type]
            )


class TestTargetHitEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, trade_id: uuid.UUID
    ) -> None:
        event = TargetHitEvent(event_id, occurred_at, trade_id, Decimal(24150))
        assert event.target_level == Decimal(24150)
        assert event.priority == EventPriority.CRITICAL

    def test_none_trade_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="trade_id must not be None"):
            TargetHitEvent(event_id, occurred_at, None, Decimal(1))  # type: ignore[arg-type]


class TestCompetitorHitEvent:
    def test_valid_construction(
        self, event_id: uuid.UUID, occurred_at: datetime, trade_id: uuid.UUID
    ) -> None:
        event = CompetitorHitEvent(event_id, occurred_at, trade_id, Decimal(24050))
        assert event.competitor_strike == Decimal(24050)

    def test_none_trade_id_raises(self, event_id: uuid.UUID, occurred_at: datetime) -> None:
        with pytest.raises(ValidationError, match="trade_id must not be None"):
            CompetitorHitEvent(event_id, occurred_at, None, Decimal(1))  # type: ignore[arg-type]

"""Tests for replay.replay_engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.events import MarketCloseEvent, MarketOpenEvent
from core.exceptions import ReplayError
from events.event_bus import EventBus
from models.market_snapshot import MarketSnapshot
from replay.replay_engine import ReplayEngine


def _candle(minute: int, price: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, minute, 0, tzinfo=UTC),
        underlying_price=Decimal(price),
    )


class TestRun:
    def test_yields_every_candle_in_order(self) -> None:
        engine = ReplayEngine()
        candles = [_candle(15, "24000"), _candle(16, "24010"), _candle(17, "24020")]

        result = list(engine.run(uuid.uuid4(), candles))

        assert result == candles

    def test_empty_candles_raises(self) -> None:
        engine = ReplayEngine()
        with pytest.raises(ReplayError, match="no candles to replay"):
            list(engine.run(uuid.uuid4(), []))

    def test_publishes_market_open_before_first_candle(self) -> None:
        bus = EventBus()
        received: list[MarketOpenEvent] = []
        bus.subscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]
        session_id = uuid.uuid4()
        engine = ReplayEngine(bus=bus)

        list(engine.run(session_id, [_candle(15, "24000")]))

        assert len(received) == 1
        assert received[0].session_id == session_id

    def test_publishes_market_close_after_last_candle(self) -> None:
        bus = EventBus()
        received: list[MarketCloseEvent] = []
        bus.subscribe(MarketCloseEvent, received.append)  # type: ignore[arg-type]
        session_id = uuid.uuid4()
        engine = ReplayEngine(bus=bus)

        list(engine.run(session_id, [_candle(15, "24000")]))

        assert len(received) == 1
        assert received[0].session_id == session_id

    def test_market_open_published_before_any_candle_is_yielded(self) -> None:
        bus = EventBus()
        received: list[MarketOpenEvent] = []
        bus.subscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]
        engine = ReplayEngine(bus=bus)

        generator = engine.run(uuid.uuid4(), [_candle(15, "24000")])
        first_candle = next(generator)

        assert len(received) == 1
        assert first_candle.underlying_price == Decimal(24000)

    def test_market_close_not_published_until_generator_exhausted(self) -> None:
        bus = EventBus()
        received: list[MarketCloseEvent] = []
        bus.subscribe(MarketCloseEvent, received.append)  # type: ignore[arg-type]
        engine = ReplayEngine(bus=bus)

        generator = engine.run(uuid.uuid4(), [_candle(15, "24000"), _candle(16, "24010")])
        next(generator)

        assert received == []

        next(generator)
        with pytest.raises(StopIteration):
            next(generator)

        assert len(received) == 1

    def test_run_without_bus_does_not_raise(self) -> None:
        engine = ReplayEngine(bus=None)
        list(engine.run(uuid.uuid4(), [_candle(15, "24000")]))

    def test_no_strategy_logic_snapshots_pass_through_unmodified(self) -> None:
        engine = ReplayEngine()
        candle = _candle(15, "24000")

        (result,) = list(engine.run(uuid.uuid4(), [candle]))

        assert result is candle


class TestInjectedClockAndIdFactory:
    def test_injected_clock_used_for_events(self) -> None:
        fixed_time = datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)
        bus = EventBus()
        received: list[MarketOpenEvent] = []
        bus.subscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]
        engine = ReplayEngine(bus=bus, clock=lambda: fixed_time)

        list(engine.run(uuid.uuid4(), [_candle(15, "24000")]))

        assert received[0].occurred_at == fixed_time

    def test_injected_id_factory_used_for_events(self) -> None:
        fixed_id = uuid.uuid4()
        bus = EventBus()
        received: list[MarketOpenEvent] = []
        bus.subscribe(MarketOpenEvent, received.append)  # type: ignore[arg-type]
        engine = ReplayEngine(bus=bus, id_factory=lambda: fixed_id)

        list(engine.run(uuid.uuid4(), [_candle(15, "24000")]))

        assert received[0].event_id == fixed_id

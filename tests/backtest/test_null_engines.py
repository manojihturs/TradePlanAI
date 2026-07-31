"""Tests for backtest.null_engines."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from backtest.null_engines import NeverTriggersStopLoss, NeverTriggersTrailingStop
from core.enums import TradeDirection
from interfaces.stop_loss_engine import StopLossEngine
from interfaces.trailing_stop_engine import TrailingStopEngine
from models.market_snapshot import MarketSnapshot
from models.trade_position import TradePosition

_TIMESTAMP = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)


def _position() -> TradePosition:
    return TradePosition(
        trade_id=uuid.uuid4(),
        entry_strike=Decimal(24000),
        entry_side=TradeDirection.CE,
        target_level=Decimal(24050),
        support_level=Decimal(23950),
        competitor_monitor_strike=Decimal(23950),
        opened_at=_TIMESTAMP,
    )


def _snapshot() -> MarketSnapshot:
    return MarketSnapshot(timestamp=_TIMESTAMP, underlying_price=Decimal(24000))


class TestNeverTriggersStopLoss:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(NeverTriggersStopLoss(), StopLossEngine)

    def test_always_returns_false(self) -> None:
        assert NeverTriggersStopLoss().check(_position(), _snapshot()) is False


class TestNeverTriggersTrailingStop:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(NeverTriggersTrailingStop(), TrailingStopEngine)

    def test_always_returns_false(self) -> None:
        assert NeverTriggersTrailingStop().check(_position(), _snapshot()) is False

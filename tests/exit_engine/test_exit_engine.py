"""Tests for exit_engine.exit_engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import ExitReason, TradeDirection
from core.exceptions import UnresolvedBusinessRuleError, ValidationError
from exit_engine.exit_engine import ExitEngine
from interfaces.stop_loss_engine import StopLossEngine
from interfaces.trailing_stop_engine import TrailingStopEngine
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from models.trade_position import TradePosition
from position_manager.position_manager import PositionManager
from trade_history.trade_history import TradeHistory
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


def _candle(low: str, high: str, when: datetime) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=when,
        underlying_price=Decimal(24000),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _no_touch(when: datetime) -> MarketSnapshot:
    return _candle("200", "210", when)


class _AlwaysFalseStopLoss:
    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        return False


class _AlwaysTrueStopLoss:
    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        return True


class _AlwaysFalseTrailingStop:
    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        return False


class _AlwaysTrueTrailingStop:
    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        return True


class _RaisingStopLoss:
    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        raise UnresolvedBusinessRuleError("Stop Loss rule is MISSING INFORMATION.")


@pytest.fixture
def candle_timestamp() -> datetime:
    return datetime(2026, 7, 30, 9, 40, 0, tzinfo=UTC)


@pytest.fixture
def position_manager(candle_timestamp: datetime) -> PositionManager:
    return PositionManager(TradeManager(clock=lambda: candle_timestamp))


def _open_ce_trade(position_manager: PositionManager) -> TradePosition:
    position = position_manager.open_position(
        trade_id=uuid.uuid4(),
        entry_strike=Decimal(24000),
        entry_side=TradeDirection.CE,
        opened_at=datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
        reference_levels=LADDER,
    )
    assert position is not None
    return position


def _open_pe_trade(position_manager: PositionManager) -> TradePosition:
    position = position_manager.open_position(
        trade_id=uuid.uuid4(),
        entry_strike=Decimal(24000),
        entry_side=TradeDirection.PE,
        opened_at=datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
        reference_levels=LADDER,
    )
    assert position is not None
    return position


def _engine(
    position_manager: PositionManager,
    stop_loss: StopLossEngine | None = None,
    trailing_stop: TrailingStopEngine | None = None,
    trade_history: TradeHistory | None = None,
) -> ExitEngine:
    return ExitEngine(
        position_manager=position_manager,
        reference_levels=LADDER,
        stop_loss_engine=stop_loss or _AlwaysFalseStopLoss(),
        trailing_stop_engine=trailing_stop or _AlwaysFalseTrailingStop(),
        trade_history=trade_history,
    )


class TestNoActiveTrade:
    def test_returns_none_when_nothing_active(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        engine = _engine(position_manager)

        result = engine.evaluate(
            candle_timestamp, _no_touch(candle_timestamp), _no_touch(candle_timestamp)
        )

        assert result is None


class TestTargetHit:
    def test_ce_target_reached_closes_with_target_hit(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        position = _open_ce_trade(position_manager)
        assert position.target_level == Decimal(24050)
        engine = _engine(position_manager)

        target_snapshot = _candle("105", "115", candle_timestamp)  # touches ce_high=110 @ 24050
        competitor_snapshot = _no_touch(candle_timestamp)

        result = engine.evaluate(candle_timestamp, target_snapshot, competitor_snapshot)

        assert result is not None
        assert result.exit_reason == ExitReason.TARGET_HIT
        assert result.is_active() is False
        assert position_manager.current_position() is None

    def test_pe_target_reached_closes_with_target_hit(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        position = _open_pe_trade(position_manager)
        assert position.target_level == Decimal(23950)
        engine = _engine(position_manager)

        target_snapshot = _candle("100", "110", candle_timestamp)  # touches pe_high=105 @ 23950
        competitor_snapshot = _no_touch(candle_timestamp)

        result = engine.evaluate(candle_timestamp, target_snapshot, competitor_snapshot)

        assert result is not None
        assert result.exit_reason == ExitReason.TARGET_HIT


class TestCompetitorHit:
    def test_ce_competitor_hit_closes_with_competitor_hit(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        position = _open_ce_trade(position_manager)
        assert position.competitor_monitor_strike == Decimal(23950)
        engine = _engine(position_manager)

        target_snapshot = _no_touch(candle_timestamp)
        # competitor side for CE entry is PE; touches pe_high=105 at strike 23950
        competitor_snapshot = _candle("100", "110", candle_timestamp)

        result = engine.evaluate(candle_timestamp, target_snapshot, competitor_snapshot)

        assert result is not None
        assert result.exit_reason == ExitReason.COMPETITOR_HIT

    def test_pe_competitor_hit_closes_with_competitor_hit(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        position = _open_pe_trade(position_manager)
        assert position.competitor_monitor_strike == Decimal(24050)
        engine = _engine(position_manager)

        target_snapshot = _no_touch(candle_timestamp)
        # competitor side for PE entry is CE; touches ce_high=110 at strike 24050
        competitor_snapshot = _candle("105", "115", candle_timestamp)

        result = engine.evaluate(candle_timestamp, target_snapshot, competitor_snapshot)

        assert result is not None
        assert result.exit_reason == ExitReason.COMPETITOR_HIT


class TestStopLoss:
    def test_stop_loss_engine_true_closes_with_stop_loss(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(position_manager, stop_loss=_AlwaysTrueStopLoss())

        result = engine.evaluate(
            candle_timestamp, _no_touch(candle_timestamp), _no_touch(candle_timestamp)
        )

        assert result is not None
        assert result.exit_reason == ExitReason.STOP_LOSS

    def test_stop_loss_engine_false_does_not_close(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(position_manager, stop_loss=_AlwaysFalseStopLoss())

        result = engine.evaluate(
            candle_timestamp, _no_touch(candle_timestamp), _no_touch(candle_timestamp)
        )

        assert result is None
        assert position_manager.current_position() is not None

    def test_stop_loss_engine_raising_propagates(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(position_manager, stop_loss=_RaisingStopLoss())

        with pytest.raises(UnresolvedBusinessRuleError, match="MISSING INFORMATION"):
            engine.evaluate(
                candle_timestamp, _no_touch(candle_timestamp), _no_touch(candle_timestamp)
            )


class TestTrailingStop:
    def test_trailing_stop_engine_true_closes_with_trailing_stop(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(position_manager, trailing_stop=_AlwaysTrueTrailingStop())

        result = engine.evaluate(
            candle_timestamp, _no_touch(candle_timestamp), _no_touch(candle_timestamp)
        )

        assert result is not None
        assert result.exit_reason == ExitReason.TRAILING_STOP


class TestPrecedenceOrder:
    def test_target_checked_before_competitor(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(position_manager)

        # both target and competitor conditions are met simultaneously
        target_snapshot = _candle("105", "115", candle_timestamp)  # touches target
        competitor_snapshot = _candle("100", "110", candle_timestamp)  # touches competitor

        result = engine.evaluate(candle_timestamp, target_snapshot, competitor_snapshot)

        assert result is not None
        assert result.exit_reason == ExitReason.TARGET_HIT  # target wins per literal check order

    def test_competitor_checked_before_stop_loss(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(position_manager, stop_loss=_AlwaysTrueStopLoss())

        target_snapshot = _no_touch(candle_timestamp)
        competitor_snapshot = _candle("100", "110", candle_timestamp)  # touches competitor

        result = engine.evaluate(candle_timestamp, target_snapshot, competitor_snapshot)

        assert result is not None
        assert result.exit_reason == ExitReason.COMPETITOR_HIT

    def test_stop_loss_checked_before_trailing_stop(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(
            position_manager,
            stop_loss=_AlwaysTrueStopLoss(),
            trailing_stop=_AlwaysTrueTrailingStop(),
        )

        result = engine.evaluate(
            candle_timestamp, _no_touch(candle_timestamp), _no_touch(candle_timestamp)
        )

        assert result is not None
        assert result.exit_reason == ExitReason.STOP_LOSS


class TestTickModeRejected:
    def test_tick_target_snapshot_raises(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(position_manager)
        tick = MarketSnapshot(timestamp=candle_timestamp, underlying_price=Decimal(100))

        with pytest.raises(ValidationError, match="requires candle-mode snapshots"):
            engine.evaluate(candle_timestamp, tick, _no_touch(candle_timestamp))


class TestUnknownStrikeInLadder:
    def test_missing_reference_level_raises(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        position_manager.open_position(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24000),
            entry_side=TradeDirection.CE,
            opened_at=datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
            reference_levels=LADDER,
        )
        engine = ExitEngine(
            position_manager=position_manager,
            reference_levels=(_level(24000),),  # missing 24050 (target) and 23950 (competitor)
            stop_loss_engine=_AlwaysFalseStopLoss(),
            trailing_stop_engine=_AlwaysFalseTrailingStop(),
        )

        with pytest.raises(ValidationError, match="No ReferenceLevel found for strike"):
            engine.evaluate(
                candle_timestamp, _no_touch(candle_timestamp), _no_touch(candle_timestamp)
            )


class TestTradeHistoryIntegration:
    def test_closed_trade_automatically_stored_in_history(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        position = _open_ce_trade(position_manager)
        history = TradeHistory()
        engine = _engine(position_manager, trade_history=history)

        target_snapshot = _candle("105", "115", candle_timestamp)
        engine.evaluate(candle_timestamp, target_snapshot, _no_touch(candle_timestamp))

        record = history.get_trade(position.trade_id)
        assert record is not None
        assert record.exit_reason == ExitReason.TARGET_HIT

    def test_no_history_injected_does_not_raise(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine = _engine(position_manager, trade_history=None)

        target_snapshot = _candle("105", "115", candle_timestamp)
        result = engine.evaluate(candle_timestamp, target_snapshot, _no_touch(candle_timestamp))

        assert result is not None


class TestDependencyInjection:
    def test_different_stop_loss_implementations_are_swappable(
        self, position_manager: PositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_trade(position_manager)
        engine_a = _engine(position_manager, stop_loss=_AlwaysFalseStopLoss())
        result_a = engine_a.evaluate(
            candle_timestamp, _no_touch(candle_timestamp), _no_touch(candle_timestamp)
        )
        assert result_a is None

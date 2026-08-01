"""Tests for qualification_engine.qualification_exit_engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import AnchorRole, ExitReason, TradeDirection
from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.qualification_signal import QualificationSignal
from models.qualified_position import QualifiedPosition
from qualification_engine.qualification_exit_engine import QualificationExitEngine
from qualification_engine.qualification_position_manager import QualificationPositionManager
from qualification_engine.qualification_trailing_stop import (
    NeverTriggersQualificationTrailingStop,
)


class _AlwaysTrueTrailingStop:
    def check(self, position: QualifiedPosition, snapshot: MarketSnapshot) -> bool:
        return True


def _candle(low: str, high: str, when: datetime) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=when,
        underlying_price=Decimal(24140),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _no_touch(when: datetime) -> MarketSnapshot:
    return _candle("9998", "9999", when)


@pytest.fixture
def candle_timestamp() -> datetime:
    return datetime(2026, 7, 30, 9, 40, 0, tzinfo=UTC)


@pytest.fixture
def position_manager() -> QualificationPositionManager:
    return QualificationPositionManager()


def _open_ce_position(position_manager: QualificationPositionManager) -> QualifiedPosition:
    signal = QualificationSignal(
        signal_id=uuid.uuid4(),
        anchor_role=AnchorRole.TOP,
        side=TradeDirection.CE,
        entry_strike=Decimal(24250),
        entry_level=Decimal("120.1"),
        target_level=Decimal("145.2"),
        stop_loss_level=Decimal("98.3"),
        competitor_exit_level=Decimal("121.5"),
        qualified_at=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
    )
    position = position_manager.open(signal)
    assert position is not None
    return position


class TestTargetHit:
    def test_own_snapshot_touching_target_closes_as_target_hit(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_position(position_manager)
        engine = QualificationExitEngine(position_manager, NeverTriggersQualificationTrailingStop())

        result = engine.evaluate(
            candle_timestamp,
            own_snapshot=_candle("145.0", "146.0", candle_timestamp),
            competitor_snapshot=_no_touch(candle_timestamp),
        )

        assert result is not None
        assert result.exit_reason == ExitReason.TARGET_HIT
        assert position_manager.is_trade_active() is False


class TestCompetitorHit:
    def test_competitor_snapshot_touching_fixed_level_closes_as_competitor_hit(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_position(position_manager)
        engine = QualificationExitEngine(position_manager, NeverTriggersQualificationTrailingStop())

        result = engine.evaluate(
            candle_timestamp,
            own_snapshot=_no_touch(candle_timestamp),
            competitor_snapshot=_candle("121.0", "122.0", candle_timestamp),
        )

        assert result is not None
        assert result.exit_reason == ExitReason.COMPETITOR_HIT


class TestStopLossHit:
    def test_own_snapshot_touching_stop_loss_closes_as_stop_loss(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_position(position_manager)
        engine = QualificationExitEngine(position_manager, NeverTriggersQualificationTrailingStop())

        result = engine.evaluate(
            candle_timestamp,
            own_snapshot=_candle("98.0", "98.5", candle_timestamp),
            competitor_snapshot=_no_touch(candle_timestamp),
        )

        assert result is not None
        assert result.exit_reason == ExitReason.STOP_LOSS


class TestTrailingStop:
    def test_injected_trailing_stop_true_closes_as_trailing_stop(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_position(position_manager)
        engine = QualificationExitEngine(position_manager, _AlwaysTrueTrailingStop())

        result = engine.evaluate(
            candle_timestamp,
            own_snapshot=_no_touch(candle_timestamp),
            competitor_snapshot=_no_touch(candle_timestamp),
        )

        assert result is not None
        assert result.exit_reason == ExitReason.TRAILING_STOP

    def test_never_triggers_null_object_never_fires(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_position(position_manager)
        engine = QualificationExitEngine(position_manager, NeverTriggersQualificationTrailingStop())

        result = engine.evaluate(
            candle_timestamp,
            own_snapshot=_no_touch(candle_timestamp),
            competitor_snapshot=_no_touch(candle_timestamp),
        )

        assert result is None
        assert position_manager.is_trade_active() is True


class TestNoTouch:
    def test_no_condition_met_returns_none(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_position(position_manager)
        engine = QualificationExitEngine(position_manager, NeverTriggersQualificationTrailingStop())

        result = engine.evaluate(
            candle_timestamp,
            own_snapshot=_no_touch(candle_timestamp),
            competitor_snapshot=_no_touch(candle_timestamp),
        )

        assert result is None


class TestValidation:
    def test_no_active_trade_raises(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        engine = QualificationExitEngine(position_manager, NeverTriggersQualificationTrailingStop())

        with pytest.raises(ValidationError, match="requires an active trade"):
            engine.evaluate(
                candle_timestamp,
                own_snapshot=_no_touch(candle_timestamp),
                competitor_snapshot=_no_touch(candle_timestamp),
            )

    def test_non_candle_own_snapshot_raises(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_position(position_manager)
        engine = QualificationExitEngine(position_manager, NeverTriggersQualificationTrailingStop())
        tick = MarketSnapshot(timestamp=candle_timestamp, underlying_price=Decimal(24140))

        with pytest.raises(ValidationError, match="candle-mode snapshots"):
            engine.evaluate(
                candle_timestamp,
                own_snapshot=tick,
                competitor_snapshot=_no_touch(candle_timestamp),
            )

    def test_non_candle_competitor_snapshot_raises(
        self, position_manager: QualificationPositionManager, candle_timestamp: datetime
    ) -> None:
        _open_ce_position(position_manager)
        engine = QualificationExitEngine(position_manager, NeverTriggersQualificationTrailingStop())
        tick = MarketSnapshot(timestamp=candle_timestamp, underlying_price=Decimal(24140))

        with pytest.raises(ValidationError, match="candle-mode snapshots"):
            engine.evaluate(
                candle_timestamp,
                own_snapshot=_no_touch(candle_timestamp),
                competitor_snapshot=tick,
            )

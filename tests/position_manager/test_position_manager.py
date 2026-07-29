"""Tests for position_manager.position_manager."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import ExitReason, TradeDirection
from core.exceptions import TradeManagerError, ValidationError
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


#: A 5-strike ladder: 23900, 23950, 24000, 24050, 24100
LADDER = tuple(_level(s) for s in (23900, 23950, 24000, 24050, 24100))


@pytest.fixture
def manager() -> PositionManager:
    return PositionManager(TradeManager())


@pytest.fixture
def opened_at() -> datetime:
    return datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)


class TestOpenPositionCEMapping:
    def test_target_support_competitor_exit_for_ce(
        self, manager: PositionManager, opened_at: datetime
    ) -> None:
        position = manager.open_position(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24000),
            entry_side=TradeDirection.CE,
            opened_at=opened_at,
            reference_levels=LADDER,
        )
        assert position is not None
        assert position.target_level == Decimal(24050)  # CE(S+1)
        assert position.support_level == Decimal(23950)  # CE(S-1)
        assert position.competitor_monitor_strike == Decimal(23950)  # PE(S-1)


class TestOpenPositionPEMapping:
    def test_target_support_competitor_exit_for_pe(
        self, manager: PositionManager, opened_at: datetime
    ) -> None:
        position = manager.open_position(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24000),
            entry_side=TradeDirection.PE,
            opened_at=opened_at,
            reference_levels=LADDER,
        )
        assert position is not None
        assert position.target_level == Decimal(23950)  # PE(S-1)
        assert position.support_level == Decimal(24050)  # PE(S+1)
        assert position.competitor_monitor_strike == Decimal(24050)  # CE(S+1)


class TestLadderBoundaries:
    def test_entry_strike_not_in_ladder_raises(
        self, manager: PositionManager, opened_at: datetime
    ) -> None:
        with pytest.raises(ValidationError, match="is not present in the supplied"):
            manager.open_position(
                trade_id=uuid.uuid4(),
                entry_strike=Decimal(99999),
                entry_side=TradeDirection.CE,
                opened_at=opened_at,
                reference_levels=LADDER,
            )

    def test_entry_strike_at_top_of_ladder_raises(
        self, manager: PositionManager, opened_at: datetime
    ) -> None:
        with pytest.raises(ValidationError, match="no adjacent strike"):
            manager.open_position(
                trade_id=uuid.uuid4(),
                entry_strike=Decimal(24100),
                entry_side=TradeDirection.CE,
                opened_at=opened_at,
                reference_levels=LADDER,
            )

    def test_entry_strike_at_bottom_of_ladder_raises(
        self, manager: PositionManager, opened_at: datetime
    ) -> None:
        with pytest.raises(ValidationError, match="no adjacent strike"):
            manager.open_position(
                trade_id=uuid.uuid4(),
                entry_strike=Decimal(23900),
                entry_side=TradeDirection.PE,
                opened_at=opened_at,
                reference_levels=LADDER,
            )


class TestSingleActiveTradeDelegation:
    def test_open_while_active_returns_none(
        self, manager: PositionManager, opened_at: datetime
    ) -> None:
        first = manager.open_position(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24000),
            entry_side=TradeDirection.CE,
            opened_at=opened_at,
            reference_levels=LADDER,
        )
        assert first is not None

        second = manager.open_position(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24050),
            entry_side=TradeDirection.CE,
            opened_at=opened_at,
            reference_levels=LADDER,
        )
        assert second is None
        assert manager.current_position() is first

    def test_close_position_delegates_to_trade_manager(
        self, manager: PositionManager, opened_at: datetime
    ) -> None:
        manager.open_position(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24000),
            entry_side=TradeDirection.CE,
            opened_at=opened_at,
            reference_levels=LADDER,
        )

        closed = manager.close_position(ExitReason.TARGET_HIT)

        assert closed.is_active() is False
        assert manager.current_position() is None
        assert manager.is_active() is False

    def test_close_without_active_trade_raises(self, manager: PositionManager) -> None:
        with pytest.raises(TradeManagerError, match="No active trade to close"):
            manager.close_position(ExitReason.TARGET_HIT)

    def test_new_trade_allowed_after_close(
        self, manager: PositionManager, opened_at: datetime
    ) -> None:
        manager.open_position(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24000),
            entry_side=TradeDirection.CE,
            opened_at=opened_at,
            reference_levels=LADDER,
        )
        manager.close_position(ExitReason.TARGET_HIT)

        second = manager.open_position(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24050),
            entry_side=TradeDirection.PE,
            opened_at=opened_at,
            reference_levels=LADDER,
        )
        assert second is not None
        assert manager.current_position() is second

    def test_current_position_none_when_idle(self, manager: PositionManager) -> None:
        assert manager.current_position() is None
        assert manager.is_active() is False

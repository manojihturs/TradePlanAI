"""Tests for trade_history.trade_history."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from core.enums import ExitReason, TradeDirection
from core.exceptions import ValidationError
from models.trade_position import TradePosition
from trade_history.trade_history import TradeHistory, TradeRecord


def _closed_position(
    *,
    entry_side: TradeDirection = TradeDirection.CE,
    exit_reason: ExitReason = ExitReason.TARGET_HIT,
    entry_strike: Decimal = Decimal(24000),
    target_level: Decimal = Decimal(24050),
    support_level: Decimal = Decimal(23950),
    competitor_monitor_strike: Decimal = Decimal(23950),
    opened_at: datetime = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
    closed_at: datetime = datetime(2026, 7, 30, 9, 45, 0, tzinfo=UTC),
) -> TradePosition:
    position = TradePosition(
        trade_id=uuid.uuid4(),
        entry_strike=entry_strike,
        entry_side=entry_side,
        target_level=target_level,
        support_level=support_level,
        competitor_monitor_strike=competitor_monitor_strike,
        opened_at=opened_at,
    )
    return position.close(exit_reason, closed_at)


class TestTradeRecordFromPosition:
    def test_target_hit_exit_strike_is_target_level(self) -> None:
        position = _closed_position(exit_reason=ExitReason.TARGET_HIT)
        record = TradeRecord.from_position(position)

        assert record.exit_strike == position.target_level
        assert record.direction == position.entry_side
        assert record.winner == position.entry_side
        assert record.pnl is None

    def test_competitor_hit_exit_strike_is_competitor_monitor_strike(self) -> None:
        position = _closed_position(exit_reason=ExitReason.COMPETITOR_HIT)
        record = TradeRecord.from_position(position)

        assert record.exit_strike == position.competitor_monitor_strike

    def test_stop_loss_exit_strike_is_entry_strike(self) -> None:
        position = _closed_position(exit_reason=ExitReason.STOP_LOSS)
        record = TradeRecord.from_position(position)

        assert record.exit_strike == position.entry_strike

    def test_trailing_stop_exit_strike_is_entry_strike(self) -> None:
        position = _closed_position(exit_reason=ExitReason.TRAILING_STOP)
        record = TradeRecord.from_position(position)

        assert record.exit_strike == position.entry_strike

    def test_duration_computed_correctly(self) -> None:
        opened_at = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)
        closed_at = datetime(2026, 7, 30, 9, 47, 30, tzinfo=UTC)
        position = _closed_position(opened_at=opened_at, closed_at=closed_at)

        record = TradeRecord.from_position(position)

        assert record.duration == timedelta(minutes=17, seconds=30)

    def test_target_support_competitor_strikes_carried_through(self) -> None:
        position = _closed_position(
            target_level=Decimal(24050),
            support_level=Decimal(23950),
            competitor_monitor_strike=Decimal(23950),
        )
        record = TradeRecord.from_position(position)

        assert record.target_strike == Decimal(24050)
        assert record.support_strike == Decimal(23950)
        assert record.competitor_exit_strike == Decimal(23950)

    def test_active_position_raises(self) -> None:
        active = TradePosition(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24000),
            entry_side=TradeDirection.CE,
            target_level=Decimal(24050),
            support_level=Decimal(23950),
            competitor_monitor_strike=Decimal(23950),
            opened_at=datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
        )
        with pytest.raises(ValidationError, match="Cannot build a TradeRecord"):
            TradeRecord.from_position(active)


class TestTradeRecordValidation:
    def test_none_trade_id_raises(self) -> None:
        position = _closed_position()
        record = TradeRecord.from_position(position)
        with pytest.raises(ValidationError, match="trade_id must not be None"):
            TradeRecord(
                trade_id=None,  # type: ignore[arg-type]
                direction=record.direction,
                winner=record.winner,
                entry_strike=record.entry_strike,
                exit_strike=record.exit_strike,
                entry_time=record.entry_time,
                exit_time=record.exit_time,
                exit_reason=record.exit_reason,
                duration=record.duration,
                target_strike=record.target_strike,
                support_strike=record.support_strike,
                competitor_exit_strike=record.competitor_exit_strike,
            )

    def test_negative_duration_raises(self) -> None:
        position = _closed_position()
        record = TradeRecord.from_position(position)
        with pytest.raises(ValidationError, match="duration must not be negative"):
            TradeRecord(
                trade_id=record.trade_id,
                direction=record.direction,
                winner=record.winner,
                entry_strike=record.entry_strike,
                exit_strike=record.exit_strike,
                entry_time=record.entry_time,
                exit_time=record.exit_time,
                exit_reason=record.exit_reason,
                duration=timedelta(seconds=-1),
                target_strike=record.target_strike,
                support_strike=record.support_strike,
                competitor_exit_strike=record.competitor_exit_strike,
            )


@pytest.fixture
def history() -> TradeHistory:
    return TradeHistory()


class TestAddTrade:
    def test_add_trade_returns_record_and_stores_it(self, history: TradeHistory) -> None:
        position = _closed_position()
        record = history.add_trade(position)

        assert history.get_all() == (record,)

    def test_add_active_position_raises(self, history: TradeHistory) -> None:
        active = TradePosition(
            trade_id=uuid.uuid4(),
            entry_strike=Decimal(24000),
            entry_side=TradeDirection.CE,
            target_level=Decimal(24050),
            support_level=Decimal(23950),
            competitor_monitor_strike=Decimal(23950),
            opened_at=datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
        )
        with pytest.raises(ValidationError, match="Cannot build a TradeRecord"):
            history.add_trade(active)


class TestGetTrade:
    def test_returns_matching_record(self, history: TradeHistory) -> None:
        position = _closed_position()
        record = history.add_trade(position)

        assert history.get_trade(position.trade_id) is record

    def test_returns_none_when_not_found(self, history: TradeHistory) -> None:
        assert history.get_trade(uuid.uuid4()) is None

    def test_skips_non_matching_records_before_finding_match(self, history: TradeHistory) -> None:
        first = history.add_trade(_closed_position())
        second_position = _closed_position()
        second = history.add_trade(second_position)

        assert history.get_trade(second_position.trade_id) is second
        assert first is not second


class TestFilterByDirection:
    def test_returns_only_matching_direction(self, history: TradeHistory) -> None:
        ce_record = history.add_trade(_closed_position(entry_side=TradeDirection.CE))
        history.add_trade(_closed_position(entry_side=TradeDirection.PE))

        assert history.filter_by_direction(TradeDirection.CE) == (ce_record,)


class TestFilterByDate:
    def test_returns_only_trades_on_that_date(self, history: TradeHistory) -> None:
        record_day_one = history.add_trade(
            _closed_position(
                opened_at=datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
                closed_at=datetime(2026, 7, 30, 9, 45, 0, tzinfo=UTC),
            )
        )
        history.add_trade(
            _closed_position(
                opened_at=datetime(2026, 7, 31, 9, 30, 0, tzinfo=UTC),
                closed_at=datetime(2026, 7, 31, 9, 45, 0, tzinfo=UTC),
            )
        )

        result = history.filter_by_date(datetime(2026, 7, 30, tzinfo=UTC).date())

        assert result == (record_day_one,)


class TestClear:
    def test_clear_removes_every_trade(self, history: TradeHistory) -> None:
        history.add_trade(_closed_position())
        history.clear()

        assert history.get_all() == ()


class TestNoGlobalState:
    def test_two_histories_are_independent(self) -> None:
        history_one = TradeHistory()
        history_two = TradeHistory()

        history_one.add_trade(_closed_position())

        assert len(history_one.get_all()) == 1
        assert len(history_two.get_all()) == 0

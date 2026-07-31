"""Tests for backtest.report."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from backtest.report import summarize_backtest
from core.enums import ExitReason, TradeDirection
from models.trade_position import TradePosition
from trade_history.trade_history import TradeRecord


def _closed_position(
    *,
    exit_reason: ExitReason = ExitReason.TARGET_HIT,
    opened_at: datetime = datetime(2026, 7, 30, 9, 25, 0, tzinfo=UTC),
    closed_at: datetime = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
) -> TradePosition:
    position = TradePosition(
        trade_id=uuid.uuid4(),
        entry_strike=Decimal(24000),
        entry_side=TradeDirection.CE,
        target_level=Decimal(24050),
        support_level=Decimal(23950),
        competitor_monitor_strike=Decimal(23950),
        opened_at=opened_at,
    )
    return position.close(exit_reason, closed_at)


class TestSummarizeBacktestNoTrades:
    def test_zero_trades(self) -> None:
        summary = summarize_backtest((), candles_processed=5)

        assert summary.total_trades == 0
        assert summary.exit_reason_counts == {}
        assert summary.average_duration is None
        assert summary.candles_processed == 5


class TestSummarizeBacktestWithTrades:
    def test_single_trade(self) -> None:
        record = TradeRecord.from_position(_closed_position())

        summary = summarize_backtest((record,), candles_processed=3)

        assert summary.total_trades == 1
        assert summary.exit_reason_counts == {ExitReason.TARGET_HIT: 1}
        assert summary.average_duration is not None
        assert summary.average_duration.total_seconds() == 300

    def test_multiple_trades_grouped_by_exit_reason(self) -> None:
        target = TradeRecord.from_position(_closed_position(exit_reason=ExitReason.TARGET_HIT))
        competitor = TradeRecord.from_position(
            _closed_position(exit_reason=ExitReason.COMPETITOR_HIT)
        )
        another_target = TradeRecord.from_position(
            _closed_position(exit_reason=ExitReason.TARGET_HIT)
        )

        summary = summarize_backtest((target, competitor, another_target), candles_processed=10)

        assert summary.total_trades == 3
        assert summary.exit_reason_counts == {
            ExitReason.TARGET_HIT: 2,
            ExitReason.COMPETITOR_HIT: 1,
        }

    def test_no_pnl_field_on_summary(self) -> None:
        # BacktestSummary must never expose a pnl/win-rate field - see
        # module docstring on why that would misrepresent unconfirmed
        # business logic as computed.
        summary = summarize_backtest((), candles_processed=0)

        assert not hasattr(summary, "pnl")
        assert not hasattr(summary, "win_rate")

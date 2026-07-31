"""Tests for backtest.runner."""

from __future__ import annotations

import uuid
from decimal import Decimal

from backtest.runner import BacktestRunner
from backtest.synthetic_data import build_synthetic_fixture
from core.enums import ExitReason, TradeDirection


class TestBacktestRunner:
    def test_full_run_detects_winner_enters_and_exits_via_target(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture)

        assert len(result.business_results) == 3
        assert all(br.success for br in result.business_results)

        trades = result.trade_history.get_all()
        assert len(trades) == 1
        trade = trades[0]
        assert trade.direction == TradeDirection.CE
        assert trade.entry_strike == fixture.anchor_strike
        assert trade.exit_strike == fixture.anchor_strike + Decimal(50)
        assert trade.exit_reason == ExitReason.TARGET_HIT
        assert trade.pnl is None

    def test_winner_recorded_on_first_candle(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture)

        first_result = result.business_results[0]
        assert first_result.context.winner is not None
        assert first_result.context.winner.winning_side == TradeDirection.CE
        assert first_result.context.winner.winning_strike == fixture.anchor_strike

    def test_exited_position_recorded_on_last_candle(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture)

        last_result = result.business_results[-1]
        assert last_result.context.exited_position is not None
        assert last_result.context.exited_position.exit_reason == ExitReason.TARGET_HIT

    def test_trade_timestamps_reflect_simulated_candle_time_not_wall_clock(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture)

        trade = result.trade_history.get_all()[0]
        assert trade.entry_time == fixture.dataset.candles[0].timestamp
        assert trade.exit_time == fixture.dataset.candles[-1].timestamp

    def test_deterministic_id_factory_is_used(self) -> None:
        fixed_id = uuid.uuid4()
        fixture = build_synthetic_fixture()

        result = BacktestRunner(id_factory=lambda: fixed_id).run(fixture)

        assert result.session_id == fixed_id

    def test_orb_stage_runs_alongside_the_rest(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture)

        for business_result in result.business_results:
            assert "orb" in business_result.completed_stages
            assert "weekly_future" in business_result.completed_stages
            assert "winner" in business_result.completed_stages
            assert "exit" in business_result.completed_stages

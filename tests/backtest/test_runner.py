"""Tests for backtest.runner."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from backtest.fixture import BacktestFixture
from backtest.runner import BacktestRunner
from backtest.synthetic_data import build_synthetic_fixture
from core.enums import ExitReason, TradeDirection, TrendDirection
from data.option_chain_dataset import OptionChainCandle, OptionChainDataset
from models.market_snapshot import MarketSnapshot
from models.strike_chain_snapshot import StrikeChainSnapshot
from reference_builder.reference_validator import StrikeCandleInput


class TestBacktestRunner:
    def test_full_run_detects_winner_enters_and_exits_via_target(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture, TrendDirection.BULLISH)

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

        result = BacktestRunner().run(fixture, TrendDirection.BULLISH)

        first_result = result.business_results[0]
        assert first_result.context.winner is not None
        assert first_result.context.winner.winning_side == TradeDirection.CE
        assert first_result.context.winner.winning_strike == fixture.anchor_strike

    def test_exited_position_recorded_on_last_candle(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture, TrendDirection.BULLISH)

        last_result = result.business_results[-1]
        assert last_result.context.exited_position is not None
        assert last_result.context.exited_position.exit_reason == ExitReason.TARGET_HIT

    def test_trade_timestamps_reflect_simulated_candle_time_not_wall_clock(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture, TrendDirection.BULLISH)

        trade = result.trade_history.get_all()[0]
        assert trade.entry_time == fixture.dataset.candles[0].timestamp
        assert trade.exit_time == fixture.dataset.candles[-1].timestamp

    def test_deterministic_id_factory_is_used(self) -> None:
        fixed_id = uuid.uuid4()
        fixture = build_synthetic_fixture()

        result = BacktestRunner(id_factory=lambda: fixed_id).run(fixture, TrendDirection.BULLISH)

        assert result.session_id == fixed_id

    def test_orb_stage_runs_alongside_the_rest(self) -> None:
        fixture = build_synthetic_fixture()

        result = BacktestRunner().run(fixture, TrendDirection.BULLISH)

        for business_result in result.business_results:
            assert "orb" in business_result.completed_stages
            assert "weekly_future" in business_result.completed_stages
            assert "winner" in business_result.completed_stages
            assert "exit" in business_result.completed_stages
            assert "qualification" in business_result.completed_stages
            assert "qualification_exit" in business_result.completed_stages


_ANCHOR = Decimal(24000)
_STRIKE_STEP = Decimal(50)
_LADDER_HALF_WIDTH = 6
_REF_TIME = datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)
_ENTRY_TIME = datetime(2026, 7, 30, 9, 25, 0, tzinfo=UTC)
_EXIT_TIME = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)


def _strikes() -> tuple[Decimal, ...]:
    return tuple(
        _ANCHOR + (Decimal(i) * _STRIKE_STEP)
        for i in range(-_LADDER_HALF_WIDTH, _LADDER_HALF_WIDTH + 1)
    )


def _offset(strike: Decimal) -> int:
    return int((strike - _ANCHOR) / _STRIKE_STEP)


def _snap(when: datetime, low: Decimal, high: Decimal) -> MarketSnapshot:
    mid = (low + high) / 2
    return MarketSnapshot(
        timestamp=when, underlying_price=_ANCHOR, open=mid, high=high, low=low, close=mid
    )


def _reference_inputs() -> tuple[StrikeCandleInput, ...]:
    # ce_high=150+o, ce_low=130+o (CE's own band, 130-151 range across
    # the ladder) and pe_high=100-o, pe_low=90-o (PE's own band,
    # 84-100 range) - deliberately kept numerically separated so a
    # qualification-column touch (pe_low, ce_high) never also falls
    # inside the OLD WinnerEngine's own ce_low/ce_high or pe_low/pe_high
    # band, which would otherwise trip AmbiguousWinnerError on the same
    # candle and halt the whole pipeline before QualificationStage
    # runs. At offset 0 this gives Weekly Future High/Low both rounding
    # to _ANCHOR + 50 (see _TOP below) - independently recomputed, not
    # assumed.
    inputs = []
    for strike in _strikes():
        o = Decimal(_offset(strike))
        inputs.append(
            StrikeCandleInput(
                strike=strike,
                ce_candle=_snap(_REF_TIME, Decimal(130) + o, Decimal(150) + o),
                pe_candle=_snap(_REF_TIME, Decimal(90) - o, Decimal(100) - o),
            )
        )
    return tuple(inputs)


# Weekly Future High = _ANCHOR + (ce_high - pe_low) @ offset 0 = _ANCHOR + (150-90) = _ANCHOR+60
# -> rounds to _ANCHOR+50. Low = _ANCHOR - (pe_high - ce_low) @ offset 0 = _ANCHOR - (100-130)
# = _ANCHOR+30 -> rounds to _ANCHOR+50. Top == Bottom == _ANCHOR+50, offset +1.
_TOP = _ANCHOR + _STRIKE_STEP
_TOP_OFFSET = 1
# Qualification (Top, CE, bullish): entry_column=pe_low, confirm_column=ce_high.
_ENTRY_LEVEL = Decimal(90) - _TOP_OFFSET  # 89
_CONFIRM_LEVEL = Decimal(150) + _TOP_OFFSET  # 151
_TARGET_LEVEL = Decimal(90) - (_TOP_OFFSET + 1)  # 88 (next strike up in the pe_low column)


def _no_touch_pair(strike: Decimal, when: datetime) -> StrikeChainSnapshot:
    return StrikeChainSnapshot(
        strike=strike,
        ce=_snap(when, Decimal(1), Decimal(2)),
        pe=_snap(when, Decimal(1), Decimal(2)),
    )


def _entry_candle() -> OptionChainCandle:
    # Top's own CE touches its own pe_low (89, unique to offset +1)
    # and own PE touches its own ce_high (151, unique to offset +1)
    # simultaneously - the confirmed dual-crossover. Neither value
    # falls inside Top's own ce_low/ce_high (131-151... note 151 IS
    # ce_high itself, but that's the PE candle touching it, not CE -
    # the old WinnerEngine only checks CE against ce band/PE against
    # pe band, never cross-column, so this does not trip it) or
    # pe_low/pe_high (89-99) bands in a way that causes both sides to
    # touch their OWN band simultaneously.
    pairs = [
        StrikeChainSnapshot(
            strike=_TOP,
            ce=_snap(_ENTRY_TIME, _ENTRY_LEVEL - Decimal("0.1"), _ENTRY_LEVEL + Decimal("0.1")),
            pe=_snap(_ENTRY_TIME, _CONFIRM_LEVEL - Decimal("0.1"), _CONFIRM_LEVEL + Decimal("0.1")),
        )
    ]
    pairs.extend(_no_touch_pair(s, _ENTRY_TIME) for s in _strikes() if s != _TOP)
    return OptionChainCandle(timestamp=_ENTRY_TIME, strikes=tuple(pairs))


def _target_hit_candle() -> OptionChainCandle:
    pairs = [
        StrikeChainSnapshot(
            strike=_TOP,
            ce=_snap(_EXIT_TIME, _TARGET_LEVEL - Decimal("0.1"), _TARGET_LEVEL + Decimal("0.1")),
            pe=_snap(_EXIT_TIME, Decimal(1), Decimal(2)),
        )
    ]
    pairs.extend(_no_touch_pair(s, _EXIT_TIME) for s in _strikes() if s != _TOP)
    return OptionChainCandle(timestamp=_EXIT_TIME, strikes=tuple(pairs))


class TestQualificationFlow:
    def test_qualification_position_closes_via_target_mid_run(self) -> None:
        fixture = BacktestFixture(
            session_date=date(2026, 7, 30),
            anchor_strike=_ANCHOR,
            reference_inputs=_reference_inputs(),
            dataset=OptionChainDataset(
                session_date=date(2026, 7, 30),
                candles=(_entry_candle(), _target_hit_candle()),
            ),
        )

        result = BacktestRunner().run(fixture, TrendDirection.BULLISH)

        assert len(result.qualification_positions) == 1
        position = result.qualification_positions[0]
        assert position.side is TradeDirection.CE
        assert position.entry_strike == _TOP
        assert position.exit_reason == ExitReason.TARGET_HIT

    def test_qualification_position_still_open_at_session_end_force_closes(self) -> None:
        fixture = BacktestFixture(
            session_date=date(2026, 7, 30),
            anchor_strike=_ANCHOR,
            reference_inputs=_reference_inputs(),
            dataset=OptionChainDataset(session_date=date(2026, 7, 30), candles=(_entry_candle(),)),
        )

        result = BacktestRunner().run(fixture, TrendDirection.BULLISH)

        assert len(result.qualification_positions) == 1
        assert result.qualification_positions[0].exit_reason == ExitReason.SESSION_END

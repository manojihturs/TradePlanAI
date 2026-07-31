"""Tests for backtest.synthetic_data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from itertools import pairwise

from backtest.synthetic_data import build_synthetic_fixture


def _find_strike(candle, strike: Decimal):  # type: ignore[no-untyped-def]
    return next(pair for pair in candle.strikes if pair.strike == strike)


def _touches(snapshot, level: Decimal) -> bool:  # type: ignore[no-untyped-def]
    return snapshot.low <= level <= snapshot.high


class TestDefaultFixture:
    def test_default_session_date_and_anchor(self) -> None:
        fixture = build_synthetic_fixture()

        assert fixture.session_date == date(2026, 7, 30)
        assert fixture.anchor_strike == Decimal(24000)

    def test_ladder_has_13_strikes_50_apart(self) -> None:
        fixture = build_synthetic_fixture()

        strikes = sorted({row.strike for row in fixture.reference_inputs})
        assert len(strikes) == 13
        assert strikes[0] == Decimal(23700)
        assert strikes[-1] == Decimal(24300)
        for earlier, later in pairwise(strikes):
            assert later - earlier == Decimal(50)

    def test_three_candles_in_chronological_order(self) -> None:
        fixture = build_synthetic_fixture()

        assert len(fixture.dataset.candles) == 3
        timestamps = [c.timestamp for c in fixture.dataset.candles]
        assert timestamps == sorted(timestamps)

    def test_winner_candle_touches_anchor_ce_but_not_pe(self) -> None:
        fixture = build_synthetic_fixture()
        winner_candle = fixture.dataset.candles[0]
        anchor_pair = _find_strike(winner_candle, fixture.anchor_strike)

        assert _touches(anchor_pair.ce, Decimal(100))  # ce_high at offset 0
        assert not _touches(anchor_pair.pe, Decimal(100))
        assert not _touches(anchor_pair.pe, Decimal(90))

    def test_filler_candle_touches_nothing_for_anchor(self) -> None:
        fixture = build_synthetic_fixture()
        filler_candle = fixture.dataset.candles[1]
        anchor_pair = _find_strike(filler_candle, fixture.anchor_strike)

        assert not _touches(anchor_pair.ce, Decimal(100))
        assert not _touches(anchor_pair.ce, Decimal(90))
        assert not _touches(anchor_pair.pe, Decimal(100))
        assert not _touches(anchor_pair.pe, Decimal(90))

    def test_exit_candle_touches_target_strike_ce(self) -> None:
        fixture = build_synthetic_fixture()
        exit_candle = fixture.dataset.candles[2]
        target_strike = fixture.anchor_strike + Decimal(50)
        target_pair = _find_strike(exit_candle, target_strike)

        assert _touches(target_pair.ce, Decimal(101))  # ce_high at offset 1

    def test_reference_inputs_share_the_first_candle_timestamp(self) -> None:
        fixture = build_synthetic_fixture()

        timestamps = {row.ce_candle.timestamp for row in fixture.reference_inputs}
        assert timestamps == {row.pe_candle.timestamp for row in fixture.reference_inputs}
        assert len(timestamps) == 1


class TestCustomFixture:
    def test_custom_session_date_and_anchor(self) -> None:
        fixture = build_synthetic_fixture(
            session_date=date(2026, 8, 3), anchor_strike=Decimal(50000)
        )

        assert fixture.session_date == date(2026, 8, 3)
        assert fixture.anchor_strike == Decimal(50000)
        strikes = sorted({row.strike for row in fixture.reference_inputs})
        assert strikes[0] == Decimal(49700)
        assert strikes[-1] == Decimal(50300)

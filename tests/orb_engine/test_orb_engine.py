"""Tests for orb_engine.orb_engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from core.enums import OptionType, ORBStatus
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from orb_engine.orb_engine import ORBEngine

_SESSION_ID = uuid.uuid4()
_TIMESTAMP = datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)

# TC-1, 2026-07-29, verified in WEEKLY_FUTURE_CALCULATION_EXAMPLES.md and
# reused across this codebase's other test suites - real captured data.
_LEVEL = ReferenceLevel(
    strike=Decimal(24200),
    ce_high=Decimal("143.45"),
    ce_low=Decimal(116),
    pe_high=Decimal("165.8"),
    pe_low=Decimal(128),
)


def _candle(minute_offset: int, high: str, low: str, *, tick_only: bool = False) -> MarketSnapshot:
    timestamp = _TIMESTAMP + timedelta(minutes=minute_offset)
    if tick_only:
        return MarketSnapshot(timestamp=timestamp, underlying_price=Decimal(high))
    return MarketSnapshot(
        timestamp=timestamp,
        underlying_price=Decimal(high),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


class TestOpeningHighLowRange:
    def test_call_side_uses_ce_values(self) -> None:
        engine = ORBEngine()

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, (), _TIMESTAMP)

        assert result.opening_high == Decimal("143.45")
        assert result.opening_low == Decimal(116)
        assert result.range == Decimal("143.45") - Decimal(116)
        assert result.strike == Decimal(24200)
        assert result.side == OptionType.CALL

    def test_put_side_uses_pe_values(self) -> None:
        engine = ORBEngine()

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.PUT, (), _TIMESTAMP)

        assert result.opening_high == Decimal("165.8")
        assert result.opening_low == Decimal(128)
        assert result.range == Decimal("165.8") - Decimal(128)


class TestBreakoutBreakdownClassification:
    def test_no_candles_yields_none(self) -> None:
        engine = ORBEngine()

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, (), _TIMESTAMP)

        assert result.status == ORBStatus.NONE

    def test_candles_within_range_yield_none(self) -> None:
        engine = ORBEngine()
        candles = (
            _candle(5, "130", "120"),
            _candle(10, "135", "118"),
        )

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.NONE

    def test_candle_crossing_above_opening_high_is_breakout(self) -> None:
        engine = ORBEngine()
        candles = (
            _candle(5, "130", "120"),
            _candle(10, "150", "140"),  # crosses opening_high=143.45
        )

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKOUT

    def test_candle_crossing_below_opening_low_is_breakdown(self) -> None:
        engine = ORBEngine()
        candles = (
            _candle(5, "130", "120"),
            _candle(10, "119", "110"),  # crosses opening_low=116
        )

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKDOWN

    def test_first_crossing_wins_breakdown_then_breakout(self) -> None:
        engine = ORBEngine()
        candles = (
            _candle(5, "119", "110"),  # breakdown first
            _candle(10, "150", "140"),  # breakout second - should not matter
        )

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKDOWN

    def test_first_crossing_wins_breakout_then_breakdown(self) -> None:
        engine = ORBEngine()
        candles = (
            _candle(5, "150", "140"),  # breakout first
            _candle(10, "100", "90"),  # breakdown second - should not matter
        )

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKOUT

    def test_single_candle_crossing_both_boundaries_prefers_breakout(self) -> None:
        engine = ORBEngine()
        candles = (_candle(5, "150", "100"),)  # spans both opening_high and opening_low

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKOUT

    def test_tick_only_candle_uses_underlying_price_for_both_bounds(self) -> None:
        engine = ORBEngine()
        candles = (_candle(5, "150", "150", tick_only=True),)

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKOUT

    def test_exact_boundary_touch_counts_as_breakout(self) -> None:
        engine = ORBEngine()
        candles = (_candle(5, "143.45", "130"),)  # high exactly equals opening_high

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKOUT

    def test_exact_boundary_touch_counts_as_breakdown(self) -> None:
        engine = ORBEngine()
        candles = (_candle(5, "130", "116"),)  # low exactly equals opening_low

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKDOWN


class TestRealisticMultiCandleSession:
    """A full 09:15-15:30 style 5-minute candle sequence, exercising the
    engine the way a real replay would feed it - candle by candle."""

    def test_realistic_session_classifies_breakout_correctly(self) -> None:
        engine = ORBEngine()
        # A plausible intraday drift: stays inside the opening range for a
        # while, then breaks out late morning.
        candles = tuple(
            _candle(offset, high, low)
            for offset, high, low in [
                (5, "125", "118"),
                (10, "130", "120"),
                (15, "128", "119"),
                (20, "132", "121"),
                (60, "138", "125"),
                (120, "148", "135"),  # crosses opening_high=143.45 here
                (180, "160", "145"),
            ]
        )

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, candles, _TIMESTAMP)

        assert result.status == ORBStatus.BREAKOUT

    def test_identifiers_and_calculated_at_are_recorded(self) -> None:
        engine = ORBEngine()

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, (), _TIMESTAMP)

        assert result.session_id == _SESSION_ID
        assert result.calculated_at == _TIMESTAMP
        assert isinstance(result.orb_result_id, uuid.UUID)


class TestIdFactoryInjection:
    def test_injected_id_factory_is_used(self) -> None:
        fixed_id = uuid.uuid4()
        engine = ORBEngine(id_factory=lambda: fixed_id)

        result = engine.calculate(_SESSION_ID, _LEVEL, OptionType.CALL, (), _TIMESTAMP)

        assert result.orb_result_id == fixed_id

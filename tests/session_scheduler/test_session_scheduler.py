"""Tests for session_scheduler.session_scheduler."""

from __future__ import annotations

from datetime import UTC, datetime, time

import pytest

from core.exceptions import ValidationError
from session_scheduler.session_scheduler import (
    DEFAULT_MARKET_CLOSE,
    DEFAULT_MARKET_OPEN,
    SessionScheduler,
)

_THURSDAY = datetime(2026, 7, 30, 10, 0, tzinfo=UTC)  # confirmed weekday, matches earlier session
_SATURDAY = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
_SUNDAY = datetime(2026, 8, 2, 10, 0, tzinfo=UTC)


class TestConstruction:
    def test_defaults_match_nse_hours(self) -> None:
        scheduler = SessionScheduler()

        assert scheduler.market_open == time(9, 15)
        assert scheduler.market_close == time(15, 30)
        assert DEFAULT_MARKET_OPEN == time(9, 15)
        assert DEFAULT_MARKET_CLOSE == time(15, 30)

    def test_close_before_open_raises(self) -> None:
        with pytest.raises(ValidationError, match="market_close must be after market_open"):
            SessionScheduler(market_open=time(15, 30), market_close=time(9, 15))

    def test_close_equal_to_open_raises(self) -> None:
        with pytest.raises(ValidationError, match="market_close must be after market_open"):
            SessionScheduler(market_open=time(9, 15), market_close=time(9, 15))


class TestIsTradingDay:
    def test_weekday_is_a_trading_day(self) -> None:
        assert SessionScheduler().is_trading_day(_THURSDAY) is True

    def test_saturday_is_not_a_trading_day(self) -> None:
        assert SessionScheduler().is_trading_day(_SATURDAY) is False

    def test_sunday_is_not_a_trading_day(self) -> None:
        assert SessionScheduler().is_trading_day(_SUNDAY) is False


class TestIsWithinSessionHours:
    def test_market_open_boundary_is_within(self) -> None:
        scheduler = SessionScheduler()
        moment = datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)

        assert scheduler.is_within_session_hours(moment) is True

    def test_just_before_open_is_not_within(self) -> None:
        scheduler = SessionScheduler()
        moment = datetime(2026, 7, 30, 9, 14, 59, tzinfo=UTC)

        assert scheduler.is_within_session_hours(moment) is False

    def test_market_close_boundary_is_not_within(self) -> None:
        scheduler = SessionScheduler()
        moment = datetime(2026, 7, 30, 15, 30, 0, tzinfo=UTC)

        assert scheduler.is_within_session_hours(moment) is False

    def test_just_before_close_is_within(self) -> None:
        scheduler = SessionScheduler()
        moment = datetime(2026, 7, 30, 15, 29, 59, tzinfo=UTC)

        assert scheduler.is_within_session_hours(moment) is True

    def test_midday_is_within(self) -> None:
        assert SessionScheduler().is_within_session_hours(_THURSDAY) is True


class TestIsSessionOpen:
    def test_weekday_during_hours_is_open(self) -> None:
        assert SessionScheduler().is_session_open(_THURSDAY) is True

    def test_weekend_during_hours_is_not_open(self) -> None:
        assert SessionScheduler().is_session_open(_SATURDAY) is False

    def test_weekday_outside_hours_is_not_open(self) -> None:
        moment = datetime(2026, 7, 30, 20, 0, tzinfo=UTC)

        assert SessionScheduler().is_session_open(moment) is False

    def test_custom_hours_are_respected(self) -> None:
        scheduler = SessionScheduler(market_open=time(10, 0), market_close=time(11, 0))
        moment = datetime(2026, 7, 30, 9, 30, tzinfo=UTC)

        assert scheduler.is_session_open(moment) is False

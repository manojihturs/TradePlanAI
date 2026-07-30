"""Tests for strike_selector.strike_selector.

Every non-edge test case is drawn directly from
``research/specifications/WEEKLY_FUTURE_TEST_CASES.md``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from models.weekly_future import WeeklyFuture
from strike_selector.strike_selector import StrikeSelector


@pytest.fixture
def session_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def selected_at() -> datetime:
    return datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


def _weekly_future(
    session_id: uuid.UUID, high: str, low: str, calculated_at: datetime
) -> WeeklyFuture:
    return WeeklyFuture(
        weekly_future_id=uuid.uuid4(),
        session_id=session_id,
        high=Decimal(high),
        low=Decimal(low),
        calculated_at=calculated_at,
    )


class TestVerifiedWorkedExamples:
    @pytest.mark.parametrize(
        "high,low,expected_top,expected_bottom",
        [
            ("24215.45", "24150.2", "24200", "24150"),  # TC-1
            ("24110.25", "24044.3", "24100", "24050"),  # TC-2
            ("23985.7", "23924.9", "24000", "23900"),  # TC-3
        ],
    )
    def test_matches_verified_example(
        self,
        session_id: uuid.UUID,
        selected_at: datetime,
        high: str,
        low: str,
        expected_top: str,
        expected_bottom: str,
    ) -> None:
        selector = StrikeSelector()
        weekly_future = _weekly_future(session_id, high, low, selected_at)

        result = selector.select(session_id, weekly_future, selected_at)

        assert result.top_strike == Decimal(expected_top)
        assert result.bottom_strike == Decimal(expected_bottom)
        assert result.session_id == session_id
        assert result.selected_at == selected_at


class TestRoundingBoundaries:
    def test_rounds_down_when_closer_to_lower_multiple(
        self, session_id: uuid.UUID, selected_at: datetime
    ) -> None:
        selector = StrikeSelector()
        weekly_future = _weekly_future(session_id, "24224", "24000", selected_at)

        result = selector.select(session_id, weekly_future, selected_at)

        assert result.top_strike == Decimal(24200)

    def test_rounds_up_when_closer_to_upper_multiple(
        self, session_id: uuid.UUID, selected_at: datetime
    ) -> None:
        selector = StrikeSelector()
        weekly_future = _weekly_future(session_id, "24226", "24000", selected_at)

        result = selector.select(session_id, weekly_future, selected_at)

        assert result.top_strike == Decimal(24250)

    def test_exact_midpoint_rounds_half_up(
        self, session_id: uuid.UUID, selected_at: datetime
    ) -> None:
        # UNRESOLVED - Awaiting Strategy Evidence: no worked example
        # demonstrates this tie-break. Documents the engineering
        # default (ROUND_HALF_UP), not a confirmed business rule.
        selector = StrikeSelector()
        weekly_future = _weekly_future(session_id, "24225", "24000", selected_at)

        result = selector.select(session_id, weekly_future, selected_at)

        assert result.top_strike == Decimal(24250)

    def test_already_a_multiple_of_50_is_unchanged(
        self, session_id: uuid.UUID, selected_at: datetime
    ) -> None:
        selector = StrikeSelector()
        weekly_future = _weekly_future(session_id, "24200", "24000", selected_at)

        result = selector.select(session_id, weekly_future, selected_at)

        assert result.top_strike == Decimal(24200)

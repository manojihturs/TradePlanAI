"""Tests for weekly_future.weekly_future_calculator.

Every non-edge test case is drawn directly from
``research/specifications/WEEKLY_FUTURE_TEST_CASES.md``, itself
derived from Product Owner-supplied worked examples verified 2026-07-30.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel
from weekly_future.weekly_future_calculator import WeeklyFutureCalculator


def _level(strike: str, ce_high: str, ce_low: str, pe_high: str, pe_low: str) -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(strike),
        ce_high=Decimal(ce_high),
        ce_low=Decimal(ce_low),
        pe_high=Decimal(pe_high),
        pe_low=Decimal(pe_low),
    )


@pytest.fixture
def session_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def calculated_at() -> datetime:
    return datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


class TestVerifiedWorkedExamples:
    @pytest.mark.parametrize(
        "strike,ce_high,ce_low,pe_high,pe_low,expected_high,expected_low",
        [
            # TC-1, 2026-07-29
            ("24200", "143.45", "116", "165.8", "128", "24215.45", "24150.2"),
            # TC-2, 2026-07-28
            ("24000", "218", "180.95", "136.65", "107.75", "24110.25", "24044.3"),
            # TC-3, 2026-07-27
            ("23950", "212.75", "176.2", "201.3", "177.05", "23985.7", "23924.9"),
        ],
    )
    def test_matches_verified_example(
        self,
        session_id: uuid.UUID,
        calculated_at: datetime,
        strike: str,
        ce_high: str,
        ce_low: str,
        pe_high: str,
        pe_low: str,
        expected_high: str,
        expected_low: str,
    ) -> None:
        calculator = WeeklyFutureCalculator(id_factory=lambda: uuid.UUID(int=1))
        level = _level(strike, ce_high, ce_low, pe_high, pe_low)

        result = calculator.calculate(session_id, level, calculated_at)

        assert result.high == Decimal(expected_high)
        assert result.low == Decimal(expected_low)
        assert result.session_id == session_id
        assert result.calculated_at == calculated_at
        assert result.weekly_future_id == uuid.UUID(int=1)


class TestSignFlipCase:
    def test_negative_intermediate_difference_handled_without_special_case(
        self, session_id: uuid.UUID, calculated_at: datetime
    ) -> None:
        # TC-2 Low: PE High (136.65) < CE Low (180.95) - the exact
        # case that made TR-001.md's narration self-contradictory.
        calculator = WeeklyFutureCalculator()
        level = _level("24000", "218", "180.95", "136.65", "107.75")

        result = calculator.calculate(session_id, level, calculated_at)

        assert result.low == Decimal("24044.3")


class TestDefaultIdFactory:
    def test_default_id_factory_produces_a_uuid(
        self, session_id: uuid.UUID, calculated_at: datetime
    ) -> None:
        calculator = WeeklyFutureCalculator()
        level = _level("24200", "143.45", "116", "165.8", "128")

        result = calculator.calculate(session_id, level, calculated_at)

        assert isinstance(result.weekly_future_id, uuid.UUID)


class TestStructuralEdgeCases:
    def test_ce_high_equals_pe_low_yields_high_equal_to_strike(
        self, session_id: uuid.UUID, calculated_at: datetime
    ) -> None:
        calculator = WeeklyFutureCalculator()
        level = _level("24000", "150", "116", "165.8", "150")

        result = calculator.calculate(session_id, level, calculated_at)

        assert result.high == Decimal(24000)

    def test_pe_high_equals_ce_low_yields_low_equal_to_strike(
        self, session_id: uuid.UUID, calculated_at: datetime
    ) -> None:
        calculator = WeeklyFutureCalculator()
        level = _level("24000", "218", "150", "150", "107.75")

        result = calculator.calculate(session_id, level, calculated_at)

        assert result.low == Decimal(24000)

    def test_invalid_reference_level_raises(self) -> None:
        with pytest.raises(ValidationError, match="ce_high"):
            _level("24000", "100", "150", "165.8", "128")

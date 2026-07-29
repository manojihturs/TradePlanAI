"""Tests for reference_builder.reference_builder."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from reference_builder.reference_builder import ReferenceBuilder
from reference_builder.reference_repository import ReferenceRepository
from reference_builder.reference_validator import EXPECTED_LADDER_SIZE, StrikeCandleInput


def _candle(low: str, high: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
        underlying_price=Decimal(24000),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


def _tick() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC), underlying_price=Decimal(24000)
    )


def _valid_inputs(count: int = EXPECTED_LADDER_SIZE) -> tuple[StrikeCandleInput, ...]:
    base = 23700
    return tuple(
        StrikeCandleInput(
            strike=Decimal(base + i * 50),
            ce_candle=_candle(str(90 + i), str(110 + i)),
            pe_candle=_candle(str(80 + i), str(100 + i)),
        )
        for i in range(count)
    )


class TestBuild:
    def test_builds_correct_number_of_levels(self) -> None:
        builder = ReferenceBuilder()
        levels = builder.build(uuid.uuid4(), _valid_inputs())

        assert len(levels) == EXPECTED_LADDER_SIZE

    def test_ce_pe_high_low_copied_directly_from_first_candle(self) -> None:
        builder = ReferenceBuilder()
        other_inputs = tuple(
            StrikeCandleInput(
                strike=Decimal(20000 + i * 50),
                ce_candle=_candle("1", "2"),
                pe_candle=_candle("1", "2"),
            )
            for i in range(EXPECTED_LADDER_SIZE - 1)
        )
        inputs = (
            StrikeCandleInput(
                strike=Decimal(24000),
                ce_candle=_candle("90", "110"),
                pe_candle=_candle("85", "105"),
            ),
        ) + other_inputs

        levels = builder.build(uuid.uuid4(), inputs)

        matching = next(level for level in levels if level.strike == Decimal(24000))
        assert matching.ce_high == Decimal(110)
        assert matching.ce_low == Decimal(90)
        assert matching.pe_high == Decimal(105)
        assert matching.pe_low == Decimal(85)

    def test_strike_order_preserved(self) -> None:
        builder = ReferenceBuilder()
        inputs = _valid_inputs()

        levels = builder.build(uuid.uuid4(), inputs)

        assert [level.strike for level in levels] == [item.strike for item in inputs]

    def test_invalid_input_count_raises(self) -> None:
        builder = ReferenceBuilder()
        with pytest.raises(ValidationError, match="Expected exactly 13 strikes"):
            builder.build(uuid.uuid4(), _valid_inputs(count=5))

    def test_non_candle_snapshot_raises(self) -> None:
        builder = ReferenceBuilder()
        inputs = list(_valid_inputs())
        inputs[0] = StrikeCandleInput(
            strike=inputs[0].strike, ce_candle=_tick(), pe_candle=_candle("1", "2")
        )

        with pytest.raises(ValidationError, match="is not candle-mode"):
            builder.build(uuid.uuid4(), tuple(inputs))

    def test_non_standard_spacing_builds_successfully(self) -> None:
        builder = ReferenceBuilder()
        strikes = [
            23700,
            23760,
            23800,
            23900,
            23950,
            24000,
            24050,
            24100,
            24200,
            24300,
            24310,
            24400,
            24500,
        ]
        inputs = tuple(
            StrikeCandleInput(
                strike=Decimal(s), ce_candle=_candle("90", "110"), pe_candle=_candle("85", "105")
            )
            for s in strikes
        )

        levels = builder.build(uuid.uuid4(), inputs)

        assert [level.strike for level in levels] == [Decimal(s) for s in strikes]


class TestRepositoryIntegration:
    def test_built_ladder_saved_when_repository_injected(self) -> None:
        repository = ReferenceRepository()
        builder = ReferenceBuilder(repository=repository)
        session_id = uuid.uuid4()

        levels = builder.build(session_id, _valid_inputs())

        assert repository.get(session_id) == levels

    def test_no_repository_injected_does_not_raise(self) -> None:
        builder = ReferenceBuilder(repository=None)
        levels = builder.build(uuid.uuid4(), _valid_inputs())

        assert len(levels) == EXPECTED_LADDER_SIZE


class TestDependencyInjection:
    def test_custom_validator_is_used(self) -> None:
        from reference_builder.reference_validator import ReferenceValidator

        calls: list[str] = []

        class TrackingValidator(ReferenceValidator):
            def validate_inputs(self, inputs: tuple[StrikeCandleInput, ...]) -> None:
                calls.append("validate_inputs")
                super().validate_inputs(inputs)

            def validate_levels(self, levels: tuple) -> None:  # type: ignore[type-arg]
                calls.append("validate_levels")
                super().validate_levels(levels)

        builder = ReferenceBuilder(validator=TrackingValidator())
        builder.build(uuid.uuid4(), _valid_inputs())

        assert calls == ["validate_inputs", "validate_levels"]

"""Tests for TrendPoint."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.trend_point import TrendPoint


def _make(
    valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime, **overrides: object
) -> TrendPoint:
    defaults: dict[str, object] = {
        "trend_point_id": valid_uuid,
        "strike_id": another_uuid,
        "value": Decimal("150.01"),
        "marked_at": valid_datetime,
    }
    defaults.update(overrides)
    return TrendPoint(**defaults)  # type: ignore[arg-type]


class TestConstructorValidation:
    def test_valid_construction_succeeds(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        tp = _make(valid_uuid, another_uuid, valid_datetime)
        assert tp.value == Decimal("150.01")
        assert tp.marked_at == valid_datetime

    def test_zero_value_is_valid(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        # Explicit per docstring: "cannot be negative" - zero is allowed.
        tp = _make(valid_uuid, another_uuid, valid_datetime, value=Decimal(0))
        assert tp.value == Decimal(0)


class TestInvalidConstructorValues:
    def test_none_trend_point_id_raises(
        self, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DomainValidationError, match="trend_point_id must not be None"):
            TrendPoint(None, another_uuid, Decimal(1), valid_datetime)  # type: ignore[arg-type]

    def test_none_strike_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DomainValidationError, match="strike_id must not be None"):
            TrendPoint(valid_uuid, None, Decimal(1), valid_datetime)  # type: ignore[arg-type]

    def test_negative_value_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        # Explicit example from the milestone: TrendPoint(value=-1)
        with pytest.raises(DomainValidationError, match="value cannot be negative"):
            _make(valid_uuid, another_uuid, valid_datetime, value=Decimal(-1))


class TestEquality:
    def test_equal_values_are_equal(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        assert _make(valid_uuid, another_uuid, valid_datetime) == _make(
            valid_uuid, another_uuid, valid_datetime
        )

    def test_different_value_not_equal(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        a = _make(valid_uuid, another_uuid, valid_datetime, value=Decimal(100))
        b = _make(valid_uuid, another_uuid, valid_datetime, value=Decimal(200))
        assert a != b


class TestImmutability:
    def test_cannot_reassign_value(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        tp = _make(valid_uuid, another_uuid, valid_datetime)
        with pytest.raises(dataclasses.FrozenInstanceError):
            tp.value = Decimal(999)  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        hash(_make(valid_uuid, another_uuid, valid_datetime))


class TestCopyUpdateMethods:
    """The explicit with_updated_value() immutable-update mechanic."""

    def test_with_updated_value_returns_new_instance(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        original = _make(valid_uuid, another_uuid, valid_datetime, value=Decimal(150))
        new_time = datetime(2026, 7, 3, 9, 45, 0)  # noqa: DTZ001
        updated = original.with_updated_value(Decimal(135), new_time)

        assert updated is not original
        assert isinstance(updated, TrendPoint)

    def test_with_updated_value_sets_new_value_and_time(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        original = _make(valid_uuid, another_uuid, valid_datetime, value=Decimal(150))
        new_time = datetime(2026, 7, 3, 9, 45, 0)  # noqa: DTZ001
        updated = original.with_updated_value(Decimal(135), new_time)

        assert updated.value == Decimal(135)
        assert updated.marked_at == new_time

    def test_with_updated_value_preserves_identity_and_strike_linkage(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        original = _make(valid_uuid, another_uuid, valid_datetime)
        updated = original.with_updated_value(Decimal(135), valid_datetime)

        assert updated.trend_point_id == original.trend_point_id
        assert updated.strike_id == original.strike_id

    def test_with_updated_value_does_not_mutate_original(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        original = _make(valid_uuid, another_uuid, valid_datetime, value=Decimal(150))
        original.with_updated_value(Decimal(135), valid_datetime)

        # Original must remain completely unchanged.
        assert original.value == Decimal(150)
        assert original.marked_at == valid_datetime

    def test_with_updated_value_still_validates(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        original = _make(valid_uuid, another_uuid, valid_datetime)
        with pytest.raises(DomainValidationError, match="value cannot be negative"):
            original.with_updated_value(Decimal(-5), valid_datetime)


class TestSerialization:
    def test_asdict_structure(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        as_dict = dataclasses.asdict(_make(valid_uuid, another_uuid, valid_datetime))
        assert as_dict["value"] == Decimal("150.01")


class TestStringRepresentation:
    def test_repr_contains_value(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        assert "150.01" in repr(_make(valid_uuid, another_uuid, valid_datetime))


class TestEdgeCases:
    def test_repeated_updates_each_produce_independent_instances(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        # Mirrors the documented TR-001 scenario: 150 -> 141 -> 135.
        step0 = _make(valid_uuid, another_uuid, valid_datetime, value=Decimal(150))
        step1 = step0.with_updated_value(Decimal(141), valid_datetime)
        step2 = step1.with_updated_value(Decimal(135), valid_datetime)

        assert step0.value == Decimal(150)
        assert step1.value == Decimal(141)
        assert step2.value == Decimal(135)
        assert len({step0, step1, step2}) == 3

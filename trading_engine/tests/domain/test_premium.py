"""Tests for Premium."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.premium import Premium


class TestConstructorValidation:
    def test_valid_construction_succeeds(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        premium = Premium(valid_uuid, Decimal("126.6"), valid_datetime)
        assert premium.value == Decimal("126.6")
        assert premium.observed_at == valid_datetime


class TestInvalidConstructorValues:
    def test_none_premium_id_raises(self, valid_datetime: datetime) -> None:
        with pytest.raises(DomainValidationError, match="premium_id must not be None"):
            Premium(None, Decimal(1), valid_datetime)  # type: ignore[arg-type]

    def test_zero_value_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DomainValidationError, match="value must be greater than 0"):
            Premium(valid_uuid, Decimal(0), valid_datetime)

    def test_negative_value_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DomainValidationError, match="value must be greater than 0"):
            Premium(valid_uuid, Decimal(-10), valid_datetime)


class TestEquality:
    def test_equal_values_are_equal(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        assert Premium(valid_uuid, Decimal(1), valid_datetime) == Premium(
            valid_uuid, Decimal(1), valid_datetime
        )

    def test_different_value_not_equal(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        assert Premium(valid_uuid, Decimal(1), valid_datetime) != Premium(
            valid_uuid, Decimal(2), valid_datetime
        )


class TestImmutability:
    def test_cannot_reassign_value(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        premium = Premium(valid_uuid, Decimal(1), valid_datetime)
        with pytest.raises(dataclasses.FrozenInstanceError):
            premium.value = Decimal(999)  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        hash(Premium(valid_uuid, Decimal(1), valid_datetime))


class TestCopyUpdate:
    def test_replace_produces_new_instance(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        original = Premium(valid_uuid, Decimal(100), valid_datetime)
        updated = dataclasses.replace(original, value=Decimal(200))
        assert updated is not original
        assert updated.value == Decimal(200)
        assert original.value == Decimal(100)


class TestSerialization:
    def test_asdict_structure(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        as_dict = dataclasses.asdict(Premium(valid_uuid, Decimal("126.6"), valid_datetime))
        assert as_dict["value"] == Decimal("126.6")


class TestStringRepresentation:
    def test_repr_contains_value(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        assert "126.6" in repr(Premium(valid_uuid, Decimal("126.6"), valid_datetime))


class TestEdgeCases:
    def test_very_small_positive_value_accepted(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        premium = Premium(valid_uuid, Decimal("0.05"), valid_datetime)
        assert premium.value == Decimal("0.05")

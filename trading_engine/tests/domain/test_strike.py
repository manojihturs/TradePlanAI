"""Tests for Strike."""

from __future__ import annotations

import dataclasses
import uuid
from decimal import Decimal

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.strike import Strike


class TestConstructorValidation:
    def test_valid_construction_succeeds(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        strike = Strike(valid_uuid, another_uuid, Decimal(24050))
        assert strike.strike_id == valid_uuid
        assert strike.session_id == another_uuid
        assert strike.price == Decimal(24050)

    def test_fractional_price_accepted(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        strike = Strike(valid_uuid, another_uuid, Decimal("24050.50"))
        assert strike.price == Decimal("24050.50")


class TestInvalidConstructorValues:
    def test_none_strike_id_raises(self, another_uuid: uuid.UUID) -> None:
        with pytest.raises(DomainValidationError, match="strike_id must not be None"):
            Strike(None, another_uuid, Decimal(100))  # type: ignore[arg-type]

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID) -> None:
        with pytest.raises(DomainValidationError, match="session_id must not be None"):
            Strike(valid_uuid, None, Decimal(100))  # type: ignore[arg-type]

    def test_zero_price_raises(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        # Explicit example from the milestone: Strike(price=0)
        with pytest.raises(DomainValidationError, match="price must be greater than 0"):
            Strike(valid_uuid, another_uuid, Decimal(0))

    def test_negative_price_raises(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        with pytest.raises(DomainValidationError, match="price must be greater than 0"):
            Strike(valid_uuid, another_uuid, Decimal(-1))


class TestEquality:
    def test_equal_values_are_equal(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        assert Strike(valid_uuid, another_uuid, Decimal(100)) == Strike(
            valid_uuid, another_uuid, Decimal(100)
        )

    def test_different_price_not_equal(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        assert Strike(valid_uuid, another_uuid, Decimal(100)) != Strike(
            valid_uuid, another_uuid, Decimal(200)
        )


class TestImmutability:
    def test_cannot_reassign_price(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        strike = Strike(valid_uuid, another_uuid, Decimal(100))
        with pytest.raises(dataclasses.FrozenInstanceError):
            strike.price = Decimal(999)  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        hash(Strike(valid_uuid, another_uuid, Decimal(100)))

    def test_usable_in_set(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        s = {
            Strike(valid_uuid, another_uuid, Decimal(100)),
            Strike(valid_uuid, another_uuid, Decimal(100)),
        }
        assert len(s) == 1


class TestCopyUpdate:
    def test_replace_produces_new_instance(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        original = Strike(valid_uuid, another_uuid, Decimal(100))
        updated = dataclasses.replace(original, price=Decimal(200))
        assert updated is not original
        assert updated.price == Decimal(200)
        assert original.price == Decimal(100)

    def test_replace_with_invalid_price_still_validates(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        # __post_init__ runs on the new instance too - replace() cannot
        # be used to bypass structural validation.
        original = Strike(valid_uuid, another_uuid, Decimal(100))
        with pytest.raises(DomainValidationError):
            dataclasses.replace(original, price=Decimal(0))


class TestSerialization:
    def test_asdict_structure(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        as_dict = dataclasses.asdict(Strike(valid_uuid, another_uuid, Decimal(24050)))
        assert as_dict["price"] == Decimal(24050)


class TestStringRepresentation:
    def test_repr_contains_price(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        assert "24050" in repr(Strike(valid_uuid, another_uuid, Decimal(24050)))


class TestEdgeCases:
    def test_very_small_positive_price_accepted(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        strike = Strike(valid_uuid, another_uuid, Decimal("0.01"))
        assert strike.price == Decimal("0.01")

    def test_very_large_price_accepted(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        strike = Strike(valid_uuid, another_uuid, Decimal(999999999))
        assert strike.price == Decimal(999999999)

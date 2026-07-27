"""Tests for Opponent."""

from __future__ import annotations

import dataclasses
import uuid
from decimal import Decimal

import pytest

from trading_engine.domain.opponent import Opponent


class TestConstructorValidation:
    def test_valid_construction_with_only_required_fields(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        opp = Opponent(valid_uuid, another_uuid)
        assert opp.opponent_id == valid_uuid
        assert opp.strike_id == another_uuid

    def test_optional_fields_default_to_none(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        opp = Opponent(valid_uuid, another_uuid)
        assert opp.own_trend_point_id is None
        assert opp.high is None
        assert opp.low is None

    def test_optional_fields_can_be_supplied(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        tp_id = uuid.uuid4()
        opp = Opponent(
            valid_uuid, another_uuid, own_trend_point_id=tp_id, high=Decimal(150), low=Decimal(100)
        )
        assert opp.own_trend_point_id == tp_id
        assert opp.high == Decimal(150)
        assert opp.low == Decimal(100)


class TestInvalidConstructorValues:
    def test_none_opponent_id_raises(self, another_uuid: uuid.UUID) -> None:
        from trading_engine.domain import DomainValidationError

        with pytest.raises(DomainValidationError, match="opponent_id must not be None"):
            Opponent(None, another_uuid)  # type: ignore[arg-type]

    def test_none_strike_id_raises(self, valid_uuid: uuid.UUID) -> None:
        from trading_engine.domain import DomainValidationError

        with pytest.raises(DomainValidationError, match="strike_id must not be None"):
            Opponent(valid_uuid, None)  # type: ignore[arg-type]

    def test_high_less_than_low_does_not_raise(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        # Deliberate: no cross-field invariant is enforced. Per
        # docs/architecture/DOMAIN_ARCHITECTURE.md, OPPONENT-002/003
        # have zero recorded behaviour, so this module must not guess
        # at a High >= Low relationship. This test documents that
        # non-enforcement, it does not assert a defect.
        opp = Opponent(valid_uuid, another_uuid, high=Decimal(10), low=Decimal(500))
        assert opp.high == Decimal(10)
        assert opp.low == Decimal(500)


class TestEquality:
    def test_equal_values_are_equal(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        assert Opponent(valid_uuid, another_uuid) == Opponent(valid_uuid, another_uuid)

    def test_different_high_not_equal(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        a = Opponent(valid_uuid, another_uuid, high=Decimal(1))
        b = Opponent(valid_uuid, another_uuid, high=Decimal(2))
        assert a != b

    def test_none_high_not_equal_to_populated_high(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        assert Opponent(valid_uuid, another_uuid, high=None) != Opponent(
            valid_uuid, another_uuid, high=Decimal(1)
        )


class TestImmutability:
    def test_cannot_reassign_high(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        opp = Opponent(valid_uuid, another_uuid)
        with pytest.raises(dataclasses.FrozenInstanceError):
            opp.high = Decimal(100)  # type: ignore[misc]


class TestHashability:
    def test_is_hashable_with_defaults(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        hash(Opponent(valid_uuid, another_uuid))

    def test_is_hashable_with_all_fields_populated(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        hash(Opponent(valid_uuid, another_uuid, uuid.uuid4(), Decimal(1), Decimal(2)))


class TestCopyUpdate:
    def test_replace_produces_new_instance(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        original = Opponent(valid_uuid, another_uuid)
        updated = dataclasses.replace(original, high=Decimal(150))
        assert updated is not original
        assert updated.high == Decimal(150)
        assert original.high is None


class TestSerialization:
    def test_asdict_structure(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        as_dict = dataclasses.asdict(Opponent(valid_uuid, another_uuid, high=Decimal(1)))
        assert as_dict["high"] == Decimal(1)
        assert as_dict["low"] is None


class TestStringRepresentation:
    def test_repr_contains_class_name(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        assert "Opponent" in repr(Opponent(valid_uuid, another_uuid))


class TestEdgeCases:
    def test_high_equal_to_low_is_permitted(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        opp = Opponent(valid_uuid, another_uuid, high=Decimal(100), low=Decimal(100))
        assert opp.high == opp.low

    def test_negative_high_low_not_rejected(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        # No validation is defined for high/low at all (Awaiting
        # Evidence) - this documents that current behaviour explicitly.
        opp = Opponent(valid_uuid, another_uuid, high=Decimal(-5), low=Decimal(-10))
        assert opp.high == Decimal(-5)

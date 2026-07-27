"""Tests for MarketSession."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import date

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.market_session import MarketSession


class TestConstructorValidation:
    def test_valid_construction_succeeds(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        session = MarketSession(valid_uuid, valid_date)
        assert session.session_id == valid_uuid
        assert session.session_date == valid_date


class TestInvalidConstructorValues:
    def test_none_session_id_raises(self, valid_date: date) -> None:
        with pytest.raises(DomainValidationError, match="session_id must not be None"):
            MarketSession(None, valid_date)  # type: ignore[arg-type]


class TestEquality:
    def test_equal_values_are_equal(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        assert MarketSession(valid_uuid, valid_date) == MarketSession(valid_uuid, valid_date)

    def test_different_session_id_not_equal(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_date: date
    ) -> None:
        assert MarketSession(valid_uuid, valid_date) != MarketSession(another_uuid, valid_date)

    def test_different_date_not_equal(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        other_date = date(2026, 7, 4)
        assert MarketSession(valid_uuid, valid_date) != MarketSession(valid_uuid, other_date)


class TestImmutability:
    def test_cannot_reassign_field(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        session = MarketSession(valid_uuid, valid_date)
        with pytest.raises(dataclasses.FrozenInstanceError):
            session.session_date = date(2026, 7, 4)  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        hash(MarketSession(valid_uuid, valid_date))

    def test_usable_in_set(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        s = {MarketSession(valid_uuid, valid_date), MarketSession(valid_uuid, valid_date)}
        assert len(s) == 1


class TestCopyUpdate:
    def test_replace_produces_new_instance(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        original = MarketSession(valid_uuid, valid_date)
        new_date = date(2026, 7, 4)
        updated = dataclasses.replace(original, session_date=new_date)
        assert updated is not original
        assert updated.session_date == new_date
        assert original.session_date == valid_date


class TestSerialization:
    def test_asdict_structure(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        as_dict = dataclasses.asdict(MarketSession(valid_uuid, valid_date))
        assert as_dict["session_id"] == valid_uuid
        assert as_dict["session_date"] == valid_date


class TestStringRepresentation:
    def test_repr_contains_class_name(self, valid_uuid: uuid.UUID, valid_date: date) -> None:
        assert "MarketSession" in repr(MarketSession(valid_uuid, valid_date))


class TestEdgeCases:
    def test_distinct_sessions_for_same_date_are_distinct_by_id(self, valid_date: date) -> None:
        session_a = MarketSession(uuid.uuid4(), valid_date)
        session_b = MarketSession(uuid.uuid4(), valid_date)
        assert session_a != session_b

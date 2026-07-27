"""Tests for DomainEvent."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.domain_event import DomainEvent


class TestConstructorValidation:
    def test_valid_construction_succeeds(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = DomainEvent(valid_uuid, valid_datetime, "some event occurred")
        assert event.event_id == valid_uuid
        assert event.occurred_at == valid_datetime
        assert event.description == "some event occurred"


class TestInvalidConstructorValues:
    def test_none_event_id_raises(self, valid_datetime: datetime) -> None:
        with pytest.raises(DomainValidationError, match="event_id must not be None"):
            DomainEvent(None, valid_datetime, "desc")  # type: ignore[arg-type]

    def test_blank_description_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DomainValidationError, match="description must not be blank"):
            DomainEvent(valid_uuid, valid_datetime, "")

    def test_whitespace_only_description_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DomainValidationError, match="description must not be blank"):
            DomainEvent(valid_uuid, valid_datetime, "   ")


class TestEquality:
    def test_equal_values_are_equal(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        assert DomainEvent(valid_uuid, valid_datetime, "x") == DomainEvent(
            valid_uuid, valid_datetime, "x"
        )

    def test_different_description_not_equal(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        assert DomainEvent(valid_uuid, valid_datetime, "x") != DomainEvent(
            valid_uuid, valid_datetime, "y"
        )


class TestImmutability:
    def test_cannot_reassign_description(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = DomainEvent(valid_uuid, valid_datetime, "x")
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.description = "changed"  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        hash(DomainEvent(valid_uuid, valid_datetime, "x"))


class TestCopyUpdate:
    def test_replace_produces_new_instance(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        original = DomainEvent(valid_uuid, valid_datetime, "original")
        updated = dataclasses.replace(original, description="updated")
        assert updated is not original
        assert updated.description == "updated"
        assert original.description == "original"


class TestSerialization:
    def test_asdict_structure(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        as_dict = dataclasses.asdict(DomainEvent(valid_uuid, valid_datetime, "x"))
        assert as_dict["description"] == "x"


class TestStringRepresentation:
    def test_repr_contains_description(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        assert "some event" in repr(DomainEvent(valid_uuid, valid_datetime, "some event"))


class TestEdgeCases:
    def test_no_concrete_subclass_exists(self) -> None:
        # Deliberate per module docstring: no specific event type is
        # evidenced yet, so DomainEvent is directly instantiable and
        # has no subclasses defined in this milestone.
        assert DomainEvent.__subclasses__() == []

    def test_is_directly_instantiable(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = DomainEvent(valid_uuid, valid_datetime, "generic occurrence")
        assert type(event) is DomainEvent

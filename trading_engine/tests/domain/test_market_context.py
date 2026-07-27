"""Tests for MarketContext."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.premium import Premium
from trading_engine.domain.strike import Strike


@pytest.fixture
def sample_strike(valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> Strike:
    return Strike(valid_uuid, another_uuid, Decimal(24050))


@pytest.fixture
def sample_premium(valid_uuid: uuid.UUID, valid_datetime: datetime) -> Premium:
    return Premium(valid_uuid, Decimal("126.6"), valid_datetime)


class TestConstructorValidation:
    def test_valid_construction_with_no_strikes_or_premiums(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        ctx = MarketContext(valid_uuid, another_uuid, valid_datetime)
        assert ctx.strikes == ()
        assert ctx.premiums == ()

    def test_valid_construction_with_strikes_and_premiums(
        self,
        valid_uuid: uuid.UUID,
        another_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_strike: Strike,
        sample_premium: Premium,
    ) -> None:
        ctx = MarketContext(
            valid_uuid, another_uuid, valid_datetime, (sample_strike,), (sample_premium,)
        )
        assert ctx.strikes == (sample_strike,)
        assert ctx.premiums == (sample_premium,)

    def test_default_collections_are_empty_tuples_not_shared_mutable_state(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        ctx1 = MarketContext(valid_uuid, another_uuid, valid_datetime)
        ctx2 = MarketContext(valid_uuid, another_uuid, valid_datetime)
        assert ctx1.strikes is not None
        assert ctx1.strikes == ctx2.strikes


class TestInvalidConstructorValues:
    def test_none_context_id_raises(
        self, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DomainValidationError, match="context_id must not be None"):
            MarketContext(None, another_uuid, valid_datetime)  # type: ignore[arg-type]

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DomainValidationError, match="session_id must not be None"):
            MarketContext(valid_uuid, None, valid_datetime)  # type: ignore[arg-type]


class TestEquality:
    def test_equal_values_are_equal(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        assert MarketContext(valid_uuid, another_uuid, valid_datetime) == MarketContext(
            valid_uuid, another_uuid, valid_datetime
        )

    def test_different_strikes_not_equal(
        self,
        valid_uuid: uuid.UUID,
        another_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_strike: Strike,
    ) -> None:
        empty = MarketContext(valid_uuid, another_uuid, valid_datetime)
        populated = MarketContext(valid_uuid, another_uuid, valid_datetime, (sample_strike,))
        assert empty != populated


class TestImmutability:
    def test_cannot_reassign_strikes(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        ctx = MarketContext(valid_uuid, another_uuid, valid_datetime)
        with pytest.raises(dataclasses.FrozenInstanceError):
            ctx.strikes = ()  # type: ignore[misc]

    def test_strikes_tuple_itself_is_immutable_collection_type(
        self,
        valid_uuid: uuid.UUID,
        another_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_strike: Strike,
    ) -> None:
        ctx = MarketContext(valid_uuid, another_uuid, valid_datetime, (sample_strike,))
        assert isinstance(ctx.strikes, tuple)


class TestHashability:
    def test_is_hashable_when_empty(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        hash(MarketContext(valid_uuid, another_uuid, valid_datetime))

    def test_is_hashable_when_populated(
        self,
        valid_uuid: uuid.UUID,
        another_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_strike: Strike,
        sample_premium: Premium,
    ) -> None:
        hash(
            MarketContext(
                valid_uuid, another_uuid, valid_datetime, (sample_strike,), (sample_premium,)
            )
        )


class TestCopyUpdate:
    def test_replace_produces_new_instance(
        self,
        valid_uuid: uuid.UUID,
        another_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_strike: Strike,
    ) -> None:
        original = MarketContext(valid_uuid, another_uuid, valid_datetime)
        updated = dataclasses.replace(original, strikes=(sample_strike,))
        assert updated is not original
        assert updated.strikes == (sample_strike,)
        assert original.strikes == ()


class TestSerialization:
    def test_asdict_structure(
        self,
        valid_uuid: uuid.UUID,
        another_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_strike: Strike,
    ) -> None:
        as_dict = dataclasses.asdict(
            MarketContext(valid_uuid, another_uuid, valid_datetime, (sample_strike,))
        )
        assert len(as_dict["strikes"]) == 1


class TestStringRepresentation:
    def test_repr_contains_class_name(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        assert "MarketContext" in repr(MarketContext(valid_uuid, another_uuid, valid_datetime))


class TestEdgeCases:
    def test_multiple_strikes_preserved_in_order(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        strike_a = Strike(uuid.uuid4(), another_uuid, Decimal(100))
        strike_b = Strike(uuid.uuid4(), another_uuid, Decimal(200))
        ctx = MarketContext(valid_uuid, another_uuid, valid_datetime, (strike_a, strike_b))
        assert ctx.strikes == (strike_a, strike_b)

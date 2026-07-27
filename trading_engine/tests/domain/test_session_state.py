"""Tests for SessionState, SessionStateType."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.session_state import SessionState, SessionStateType
from trading_engine.domain.trend_point import TrendPoint


@pytest.fixture
def sample_trend_point(
    valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
) -> TrendPoint:
    return TrendPoint(valid_uuid, another_uuid, Decimal(150), valid_datetime)


class TestConstructorValidation:
    def test_valid_construction_with_defaults(self, valid_uuid: uuid.UUID) -> None:
        state = SessionState(valid_uuid)
        assert state.current_state is SessionStateType.NONE
        assert state.trend_points == ()

    def test_valid_construction_with_explicit_values(
        self, valid_uuid: uuid.UUID, sample_trend_point: TrendPoint
    ) -> None:
        state = SessionState(valid_uuid, SessionStateType.STRIKE_SELECTED, (sample_trend_point,))
        assert state.current_state is SessionStateType.STRIKE_SELECTED
        assert state.trend_points == (sample_trend_point,)


class TestInvalidConstructorValues:
    def test_none_session_id_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="session_id must not be None"):
            SessionState(None)  # type: ignore[arg-type]


class TestEquality:
    def test_equal_values_are_equal(self, valid_uuid: uuid.UUID) -> None:
        assert SessionState(valid_uuid) == SessionState(valid_uuid)

    def test_different_state_not_equal(self, valid_uuid: uuid.UUID) -> None:
        a = SessionState(valid_uuid, SessionStateType.STRIKE_SELECTED)
        b = SessionState(valid_uuid, SessionStateType.TREND_TRACKING)
        assert a != b


class TestImmutability:
    def test_cannot_reassign_current_state(self, valid_uuid: uuid.UUID) -> None:
        state = SessionState(valid_uuid)
        with pytest.raises(dataclasses.FrozenInstanceError):
            state.current_state = SessionStateType.REVERSAL_IDENTIFIED  # type: ignore[misc]


class TestHashability:
    def test_is_hashable_when_default(self, valid_uuid: uuid.UUID) -> None:
        hash(SessionState(valid_uuid))

    def test_is_hashable_with_trend_points(
        self, valid_uuid: uuid.UUID, sample_trend_point: TrendPoint
    ) -> None:
        hash(SessionState(valid_uuid, trend_points=(sample_trend_point,)))


class TestCopyUpdateMethods:
    """The explicit with_state() immutable-update mechanic."""

    def test_with_state_returns_new_instance(self, valid_uuid: uuid.UUID) -> None:
        original = SessionState(valid_uuid)
        updated = original.with_state(SessionStateType.STRIKE_SELECTED)
        assert updated is not original
        assert isinstance(updated, SessionState)

    def test_with_state_sets_new_state(self, valid_uuid: uuid.UUID) -> None:
        original = SessionState(valid_uuid)
        updated = original.with_state(SessionStateType.OPPONENT_ENGAGEMENT)
        assert updated.current_state is SessionStateType.OPPONENT_ENGAGEMENT

    def test_with_state_preserves_session_id_and_trend_points(
        self, valid_uuid: uuid.UUID, sample_trend_point: TrendPoint
    ) -> None:
        original = SessionState(valid_uuid, trend_points=(sample_trend_point,))
        updated = original.with_state(SessionStateType.TREND_TRACKING)
        assert updated.session_id == original.session_id
        assert updated.trend_points == original.trend_points

    def test_with_state_does_not_mutate_original(self, valid_uuid: uuid.UUID) -> None:
        original = SessionState(valid_uuid, SessionStateType.NONE)
        original.with_state(SessionStateType.REVERSAL_IDENTIFIED)
        assert original.current_state is SessionStateType.NONE

    def test_no_transition_validation_is_performed(self, valid_uuid: uuid.UUID) -> None:
        # Deliberate: docs/STATE_MACHINE.md leaves 4 of 5 transitions
        # UNKNOWN. This module must not invent transition rules, so
        # even a "backwards" or otherwise implausible transition must
        # succeed structurally.
        original = SessionState(valid_uuid, SessionStateType.REVERSAL_IDENTIFIED)
        updated = original.with_state(SessionStateType.STRIKE_SELECTED)
        assert updated.current_state is SessionStateType.STRIKE_SELECTED


class TestEnumBehaviour:
    def test_session_state_type_members_match_state_machine_doc(self) -> None:
        expected = {
            "NONE",
            "STRIKE_SELECTED",
            "TREND_TRACKING",
            "OPPONENT_ENGAGEMENT",
            "OPPONENT_DEFEATED",
            "REVERSAL_IDENTIFIED",
        }
        assert {member.name for member in SessionStateType} == expected

    def test_none_is_distinct_from_the_five_evidenced_states(self) -> None:
        assert SessionStateType.NONE not in {
            SessionStateType.STRIKE_SELECTED,
            SessionStateType.TREND_TRACKING,
            SessionStateType.OPPONENT_ENGAGEMENT,
            SessionStateType.OPPONENT_DEFEATED,
            SessionStateType.REVERSAL_IDENTIFIED,
        }

    def test_invalid_enum_value_raises(self) -> None:
        with pytest.raises(ValueError):
            SessionStateType("NOT_A_STATE")


class TestSerialization:
    def test_asdict_structure(self, valid_uuid: uuid.UUID) -> None:
        as_dict = dataclasses.asdict(SessionState(valid_uuid, SessionStateType.STRIKE_SELECTED))
        assert as_dict["current_state"] is SessionStateType.STRIKE_SELECTED


class TestStringRepresentation:
    def test_repr_contains_current_state(self, valid_uuid: uuid.UUID) -> None:
        assert "STRIKE_SELECTED" in repr(SessionState(valid_uuid, SessionStateType.STRIKE_SELECTED))


class TestEdgeCases:
    def test_default_state_is_none_not_strike_selected(self, valid_uuid: uuid.UUID) -> None:
        # Structural default, not one of the five evidenced states.
        assert SessionState(valid_uuid).current_state is SessionStateType.NONE

    def test_chained_with_state_calls_produce_independent_snapshots(
        self, valid_uuid: uuid.UUID
    ) -> None:
        s0 = SessionState(valid_uuid)
        s1 = s0.with_state(SessionStateType.STRIKE_SELECTED)
        s2 = s1.with_state(SessionStateType.TREND_TRACKING)
        assert s0.current_state is SessionStateType.NONE
        assert s1.current_state is SessionStateType.STRIKE_SELECTED
        assert s2.current_state is SessionStateType.TREND_TRACKING

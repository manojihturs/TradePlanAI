"""Tests for reference_builder.reference_repository."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from models.reference_level import ReferenceLevel
from reference_builder.reference_repository import ReferenceRepository


def _level(strike: int) -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(strike),
        ce_high=Decimal(110),
        ce_low=Decimal(90),
        pe_high=Decimal(105),
        pe_low=Decimal(85),
    )


@pytest.fixture
def repository() -> ReferenceRepository:
    return ReferenceRepository()


class TestSaveAndGet:
    def test_get_returns_saved_ladder(self, repository: ReferenceRepository) -> None:
        session_id = uuid.uuid4()
        ladder = (_level(24000), _level(24050))

        repository.save(session_id, ladder)

        assert repository.get(session_id) == ladder

    def test_get_unknown_session_returns_none(self, repository: ReferenceRepository) -> None:
        assert repository.get(uuid.uuid4()) is None

    def test_save_overwrites_previous_ladder(self, repository: ReferenceRepository) -> None:
        session_id = uuid.uuid4()
        repository.save(session_id, (_level(24000),))
        repository.save(session_id, (_level(24050),))

        assert repository.get(session_id) == (_level(24050),)

    def test_different_sessions_independent(self, repository: ReferenceRepository) -> None:
        first = uuid.uuid4()
        second = uuid.uuid4()
        repository.save(first, (_level(24000),))

        assert repository.get(first) == (_level(24000),)
        assert repository.get(second) is None


class TestClear:
    def test_clear_removes_every_ladder(self, repository: ReferenceRepository) -> None:
        session_id = uuid.uuid4()
        repository.save(session_id, (_level(24000),))

        repository.clear()

        assert repository.get(session_id) is None


class TestNoGlobalState:
    def test_two_repositories_are_independent(self) -> None:
        repo_one = ReferenceRepository()
        repo_two = ReferenceRepository()
        session_id = uuid.uuid4()

        repo_one.save(session_id, (_level(24000),))

        assert repo_one.get(session_id) is not None
        assert repo_two.get(session_id) is None

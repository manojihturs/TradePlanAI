"""Tests for business.execution_context."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from business.execution_context import ExecutionContext, ExecutionMode, default_id_factory
from core.exceptions import ValidationError


def _fixed_clock() -> datetime:
    return datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


class TestDefaults:
    def test_defaults_produce_tz_aware_clock(self) -> None:
        context = ExecutionContext(mode=ExecutionMode.LIVE)

        assert context.clock().tzinfo is not None

    def test_default_id_factory_produces_uuid(self) -> None:
        assert isinstance(default_id_factory(), uuid.UUID)

    def test_default_id_factory_is_the_context_default(self) -> None:
        context = ExecutionContext(mode=ExecutionMode.LIVE)

        assert isinstance(context.id_factory(), uuid.UUID)

    def test_event_bus_defaults_to_none(self) -> None:
        context = ExecutionContext(mode=ExecutionMode.LIVE)

        assert context.event_bus is None


class TestInjection:
    def test_injected_clock_is_used(self) -> None:
        context = ExecutionContext(mode=ExecutionMode.REPLAY, clock=_fixed_clock)

        assert context.clock() == _fixed_clock()

    def test_injected_id_factory_is_used(self) -> None:
        fixed_id = uuid.uuid4()
        context = ExecutionContext(mode=ExecutionMode.LIVE, id_factory=lambda: fixed_id)

        assert context.id_factory() == fixed_id

    def test_live_and_replay_are_distinct(self) -> None:
        assert ExecutionMode.LIVE is not ExecutionMode.REPLAY


class TestValidation:
    def test_none_mode_raises(self) -> None:
        with pytest.raises(ValidationError, match="mode must not be None"):
            ExecutionContext(mode=None)  # type: ignore[arg-type]

    def test_none_clock_raises(self) -> None:
        with pytest.raises(ValidationError, match="clock must not be None"):
            ExecutionContext(mode=ExecutionMode.LIVE, clock=None)  # type: ignore[arg-type]

    def test_none_id_factory_raises(self) -> None:
        with pytest.raises(ValidationError, match="id_factory must not be None"):
            ExecutionContext(mode=ExecutionMode.LIVE, id_factory=None)  # type: ignore[arg-type]

"""Tests for business.pipeline_context."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from business.pipeline_context import PipelineContext
from core.enums import EventPriority, TradeDirection
from core.events import WinnerDetectedEvent
from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel
from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture


def _ts() -> datetime:
    return datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


def _context() -> PipelineContext:
    return PipelineContext(session_id=uuid.uuid4(), candle_timestamp=_ts())


class TestConstruction:
    def test_valid_construction(self) -> None:
        context = _context()

        assert context.reference_data == ()
        assert context.weekly_future is None
        assert context.selected_strike is None
        assert context.tp_state is None
        assert context.qualification_state is None
        assert context.winner is None
        assert context.diagnostics == ()

    def test_none_session_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="session_id must not be None"):
            PipelineContext(session_id=None, candle_timestamp=_ts())  # type: ignore[arg-type]

    def test_none_candle_timestamp_raises(self) -> None:
        with pytest.raises(ValidationError, match="candle_timestamp must not be None"):
            PipelineContext(session_id=uuid.uuid4(), candle_timestamp=None)  # type: ignore[arg-type]


class TestWithMethods:
    def test_with_diagnostic_appends_and_does_not_mutate(self) -> None:
        original = _context()

        updated = original.with_diagnostic("stage started")

        assert original.diagnostics == ()
        assert updated.diagnostics == ("stage started",)

    def test_with_diagnostic_accumulates(self) -> None:
        context = _context().with_diagnostic("one").with_diagnostic("two")

        assert context.diagnostics == ("one", "two")

    def test_with_reference_data(self) -> None:
        level = ReferenceLevel(
            strike=Decimal(24000),
            ce_high=Decimal(110),
            ce_low=Decimal(90),
            pe_high=Decimal(105),
            pe_low=Decimal(85),
        )

        context = _context().with_reference_data((level,))

        assert context.reference_data == (level,)

    def test_with_weekly_future(self) -> None:
        weekly_future = WeeklyFuture(
            weekly_future_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            high=Decimal(26200),
            low=Decimal(26100),
            calculated_at=_ts(),
        )

        context = _context().with_weekly_future(weekly_future)

        assert context.weekly_future is weekly_future

    def test_with_selected_strike(self) -> None:
        selection = StrikeSelection(
            session_id=uuid.uuid4(),
            top_strike=Decimal(24100),
            bottom_strike=Decimal(23900),
            selected_at=_ts(),
        )

        context = _context().with_selected_strike(selection)

        assert context.selected_strike is selection

    def test_with_tp_state(self) -> None:
        context = _context().with_tp_state({"qualified": True})

        assert context.tp_state == {"qualified": True}

    def test_with_qualification_state(self) -> None:
        context = _context().with_qualification_state(True)

        assert context.qualification_state is True

    def test_with_winner(self) -> None:
        winner = WinnerDetectedEvent(
            event_id=uuid.uuid4(),
            occurred_at=_ts(),
            session_id=uuid.uuid4(),
            candle_timestamp=_ts(),
            winning_side=TradeDirection.CE,
            winning_strike=Decimal(24100),
            priority=EventPriority.HIGH,
        )

        context = _context().with_winner(winner)

        assert context.winner is winner

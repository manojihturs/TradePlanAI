"""Tests for application.replay_view."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from application.replay_configuration import ReplayConfiguration
from application.replay_result import ReplayResult
from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
from application.replay_view import (
    MISSING_VALUE_PLACEHOLDER,
    VIEW_COLUMNS,
    ReplayViewRow,
    build_view_rows,
    render_view_table,
)
from business.business_result import BusinessResult
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError
from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture

_SESSION_ID = uuid.uuid4()
_TIMESTAMP = datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC)


def _context(*, with_outputs: bool) -> PipelineContext:
    context = PipelineContext(session_id=_SESSION_ID, candle_timestamp=_TIMESTAMP)
    if not with_outputs:
        return context
    weekly_future = WeeklyFuture(
        weekly_future_id=uuid.uuid4(),
        session_id=_SESSION_ID,
        high=Decimal("24215.45"),
        low=Decimal("24150.2"),
        calculated_at=_TIMESTAMP,
    )
    selected_strike = StrikeSelection(
        session_id=_SESSION_ID,
        top_strike=Decimal(24200),
        bottom_strike=Decimal(24150),
        selected_at=_TIMESTAMP,
    )
    return (
        context.with_reference_strike(Decimal(24200))
        .with_weekly_future(weekly_future)
        .with_selected_strike(selected_strike)
    )


def _business_result(*, success: bool, with_outputs: bool) -> BusinessResult:
    return BusinessResult(success=success, context=_context(with_outputs=with_outputs))


def _replay_result(business_results: tuple[BusinessResult, ...]) -> ReplayResult:
    session = ReplaySession(
        session_id=_SESSION_ID,
        dataset_id="ds-1",
        started_at=_TIMESTAMP,
        status=ReplayStatus.COMPLETED,
        ended_at=_TIMESTAMP,
        statistics=ReplayStatistics(
            candles_processed=len(business_results),
            events_recorded=0,
            business_runs_succeeded=sum(1 for r in business_results if r.success),
            business_runs_failed=sum(1 for r in business_results if not r.success),
        ),
    )
    return ReplayResult(
        session=session,
        configuration=ReplayConfiguration(start_date=date(2026, 7, 29), end_date=date(2026, 7, 29)),
        generated_at=_TIMESTAMP,
        business_results=business_results,
    )


class TestBuildViewRows:
    def test_row_formatted_when_outputs_present(self) -> None:
        result = _replay_result((_business_result(success=True, with_outputs=True),))

        rows = build_view_rows(result)

        assert len(rows) == 1
        row = rows[0]
        assert row.candle == "2026-07-29T09:20:00+00:00"
        assert row.reference_strike == "24200"
        assert row.weekly_future_high == "24215.45"
        assert row.weekly_future_low == "24150.2"
        assert row.top_strike == "24200"
        assert row.bottom_strike == "24150"

    def test_row_uses_placeholder_when_stage_never_ran(self) -> None:
        result = _replay_result((_business_result(success=False, with_outputs=False),))

        rows = build_view_rows(result)

        row = rows[0]
        assert row.reference_strike == MISSING_VALUE_PLACEHOLDER
        assert row.weekly_future_high == MISSING_VALUE_PLACEHOLDER
        assert row.weekly_future_low == MISSING_VALUE_PLACEHOLDER
        assert row.top_strike == MISSING_VALUE_PLACEHOLDER
        assert row.bottom_strike == MISSING_VALUE_PLACEHOLDER

    def test_one_row_per_business_result_in_order(self) -> None:
        results = tuple(_business_result(success=True, with_outputs=True) for _ in range(3))
        result = _replay_result(results)

        rows = build_view_rows(result)

        assert len(rows) == 3

    def test_empty_business_results_yields_empty_rows(self) -> None:
        result = _replay_result(())

        rows = build_view_rows(result)

        assert rows == ()


class TestReplayViewRowValidation:
    def test_rejects_blank_candle(self) -> None:
        with pytest.raises(ValidationError, match="candle must not be blank"):
            ReplayViewRow(
                candle="",
                reference_strike=MISSING_VALUE_PLACEHOLDER,
                weekly_future_high=MISSING_VALUE_PLACEHOLDER,
                weekly_future_low=MISSING_VALUE_PLACEHOLDER,
                top_strike=MISSING_VALUE_PLACEHOLDER,
                bottom_strike=MISSING_VALUE_PLACEHOLDER,
            )

    def test_as_columns_matches_view_columns_order(self) -> None:
        row = ReplayViewRow(
            candle="2026-07-29T09:20:00+00:00",
            reference_strike="24200",
            weekly_future_high="24215.45",
            weekly_future_low="24150.2",
            top_strike="24200",
            bottom_strike="24150",
        )

        assert row.as_columns() == (
            "2026-07-29T09:20:00+00:00",
            "24200",
            "24215.45",
            "24150.2",
            "24200",
            "24150",
        )
        assert len(row.as_columns()) == len(VIEW_COLUMNS)


class TestRenderViewTable:
    def test_renders_header_and_rows(self) -> None:
        result = _replay_result(
            (
                _business_result(success=True, with_outputs=True),
                _business_result(success=False, with_outputs=False),
            )
        )
        rows = build_view_rows(result)

        table = render_view_table(rows)
        lines = table.splitlines()

        assert lines[0].startswith("Candle")
        assert "Reference Strike" in lines[0]
        assert "24200" in lines[1]
        assert MISSING_VALUE_PLACEHOLDER in lines[2]
        assert len(lines) == 3

    def test_renders_header_only_for_empty_rows(self) -> None:
        table = render_view_table(())

        lines = table.splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("Candle")

    def test_columns_are_aligned_to_widest_value(self) -> None:
        rows = (
            ReplayViewRow(
                candle="2026-07-29T09:20:00+00:00",
                reference_strike="24200",
                weekly_future_high="24215.45",
                weekly_future_low="24150.2",
                top_strike="24200",
                bottom_strike="24150",
            ),
        )

        table = render_view_table(rows)
        lines = table.splitlines()

        assert lines[0].startswith("Candle".ljust(len("2026-07-29T09:20:00+00:00")))

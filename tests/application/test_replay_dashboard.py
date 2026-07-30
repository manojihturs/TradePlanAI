"""Tests for application.replay_dashboard."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from application.replay_configuration import ReplayConfiguration
from application.replay_dashboard import (
    CSV_HEADER,
    ReplayDashboardRow,
    ReplayDashboardSummary,
    build_dashboard_rows,
    build_dashboard_summary,
    write_dashboard_csv,
)
from application.replay_result import ReplayResult
from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
from business.business_errors import StageExecutionError
from business.business_result import BusinessResult
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError
from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture

_SESSION_ID = uuid.uuid4()
_DAY_1_T1 = datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC)
_DAY_1_T2 = datetime(2026, 7, 29, 9, 25, 0, tzinfo=UTC)
_DAY_2_T1 = datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


def _context(timestamp: datetime, *, with_outputs: bool) -> PipelineContext:
    context = PipelineContext(session_id=_SESSION_ID, candle_timestamp=timestamp)
    if not with_outputs:
        return context
    weekly_future = WeeklyFuture(
        weekly_future_id=uuid.uuid4(),
        session_id=_SESSION_ID,
        high=Decimal("24215.45"),
        low=Decimal("24150.2"),
        calculated_at=timestamp,
    )
    selected_strike = StrikeSelection(
        session_id=_SESSION_ID,
        top_strike=Decimal(24200),
        bottom_strike=Decimal(24150),
        selected_at=timestamp,
    )
    return (
        context.with_reference_strike(Decimal(24200))
        .with_weekly_future(weekly_future)
        .with_selected_strike(selected_strike)
    )


def _replay_result(business_results: tuple[BusinessResult, ...]) -> ReplayResult:
    session = ReplaySession(
        session_id=_SESSION_ID,
        dataset_id="ds-1",
        started_at=_DAY_1_T1,
        status=ReplayStatus.COMPLETED,
        ended_at=_DAY_2_T1,
        statistics=ReplayStatistics(
            candles_processed=len(business_results),
            events_recorded=0,
            business_runs_succeeded=sum(1 for r in business_results if r.success),
            business_runs_failed=sum(1 for r in business_results if not r.success),
        ),
    )
    return ReplayResult(
        session=session,
        configuration=ReplayConfiguration(start_date=date(2026, 7, 29), end_date=date(2026, 7, 30)),
        generated_at=_DAY_2_T1,
        business_results=business_results,
    )


class TestBuildDashboardRows:
    def test_groups_by_calendar_day(self) -> None:
        results = (
            BusinessResult(success=True, context=_context(_DAY_1_T1, with_outputs=True)),
            BusinessResult(success=True, context=_context(_DAY_1_T2, with_outputs=True)),
            BusinessResult(success=True, context=_context(_DAY_2_T1, with_outputs=True)),
        )
        result = _replay_result(results)

        rows = build_dashboard_rows(result)

        assert len(rows) == 2
        assert rows[0].trading_day == date(2026, 7, 29)
        assert rows[1].trading_day == date(2026, 7, 30)

    def test_row_reports_first_seen_day_values(self) -> None:
        results = (BusinessResult(success=True, context=_context(_DAY_1_T1, with_outputs=True)),)
        result = _replay_result(results)

        rows = build_dashboard_rows(result)

        row = rows[0]
        assert row.reference_strike == Decimal(24200)
        assert row.weekly_future_high == Decimal("24215.45")
        assert row.weekly_future_low == Decimal("24150.2")
        assert row.top_strike == Decimal(24200)
        assert row.bottom_strike == Decimal(24150)

    def test_row_none_when_stage_never_ran(self) -> None:
        results = (BusinessResult(success=True, context=_context(_DAY_1_T1, with_outputs=False)),)
        result = _replay_result(results)

        rows = build_dashboard_rows(result)

        row = rows[0]
        assert row.reference_strike is None
        assert row.weekly_future_high is None
        assert row.top_strike is None

    def test_execution_time_is_candle_span_within_day(self) -> None:
        results = (
            BusinessResult(success=True, context=_context(_DAY_1_T1, with_outputs=True)),
            BusinessResult(success=True, context=_context(_DAY_1_T2, with_outputs=True)),
        )
        result = _replay_result(results)

        rows = build_dashboard_rows(result)

        assert rows[0].execution_time == timedelta(minutes=5)

    def test_status_passed_when_all_candles_succeed(self) -> None:
        results = (BusinessResult(success=True, context=_context(_DAY_1_T1, with_outputs=True)),)
        result = _replay_result(results)

        rows = build_dashboard_rows(result)

        assert rows[0].status == "PASSED"
        assert rows[0].errors == ()

    def test_status_failed_with_error_text_when_any_candle_fails(self) -> None:
        error = StageExecutionError("boom")
        results = (
            BusinessResult(success=True, context=_context(_DAY_1_T1, with_outputs=True)),
            BusinessResult(
                success=False, context=_context(_DAY_1_T2, with_outputs=False), error=error
            ),
        )
        result = _replay_result(results)

        rows = build_dashboard_rows(result)

        assert rows[0].status == "FAILED"
        assert len(rows[0].errors) == 1
        assert "boom" in rows[0].errors[0]

    def test_status_failed_records_unresolved_when_error_is_none(self) -> None:
        results = (BusinessResult(success=False, context=_context(_DAY_1_T1, with_outputs=False)),)
        result = _replay_result(results)

        rows = build_dashboard_rows(result)

        assert rows[0].errors == ("UNRESOLVED",)

    def test_empty_business_results_yields_empty_rows(self) -> None:
        result = _replay_result(())

        rows = build_dashboard_rows(result)

        assert rows == ()


class TestReplayDashboardRowValidation:
    def test_rejects_none_trading_day(self) -> None:
        with pytest.raises(ValidationError, match="trading_day must not be None"):
            ReplayDashboardRow(
                trading_day=None,  # type: ignore[arg-type]
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
                execution_time=timedelta(),
                status="PASSED",
            )

    def test_rejects_invalid_status(self) -> None:
        with pytest.raises(ValidationError, match="status must be"):
            ReplayDashboardRow(
                trading_day=date(2026, 7, 29),
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
                execution_time=timedelta(),
                status="BOGUS",
            )

    def test_rejects_negative_execution_time(self) -> None:
        with pytest.raises(ValidationError, match="execution_time must not be negative"):
            ReplayDashboardRow(
                trading_day=date(2026, 7, 29),
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
                execution_time=timedelta(seconds=-1),
                status="PASSED",
            )


class TestBuildDashboardSummary:
    def test_summary_counts_and_timings(self) -> None:
        rows = (
            ReplayDashboardRow(
                trading_day=date(2026, 7, 29),
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
                execution_time=timedelta(minutes=5),
                status="PASSED",
            ),
            ReplayDashboardRow(
                trading_day=date(2026, 7, 30),
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
                execution_time=timedelta(minutes=15),
                status="FAILED",
                errors=("boom",),
            ),
        )

        summary = build_dashboard_summary(rows)

        assert summary.days_processed == 2
        assert summary.days_passed == 1
        assert summary.days_failed == 1
        assert summary.average_execution_time == timedelta(minutes=10)
        assert summary.fastest_execution_time == timedelta(minutes=5)
        assert summary.slowest_execution_time == timedelta(minutes=15)

    def test_summary_of_empty_rows(self) -> None:
        summary = build_dashboard_summary(())

        assert summary.days_processed == 0
        assert summary.days_passed == 0
        assert summary.days_failed == 0
        assert summary.average_execution_time is None
        assert summary.fastest_execution_time is None
        assert summary.slowest_execution_time is None


class TestReplayDashboardSummaryValidation:
    def test_rejects_negative_days_processed(self) -> None:
        with pytest.raises(ValidationError, match="must not be negative"):
            ReplayDashboardSummary(
                days_processed=-1,
                days_passed=0,
                days_failed=0,
                average_execution_time=None,
                fastest_execution_time=None,
                slowest_execution_time=None,
            )

    def test_rejects_mismatched_totals(self) -> None:
        with pytest.raises(ValidationError, match="days_passed \\+ days_failed"):
            ReplayDashboardSummary(
                days_processed=5,
                days_passed=1,
                days_failed=1,
                average_execution_time=None,
                fastest_execution_time=None,
                slowest_execution_time=None,
            )


class TestWriteDashboardCsv:
    def test_writes_header_and_rows(self, tmp_path: Path) -> None:
        results = (BusinessResult(success=True, context=_context(_DAY_1_T1, with_outputs=True)),)
        result = _replay_result(results)
        rows = build_dashboard_rows(result)
        csv_path = tmp_path / "dashboard.csv"

        write_dashboard_csv(rows, csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(CSV_HEADER)
        assert lines[1] == "2026-07-29,24200,24215.45,24150.2,24200,24150,0.0,PASSED,"

    def test_joins_multiple_errors_with_semicolon(self, tmp_path: Path) -> None:
        results = (
            BusinessResult(success=False, context=_context(_DAY_1_T1, with_outputs=False)),
            BusinessResult(success=False, context=_context(_DAY_1_T2, with_outputs=False)),
        )
        result = _replay_result(results)
        rows = build_dashboard_rows(result)
        csv_path = tmp_path / "dashboard.csv"

        write_dashboard_csv(rows, csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert "UNRESOLVED; UNRESOLVED" in lines[1]

    def test_writes_empty_rows_as_header_only(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "empty.csv"

        write_dashboard_csv((), csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines == [",".join(CSV_HEADER)]

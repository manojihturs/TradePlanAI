"""Tests for application.replay_report."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from application.replay_configuration import ReplayConfiguration
from application.replay_report import (
    CSV_HEADER,
    ReplayReportRow,
    build_report_rows,
    write_report_csv,
)
from application.replay_result import ReplayResult
from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
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
    return context.with_weekly_future(weekly_future).with_selected_strike(selected_strike)


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


class TestBuildReportRows:
    def test_row_populated_when_outputs_present(self) -> None:
        result = _replay_result((_business_result(success=True, with_outputs=True),))

        rows = build_report_rows(result)

        assert len(rows) == 1
        row = rows[0]
        assert row.candle_timestamp == _TIMESTAMP
        assert row.success is True
        assert row.weekly_future_high == Decimal("24215.45")
        assert row.weekly_future_low == Decimal("24150.2")
        assert row.top_strike == Decimal(24200)
        assert row.bottom_strike == Decimal(24150)

    def test_row_has_none_fields_when_stage_never_ran(self) -> None:
        result = _replay_result((_business_result(success=False, with_outputs=False),))

        rows = build_report_rows(result)

        row = rows[0]
        assert row.success is False
        assert row.weekly_future_high is None
        assert row.weekly_future_low is None
        assert row.top_strike is None
        assert row.bottom_strike is None

    def test_one_row_per_business_result_in_order(self) -> None:
        results = tuple(_business_result(success=True, with_outputs=True) for _ in range(3))
        result = _replay_result(results)

        rows = build_report_rows(result)

        assert len(rows) == 3

    def test_empty_business_results_yields_empty_rows(self) -> None:
        result = _replay_result(())

        rows = build_report_rows(result)

        assert rows == ()


class TestReplayReportRowValidation:
    def test_rejects_none_candle_timestamp(self) -> None:
        with pytest.raises(ValidationError, match="candle_timestamp"):
            ReplayReportRow(
                candle_timestamp=None,  # type: ignore[arg-type]
                success=True,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
            )


class TestWriteReportCsv:
    def test_writes_header_and_rows(self, tmp_path: Path) -> None:
        result = _replay_result(
            (
                _business_result(success=True, with_outputs=True),
                _business_result(success=False, with_outputs=False),
            )
        )
        rows = build_report_rows(result)
        csv_path = tmp_path / "report.csv"

        write_report_csv(rows, csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(CSV_HEADER)
        assert lines[1] == "2026-07-29T09:20:00+00:00,True,24215.45,24150.2,24200,24150"
        assert lines[2] == "2026-07-29T09:20:00+00:00,False,,,,"

    def test_writes_empty_rows_as_header_only(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "empty.csv"

        write_report_csv((), csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines == [",".join(CSV_HEADER)]

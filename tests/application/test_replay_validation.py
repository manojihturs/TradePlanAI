"""Tests for application.replay_validation."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from application.replay_configuration import ReplayConfiguration
from application.replay_result import ReplayResult
from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
from application.replay_validation import (
    ReplayValidationFailure,
    ReplayValidationSummary,
    build_validation_summary,
    render_validation_log,
)
from business.business_errors import StageExecutionError
from business.business_result import BusinessResult
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError
from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture

_SESSION_ID = uuid.uuid4()
_STARTED_AT = datetime(2026, 7, 29, 9, 15, 0, tzinfo=UTC)
_TIMESTAMP_1 = datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC)
_TIMESTAMP_2 = datetime(2026, 7, 29, 9, 25, 0, tzinfo=UTC)
_ENDED_AT = datetime(2026, 7, 29, 9, 30, 0, tzinfo=UTC)


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
        started_at=_STARTED_AT,
        status=ReplayStatus.COMPLETED,
        ended_at=_ENDED_AT,
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
        generated_at=_ENDED_AT,
        business_results=business_results,
    )


class TestBuildValidationSummary:
    def test_summary_reports_first_seen_session_values(self) -> None:
        results = (
            BusinessResult(success=True, context=_context(_TIMESTAMP_1, with_outputs=True)),
            BusinessResult(success=True, context=_context(_TIMESTAMP_2, with_outputs=True)),
        )
        result = _replay_result(results)

        summary = build_validation_summary(result)

        assert summary.dataset_id == "ds-1"
        assert summary.candles_processed == 2
        assert summary.succeeded_count == 2
        assert summary.failed_count == 0
        assert summary.execution_time == timedelta(minutes=15)
        assert summary.reference_strike == Decimal(24200)
        assert summary.weekly_future_high == Decimal("24215.45")
        assert summary.weekly_future_low == Decimal("24150.2")
        assert summary.top_strike == Decimal(24200)
        assert summary.bottom_strike == Decimal(24150)
        assert summary.failures == ()

    def test_summary_none_when_stage_never_ran(self) -> None:
        results = (
            BusinessResult(success=True, context=_context(_TIMESTAMP_1, with_outputs=False)),
        )
        result = _replay_result(results)

        summary = build_validation_summary(result)

        assert summary.reference_strike is None
        assert summary.weekly_future_high is None
        assert summary.weekly_future_low is None
        assert summary.top_strike is None
        assert summary.bottom_strike is None

    def test_records_failure_with_error_text(self) -> None:
        error = StageExecutionError("weekly_future stage raised ValidationError: boom")
        results = (
            BusinessResult(
                success=False,
                context=_context(_TIMESTAMP_1, with_outputs=False),
                error=error,
            ),
        )
        result = _replay_result(results)

        summary = build_validation_summary(result)

        assert summary.failed_count == 1
        assert len(summary.failures) == 1
        failure = summary.failures[0]
        assert failure.candle_timestamp == _TIMESTAMP_1
        assert "boom" in failure.error

    def test_records_failure_as_unresolved_when_error_is_none(self) -> None:
        results = (
            BusinessResult(success=False, context=_context(_TIMESTAMP_1, with_outputs=False)),
        )
        result = _replay_result(results)

        summary = build_validation_summary(result)

        assert summary.failures[0].error == "UNRESOLVED"

    def test_multiple_failures_preserve_candle_order(self) -> None:
        results = (
            BusinessResult(success=False, context=_context(_TIMESTAMP_1, with_outputs=False)),
            BusinessResult(success=False, context=_context(_TIMESTAMP_2, with_outputs=False)),
        )
        result = _replay_result(results)

        summary = build_validation_summary(result)

        assert [f.candle_timestamp for f in summary.failures] == [
            _TIMESTAMP_1,
            _TIMESTAMP_2,
        ]

    def test_empty_business_results(self) -> None:
        result = _replay_result(())

        summary = build_validation_summary(result)

        assert summary.candles_processed == 0
        assert summary.succeeded_count == 0
        assert summary.failed_count == 0
        assert summary.failures == ()


class TestReplayValidationSummaryValidation:
    def test_rejects_blank_dataset_id(self) -> None:
        with pytest.raises(ValidationError, match="dataset_id must not be blank"):
            ReplayValidationSummary(
                dataset_id="",
                candles_processed=0,
                succeeded_count=0,
                failed_count=0,
                execution_time=None,
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
            )

    def test_rejects_negative_candles_processed(self) -> None:
        with pytest.raises(ValidationError, match="must not be negative"):
            ReplayValidationSummary(
                dataset_id="ds-1",
                candles_processed=-1,
                succeeded_count=0,
                failed_count=0,
                execution_time=None,
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
            )

    def test_rejects_mismatched_success_failure_totals(self) -> None:
        with pytest.raises(ValidationError, match="succeeded_count \\+ failed_count"):
            ReplayValidationSummary(
                dataset_id="ds-1",
                candles_processed=5,
                succeeded_count=1,
                failed_count=1,
                execution_time=None,
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
            )

    def test_rejects_failures_length_mismatch(self) -> None:
        with pytest.raises(ValidationError, match="failures length must equal failed_count"):
            ReplayValidationSummary(
                dataset_id="ds-1",
                candles_processed=1,
                succeeded_count=0,
                failed_count=1,
                execution_time=None,
                reference_strike=None,
                weekly_future_high=None,
                weekly_future_low=None,
                top_strike=None,
                bottom_strike=None,
                failures=(),
            )


class TestReplayValidationFailureValidation:
    def test_rejects_none_candle_timestamp(self) -> None:
        with pytest.raises(ValidationError, match="candle_timestamp"):
            ReplayValidationFailure(candle_timestamp=None, error="boom")  # type: ignore[arg-type]

    def test_rejects_blank_error(self) -> None:
        with pytest.raises(ValidationError, match="error must not be blank"):
            ReplayValidationFailure(candle_timestamp=_TIMESTAMP_1, error="")


class TestRenderValidationLog:
    def test_renders_fields_and_failures(self) -> None:
        results = (
            BusinessResult(success=True, context=_context(_TIMESTAMP_1, with_outputs=True)),
            BusinessResult(success=False, context=_context(_TIMESTAMP_2, with_outputs=False)),
        )
        result = _replay_result(results)
        summary = build_validation_summary(result)

        log = render_validation_log(summary)

        assert "dataset_id=ds-1" in log
        assert "candles_processed=2" in log
        assert "reference_strike=24200" in log
        assert f"FAILURE candle={_TIMESTAMP_2.isoformat()} error=UNRESOLVED" in log

    def test_renders_none_execution_time(self) -> None:
        summary = ReplayValidationSummary(
            dataset_id="ds-1",
            candles_processed=0,
            succeeded_count=0,
            failed_count=0,
            execution_time=None,
            reference_strike=None,
            weekly_future_high=None,
            weekly_future_low=None,
            top_strike=None,
            bottom_strike=None,
        )

        log = render_validation_log(summary)

        assert "execution_time_seconds=None" in log

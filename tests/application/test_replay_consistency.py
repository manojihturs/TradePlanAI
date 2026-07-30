"""Tests for application.replay_consistency."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from application.replay_configuration import ReplayConfiguration
from application.replay_consistency import (
    CHECK_PIPELINE_COMPLETED,
    CHECK_REFERENCE_LEVEL,
    CHECK_REFERENCE_STRIKE,
    CHECK_STRIKE_SELECTION,
    CHECK_WEEKLY_FUTURE,
    ReplayConsistencyIssue,
    render_consistency_report,
    validate_replay_consistency,
)
from application.replay_result import ReplayResult
from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
from business.business_errors import StageExecutionError
from business.business_result import BusinessResult
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel
from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture

_SESSION_ID = uuid.uuid4()
_TIMESTAMP = datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC)


def _reference_level() -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(24200),
        ce_high=Decimal("143.45"),
        ce_low=Decimal(116),
        pe_high=Decimal("165.8"),
        pe_low=Decimal(128),
    )


def _complete_context() -> PipelineContext:
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
        PipelineContext(
            session_id=_SESSION_ID,
            candle_timestamp=_TIMESTAMP,
            reference_data=(_reference_level(),),
        )
        .with_reference_strike(Decimal(24200))
        .with_weekly_future(weekly_future)
        .with_selected_strike(selected_strike)
    )


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


class TestValidateReplayConsistency:
    def test_fully_consistent_candle_has_no_issues(self) -> None:
        results = (BusinessResult(success=True, context=_complete_context()),)
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        assert issues == ()

    def test_missing_reference_strike_is_reported(self) -> None:
        context = PipelineContext(
            session_id=_SESSION_ID,
            candle_timestamp=_TIMESTAMP,
            reference_data=(_reference_level(),),
        )
        results = (BusinessResult(success=True, context=context),)
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        assert any(issue.check == CHECK_REFERENCE_STRIKE for issue in issues)

    def test_missing_reference_level_is_reported(self) -> None:
        context = PipelineContext(session_id=_SESSION_ID, candle_timestamp=_TIMESTAMP)
        results = (BusinessResult(success=True, context=context),)
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        assert any(issue.check == CHECK_REFERENCE_LEVEL for issue in issues)

    def test_missing_weekly_future_is_reported(self) -> None:
        context = PipelineContext(
            session_id=_SESSION_ID,
            candle_timestamp=_TIMESTAMP,
            reference_data=(_reference_level(),),
        ).with_reference_strike(Decimal(24200))
        results = (BusinessResult(success=True, context=context),)
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        assert any(issue.check == CHECK_WEEKLY_FUTURE for issue in issues)

    def test_missing_strike_selection_is_reported(self) -> None:
        weekly_future = WeeklyFuture(
            weekly_future_id=uuid.uuid4(),
            session_id=_SESSION_ID,
            high=Decimal("24215.45"),
            low=Decimal("24150.2"),
            calculated_at=_TIMESTAMP,
        )
        context = (
            PipelineContext(
                session_id=_SESSION_ID,
                candle_timestamp=_TIMESTAMP,
                reference_data=(_reference_level(),),
            )
            .with_reference_strike(Decimal(24200))
            .with_weekly_future(weekly_future)
        )
        results = (BusinessResult(success=True, context=context),)
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        assert any(issue.check == CHECK_STRIKE_SELECTION for issue in issues)

    def test_pipeline_not_completed_is_reported_with_error_text(self) -> None:
        error = StageExecutionError("boom")
        context = PipelineContext(session_id=_SESSION_ID, candle_timestamp=_TIMESTAMP)
        results = (BusinessResult(success=False, context=context, error=error),)
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        completed_issues = [i for i in issues if i.check == CHECK_PIPELINE_COMPLETED]
        assert len(completed_issues) == 1
        assert "boom" in completed_issues[0].message

    def test_pipeline_not_completed_reports_unresolved_when_error_is_none(self) -> None:
        context = PipelineContext(session_id=_SESSION_ID, candle_timestamp=_TIMESTAMP)
        results = (BusinessResult(success=False, context=context),)
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        completed_issue = next(i for i in issues if i.check == CHECK_PIPELINE_COMPLETED)
        assert "UNRESOLVED" in completed_issue.message

    def test_missing_everything_reports_all_five_checks(self) -> None:
        context = PipelineContext(session_id=_SESSION_ID, candle_timestamp=_TIMESTAMP)
        results = (BusinessResult(success=False, context=context),)
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        checks = {issue.check for issue in issues}
        assert checks == {
            CHECK_REFERENCE_STRIKE,
            CHECK_REFERENCE_LEVEL,
            CHECK_WEEKLY_FUTURE,
            CHECK_STRIKE_SELECTION,
            CHECK_PIPELINE_COMPLETED,
        }

    def test_issues_preserve_candle_order(self) -> None:
        early = PipelineContext(session_id=_SESSION_ID, candle_timestamp=_TIMESTAMP)
        late_ts = datetime(2026, 7, 29, 9, 25, 0, tzinfo=UTC)
        late = PipelineContext(session_id=_SESSION_ID, candle_timestamp=late_ts)
        results = (
            BusinessResult(success=False, context=early),
            BusinessResult(success=False, context=late),
        )
        result = _replay_result(results)

        issues = validate_replay_consistency(result)

        assert issues[0].candle_timestamp == _TIMESTAMP
        assert issues[-1].candle_timestamp == late_ts

    def test_empty_business_results_yields_no_issues(self) -> None:
        result = _replay_result(())

        issues = validate_replay_consistency(result)

        assert issues == ()


class TestReplayConsistencyIssueValidation:
    def test_rejects_none_candle_timestamp(self) -> None:
        with pytest.raises(ValidationError, match="candle_timestamp must not be None"):
            ReplayConsistencyIssue(
                candle_timestamp=None,  # type: ignore[arg-type]
                check=CHECK_REFERENCE_STRIKE,
                message="missing",
            )

    def test_rejects_blank_check(self) -> None:
        with pytest.raises(ValidationError, match="check must not be blank"):
            ReplayConsistencyIssue(candle_timestamp=_TIMESTAMP, check="  ", message="missing")

    def test_rejects_blank_message(self) -> None:
        with pytest.raises(ValidationError, match="message must not be blank"):
            ReplayConsistencyIssue(
                candle_timestamp=_TIMESTAMP, check=CHECK_REFERENCE_STRIKE, message=""
            )


class TestRenderConsistencyReport:
    def test_reports_no_inconsistencies_when_empty(self) -> None:
        report = render_consistency_report(())

        assert report == "No inconsistencies found."

    def test_reports_one_line_per_issue(self) -> None:
        issues = (
            ReplayConsistencyIssue(
                candle_timestamp=_TIMESTAMP,
                check=CHECK_REFERENCE_STRIKE,
                message="Reference Strike is missing.",
            ),
            ReplayConsistencyIssue(
                candle_timestamp=_TIMESTAMP,
                check=CHECK_WEEKLY_FUTURE,
                message="Weekly Future was not generated.",
            ),
        )

        report = render_consistency_report(issues)
        lines = report.splitlines()

        assert len(lines) == 2
        assert CHECK_REFERENCE_STRIKE in lines[0]
        assert CHECK_WEEKLY_FUTURE in lines[1]

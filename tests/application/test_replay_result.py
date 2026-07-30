"""Tests for application.replay_result."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from application.replay_configuration import ReplayConfiguration
from application.replay_result import ReplayResult
from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
from business.business_result import BusinessResult
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError


def _ts(second: int = 0) -> datetime:
    return datetime(2026, 7, 30, 9, 0, second, tzinfo=UTC)


def _config() -> ReplayConfiguration:
    return ReplayConfiguration(start_date=date(2026, 7, 1), end_date=date(2026, 7, 31))


def _session() -> ReplaySession:
    return ReplaySession(
        session_id=uuid.uuid4(),
        dataset_id="EXP-001",
        started_at=_ts(0),
        status=ReplayStatus.COMPLETED,
        ended_at=_ts(5),
        statistics=ReplayStatistics(
            candles_processed=1,
            events_recorded=0,
            business_runs_succeeded=1,
            business_runs_failed=0,
        ),
    )


def _business_result(success: bool) -> BusinessResult:
    context = PipelineContext(session_id=uuid.uuid4(), candle_timestamp=_ts(0))
    return BusinessResult(success=success, context=context)


class TestConstruction:
    def test_valid_construction(self) -> None:
        result = ReplayResult(session=_session(), configuration=_config(), generated_at=_ts(6))

        assert result.business_results == ()
        assert result.events == ()

    def test_counts_success_and_failure(self) -> None:
        result = ReplayResult(
            session=_session(),
            configuration=_config(),
            generated_at=_ts(6),
            business_results=(
                _business_result(True),
                _business_result(False),
                _business_result(True),
            ),
        )

        assert result.succeeded_count == 2
        assert result.failed_count == 1


class TestValidation:
    def test_none_session_raises(self) -> None:
        with pytest.raises(ValidationError, match="session must not be None"):
            ReplayResult(session=None, configuration=_config(), generated_at=_ts(6))  # type: ignore[arg-type]

    def test_none_configuration_raises(self) -> None:
        with pytest.raises(ValidationError, match="configuration must not be None"):
            ReplayResult(session=_session(), configuration=None, generated_at=_ts(6))  # type: ignore[arg-type]

    def test_none_generated_at_raises(self) -> None:
        with pytest.raises(ValidationError, match="generated_at must not be None"):
            ReplayResult(session=_session(), configuration=_config(), generated_at=None)  # type: ignore[arg-type]

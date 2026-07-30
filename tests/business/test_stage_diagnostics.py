"""Tests for business.stage_diagnostics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from business.stage_diagnostics import StageDiagnostic
from core.exceptions import ValidationError


def _ts(offset_seconds: int = 0) -> datetime:
    return datetime(2026, 7, 30, 9, 20, offset_seconds, tzinfo=UTC)


class TestConstruction:
    def test_valid_success_construction(self) -> None:
        diagnostic = StageDiagnostic(
            stage_name="weekly_future",
            start_time=_ts(0),
            end_time=_ts(2),
            duration=timedelta(seconds=2),
            success=True,
        )

        assert diagnostic.stage_name == "weekly_future"
        assert diagnostic.failure_reason is None

    def test_valid_failure_construction(self) -> None:
        diagnostic = StageDiagnostic(
            stage_name="weekly_future",
            start_time=_ts(0),
            end_time=_ts(0),
            duration=timedelta(),
            success=False,
            failure_reason="prerequisites not met",
        )

        assert diagnostic.failure_reason == "prerequisites not met"

    def test_blank_stage_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="stage_name must not be blank"):
            StageDiagnostic(
                stage_name="  ",
                start_time=_ts(0),
                end_time=_ts(0),
                duration=timedelta(),
                success=True,
            )

    def test_none_start_time_raises(self) -> None:
        with pytest.raises(ValidationError, match="start_time must not be None"):
            StageDiagnostic(
                stage_name="weekly_future",
                start_time=None,  # type: ignore[arg-type]
                end_time=_ts(0),
                duration=timedelta(),
                success=True,
            )

    def test_none_end_time_raises(self) -> None:
        with pytest.raises(ValidationError, match="end_time must not be None"):
            StageDiagnostic(
                stage_name="weekly_future",
                start_time=_ts(0),
                end_time=None,  # type: ignore[arg-type]
                duration=timedelta(),
                success=True,
            )

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValidationError, match="end_time must not be before start_time"):
            StageDiagnostic(
                stage_name="weekly_future",
                start_time=_ts(5),
                end_time=_ts(0),
                duration=timedelta(),
                success=True,
            )

    def test_success_with_failure_reason_raises(self) -> None:
        with pytest.raises(ValidationError, match="failure_reason must be None"):
            StageDiagnostic(
                stage_name="weekly_future",
                start_time=_ts(0),
                end_time=_ts(0),
                duration=timedelta(),
                success=True,
                failure_reason="should not be here",
            )

    def test_failure_without_reason_raises(self) -> None:
        with pytest.raises(ValidationError, match="failure_reason must be set"):
            StageDiagnostic(
                stage_name="weekly_future",
                start_time=_ts(0),
                end_time=_ts(0),
                duration=timedelta(),
                success=False,
            )

"""Tests for application.replay_session."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
from core.exceptions import ValidationError


def _ts(second: int = 0) -> datetime:
    return datetime(2026, 7, 30, 9, 0, second, tzinfo=UTC)


def _stats(**overrides: int) -> ReplayStatistics:
    defaults = {
        "candles_processed": 1,
        "events_recorded": 1,
        "business_runs_succeeded": 1,
        "business_runs_failed": 0,
    }
    defaults.update(overrides)
    return ReplayStatistics(**defaults)


class TestReplayStatistics:
    def test_valid_construction(self) -> None:
        stats = _stats()

        assert stats.candles_processed == 1

    @pytest.mark.parametrize(
        "field_name",
        ["candles_processed", "events_recorded", "business_runs_succeeded", "business_runs_failed"],
    )
    def test_negative_field_raises(self, field_name: str) -> None:
        with pytest.raises(ValidationError, match=f"{field_name} must not be negative"):
            _stats(**{field_name: -1})


class TestReplaySession:
    def test_valid_pending(self) -> None:
        session = ReplaySession(
            session_id=uuid.uuid4(),
            dataset_id="EXP-001",
            started_at=_ts(0),
            status=ReplayStatus.PENDING,
        )

        assert session.duration_seconds is None

    def test_valid_completed(self) -> None:
        session = ReplaySession(
            session_id=uuid.uuid4(),
            dataset_id="EXP-001",
            started_at=_ts(0),
            status=ReplayStatus.COMPLETED,
            ended_at=_ts(5),
            statistics=_stats(),
        )

        assert session.duration_seconds == 5.0

    def test_none_session_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="session_id must not be None"):
            ReplaySession(
                session_id=None,  # type: ignore[arg-type]
                dataset_id="EXP-001",
                started_at=_ts(0),
                status=ReplayStatus.PENDING,
            )

    def test_blank_dataset_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="dataset_id must not be blank"):
            ReplaySession(
                session_id=uuid.uuid4(),
                dataset_id="  ",
                started_at=_ts(0),
                status=ReplayStatus.PENDING,
            )

    def test_none_started_at_raises(self) -> None:
        with pytest.raises(ValidationError, match="started_at must not be None"):
            ReplaySession(
                session_id=uuid.uuid4(),
                dataset_id="EXP-001",
                started_at=None,  # type: ignore[arg-type]
                status=ReplayStatus.PENDING,
            )

    def test_none_status_raises(self) -> None:
        with pytest.raises(ValidationError, match="status must not be None"):
            ReplaySession(
                session_id=uuid.uuid4(),
                dataset_id="EXP-001",
                started_at=_ts(0),
                status=None,  # type: ignore[arg-type]
            )

    def test_completed_without_ended_at_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be set when status is"):
            ReplaySession(
                session_id=uuid.uuid4(),
                dataset_id="EXP-001",
                started_at=_ts(0),
                status=ReplayStatus.COMPLETED,
                statistics=_stats(),
            )

    def test_completed_without_statistics_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be set when status is"):
            ReplaySession(
                session_id=uuid.uuid4(),
                dataset_id="EXP-001",
                started_at=_ts(0),
                status=ReplayStatus.COMPLETED,
                ended_at=_ts(1),
            )

    def test_pending_with_ended_at_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be None when status is"):
            ReplaySession(
                session_id=uuid.uuid4(),
                dataset_id="EXP-001",
                started_at=_ts(0),
                status=ReplayStatus.PENDING,
                ended_at=_ts(1),
            )

    def test_ended_before_started_raises(self) -> None:
        with pytest.raises(ValidationError, match="ended_at must not be before started_at"):
            ReplaySession(
                session_id=uuid.uuid4(),
                dataset_id="EXP-001",
                started_at=_ts(5),
                status=ReplayStatus.COMPLETED,
                ended_at=_ts(0),
                statistics=_stats(),
            )

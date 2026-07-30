"""Tests for application.strategy_timeline."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from application.strategy_timeline import (
    CSV_HEADER,
    StrategyTimeline,
    TimelineEvent,
    build_strategy_timeline,
    write_timeline_csv,
    write_timeline_json,
)
from business.business_errors import StageExecutionError
from business.business_result import BusinessResult
from business.pipeline_context import PipelineContext
from business.stage_diagnostics import StageDiagnostic
from core.enums import OptionType, ORBStatus, TimelineEventType
from core.exceptions import ValidationError
from models.orb_result import ORBResult
from models.reference_level import ReferenceLevel
from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture

_SESSION_ID = uuid.uuid4()
_T1 = datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC)
_T2 = datetime(2026, 7, 29, 9, 25, 0, tzinfo=UTC)
_FINISHED_AT = datetime(2026, 7, 29, 9, 30, 0, tzinfo=UTC)


def _reference_level() -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(24200),
        ce_high=Decimal("143.45"),
        ce_low=Decimal(116),
        pe_high=Decimal("165.8"),
        pe_low=Decimal(128),
    )


def _weekly_future() -> WeeklyFuture:
    return WeeklyFuture(
        weekly_future_id=uuid.uuid4(),
        session_id=_SESSION_ID,
        high=Decimal("24215.45"),
        low=Decimal("24150.2"),
        calculated_at=_T1,
    )


def _strike_selection() -> StrikeSelection:
    return StrikeSelection(
        session_id=_SESSION_ID,
        top_strike=Decimal(24200),
        bottom_strike=Decimal(24150),
        selected_at=_T1,
    )


def _orb_result(timestamp: datetime, status: ORBStatus) -> ORBResult:
    return ORBResult(
        orb_result_id=uuid.uuid4(),
        session_id=_SESSION_ID,
        strike=Decimal(24200),
        side=OptionType.CALL,
        opening_high=Decimal("143.45"),
        opening_low=Decimal(116),
        range=Decimal("27.45"),
        status=status,
        calculated_at=timestamp,
    )


def _context(timestamp: datetime, **overrides: object) -> PipelineContext:
    context = PipelineContext(
        session_id=_SESSION_ID, candle_timestamp=timestamp, reference_data=(_reference_level(),)
    )
    if overrides.get("weekly_future"):
        context = context.with_weekly_future(_weekly_future())
    if overrides.get("selected_strike"):
        context = context.with_selected_strike(_strike_selection())
    if orb_status := overrides.get("orb_status"):
        context = context.with_orb_result(_orb_result(timestamp, orb_status))  # type: ignore[arg-type]
    return context


class TestBuildStrategyTimeline:
    def test_full_first_candle_emits_four_events_plus_finished(self) -> None:
        results = (
            BusinessResult(
                success=True,
                context=_context(
                    _T1, weekly_future=True, selected_strike=True, orb_status=ORBStatus.NONE
                ),
            ),
        )

        timeline = build_strategy_timeline(results, _FINISHED_AT)

        types = [event.event_type for event in timeline.events]
        assert types == [
            TimelineEventType.REFERENCE_LEVEL_CREATED,
            TimelineEventType.WEEKLY_FUTURE_CALCULATED,
            TimelineEventType.STRIKE_SELECTED,
            TimelineEventType.ORB_CALCULATED,
            TimelineEventType.REPLAY_FINISHED,
        ]

    def test_events_are_in_chronological_order(self) -> None:
        results = (
            BusinessResult(context=_context(_T1, weekly_future=True), success=True),
            BusinessResult(context=_context(_T2, orb_status=ORBStatus.BREAKOUT), success=True),
        )

        timeline = build_strategy_timeline(results, _FINISHED_AT)

        timestamps = [event.timestamp for event in timeline.events]
        assert timestamps == sorted(timestamps)

    def test_reference_level_weekly_future_and_strike_emit_only_once(self) -> None:
        results = tuple(
            BusinessResult(
                success=True,
                context=_context(_T1, weekly_future=True, selected_strike=True),
            )
            for _ in range(3)
        )

        timeline = build_strategy_timeline(results, _FINISHED_AT)

        one_time_types = {
            TimelineEventType.REFERENCE_LEVEL_CREATED,
            TimelineEventType.WEEKLY_FUTURE_CALCULATED,
            TimelineEventType.STRIKE_SELECTED,
        }
        for event_type in one_time_types:
            count = sum(1 for event in timeline.events if event.event_type == event_type)
            assert count == 1, f"{event_type} emitted {count} times, expected 1"

    def test_orb_calculated_emits_once_per_candle(self) -> None:
        results = (
            BusinessResult(success=True, context=_context(_T1, orb_status=ORBStatus.NONE)),
            BusinessResult(success=True, context=_context(_T2, orb_status=ORBStatus.BREAKOUT)),
        )

        timeline = build_strategy_timeline(results, _FINISHED_AT)

        orb_events = [
            e for e in timeline.events if e.event_type == TimelineEventType.ORB_CALCULATED
        ]
        assert len(orb_events) == 2
        assert orb_events[0].payload["status"] == "NONE"
        assert orb_events[1].payload["status"] == "BREAKOUT"

    def test_pipeline_error_with_genuine_fault_names_failing_stage(self) -> None:
        error = StageExecutionError("weekly_future raised ValidationError: boom")
        stage_diagnostics = (
            StageDiagnostic(
                stage_name="weekly_future",
                start_time=_T1,
                end_time=_T1,
                duration=_T1 - _T1,
                success=False,
                failure_reason="FAILED - ValidationError: boom",
            ),
        )
        results = (
            BusinessResult(
                success=False,
                context=_context(_T1),
                error=error,
                stage_diagnostics=stage_diagnostics,
            ),
        )

        timeline = build_strategy_timeline(results, _FINISHED_AT)

        error_event = next(
            e for e in timeline.events if e.event_type == TimelineEventType.PIPELINE_ERROR
        )
        assert error_event.stage == "weekly_future"
        assert "boom" in error_event.payload["error"]

    def test_pipeline_error_skips_successful_diagnostics_to_find_the_failing_one(self) -> None:
        error = StageExecutionError("orb raised ValidationError: boom")
        stage_diagnostics = (
            StageDiagnostic(
                stage_name="weekly_future",
                start_time=_T1,
                end_time=_T1,
                duration=_T1 - _T1,
                success=True,
            ),
            StageDiagnostic(
                stage_name="orb",
                start_time=_T1,
                end_time=_T1,
                duration=_T1 - _T1,
                success=False,
                failure_reason="FAILED - ValidationError: boom",
            ),
        )
        results = (
            BusinessResult(
                success=False,
                context=_context(_T1),
                error=error,
                stage_diagnostics=stage_diagnostics,
            ),
        )

        timeline = build_strategy_timeline(results, _FINISHED_AT)

        error_event = next(
            e for e in timeline.events if e.event_type == TimelineEventType.PIPELINE_ERROR
        )
        assert error_event.stage == "orb"

    def test_pipeline_error_unresolved_when_error_is_none(self) -> None:
        results = (BusinessResult(success=False, context=_context(_T1)),)

        timeline = build_strategy_timeline(results, _FINISHED_AT)

        error_event = next(
            e for e in timeline.events if e.event_type == TimelineEventType.PIPELINE_ERROR
        )
        assert error_event.payload["error"] == "UNRESOLVED"
        assert error_event.stage == "pipeline"

    def test_replay_finished_is_always_last_with_correct_counts(self) -> None:
        results = (
            BusinessResult(success=True, context=_context(_T1)),
            BusinessResult(success=False, context=_context(_T2)),
        )

        timeline = build_strategy_timeline(results, _FINISHED_AT)

        last_event = timeline.events[-1]
        assert last_event.event_type == TimelineEventType.REPLAY_FINISHED
        assert last_event.timestamp == _FINISHED_AT
        assert last_event.payload == {"succeeded": "1", "failed": "1", "total": "2"}

    def test_empty_business_results_yields_only_replay_finished(self) -> None:
        timeline = build_strategy_timeline((), _FINISHED_AT)

        assert len(timeline.events) == 1
        assert timeline.events[0].event_type == TimelineEventType.REPLAY_FINISHED
        assert timeline.events[0].payload == {"succeeded": "0", "failed": "0", "total": "0"}


class TestTimelineEventValidation:
    def test_rejects_none_timestamp(self) -> None:
        with pytest.raises(ValidationError, match="timestamp must not be None"):
            TimelineEvent(
                timestamp=None,  # type: ignore[arg-type]
                trading_date=_T1.date(),
                stage="replay",
                event_type=TimelineEventType.REPLAY_FINISHED,
                summary="ok",
            )

    def test_rejects_none_trading_date(self) -> None:
        with pytest.raises(ValidationError, match="trading_date must not be None"):
            TimelineEvent(
                timestamp=_T1,
                trading_date=None,  # type: ignore[arg-type]
                stage="replay",
                event_type=TimelineEventType.REPLAY_FINISHED,
                summary="ok",
            )

    def test_rejects_blank_stage(self) -> None:
        with pytest.raises(ValidationError, match="stage must not be blank"):
            TimelineEvent(
                timestamp=_T1,
                trading_date=_T1.date(),
                stage="  ",
                event_type=TimelineEventType.REPLAY_FINISHED,
                summary="ok",
            )

    def test_rejects_blank_summary(self) -> None:
        with pytest.raises(ValidationError, match="summary must not be blank"):
            TimelineEvent(
                timestamp=_T1,
                trading_date=_T1.date(),
                stage="replay",
                event_type=TimelineEventType.REPLAY_FINISHED,
                summary="",
            )


class TestWriteTimelineJson:
    def test_writes_events_as_json_list(self, tmp_path: Path) -> None:
        results = (BusinessResult(success=True, context=_context(_T1, weekly_future=True)),)
        timeline = build_strategy_timeline(results, _FINISHED_AT)
        json_path = tmp_path / "timeline.json"

        write_timeline_json(timeline, json_path)

        import json

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert data[0]["event_type"] == "REFERENCE_LEVEL_CREATED"
        assert data[-1]["event_type"] == "REPLAY_FINISHED"

    def test_writes_empty_timeline_as_finished_only(self, tmp_path: Path) -> None:
        timeline = build_strategy_timeline((), _FINISHED_AT)
        json_path = tmp_path / "timeline.json"

        write_timeline_json(timeline, json_path)

        import json

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert len(data) == 1


class TestWriteTimelineCsv:
    def test_writes_header_and_rows(self, tmp_path: Path) -> None:
        results = (BusinessResult(success=True, context=_context(_T1, weekly_future=True)),)
        timeline = build_strategy_timeline(results, _FINISHED_AT)
        csv_path = tmp_path / "timeline.csv"

        write_timeline_csv(timeline, csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(CSV_HEADER)
        assert len(lines) == len(timeline.events) + 1
        assert "high=" in lines[2]

    def test_writes_empty_events_as_header_only(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "empty.csv"

        write_timeline_csv(StrategyTimeline(events=()), csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines == [",".join(CSV_HEADER)]

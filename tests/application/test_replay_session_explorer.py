"""Tests for application.replay_session_explorer."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import openpyxl

from application.replay_configuration import ReplayConfiguration
from application.replay_result import ReplayResult
from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
from application.replay_session_explorer import (
    ExplorerFilter,
    ReplaySessionExplorer,
    ReplaySessionState,
)
from application.strategy_timeline import build_strategy_timeline
from business.business_result import BusinessResult
from business.pipeline_context import PipelineContext
from core.enums import OptionType, ORBStatus, TimelineEventType
from models.orb_result import ORBResult
from models.reference_level import ReferenceLevel
from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture

_SESSION_ID = uuid.uuid4()
_T0 = datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC)


def _reference_level() -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(24200),
        ce_high=Decimal("143.45"),
        ce_low=Decimal(116),
        pe_high=Decimal("165.8"),
        pe_low=Decimal(128),
    )


def _context(
    timestamp: datetime, *, orb_status: ORBStatus = ORBStatus.NONE, first: bool = False
) -> PipelineContext:
    context = PipelineContext(
        session_id=_SESSION_ID,
        candle_timestamp=timestamp,
        reference_data=(_reference_level(),),
    )
    context = context.with_reference_strike(Decimal(24200))
    if first:
        context = context.with_weekly_future(
            WeeklyFuture(
                weekly_future_id=uuid.uuid4(),
                session_id=_SESSION_ID,
                high=Decimal("24215.45"),
                low=Decimal("24150.2"),
                calculated_at=timestamp,
            )
        ).with_selected_strike(
            StrikeSelection(
                session_id=_SESSION_ID,
                top_strike=Decimal(24200),
                bottom_strike=Decimal(24150),
                selected_at=timestamp,
            )
        )
    context = context.with_orb_result(
        ORBResult(
            orb_result_id=uuid.uuid4(),
            session_id=_SESSION_ID,
            strike=Decimal(24200),
            side=OptionType.CALL,
            opening_high=Decimal("143.45"),
            opening_low=Decimal(116),
            range=Decimal("27.45"),
            status=orb_status,
            calculated_at=timestamp,
        )
    )
    return context


def _replay_result(business_results: tuple[BusinessResult, ...]) -> ReplayResult:
    if business_results:
        started_at = business_results[0].context.candle_timestamp
        ended_at = business_results[-1].context.candle_timestamp + timedelta(minutes=5)
    else:
        started_at = _T0
        ended_at = _T0
    session = ReplaySession(
        session_id=_SESSION_ID,
        dataset_id="ds-1",
        started_at=started_at,
        status=ReplayStatus.COMPLETED,
        ended_at=ended_at,
        statistics=ReplayStatistics(
            candles_processed=len(business_results),
            events_recorded=0,
            business_runs_succeeded=sum(1 for r in business_results if r.success),
            business_runs_failed=sum(1 for r in business_results if not r.success),
        ),
    )
    timeline = build_strategy_timeline(business_results, ended_at)
    return ReplayResult(
        session=session,
        configuration=ReplayConfiguration(start_date=date(2026, 7, 29), end_date=date(2026, 7, 29)),
        generated_at=ended_at,
        business_results=business_results,
        strategy_timeline=timeline,
    )


def _three_candle_result() -> ReplayResult:
    results = (
        BusinessResult(success=True, context=_context(_T0, first=True, orb_status=ORBStatus.NONE)),
        BusinessResult(
            success=True,
            context=_context(_T0 + timedelta(minutes=5), orb_status=ORBStatus.BREAKOUT),
        ),
        BusinessResult(
            success=True,
            context=_context(_T0 + timedelta(minutes=10), orb_status=ORBStatus.BREAKDOWN),
        ),
    )
    return _replay_result(results)


class TestCreateAndInitialState:
    def test_create_starts_at_first_event(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.current()

        assert state.current_event_index == 0
        assert state.current_event is not None
        assert state.current_event.event_type == TimelineEventType.REFERENCE_LEVEL_CREATED
        assert state.previous_event is None
        assert state.next_event is not None


class TestNavigationForwardBackward:
    def test_next_advances_one_event(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.next()

        assert state.current_event_index == 1

    def test_next_never_goes_past_the_last_event(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        for _ in range(50):
            state = explorer.next()

        last_index = len(explorer._filtered_events) - 1  # type: ignore[attr-defined]
        assert state.current_event_index == last_index

    def test_previous_never_goes_before_the_first_event(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        for _ in range(10):
            state = explorer.previous()

        assert state.current_event_index == 0

    def test_previous_after_next_returns_to_start(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        explorer.next()
        state = explorer.previous()

        assert state.current_event_index == 0

    def test_current_event_and_neighbors_are_consistent(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        explorer.next()
        state = explorer.current()

        all_events = explorer._filtered_events  # type: ignore[attr-defined]
        assert state.current_event == all_events[1]
        assert state.previous_event == all_events[0]
        assert state.next_event == all_events[2]


class TestJumpByTimestamp:
    def test_jumps_to_exact_timestamp(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.jump_to_timestamp(_T0 + timedelta(minutes=5))

        assert state.current_timestamp == _T0 + timedelta(minutes=5)

    def test_jumps_to_nearest_timestamp_when_no_exact_match(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.jump_to_timestamp(_T0 + timedelta(minutes=4))

        assert state.current_timestamp == _T0 + timedelta(minutes=5)

    def test_jump_on_empty_filtered_view_never_throws(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.filter_by_stage("does-not-exist")

        state = explorer.jump_to_timestamp(_T0)

        assert state == ReplaySessionState(None, None, None, None, None, None)


class TestJumpByStage:
    def test_jumps_to_first_event_for_that_stage(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.jump_to_stage("orb")

        assert state.current_event is not None
        assert state.current_event.stage == "orb"

    def test_jump_to_unknown_stage_does_not_move_and_does_not_throw(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        before = explorer.current()

        state = explorer.jump_to_stage("does-not-exist")

        assert state.current_event_index == before.current_event_index


class TestJumpToEventAndReset:
    def test_jump_to_event_clamps_out_of_range_high(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.jump_to_event(9999)

        last_index = len(explorer._filtered_events) - 1  # type: ignore[attr-defined]
        assert state.current_event_index == last_index

    def test_jump_to_event_clamps_out_of_range_negative(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.jump_to_event(-100)

        assert state.current_event_index == 0

    def test_reset_returns_to_first_event(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.next()
        explorer.next()

        state = explorer.reset()

        assert state.current_event_index == 0


class TestFiltering:
    def test_filter_by_stage_restricts_navigation(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.filter_by_stage("orb")

        assert state.current_event is not None
        assert state.current_event.stage == "orb"
        for event in explorer._filtered_events:  # type: ignore[attr-defined]
            assert event.stage == "orb"

    def test_filter_by_event_type(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        explorer.filter_by_event_type(TimelineEventType.ORB_CALCULATED)

        for event in explorer._filtered_events:  # type: ignore[attr-defined]
            assert event.event_type == TimelineEventType.ORB_CALCULATED

    def test_filter_by_time_range(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        explorer.filter_by_time_range(_T0 + timedelta(minutes=5), _T0 + timedelta(minutes=10))

        for event in explorer._filtered_events:  # type: ignore[attr-defined]
            assert _T0 + timedelta(minutes=5) <= event.timestamp <= _T0 + timedelta(minutes=10)

    def test_filter_breakouts_only(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        explorer.filter_breakouts_only()

        events = explorer._filtered_events  # type: ignore[attr-defined]
        assert len(events) == 1
        assert events[0].payload["status"] == "BREAKOUT"

    def test_filter_breakdowns_only(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        explorer.filter_breakdowns_only()

        events = explorer._filtered_events  # type: ignore[attr-defined]
        assert len(events) == 1
        assert events[0].payload["status"] == "BREAKDOWN"

    def test_clear_filters_restores_full_view(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        full_count = len(explorer._filtered_events)  # type: ignore[attr-defined]
        explorer.filter_by_stage("orb")

        explorer.clear_filters()

        assert len(explorer._filtered_events) == full_count  # type: ignore[attr-defined]

    def test_filters_never_modify_replay_result(self) -> None:
        result = _three_candle_result()
        original_events = result.strategy_timeline.events
        explorer = ReplaySessionExplorer.create(result)

        explorer.filter_by_stage("orb")
        explorer.filter_breakouts_only()

        assert result.strategy_timeline.events is original_events


class TestSearching:
    def test_search_text_matches_summary_case_insensitively(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        matches = explorer.search_text("breakout")

        assert len(matches) == 1
        assert "BREAKOUT" in matches[0].summary

    def test_search_strike_matches_payload_values(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        matches = explorer.search_strike(Decimal(24200))

        assert len(matches) >= 1

    def test_search_timestamp_matches_exact_events(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        matches = explorer.search_timestamp(_T0)

        assert len(matches) >= 1
        assert all(event.timestamp == _T0 for event in matches)

    def test_search_does_not_move_the_cursor(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        before = explorer.current()

        explorer.search_text("breakout")

        assert explorer.current() == before

    def test_search_respects_active_filters(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.filter_by_event_type(TimelineEventType.WEEKLY_FUTURE_CALCULATED)

        matches = explorer.search_text("breakout")

        assert matches == ()


class TestEmptyReplay:
    def test_empty_replay_current_state_is_all_none(self) -> None:
        explorer = ReplaySessionExplorer.create(_replay_result(()))

        # Only REPLAY_FINISHED is emitted even for an empty replay.
        state = explorer.current()

        assert state.current_event is not None  # REPLAY_FINISHED still exists
        assert state.current_event.event_type == TimelineEventType.REPLAY_FINISHED

    def test_filter_matching_nothing_yields_all_none_state(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        state = explorer.filter_by_stage("no-such-stage")

        assert state == ReplaySessionState(None, None, None, None, None, None)

    def test_navigation_on_empty_filtered_view_never_throws(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.filter_by_stage("no-such-stage")

        assert explorer.next() == ReplaySessionState(None, None, None, None, None, None)
        assert explorer.previous() == ReplaySessionState(None, None, None, None, None, None)
        assert explorer.jump_to_event(5) == ReplaySessionState(None, None, None, None, None, None)


class TestSingleEventReplay:
    def test_single_event_has_no_previous_or_next(self) -> None:
        results = (BusinessResult(success=False, context=_context(_T0)),)
        result = _replay_result(results)
        explorer = ReplaySessionExplorer.create(result)
        explorer.filter_by_event_type(TimelineEventType.REPLAY_FINISHED)

        state = explorer.current()

        assert state.current_event is not None
        assert state.previous_event is None
        assert state.next_event is None

    def test_next_and_previous_stay_put(self) -> None:
        results = (BusinessResult(success=False, context=_context(_T0)),)
        result = _replay_result(results)
        explorer = ReplaySessionExplorer.create(result)
        explorer.filter_by_event_type(TimelineEventType.REPLAY_FINISHED)

        assert explorer.next().current_event_index == 0
        assert explorer.previous().current_event_index == 0


class TestLargeReplay:
    def test_handles_1000_plus_events(self) -> None:
        results = tuple(
            BusinessResult(
                success=True,
                context=_context(
                    _T0 + timedelta(minutes=5 * i),
                    first=(i == 0),
                    orb_status=ORBStatus.BREAKOUT if i % 2 == 0 else ORBStatus.BREAKDOWN,
                ),
            )
            for i in range(1000)
        )
        result = _replay_result(results)
        explorer = ReplaySessionExplorer.create(result)

        assert len(explorer._filtered_events) > 1000  # type: ignore[attr-defined]

        last_state = explorer.jump_to_event(999999)
        assert last_state.current_event_index == len(explorer._filtered_events) - 1  # type: ignore[attr-defined]

        explorer.filter_breakouts_only()
        breakout_events = explorer._filtered_events  # type: ignore[attr-defined]
        assert len(breakout_events) == 500


class TestFilterProperty:
    def test_filter_property_reflects_applied_filter(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        explorer.filter_by_stage("orb")

        assert explorer.filter.stage == "orb"

    def test_filter_property_defaults_to_no_criteria(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        assert explorer.filter == ExplorerFilter()


class TestExplorerFilterMatches:
    def test_no_criteria_matches_everything(self) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())

        assert ExplorerFilter().matches(explorer.current().current_event)  # type: ignore[arg-type]


class TestExportCurrentView:
    def test_export_current_json(self, tmp_path: Path) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        json_path = tmp_path / "current.json"

        explorer.export_current_json(json_path)

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["current_event_index"] == 0
        assert data["previous_event"] is None
        assert data["next_event"] is not None

    def test_export_current_csv(self, tmp_path: Path) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.next()
        csv_path = tmp_path / "current.csv"

        explorer.export_current_csv(csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "role,timestamp,trading_date,stage,event_type,summary"
        assert len(lines) == 4  # header + previous + current + next

    def test_export_current_csv_blank_row_when_no_previous_event(self, tmp_path: Path) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        csv_path = tmp_path / "current_first.csv"

        explorer.export_current_csv(csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines[1] == "previous,,,,,"

    def test_export_current_excel(self, tmp_path: Path) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        xlsx_path = tmp_path / "current.xlsx"

        explorer.export_current_excel(xlsx_path)

        workbook = openpyxl.load_workbook(str(xlsx_path))
        assert workbook.sheetnames == ["Current View"]
        assert workbook["Current View"].max_row == 4

    def test_export_current_with_empty_filtered_view(self, tmp_path: Path) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.filter_by_stage("no-such-stage")
        json_path = tmp_path / "empty.json"

        explorer.export_current_json(json_path)

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["current_event_index"] is None
        assert data["current_event"] is None


class TestExportFilteredView:
    def test_export_filtered_json(self, tmp_path: Path) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.filter_by_stage("orb")
        json_path = tmp_path / "filtered.json"

        explorer.export_filtered_json(json_path)

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert len(data) == 3
        assert all(item["stage"] == "orb" for item in data)

    def test_export_filtered_csv(self, tmp_path: Path) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.filter_by_stage("orb")
        csv_path = tmp_path / "filtered.csv"

        explorer.export_filtered_csv(csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 4  # header + 3 orb events

    def test_export_filtered_excel(self, tmp_path: Path) -> None:
        explorer = ReplaySessionExplorer.create(_three_candle_result())
        explorer.filter_by_stage("orb")
        xlsx_path = tmp_path / "filtered.xlsx"

        explorer.export_filtered_excel(xlsx_path)

        workbook = openpyxl.load_workbook(str(xlsx_path))
        assert workbook.sheetnames == ["Filtered Timeline"]
        assert workbook["Filtered Timeline"].max_row == 4


class TestReplayResultImmutability:
    def test_explorer_never_mutates_replay_result(self) -> None:
        result = _three_candle_result()
        original_business_results = result.business_results
        original_timeline_events = result.strategy_timeline.events

        explorer = ReplaySessionExplorer.create(result)
        explorer.next()
        explorer.filter_by_stage("orb")
        explorer.search_text("breakout")
        explorer.jump_to_timestamp(_T0)
        explorer.reset()

        assert result.business_results is original_business_results
        assert result.strategy_timeline.events is original_timeline_events

"""Tests for application.replay_event_model."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from application.replay_event_model import (
    ReplayEvent,
    ReplayEventCollection,
    ReplayEventQuery,
    ReplayEventStatistics,
    build_statistics,
)
from application.strategy_timeline import StrategyTimeline, TimelineEvent
from core.enums import ORBStatus, TimelineEventType
from core.exceptions import ValidationError

_T0 = datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC)
_T1 = datetime(2026, 7, 29, 9, 25, 0, tzinfo=UTC)
_T2 = datetime(2026, 7, 29, 9, 30, 0, tzinfo=UTC)


def _event(
    timestamp: datetime,
    stage: str,
    event_type: TimelineEventType,
    summary: str = "an event",
    payload: dict[str, str] | None = None,
) -> ReplayEvent:
    return TimelineEvent(
        timestamp=timestamp,
        trading_date=timestamp.date(),
        stage=stage,
        event_type=event_type,
        summary=summary,
        payload=payload or {},
    )


def _sample_events() -> tuple[ReplayEvent, ...]:
    return (
        _event(
            _T0,
            "reference_builder",
            TimelineEventType.REFERENCE_LEVEL_CREATED,
            "Reference ladder built with 13 levels.",
            {"level_count": "13"},
        ),
        _event(
            _T0,
            "weekly_future",
            TimelineEventType.WEEKLY_FUTURE_CALCULATED,
            "Weekly Future High=24215.45 Low=24150.2.",
            {"high": "24215.45", "low": "24150.2"},
        ),
        _event(
            _T0,
            "weekly_future",
            TimelineEventType.STRIKE_SELECTED,
            "Top Strike=24200 Bottom Strike=24150.",
            {"top_strike": "24200", "bottom_strike": "24150"},
        ),
        _event(
            _T1,
            "orb",
            TimelineEventType.ORB_CALCULATED,
            "ORB CALL 24200: status=BREAKOUT.",
            {"strike": "24200", "status": "BREAKOUT"},
        ),
        _event(
            _T2,
            "orb",
            TimelineEventType.ORB_CALCULATED,
            "ORB CALL 24200: status=BREAKDOWN.",
            {"strike": "24200", "status": "BREAKDOWN"},
        ),
        _event(_T2, "replay", TimelineEventType.REPLAY_FINISHED, "Replay finished: 2, 0."),
    )


def _collection() -> ReplayEventCollection:
    return ReplayEventCollection(events=_sample_events())


class TestReplayEventCollection:
    def test_len_and_iteration(self) -> None:
        collection = _collection()

        assert len(collection) == 6
        assert list(collection) == list(_sample_events())

    def test_indexing(self) -> None:
        collection = _collection()

        assert collection[0] == _sample_events()[0]

    def test_first_and_last(self) -> None:
        collection = _collection()

        assert collection.first() == _sample_events()[0]
        assert collection.last() == _sample_events()[-1]

    def test_first_and_last_on_empty_collection(self) -> None:
        collection = ReplayEventCollection()

        assert collection.first() is None
        assert collection.last() is None

    def test_is_empty(self) -> None:
        assert ReplayEventCollection().is_empty is True
        assert _collection().is_empty is False

    def test_stages_in_first_seen_order(self) -> None:
        collection = _collection()

        assert collection.stages() == ("reference_builder", "weekly_future", "orb", "replay")

    def test_event_types_in_first_seen_order(self) -> None:
        collection = _collection()

        assert collection.event_types() == (
            TimelineEventType.REFERENCE_LEVEL_CREATED,
            TimelineEventType.WEEKLY_FUTURE_CALCULATED,
            TimelineEventType.STRIKE_SELECTED,
            TimelineEventType.ORB_CALCULATED,
            TimelineEventType.REPLAY_FINISHED,
        )

    def test_from_timeline(self) -> None:
        timeline = StrategyTimeline(events=_sample_events())

        collection = ReplayEventCollection.from_timeline(timeline)

        assert collection.events == timeline.events


class TestReplayEventQueryChaining:
    def test_by_stage(self) -> None:
        query = ReplayEventQuery().by_stage("orb")

        result = query.apply(_collection())

        assert len(result) == 2
        assert all(event.stage == "orb" for event in result)

    def test_by_event_type(self) -> None:
        query = ReplayEventQuery().by_event_type(TimelineEventType.ORB_CALCULATED)

        result = query.apply(_collection())

        assert len(result) == 2

    def test_by_time_range(self) -> None:
        query = ReplayEventQuery().by_time_range(_T1, _T2)

        result = query.apply(_collection())

        assert all(_T1 <= event.timestamp <= _T2 for event in result)
        assert len(result) == 3  # both T2 events + the T1 event

    def test_by_time_range_excludes_events_after_end(self) -> None:
        query = ReplayEventQuery().by_time_range(_T0, _T1)

        result = query.apply(_collection())

        assert all(event.timestamp <= _T1 for event in result)
        assert len(result) == 4  # the three T0 events + the T1 event

    def test_by_orb_status_breakout(self) -> None:
        query = ReplayEventQuery().by_orb_status(ORBStatus.BREAKOUT)

        result = query.apply(_collection())

        assert len(result) == 1
        assert result[0].payload["status"] == "BREAKOUT"

    def test_by_orb_status_excludes_non_orb_events(self) -> None:
        query = ReplayEventQuery().by_orb_status(ORBStatus.BREAKOUT)

        result = query.apply(_collection())

        assert all(event.event_type == TimelineEventType.ORB_CALCULATED for event in result)

    def test_containing_text_case_insensitive(self) -> None:
        query = ReplayEventQuery().containing_text("breakout")

        result = query.apply(_collection())

        assert len(result) == 1

    def test_containing_strike(self) -> None:
        query = ReplayEventQuery().containing_strike(Decimal(24200))

        result = query.apply(_collection())

        assert len(result) == 3  # strike selected + 2 orb events

    def test_at_timestamp(self) -> None:
        query = ReplayEventQuery().at_timestamp(_T0)

        result = query.apply(_collection())

        assert len(result) == 3

    def test_chained_query_combines_all_constraints(self) -> None:
        query = (
            ReplayEventQuery()
            .by_stage("orb")
            .by_event_type(TimelineEventType.ORB_CALCULATED)
            .by_orb_status(ORBStatus.BREAKDOWN)
        )

        result = query.apply(_collection())

        assert len(result) == 1
        assert result[0].timestamp == _T2

    def test_query_is_immutable_across_chained_calls(self) -> None:
        base = ReplayEventQuery()
        stage_query = base.by_stage("orb")

        assert base.stage is None
        assert stage_query.stage == "orb"

    def test_apply_never_mutates_the_collection(self) -> None:
        collection = _collection()
        original_events = collection.events

        ReplayEventQuery().by_stage("orb").apply(collection)

        assert collection.events is original_events

    def test_no_criteria_matches_everything(self) -> None:
        result = ReplayEventQuery().apply(_collection())

        assert len(result) == len(_collection())

    def test_matches_on_a_single_event(self) -> None:
        event = _sample_events()[0]

        assert ReplayEventQuery().by_stage("reference_builder").matches(event)
        assert not ReplayEventQuery().by_stage("orb").matches(event)


class TestBuildStatistics:
    def test_full_collection_statistics(self) -> None:
        stats = build_statistics(_collection())

        assert stats.total_events == 6
        assert stats.event_counts_by_type["ORB_CALCULATED"] == 2
        assert stats.event_counts_by_stage["orb"] == 2
        assert stats.breakout_count == 1
        assert stats.breakdown_count == 1
        assert stats.first_timestamp == _T0
        assert stats.last_timestamp == _T2
        assert stats.span_seconds == (_T2 - _T0).total_seconds()

    def test_empty_collection_statistics(self) -> None:
        stats = build_statistics(ReplayEventCollection())

        assert stats.total_events == 0
        assert stats.event_counts_by_type == {}
        assert stats.event_counts_by_stage == {}
        assert stats.breakout_count == 0
        assert stats.breakdown_count == 0
        assert stats.first_timestamp is None
        assert stats.last_timestamp is None
        assert stats.span_seconds is None

    def test_single_event_collection_has_zero_span(self) -> None:
        collection = ReplayEventCollection(events=(_sample_events()[0],))

        stats = build_statistics(collection)

        assert stats.total_events == 1
        assert stats.span_seconds == 0.0

    def test_orb_calculated_with_none_status_counted_in_neither(self) -> None:
        events = (
            *_sample_events(),
            _event(
                _T2,
                "orb",
                TimelineEventType.ORB_CALCULATED,
                "ORB CALL 24200: status=NONE.",
                {"strike": "24200", "status": "NONE"},
            ),
        )
        stats = build_statistics(ReplayEventCollection(events=events))

        assert stats.event_counts_by_type["ORB_CALCULATED"] == 3
        assert stats.breakout_count == 1
        assert stats.breakdown_count == 1

    def test_filtered_collection_statistics(self) -> None:
        filtered = ReplayEventQuery().by_stage("orb").apply(_collection())

        stats = build_statistics(filtered)

        assert stats.total_events == 2
        assert stats.breakout_count == 1
        assert stats.breakdown_count == 1


class TestReplayEventStatisticsValidation:
    def test_rejects_negative_total_events(self) -> None:
        with pytest.raises(ValidationError, match="total_events must not be negative"):
            ReplayEventStatistics(
                total_events=-1,
                event_counts_by_type={},
                event_counts_by_stage={},
                breakout_count=0,
                breakdown_count=0,
                first_timestamp=None,
                last_timestamp=None,
                span_seconds=None,
            )

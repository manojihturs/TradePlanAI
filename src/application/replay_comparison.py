"""ReplayComparison: highlight differences between two ReplayResults.

Traceability
------------
Phase 3, Prompt 5: "Replay Comparison" (Product Mode). Read-only, no
calculation, never modifies either ``ReplayResult``. Every compared
value is read, not recomputed: Weekly Future/Strike/ORB/summary values
come from ``application.strategy_inspector.build_view`` (the same
last-candle "final state" read that screen already uses); timeline
statistics come from ``application.replay_event_model.build_statistics``
over a ``ReplayEventCollection`` built from each side's
``strategy_timeline`` - exactly the reuse the "Replay Event Model"
sprint set up this module to make possible.

Every difference is reported as a :class:`FieldDifference` - ``(field,
value_a, value_b, differs)`` - a uniform shape reused across every
section (Weekly Future, Strike, ORB, Duration, Pipeline Diagnostics)
so a caller (or exporter) doesn't need section-specific handling.
Timeline differences are aggregate/structural (event counts by type/
stage, breakout/breakdown counts, stages/event types unique to one
side) rather than an event-by-event diff - the two sessions' timelines
are not assumed to be the same length or aligned in time, so pairing
individual events would be inventing a matching rule with no evidence
behind it.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from application.replay_event_model import ReplayEventCollection, build_statistics
from application.replay_result import ReplayResult
from application.strategy_inspector import StrategyInspectorView, build_view

_CSV_HEADER = ("section", "field", "value_a", "value_b", "differs")


@dataclass(frozen=True, slots=True)
class FieldDifference:
    """One compared field's values from both sessions.

    Attributes:
        field: The field's name (e.g. ``"high"``, ``"top_strike"``).
        value_a: Session A's value, pre-stringified (or ``None``).
        value_b: Session B's value, pre-stringified (or ``None``).
        differs: Whether ``value_a != value_b``.
    """

    field: str
    value_a: str | None
    value_b: str | None
    differs: bool


@dataclass(frozen=True, slots=True)
class TimelineDifference:
    """Aggregate/structural differences between two sessions'
    strategy timelines - not an event-by-event diff, see module
    docstring.

    Attributes:
        total_events_a: Session A's total timeline event count.
        total_events_b: Session B's total timeline event count.
        event_counts_by_type_a: Session A's ``{event_type: count}``.
        event_counts_by_type_b: Session B's ``{event_type: count}``.
        breakout_count_a: Session A's ``BREAKOUT`` ORB event count.
        breakout_count_b: Session B's ``BREAKOUT`` ORB event count.
        breakdown_count_a: Session A's ``BREAKDOWN`` ORB event count.
        breakdown_count_b: Session B's ``BREAKDOWN`` ORB event count.
        stages_only_in_a: Stage names present in A but not B.
        stages_only_in_b: Stage names present in B but not A.
        event_types_only_in_a: Event type names present in A but not B.
        event_types_only_in_b: Event type names present in B but not A.
    """

    total_events_a: int
    total_events_b: int
    event_counts_by_type_a: dict[str, int]
    event_counts_by_type_b: dict[str, int]
    breakout_count_a: int
    breakout_count_b: int
    breakdown_count_a: int
    breakdown_count_b: int
    stages_only_in_a: tuple[str, ...]
    stages_only_in_b: tuple[str, ...]
    event_types_only_in_a: tuple[str, ...]
    event_types_only_in_b: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReplayComparisonReport:
    """The full read-only comparison of two ``ReplayResult``s.

    Attributes:
        dataset_id_a: Session A's ``ReplaySession.dataset_id``.
        dataset_id_b: Session B's ``ReplaySession.dataset_id``.
        weekly_future_differences: Weekly Future High/Low.
        strike_differences: Top/Bottom Strike.
        orb_differences: Opening High/Low/Range/Status.
        duration_differences: Replay/session duration and status.
        pipeline_diagnostics_differences: Succeeded/failed candle
            counts and pipeline status.
        timeline: Structural timeline comparison.
    """

    dataset_id_a: str
    dataset_id_b: str
    weekly_future_differences: tuple[FieldDifference, ...]
    strike_differences: tuple[FieldDifference, ...]
    orb_differences: tuple[FieldDifference, ...]
    duration_differences: tuple[FieldDifference, ...]
    pipeline_diagnostics_differences: tuple[FieldDifference, ...]
    timeline: TimelineDifference

    @property
    def has_differences(self) -> bool:
        """Whether any scalar field (Weekly Future/Strike/ORB/
        Duration/Pipeline Diagnostics) differs. Does not consider
        :attr:`timeline`, which is a structural summary, not a set of
        pass/fail fields."""
        return any(
            diff.differs
            for section in (
                self.weekly_future_differences,
                self.strike_differences,
                self.orb_differences,
                self.duration_differences,
                self.pipeline_diagnostics_differences,
            )
            for diff in section
        )


def _diff(field_name: str, value_a: object, value_b: object) -> FieldDifference:
    str_a = str(value_a) if value_a is not None else None
    str_b = str(value_b) if value_b is not None else None
    return FieldDifference(field=field_name, value_a=str_a, value_b=str_b, differs=str_a != str_b)


def _weekly_future_diffs(
    view_a: StrategyInspectorView, view_b: StrategyInspectorView
) -> tuple[FieldDifference, ...]:
    return (
        _diff("high", view_a.weekly_future.high, view_b.weekly_future.high),
        _diff("low", view_a.weekly_future.low, view_b.weekly_future.low),
    )


def _strike_diffs(
    view_a: StrategyInspectorView, view_b: StrategyInspectorView
) -> tuple[FieldDifference, ...]:
    return (
        _diff("top_strike", view_a.weekly_future.top_strike, view_b.weekly_future.top_strike),
        _diff(
            "bottom_strike",
            view_a.weekly_future.bottom_strike,
            view_b.weekly_future.bottom_strike,
        ),
    )


def _orb_diffs(
    view_a: StrategyInspectorView, view_b: StrategyInspectorView
) -> tuple[FieldDifference, ...]:
    status_a = view_a.orb.status.value if view_a.orb.status else None
    status_b = view_b.orb.status.value if view_b.orb.status else None
    return (
        _diff("opening_high", view_a.orb.opening_high, view_b.orb.opening_high),
        _diff("opening_low", view_a.orb.opening_low, view_b.orb.opening_low),
        _diff("range", view_a.orb.range, view_b.orb.range),
        _diff("status", status_a, status_b),
    )


def _duration_diffs(
    view_a: StrategyInspectorView, view_b: StrategyInspectorView
) -> tuple[FieldDifference, ...]:
    return (
        _diff(
            "session_duration_seconds",
            view_a.summary.session_duration_seconds,
            view_b.summary.session_duration_seconds,
        ),
        _diff(
            "replay_status",
            view_a.summary.replay_status.value,
            view_b.summary.replay_status.value,
        ),
    )


def _pipeline_diagnostics_diffs(
    result_a: ReplayResult, result_b: ReplayResult
) -> tuple[FieldDifference, ...]:
    return (
        _diff("succeeded_count", result_a.succeeded_count, result_b.succeeded_count),
        _diff("failed_count", result_a.failed_count, result_b.failed_count),
    )


def _timeline_diff(result_a: ReplayResult, result_b: ReplayResult) -> TimelineDifference:
    collection_a = ReplayEventCollection.from_timeline(result_a.strategy_timeline)
    collection_b = ReplayEventCollection.from_timeline(result_b.strategy_timeline)
    stats_a = build_statistics(collection_a)
    stats_b = build_statistics(collection_b)

    stages_a = set(collection_a.stages())
    stages_b = set(collection_b.stages())
    types_a = {event_type.value for event_type in collection_a.event_types()}
    types_b = {event_type.value for event_type in collection_b.event_types()}

    return TimelineDifference(
        total_events_a=stats_a.total_events,
        total_events_b=stats_b.total_events,
        event_counts_by_type_a=stats_a.event_counts_by_type,
        event_counts_by_type_b=stats_b.event_counts_by_type,
        breakout_count_a=stats_a.breakout_count,
        breakout_count_b=stats_b.breakout_count,
        breakdown_count_a=stats_a.breakdown_count,
        breakdown_count_b=stats_b.breakdown_count,
        stages_only_in_a=tuple(sorted(stages_a - stages_b)),
        stages_only_in_b=tuple(sorted(stages_b - stages_a)),
        event_types_only_in_a=tuple(sorted(types_a - types_b)),
        event_types_only_in_b=tuple(sorted(types_b - types_a)),
    )


def build_comparison(result_a: ReplayResult, result_b: ReplayResult) -> ReplayComparisonReport:
    """Build a :class:`ReplayComparisonReport` for ``result_a`` vs.
    ``result_b`` - reads only, recalculates nothing, mutates neither
    ``ReplayResult``."""
    view_a = build_view(result_a)
    view_b = build_view(result_b)

    return ReplayComparisonReport(
        dataset_id_a=result_a.session.dataset_id,
        dataset_id_b=result_b.session.dataset_id,
        weekly_future_differences=_weekly_future_diffs(view_a, view_b),
        strike_differences=_strike_diffs(view_a, view_b),
        orb_differences=_orb_diffs(view_a, view_b),
        duration_differences=_duration_diffs(view_a, view_b),
        pipeline_diagnostics_differences=_pipeline_diagnostics_diffs(result_a, result_b),
        timeline=_timeline_diff(result_a, result_b),
    )


def _section_rows(
    report: ReplayComparisonReport,
) -> tuple[tuple[str, str, str | None, str | None, bool], ...]:
    rows: list[tuple[str, str, str | None, str | None, bool]] = []
    for section_name, diffs in (
        ("weekly_future", report.weekly_future_differences),
        ("strike", report.strike_differences),
        ("orb", report.orb_differences),
        ("duration", report.duration_differences),
        ("pipeline_diagnostics", report.pipeline_diagnostics_differences),
    ):
        for diff in diffs:
            rows.append((section_name, diff.field, diff.value_a, diff.value_b, diff.differs))
    return tuple(rows)


def write_json(report: ReplayComparisonReport, path: Path) -> None:
    """Write ``report`` to a JSON file at ``path``."""

    def _section(diffs: tuple[FieldDifference, ...]) -> list[dict[str, Any]]:
        return [
            {"field": d.field, "value_a": d.value_a, "value_b": d.value_b, "differs": d.differs}
            for d in diffs
        ]

    payload = {
        "dataset_id_a": report.dataset_id_a,
        "dataset_id_b": report.dataset_id_b,
        "has_differences": report.has_differences,
        "weekly_future": _section(report.weekly_future_differences),
        "strike": _section(report.strike_differences),
        "orb": _section(report.orb_differences),
        "duration": _section(report.duration_differences),
        "pipeline_diagnostics": _section(report.pipeline_diagnostics_differences),
        "timeline": {
            "total_events_a": report.timeline.total_events_a,
            "total_events_b": report.timeline.total_events_b,
            "event_counts_by_type_a": report.timeline.event_counts_by_type_a,
            "event_counts_by_type_b": report.timeline.event_counts_by_type_b,
            "breakout_count_a": report.timeline.breakout_count_a,
            "breakout_count_b": report.timeline.breakout_count_b,
            "breakdown_count_a": report.timeline.breakdown_count_a,
            "breakdown_count_b": report.timeline.breakdown_count_b,
            "stages_only_in_a": list(report.timeline.stages_only_in_a),
            "stages_only_in_b": list(report.timeline.stages_only_in_b),
            "event_types_only_in_a": list(report.timeline.event_types_only_in_a),
            "event_types_only_in_b": list(report.timeline.event_types_only_in_b),
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(report: ReplayComparisonReport, path: Path) -> None:
    """Write ``report`` to a CSV file at ``path`` - one ``(section,
    field, value_a, value_b, differs)`` row per compared scalar field,
    plus a handful of ``timeline`` rows for the structural counts."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(_CSV_HEADER)
        for row in _section_rows(report):
            writer.writerow(row)
        writer.writerow(
            (
                "timeline",
                "total_events",
                report.timeline.total_events_a,
                report.timeline.total_events_b,
                report.timeline.total_events_a != report.timeline.total_events_b,
            )
        )
        writer.writerow(
            (
                "timeline",
                "breakout_count",
                report.timeline.breakout_count_a,
                report.timeline.breakout_count_b,
                report.timeline.breakout_count_a != report.timeline.breakout_count_b,
            )
        )
        writer.writerow(
            (
                "timeline",
                "breakdown_count",
                report.timeline.breakdown_count_a,
                report.timeline.breakdown_count_b,
                report.timeline.breakdown_count_a != report.timeline.breakdown_count_b,
            )
        )


def write_excel(report: ReplayComparisonReport, path: Path) -> None:
    """Write ``report`` to a 2-sheet ``.xlsx`` workbook at ``path`` -
    "Differences" (every scalar field, both sessions' values, and
    whether they differ) and "Timeline" (the structural comparison)."""
    workbook = Workbook()

    diffs_sheet = workbook.active
    assert diffs_sheet is not None  # a freshly constructed Workbook always has an active sheet
    diffs_sheet.title = "Differences"
    diffs_sheet.append(["Section", "Field", "Value A", "Value B", "Differs"])
    for row in _section_rows(report):
        diffs_sheet.append(list(row))

    timeline_sheet = workbook.create_sheet("Timeline")
    timeline_sheet.append(["Metric", "Session A", "Session B"])
    timeline_sheet.append(
        ["total_events", report.timeline.total_events_a, report.timeline.total_events_b]
    )
    timeline_sheet.append(
        ["breakout_count", report.timeline.breakout_count_a, report.timeline.breakout_count_b]
    )
    timeline_sheet.append(
        ["breakdown_count", report.timeline.breakdown_count_a, report.timeline.breakdown_count_b]
    )
    timeline_sheet.append(["stages_only_in_a", "; ".join(report.timeline.stages_only_in_a), ""])
    timeline_sheet.append(["stages_only_in_b", "", "; ".join(report.timeline.stages_only_in_b)])
    timeline_sheet.append(
        [
            "event_types_only_in_a",
            "; ".join(report.timeline.event_types_only_in_a),
            "",
        ]
    )
    timeline_sheet.append(
        [
            "event_types_only_in_b",
            "",
            "; ".join(report.timeline.event_types_only_in_b),
        ]
    )

    workbook.save(str(path))


class ReplayComparison:
    """Read-only facade comparing two ``ReplayResult``s. Never
    mutates either result; builds its :class:`ReplayComparisonReport`
    once, at construction."""

    def __init__(self, result_a: ReplayResult, result_b: ReplayResult) -> None:
        self._report = build_comparison(result_a, result_b)

    @property
    def report(self) -> ReplayComparisonReport:
        return self._report

    def export_json(self, path: Path) -> None:
        write_json(self._report, path)

    def export_csv(self, path: Path) -> None:
        write_csv(self._report, path)

    def export_excel(self, path: Path) -> None:
        write_excel(self._report, path)

"""StrategyInspector: the primary read-only analysis screen for a ReplayResult.

Traceability
------------
Sprint: "Strategy Inspector" (Product Mode). Read-only, no business
calculation, never mutates the ``application.replay_result.ReplayResult``
it's built from - every value here is a direct read of a field that
``business.pipeline_context.PipelineContext``/
``application.replay_session.ReplaySession`` already carries, taken
from the *last* candle in ``result.business_results`` (the most
complete/final state of the session - Reference Level/Weekly
Future/Strike Selection are constant after their first candle per
Specification Rule 1, and ORB's Breakout Status is whatever it last
resolved to). If ``business_results`` is empty, every section field is
``None`` - a real, reportable state (e.g. zero stages registered),
not an error.

Sections mirror the sprint's own instruction exactly: Replay Summary,
Reference Levels, Weekly Future, ORB, Timeline. "Pipeline Status" is
``"PASSED"`` only if every candle's ``BusinessResult.success`` was
``True``, otherwise ``"FAILED"`` - distinct from "Replay Status"
(``application.replay_session.ReplayStatus``, the run's own lifecycle
state, e.g. ``COMPLETED``), since a replay can complete its lifecycle
while individual candles still failed.

Timeline is exposed as-is from ``result.strategy_timeline`` (already
chronologically ordered by
``application.strategy_timeline.build_strategy_timeline`` - "allow
chronological iteration" is satisfied by iterating
``StrategyInspectorView.timeline.events`` directly, no new ordering
logic).

Excel export uses ``openpyxl.Workbook``, matching this repository's
existing precedent (``application.trading_analysis_dashboard.write_excel``,
itself matching ``strategy/multi_day_backtest.py``).
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from application.replay_result import ReplayResult
from application.replay_session import ReplayStatus
from application.strategy_timeline import StrategyTimeline
from core.enums import ORBStatus
from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel

_STATUS_PASSED = "PASSED"
_STATUS_FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ReplaySummarySection:
    """Attributes:
    trading_date: The final candle's calendar date, or ``None``.
    session_duration_seconds: ``ReplaySession.duration_seconds``.
    replay_status: The session's own lifecycle status.
    pipeline_status: ``"PASSED"``/``"FAILED"`` - see module docstring.
    """

    trading_date: date | None
    session_duration_seconds: float | None
    replay_status: ReplayStatus
    pipeline_status: str


@dataclass(frozen=True, slots=True)
class ReferenceLevelsSection:
    """Attributes:
    atm: The session's ATM/anchor strike, or ``None``.
    ladder: The 13-level reference ladder, or empty.
    """

    atm: Decimal | None
    ladder: tuple[ReferenceLevel, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class WeeklyFutureSection:
    """Attributes: Weekly Future High/Low and Top/Bottom Strike, or
    all ``None`` if the stage never ran."""

    high: Decimal | None
    low: Decimal | None
    top_strike: Decimal | None
    bottom_strike: Decimal | None


@dataclass(frozen=True, slots=True)
class ORBSection:
    """Attributes: Opening High/Low/Range and Breakout Status, or all
    ``None`` if the stage never ran."""

    opening_high: Decimal | None
    opening_low: Decimal | None
    range: Decimal | None
    status: ORBStatus | None


@dataclass(frozen=True, slots=True)
class StrategyInspectorView:
    """The full read-only rendering of one ``ReplayResult``.

    Attributes:
        summary: Replay Summary section.
        reference_levels: Reference Levels section.
        weekly_future: Weekly Future section.
        orb: ORB section.
        timeline: The session's chronological event log, unchanged
            from ``ReplayResult.strategy_timeline``.
    """

    summary: ReplaySummarySection
    reference_levels: ReferenceLevelsSection
    weekly_future: WeeklyFutureSection
    orb: ORBSection
    timeline: StrategyTimeline

    def __post_init__(self) -> None:
        if self.summary is None:
            raise ValidationError("StrategyInspectorView.summary must not be None.")


def build_view(result: ReplayResult) -> StrategyInspectorView:
    """Build a :class:`StrategyInspectorView` from ``result`` - reads
    only, never recalculates, never mutates ``result``."""
    last_context = result.business_results[-1].context if result.business_results else None

    pipeline_status = (
        _STATUS_PASSED if result.business_results and result.failed_count == 0 else _STATUS_FAILED
    )

    summary = ReplaySummarySection(
        trading_date=last_context.candle_timestamp.date() if last_context else None,
        session_duration_seconds=result.session.duration_seconds,
        replay_status=result.session.status,
        pipeline_status=pipeline_status,
    )
    reference_levels = ReferenceLevelsSection(
        atm=last_context.reference_strike if last_context else None,
        ladder=last_context.reference_data if last_context else (),
    )
    weekly_future_value = last_context.weekly_future if last_context else None
    strike_value = last_context.selected_strike if last_context else None
    weekly_future = WeeklyFutureSection(
        high=weekly_future_value.high if weekly_future_value else None,
        low=weekly_future_value.low if weekly_future_value else None,
        top_strike=strike_value.top_strike if strike_value else None,
        bottom_strike=strike_value.bottom_strike if strike_value else None,
    )
    orb_value = last_context.orb_result if last_context else None
    orb = ORBSection(
        opening_high=orb_value.opening_high if orb_value else None,
        opening_low=orb_value.opening_low if orb_value else None,
        range=orb_value.range if orb_value else None,
        status=orb_value.status if orb_value else None,
    )

    return StrategyInspectorView(
        summary=summary,
        reference_levels=reference_levels,
        weekly_future=weekly_future,
        orb=orb,
        timeline=result.strategy_timeline,
    )


def _summary_rows(view: StrategyInspectorView) -> tuple[tuple[str, str, object], ...]:
    """Every scalar field across the four non-timeline sections, as
    ``(section, field, value)`` triples - shared by the CSV/Excel/JSON
    exporters below."""
    return (
        ("replay_summary", "trading_date", view.summary.trading_date),
        ("replay_summary", "session_duration_seconds", view.summary.session_duration_seconds),
        ("replay_summary", "replay_status", view.summary.replay_status.value),
        ("replay_summary", "pipeline_status", view.summary.pipeline_status),
        ("reference_levels", "atm", view.reference_levels.atm),
        ("reference_levels", "ladder_size", len(view.reference_levels.ladder)),
        ("weekly_future", "high", view.weekly_future.high),
        ("weekly_future", "low", view.weekly_future.low),
        ("weekly_future", "top_strike", view.weekly_future.top_strike),
        ("weekly_future", "bottom_strike", view.weekly_future.bottom_strike),
        ("orb", "opening_high", view.orb.opening_high),
        ("orb", "opening_low", view.orb.opening_low),
        ("orb", "range", view.orb.range),
        ("orb", "status", view.orb.status.value if view.orb.status else None),
    )


def write_json(view: StrategyInspectorView, path: Path) -> None:
    """Write ``view`` to a JSON file at ``path`` - one object per
    section, plus the timeline as a list of event objects."""
    payload = {
        "replay_summary": {
            "trading_date": (
                view.summary.trading_date.isoformat() if view.summary.trading_date else None
            ),
            "session_duration_seconds": view.summary.session_duration_seconds,
            "replay_status": view.summary.replay_status.value,
            "pipeline_status": view.summary.pipeline_status,
        },
        "reference_levels": {
            "atm": str(view.reference_levels.atm) if view.reference_levels.atm else None,
            "ladder": [
                {
                    "strike": str(level.strike),
                    "ce_high": str(level.ce_high),
                    "ce_low": str(level.ce_low),
                    "pe_high": str(level.pe_high),
                    "pe_low": str(level.pe_low),
                }
                for level in view.reference_levels.ladder
            ],
        },
        "weekly_future": {
            "high": str(view.weekly_future.high) if view.weekly_future.high is not None else None,
            "low": str(view.weekly_future.low) if view.weekly_future.low is not None else None,
            "top_strike": (
                str(view.weekly_future.top_strike)
                if view.weekly_future.top_strike is not None
                else None
            ),
            "bottom_strike": (
                str(view.weekly_future.bottom_strike)
                if view.weekly_future.bottom_strike is not None
                else None
            ),
        },
        "orb": {
            "opening_high": (
                str(view.orb.opening_high) if view.orb.opening_high is not None else None
            ),
            "opening_low": (
                str(view.orb.opening_low) if view.orb.opening_low is not None else None
            ),
            "range": str(view.orb.range) if view.orb.range is not None else None,
            "status": view.orb.status.value if view.orb.status else None,
        },
        "timeline": [
            {
                "timestamp": event.timestamp.isoformat(),
                "trading_date": event.trading_date.isoformat(),
                "stage": event.stage,
                "event_type": event.event_type.value,
                "summary": event.summary,
                "payload": event.payload,
            }
            for event in view.timeline.events
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(view: StrategyInspectorView, path: Path) -> None:
    """Write ``view`` to a CSV file at ``path`` - one ``(section,
    field, value)`` row per scalar, one ``reference_ladder`` row per
    strike level, one ``timeline`` row per event."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(("section", "field", "value"))
        for section, field_name, value in _summary_rows(view):
            writer.writerow((section, field_name, value))
        for level in view.reference_levels.ladder:
            writer.writerow(
                (
                    "reference_ladder",
                    str(level.strike),
                    (
                        f"ce_high={level.ce_high}; ce_low={level.ce_low}; "
                        f"pe_high={level.pe_high}; pe_low={level.pe_low}"
                    ),
                )
            )
        for event in view.timeline.events:
            writer.writerow(
                (
                    "timeline",
                    f"{event.timestamp.isoformat()} {event.event_type.value}",
                    event.summary,
                )
            )


def write_excel(view: StrategyInspectorView, path: Path) -> None:
    """Write ``view`` to a 3-sheet ``.xlsx`` workbook at ``path`` -
    "Summary", "Reference Ladder", "Timeline" - overwritten if it
    already exists."""
    workbook = Workbook()

    summary_sheet = workbook.active
    assert summary_sheet is not None  # a freshly constructed Workbook always has an active sheet
    summary_sheet.title = "Summary"
    summary_sheet.append(["Section", "Field", "Value"])
    for section, field_name, value in _summary_rows(view):
        summary_sheet.append([section, field_name, value])

    ladder_sheet = workbook.create_sheet("Reference Ladder")
    ladder_sheet.append(["Strike", "CE High", "CE Low", "PE High", "PE Low"])
    for level in view.reference_levels.ladder:
        ladder_sheet.append(
            [str(level.strike), level.ce_high, level.ce_low, level.pe_high, level.pe_low]
        )

    timeline_sheet = workbook.create_sheet("Timeline")
    timeline_sheet.append(["Timestamp", "Trading Date", "Stage", "Event Type", "Summary"])
    for event in view.timeline.events:
        timeline_sheet.append(
            [
                event.timestamp.isoformat(),
                event.trading_date.isoformat(),
                event.stage,
                event.event_type.value,
                event.summary,
            ]
        )

    workbook.save(str(path))


class StrategyInspector:
    """Read-only facade over a single ``ReplayResult`` - the primary
    analysis screen every future engine's output will also appear
    through, once wired into ``PipelineContext``.

    Never recalculates a value and never mutates the ``ReplayResult``
    it was built from.
    """

    def __init__(self, result: ReplayResult) -> None:
        self._result = result
        self._view = build_view(result)

    @property
    def view(self) -> StrategyInspectorView:
        return self._view

    def export_json(self, path: Path) -> None:
        write_json(self._view, path)

    def export_csv(self, path: Path) -> None:
        write_csv(self._view, path)

    def export_excel(self, path: Path) -> None:
        write_excel(self._view, path)

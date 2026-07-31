"""ReplaySessionExplorer: an interactive, read-only debugger over a ReplayResult.

Traceability
------------
Phase 3, Prompt 3: "Replay Session Explorer" (Product Mode). No
business calculation, no pipeline execution, and
``application.replay_result.ReplayResult`` is never mutated - the
explorer navigates and filters
``ReplayResult.strategy_timeline.events`` (already built by
``application.strategy_timeline.build_strategy_timeline``), keeping
its own cursor (``_index``) and filter (``ExplorerFilter``) as
private, mutable *explorer* state, entirely separate from the
immutable ``ReplayResult`` it reads. This is deliberately a different
tool from ``application.strategy_inspector.StrategyInspector`` (the
session's *final-state* summary screen) - the Explorer instead lets a
developer step through the timeline exactly as the pipeline produced
it, one event at a time.

Navigation is always computed against the *currently filtered* view
(``self._filtered_events``), never the raw, unfiltered timeline - so
``next()``/``previous()`` "respect active filters" by construction,
not as a special case. Every navigation method clamps its resulting
index into ``[0, len(filtered_events) - 1]`` (or returns an
all-``None`` :class:`ReplaySessionState` if the filtered view is
empty) - out-of-range navigation never raises.

Export re-reads deliberately reuse
``application.strategy_timeline.write_timeline_json``/``write_timeline_csv``
for the *filtered* exports (wrapping the filtered events in a fresh
``StrategyTimeline`` - no serialization logic is duplicated); the
*current* exports (previous/current/next) have their own small
writers below, since that shape (three rows plus cursor metadata) is
specific to this module.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from application.replay_result import ReplayResult
from application.strategy_timeline import (
    StrategyTimeline,
    TimelineEvent,
    write_timeline_csv,
    write_timeline_json,
)
from core.enums import ORBStatus, TimelineEventType

_CURRENT_VIEW_HEADER = ("role", "timestamp", "trading_date", "stage", "event_type", "summary")


@dataclass(frozen=True, slots=True)
class ExplorerFilter:
    """Optional predicates narrowing which timeline events the
    Explorer navigates/searches over. Every field is optional; an
    unset field imposes no constraint. Never applied to
    ``ReplayResult`` itself - only to the Explorer's own view.

    Attributes:
        stage: Keep only events whose ``stage`` equals this value.
        event_type: Keep only events of this
            :class:`~core.enums.TimelineEventType`.
        start_time: Keep only events at or after this timestamp.
        end_time: Keep only events at or before this timestamp.
        orb_status: Keep only ``ORB_CALCULATED`` events whose payload
            ``status`` equals this value - every other event type is
            excluded when this is set (see :meth:`ReplaySessionExplorer.filter_breakouts_only`).
    """

    stage: str | None = None
    event_type: TimelineEventType | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    orb_status: ORBStatus | None = None

    def matches(self, event: TimelineEvent) -> bool:
        if self.stage is not None and event.stage != self.stage:
            return False
        if self.event_type is not None and event.event_type != self.event_type:
            return False
        if self.start_time is not None and event.timestamp < self.start_time:
            return False
        if self.end_time is not None and event.timestamp > self.end_time:
            return False
        if self.orb_status is not None:
            if event.event_type != TimelineEventType.ORB_CALCULATED:
                return False
            if event.payload.get("status") != self.orb_status.value:
                return False
        return True


@dataclass(frozen=True, slots=True)
class ReplaySessionState:
    """The Explorer's current position within the (filtered) timeline.

    Every field is ``None`` together when the filtered view is empty
    - a real, reportable state (e.g. a filter matching nothing), not
    an error.

    Attributes:
        current_event_index: Index into the filtered event list.
        current_event: The event at that index.
        previous_event: The prior event in the filtered list, or
            ``None`` if ``current_event`` is first.
        next_event: The following event in the filtered list, or
            ``None`` if ``current_event`` is last.
        current_stage: ``current_event.stage``, restated for
            convenience.
        current_timestamp: ``current_event.timestamp``, restated for
            convenience.
    """

    current_event_index: int | None
    current_event: TimelineEvent | None
    previous_event: TimelineEvent | None
    next_event: TimelineEvent | None
    current_stage: str | None
    current_timestamp: datetime | None


_EMPTY_STATE = ReplaySessionState(None, None, None, None, None, None)


class ReplaySessionExplorer:
    """An interactive, read-only cursor over one ``ReplayResult``'s
    strategy timeline.

    Constructor-injected ``ReplayResult`` only - never mutated. All
    cursor/filter state lives on the Explorer instance itself.
    """

    def __init__(self, result: ReplayResult) -> None:
        self._result = result
        self._all_events = result.strategy_timeline.events
        self._filter = ExplorerFilter()
        self._index = 0

    @classmethod
    def create(cls, result: ReplayResult) -> ReplaySessionExplorer:
        return cls(result)

    @property
    def filter(self) -> ExplorerFilter:
        return self._filter

    @property
    def _filtered_events(self) -> tuple[TimelineEvent, ...]:
        return tuple(event for event in self._all_events if self._filter.matches(event))

    def _state_at(self, index: int) -> ReplaySessionState:
        events = self._filtered_events
        if not events:
            return _EMPTY_STATE
        clamped = max(0, min(index, len(events) - 1))
        current = events[clamped]
        previous = events[clamped - 1] if clamped > 0 else None
        following = events[clamped + 1] if clamped < len(events) - 1 else None
        return ReplaySessionState(
            current_event_index=clamped,
            current_event=current,
            previous_event=previous,
            next_event=following,
            current_stage=current.stage,
            current_timestamp=current.timestamp,
        )

    def _move_to(self, index: int) -> ReplaySessionState:
        state = self._state_at(index)
        self._index = state.current_event_index if state.current_event_index is not None else 0
        return state

    # -- Navigation -----------------------------------------------------

    def current(self) -> ReplaySessionState:
        return self._move_to(self._index)

    def next(self) -> ReplaySessionState:
        return self._move_to(self._index + 1)

    def previous(self) -> ReplaySessionState:
        return self._move_to(self._index - 1)

    def jump_to_event(self, index: int) -> ReplaySessionState:
        return self._move_to(index)

    def jump_to_timestamp(self, timestamp: datetime) -> ReplaySessionState:
        """Move to the event nearest ``timestamp`` in the filtered
        view (exact match if one exists)."""
        events = self._filtered_events
        if not events:
            return self._move_to(self._index)
        nearest = min(
            range(len(events)),
            key=lambda i: abs((events[i].timestamp - timestamp).total_seconds()),
        )
        return self._move_to(nearest)

    def jump_to_stage(self, stage_name: str) -> ReplaySessionState:
        """Move to the first event whose ``stage`` equals
        ``stage_name`` in the filtered view. No match leaves the
        cursor where it was."""
        for index, event in enumerate(self._filtered_events):
            if event.stage == stage_name:
                return self._move_to(index)
        return self.current()

    def reset(self) -> ReplaySessionState:
        """Move the cursor back to the first event in the filtered
        view. Does not clear filters - see :meth:`clear_filters`."""
        return self._move_to(0)

    # -- Filtering --------------------------------------------------------

    def filter_by_stage(self, stage_name: str) -> ReplaySessionState:
        self._filter = replace(self._filter, stage=stage_name)
        return self.current()

    def filter_by_event_type(self, event_type: TimelineEventType) -> ReplaySessionState:
        self._filter = replace(self._filter, event_type=event_type)
        return self.current()

    def filter_by_time_range(self, start: datetime, end: datetime) -> ReplaySessionState:
        self._filter = replace(self._filter, start_time=start, end_time=end)
        return self.current()

    def filter_breakouts_only(self) -> ReplaySessionState:
        self._filter = replace(self._filter, orb_status=ORBStatus.BREAKOUT)
        return self.current()

    def filter_breakdowns_only(self) -> ReplaySessionState:
        self._filter = replace(self._filter, orb_status=ORBStatus.BREAKDOWN)
        return self.current()

    def clear_filters(self) -> ReplaySessionState:
        self._filter = ExplorerFilter()
        return self.current()

    # -- Search (read-only, does not move the cursor) ---------------------

    def search_text(self, text: str) -> tuple[TimelineEvent, ...]:
        """Every filtered event whose ``summary`` contains ``text``
        (case-insensitive)."""
        needle = text.lower()
        return tuple(event for event in self._filtered_events if needle in event.summary.lower())

    def search_strike(self, strike: Decimal) -> tuple[TimelineEvent, ...]:
        """Every filtered event whose payload carries ``strike`` as a
        value (e.g. an ORB event's ``strike``, a Strike Selected
        event's ``top_strike``/``bottom_strike``)."""
        needle = str(strike)
        return tuple(event for event in self._filtered_events if needle in event.payload.values())

    def search_timestamp(self, timestamp: datetime) -> tuple[TimelineEvent, ...]:
        """Every filtered event at exactly ``timestamp``."""
        return tuple(event for event in self._filtered_events if event.timestamp == timestamp)

    # -- Export -------------------------------------------------------------

    def export_current_json(self, path: Path) -> None:
        write_current_view_json(self.current(), path)

    def export_current_csv(self, path: Path) -> None:
        write_current_view_csv(self.current(), path)

    def export_current_excel(self, path: Path) -> None:
        write_current_view_excel(self.current(), path)

    def export_filtered_json(self, path: Path) -> None:
        write_timeline_json(StrategyTimeline(events=self._filtered_events), path)

    def export_filtered_csv(self, path: Path) -> None:
        write_timeline_csv(StrategyTimeline(events=self._filtered_events), path)

    def export_filtered_excel(self, path: Path) -> None:
        write_filtered_view_excel(self._filtered_events, path)


def _event_to_dict(event: TimelineEvent | None) -> dict[str, object] | None:
    if event is None:
        return None
    return {
        "timestamp": event.timestamp.isoformat(),
        "trading_date": event.trading_date.isoformat(),
        "stage": event.stage,
        "event_type": event.event_type.value,
        "summary": event.summary,
        "payload": event.payload,
    }


def write_current_view_json(state: ReplaySessionState, path: Path) -> None:
    """Write ``state`` (previous/current/next events plus cursor
    metadata) to a JSON file at ``path``."""
    payload = {
        "current_event_index": state.current_event_index,
        "current_stage": state.current_stage,
        "current_timestamp": (
            state.current_timestamp.isoformat() if state.current_timestamp else None
        ),
        "previous_event": _event_to_dict(state.previous_event),
        "current_event": _event_to_dict(state.current_event),
        "next_event": _event_to_dict(state.next_event),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_current_view_csv(state: ReplaySessionState, path: Path) -> None:
    """Write ``state`` to a CSV file at ``path`` - one row each for
    previous/current/next (a blank row if that slot is ``None``)."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(_CURRENT_VIEW_HEADER)
        for role, event in (
            ("previous", state.previous_event),
            ("current", state.current_event),
            ("next", state.next_event),
        ):
            if event is None:
                writer.writerow((role, "", "", "", "", ""))
            else:
                writer.writerow(
                    (
                        role,
                        event.timestamp.isoformat(),
                        event.trading_date.isoformat(),
                        event.stage,
                        event.event_type.value,
                        event.summary,
                    )
                )


def write_current_view_excel(state: ReplaySessionState, path: Path) -> None:
    """Write ``state`` to a single-sheet ``.xlsx`` workbook at
    ``path``, mirroring :func:`write_current_view_csv`'s rows."""
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None  # a freshly constructed Workbook always has an active sheet
    sheet.title = "Current View"
    sheet.append(list(_CURRENT_VIEW_HEADER))
    for role, event in (
        ("previous", state.previous_event),
        ("current", state.current_event),
        ("next", state.next_event),
    ):
        if event is None:
            sheet.append([role, "", "", "", "", ""])
        else:
            sheet.append(
                [
                    role,
                    event.timestamp.isoformat(),
                    event.trading_date.isoformat(),
                    event.stage,
                    event.event_type.value,
                    event.summary,
                ]
            )
    workbook.save(str(path))


def write_filtered_view_excel(events: tuple[TimelineEvent, ...], path: Path) -> None:
    """Write ``events`` to a single-sheet ``.xlsx`` workbook at
    ``path`` - one row per event, in order."""
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None  # a freshly constructed Workbook always has an active sheet
    sheet.title = "Filtered Timeline"
    sheet.append(["Timestamp", "Trading Date", "Stage", "Event Type", "Summary"])
    for event in events:
        sheet.append(
            [
                event.timestamp.isoformat(),
                event.trading_date.isoformat(),
                event.stage,
                event.event_type.value,
                event.summary,
            ]
        )
    workbook.save(str(path))

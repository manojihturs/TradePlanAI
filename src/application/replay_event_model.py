"""ReplayEvent model: a shared, reusable event abstraction over a StrategyTimeline.

Traceability
------------
Phase 3, Prompt 4: "Replay Event Model" (Product Mode) - a shared
foundation so Replay Comparison and Replay Analytics don't each
reimplement the filtering/search logic
``application.replay_session_explorer`` already built. No new event
*shape* is invented: ``application.strategy_timeline.TimelineEvent``
already is the shared event abstraction (timestamp, stage,
event_type, summary, structured payload) - ``ReplayEvent`` below is a
plain alias for it, not a duplicate type.

- :class:`ReplayEventCollection`: an immutable, ordered set of events
  (e.g. "every event in session A") - the type Replay Comparison will
  hold one of per compared session.
- :class:`ReplayEventQuery`: a fluent, reusable filter/search builder
  over a :class:`ReplayEventCollection` - the same vocabulary
  ``application.replay_session_explorer.ExplorerFilter``/its search
  methods already use (stage/event type/time range/ORB status/text/
  strike/timestamp), generalized so it isn't tied to a cursor and can
  be applied to any collection, reused across sessions.
- :func:`build_statistics`/:class:`ReplayEventStatistics`: aggregate
  counts/timings over a :class:`ReplayEventCollection` - the type
  Replay Analytics will build its report from.

Not yet wired into ``ReplaySessionExplorer``'s own ``ExplorerFilter``
(that remains its own, already-tested implementation) - this module
is the shared foundation the *future* consumers (Comparison,
Analytics) will use; "Explorer uses ``ReplayEventQuery``" is the
longer-term target this lays the groundwork for, not a requirement of
this sprint.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal

from application.strategy_timeline import StrategyTimeline, TimelineEvent
from core.enums import ORBStatus, TimelineEventType
from core.exceptions import ValidationError

#: The shared event type every consumer below operates on - an alias,
#: not a new dataclass. See module docstring.
ReplayEvent = TimelineEvent


@dataclass(frozen=True, slots=True)
class ReplayEventCollection:
    """An immutable, ordered collection of :data:`ReplayEvent`.

    Attributes:
        events: The events themselves, in whatever order supplied
            (typically chronological, matching
            ``application.strategy_timeline.StrategyTimeline``).
    """

    events: tuple[ReplayEvent, ...] = field(default_factory=tuple)

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self) -> Iterator[ReplayEvent]:
        return iter(self.events)

    def __getitem__(self, index: int) -> ReplayEvent:
        return self.events[index]

    @classmethod
    def from_timeline(cls, timeline: StrategyTimeline) -> ReplayEventCollection:
        """Build a collection from an already-built
        ``application.strategy_timeline.StrategyTimeline`` - no new
        events are computed."""
        return cls(events=timeline.events)

    @property
    def is_empty(self) -> bool:
        return len(self.events) == 0

    def first(self) -> ReplayEvent | None:
        return self.events[0] if self.events else None

    def last(self) -> ReplayEvent | None:
        return self.events[-1] if self.events else None

    def stages(self) -> tuple[str, ...]:
        """Every distinct ``stage`` present, in first-seen order."""
        seen: list[str] = []
        for event in self.events:
            if event.stage not in seen:
                seen.append(event.stage)
        return tuple(seen)

    def event_types(self) -> tuple[TimelineEventType, ...]:
        """Every distinct ``event_type`` present, in first-seen order."""
        seen: list[TimelineEventType] = []
        for event in self.events:
            if event.event_type not in seen:
                seen.append(event.event_type)
        return tuple(seen)


@dataclass(frozen=True, slots=True)
class ReplayEventQuery:
    """A fluent, reusable filter/search builder over a
    :class:`ReplayEventCollection`. Every field is optional; an unset
    field imposes no constraint. Chainable - each ``by_*``/
    ``containing_*``/``at_*`` method returns a *new* query, the
    original is never mutated.

    Attributes:
        stage: Keep only events whose ``stage`` equals this value.
        event_type: Keep only events of this
            :class:`~core.enums.TimelineEventType`.
        start_time: Keep only events at or after this timestamp.
        end_time: Keep only events at or before this timestamp.
        orb_status: Keep only ``ORB_CALCULATED`` events whose payload
            ``status`` equals this value.
        text: Keep only events whose ``summary`` contains this text
            (case-insensitive).
        strike: Keep only events whose payload carries this strike as
            a value.
        timestamp: Keep only events at exactly this timestamp.
    """

    stage: str | None = None
    event_type: TimelineEventType | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    orb_status: ORBStatus | None = None
    text: str | None = None
    strike: Decimal | None = None
    timestamp: datetime | None = None

    def by_stage(self, stage: str) -> ReplayEventQuery:
        return replace(self, stage=stage)

    def by_event_type(self, event_type: TimelineEventType) -> ReplayEventQuery:
        return replace(self, event_type=event_type)

    def by_time_range(self, start: datetime, end: datetime) -> ReplayEventQuery:
        return replace(self, start_time=start, end_time=end)

    def by_orb_status(self, status: ORBStatus) -> ReplayEventQuery:
        return replace(self, orb_status=status)

    def containing_text(self, text: str) -> ReplayEventQuery:
        return replace(self, text=text)

    def containing_strike(self, strike: Decimal) -> ReplayEventQuery:
        return replace(self, strike=strike)

    def at_timestamp(self, timestamp: datetime) -> ReplayEventQuery:
        return replace(self, timestamp=timestamp)

    def matches(self, event: ReplayEvent) -> bool:
        """Whether ``event`` satisfies every constraint set on this query."""
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
        if self.text is not None and self.text.lower() not in event.summary.lower():
            return False
        if self.strike is not None and str(self.strike) not in event.payload.values():
            return False
        return self.timestamp is None or event.timestamp == self.timestamp

    def apply(self, collection: ReplayEventCollection) -> ReplayEventCollection:
        """Return a new :class:`ReplayEventCollection` containing only
        the events in ``collection`` this query matches - ``collection``
        itself is never modified."""
        return ReplayEventCollection(
            events=tuple(event for event in collection.events if self.matches(event))
        )


@dataclass(frozen=True, slots=True)
class ReplayEventStatistics:
    """Aggregate counts/timings over a :class:`ReplayEventCollection`.

    Attributes:
        total_events: How many events the collection held.
        event_counts_by_type: ``{event_type.value: count}``.
        event_counts_by_stage: ``{stage: count}``.
        breakout_count: How many ``ORB_CALCULATED`` events had
            ``BREAKOUT`` status.
        breakdown_count: How many had ``BREAKDOWN`` status.
        first_timestamp: The earliest event's timestamp, or ``None``.
        last_timestamp: The latest event's timestamp, or ``None``.
        span_seconds: ``last_timestamp - first_timestamp`` in seconds,
            or ``None`` if the collection is empty.
    """

    total_events: int
    event_counts_by_type: dict[str, int]
    event_counts_by_stage: dict[str, int]
    breakout_count: int
    breakdown_count: int
    first_timestamp: datetime | None
    last_timestamp: datetime | None
    span_seconds: float | None

    def __post_init__(self) -> None:
        if self.total_events < 0:
            raise ValidationError("ReplayEventStatistics.total_events must not be negative.")


def build_statistics(collection: ReplayEventCollection) -> ReplayEventStatistics:
    """Build a :class:`ReplayEventStatistics` from ``collection`` -
    read-only, no value is recomputed, only counted/aggregated."""
    by_type: dict[str, int] = {}
    by_stage: dict[str, int] = {}
    breakout_count = 0
    breakdown_count = 0

    for event in collection.events:
        by_type[event.event_type.value] = by_type.get(event.event_type.value, 0) + 1
        by_stage[event.stage] = by_stage.get(event.stage, 0) + 1
        if event.event_type == TimelineEventType.ORB_CALCULATED:
            status = event.payload.get("status")
            if status == ORBStatus.BREAKOUT.value:
                breakout_count += 1
            elif status == ORBStatus.BREAKDOWN.value:
                breakdown_count += 1

    first_event = collection.first()
    last_event = collection.last()
    first_timestamp = first_event.timestamp if first_event else None
    last_timestamp = last_event.timestamp if last_event else None
    span_seconds = (
        (last_timestamp - first_timestamp).total_seconds()
        if first_timestamp is not None and last_timestamp is not None
        else None
    )

    return ReplayEventStatistics(
        total_events=len(collection),
        event_counts_by_type=by_type,
        event_counts_by_stage=by_stage,
        breakout_count=breakout_count,
        breakdown_count=breakdown_count,
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
        span_seconds=span_seconds,
    )

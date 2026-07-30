"""StrategyTimeline / TimelineEvent: chronological audit trail over a replay.

Traceability
------------
Sprint: "Strategy Timeline" (Delivery Mode) - observability only, no
new business logic. Built from an already-completed sequence of
``business.business_result.BusinessResult`` (one per candle) - the
same already-computed ``business.pipeline_context.PipelineContext``
fields every other reporting module in this package reads
(``application.replay_report``, ``application.replay_dashboard``,
etc.), reshaped into a chronological event log rather than a table.

Event semantics
----------------
- ``REFERENCE_LEVEL_CREATED`` / ``WEEKLY_FUTURE_CALCULATED`` /
  ``STRIKE_SELECTED``: emitted **once**, at the first candle where
  that field appears - these are session-level facts, computed once
  and constant afterward (Specification Rule 1's "first candle"
  semantics), so repeating them every candle would just be noise.
- ``ORB_CALCULATED``: emitted **once per candle** where an
  ``orb_result`` is present, since (unlike Weekly Future/Strike) its
  Breakout Status can genuinely change as later candles accumulate
  (see ``business.stages.orb_stage.ORBStage``) - each occurrence is a
  real state change worth recording, not noise.
- ``PIPELINE_ERROR``: emitted once per candle whose ``BusinessResult``
  was not successful, carrying the same error-text convention
  ``application.replay_validation`` already uses (``"UNRESOLVED"`` for
  a graceful stop, otherwise ``str(BusinessResult.error)``) - and,
  when available, the specific failing stage's name from
  ``BusinessResult.stage_diagnostics`` (added by the earlier "Pipeline
  Diagnostics" sprint), not just a generic label.
- ``REPLAY_FINISHED``: emitted once, after every candle, summarizing
  succeeded/failed counts.

``TimelineEvent.payload`` values are pre-stringified (never raw
``Decimal``/``Enum``), so JSON/CSV export needs no further conversion.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from business.business_result import BusinessResult
from core.enums import TimelineEventType
from core.exceptions import ValidationError

_UNRESOLVED_LABEL = "UNRESOLVED"

CSV_HEADER = ("timestamp", "trading_date", "stage", "event_type", "summary", "payload")


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """One chronological fact about a replay.

    Attributes:
        timestamp: When this event occurred.
        trading_date: ``timestamp.date()`` - kept as its own field for
            easy grouping/filtering without re-deriving it.
        stage: Which stage produced this event (e.g. ``"weekly_future"``,
            ``"orb"``, ``"replay"``) - a label, not necessarily a
            registered ``PipelineStage.name`` (``REFERENCE_LEVEL_CREATED``
            comes from ``ReferenceBuilder``, which is not itself a stage).
        event_type: One of :class:`~core.enums.TimelineEventType`.
        summary: A human-readable one-line description.
        payload: Structured detail, every value already a string.
    """

    timestamp: datetime
    trading_date: date
    stage: str
    event_type: TimelineEventType
    summary: str
    payload: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp is None:
            raise ValidationError("TimelineEvent.timestamp must not be None.")
        if self.trading_date is None:
            raise ValidationError("TimelineEvent.trading_date must not be None.")
        if not self.stage or not self.stage.strip():
            raise ValidationError("TimelineEvent.stage must not be blank.")
        if not self.summary or not self.summary.strip():
            raise ValidationError("TimelineEvent.summary must not be blank.")


@dataclass(frozen=True, slots=True)
class StrategyTimeline:
    """An ordered sequence of :class:`TimelineEvent`."""

    events: tuple[TimelineEvent, ...] = field(default_factory=tuple)


def build_strategy_timeline(
    business_results: tuple[BusinessResult, ...], finished_at: datetime
) -> StrategyTimeline:
    """Build a :class:`StrategyTimeline` from an already-completed
    sequence of ``BusinessResult`` - see module docstring for exactly
    when each event type is emitted."""
    events: list[TimelineEvent] = []
    seen_reference_level = False
    seen_weekly_future = False
    seen_strike = False
    succeeded = 0
    failed = 0

    for business_result in business_results:
        context = business_result.context
        trading_date = context.candle_timestamp.date()

        if not seen_reference_level and context.reference_data:
            events.append(
                TimelineEvent(
                    timestamp=context.candle_timestamp,
                    trading_date=trading_date,
                    stage="reference_builder",
                    event_type=TimelineEventType.REFERENCE_LEVEL_CREATED,
                    summary=f"Reference ladder built with {len(context.reference_data)} levels.",
                    payload={"level_count": str(len(context.reference_data))},
                )
            )
            seen_reference_level = True

        if not seen_weekly_future and context.weekly_future is not None:
            wf = context.weekly_future
            events.append(
                TimelineEvent(
                    timestamp=context.candle_timestamp,
                    trading_date=trading_date,
                    stage="weekly_future",
                    event_type=TimelineEventType.WEEKLY_FUTURE_CALCULATED,
                    summary=f"Weekly Future High={wf.high} Low={wf.low}.",
                    payload={"high": str(wf.high), "low": str(wf.low)},
                )
            )
            seen_weekly_future = True

        if not seen_strike and context.selected_strike is not None:
            selection = context.selected_strike
            events.append(
                TimelineEvent(
                    timestamp=context.candle_timestamp,
                    trading_date=trading_date,
                    stage="weekly_future",
                    event_type=TimelineEventType.STRIKE_SELECTED,
                    summary=(
                        f"Top Strike={selection.top_strike} "
                        f"Bottom Strike={selection.bottom_strike}."
                    ),
                    payload={
                        "top_strike": str(selection.top_strike),
                        "bottom_strike": str(selection.bottom_strike),
                    },
                )
            )
            seen_strike = True

        if context.orb_result is not None:
            orb = context.orb_result
            events.append(
                TimelineEvent(
                    timestamp=context.candle_timestamp,
                    trading_date=trading_date,
                    stage="orb",
                    event_type=TimelineEventType.ORB_CALCULATED,
                    summary=(f"ORB {orb.side.value} {orb.strike}: status={orb.status.value}."),
                    payload={
                        "strike": str(orb.strike),
                        "side": orb.side.value,
                        "opening_high": str(orb.opening_high),
                        "opening_low": str(orb.opening_low),
                        "status": orb.status.value,
                    },
                )
            )

        if business_result.success:
            succeeded += 1
        else:
            failed += 1
            error_text = str(business_result.error) if business_result.error else _UNRESOLVED_LABEL
            failing_stage = "pipeline"
            for diagnostic in business_result.stage_diagnostics:
                if not diagnostic.success:
                    failing_stage = diagnostic.stage_name
                    break
            events.append(
                TimelineEvent(
                    timestamp=context.candle_timestamp,
                    trading_date=trading_date,
                    stage=failing_stage,
                    event_type=TimelineEventType.PIPELINE_ERROR,
                    summary=f"Pipeline error at {failing_stage}: {error_text}",
                    payload={"error": error_text},
                )
            )

    events.append(
        TimelineEvent(
            timestamp=finished_at,
            trading_date=finished_at.date(),
            stage="replay",
            event_type=TimelineEventType.REPLAY_FINISHED,
            summary=f"Replay finished: {succeeded} succeeded, {failed} failed.",
            payload={
                "succeeded": str(succeeded),
                "failed": str(failed),
                "total": str(len(business_results)),
            },
        )
    )

    return StrategyTimeline(events=tuple(events))


def write_timeline_json(timeline: StrategyTimeline, path: Path) -> None:
    """Write ``timeline`` to a JSON file at ``path`` - a list of
    event objects, in order."""
    payload = [
        {
            "timestamp": event.timestamp.isoformat(),
            "trading_date": event.trading_date.isoformat(),
            "stage": event.stage,
            "event_type": event.event_type.value,
            "summary": event.summary,
            "payload": event.payload,
        }
        for event in timeline.events
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_timeline_csv(timeline: StrategyTimeline, path: Path) -> None:
    """Write ``timeline`` to a CSV file at ``path``, one row per
    event, header first. ``payload`` is written as a single
    ``"key=value; ..."`` column."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADER)
        for event in timeline.events:
            payload_text = "; ".join(f"{key}={value}" for key, value in event.payload.items())
            writer.writerow(
                (
                    event.timestamp.isoformat(),
                    event.trading_date.isoformat(),
                    event.stage,
                    event.event_type.value,
                    event.summary,
                    payload_text,
                )
            )

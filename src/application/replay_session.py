"""ReplaySession/ReplayStatistics/ReplayStatus: one replay run's identity and outcome.

Traceability
------------
Field set matches this sprint's own instruction (session ID, dataset
ID, start time, end time, status, statistics) - infrastructure only.
Mirrors the immutable, replace-not-mutate session pattern already
used across this codebase (``models.trade_position.TradePosition``)
and its sibling project (``TradePlanAI-Lab``'s
``lab.execution.models.ExecutionSession``) - built once, at the end
of the run, rather than mutated through intermediate states.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, unique

from core.exceptions import ValidationError


@unique
class ReplayStatus(Enum):
    """A :class:`ReplaySession`'s own lifecycle position - a pure
    infrastructure concept, no business rule."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ReplayStatistics:
    """Counts summarizing one replay run.

    Attributes:
        candles_processed: How many candles were fed through the
            pipeline.
        events_recorded: How many domain events were captured, if an
            :class:`~event_recorder.event_recorder.EventRecorder` was
            injected into the :class:`~application.replay_runner.ReplayRunner`.
        business_runs_succeeded: How many per-candle
            ``business.orchestrator.BusinessOrchestrator.run()`` calls
            returned a successful
            ``business.business_result.BusinessResult``.
        business_runs_failed: How many did not - including a graceful
            stop on ``core.exceptions.UnresolvedBusinessRuleError``,
            not only a genuine fault (see
            ``business.business_result.BusinessResult.error`` to tell
            the two apart for any individual result).
    """

    candles_processed: int
    events_recorded: int
    business_runs_succeeded: int
    business_runs_failed: int

    def __post_init__(self) -> None:
        for name in (
            "candles_processed",
            "events_recorded",
            "business_runs_succeeded",
            "business_runs_failed",
        ):
            if getattr(self, name) < 0:
                raise ValidationError(f"ReplayStatistics.{name} must not be negative.")


@dataclass(frozen=True, slots=True)
class ReplaySession:
    """One replay run's own identity and lifecycle position.

    Attributes:
        session_id: This run's identifier.
        dataset_id: Which historical dataset was replayed.
        started_at: When the run began.
        status: The run's current :class:`ReplayStatus`.
        ended_at: When the run ended. Required when ``status`` is
            ``COMPLETED``/``FAILED``; must be ``None`` otherwise.
        statistics: Populated alongside ``ended_at``, under the same
            rule.
    """

    session_id: uuid.UUID
    dataset_id: str
    started_at: datetime
    status: ReplayStatus
    ended_at: datetime | None = None
    statistics: ReplayStatistics | None = None

    def __post_init__(self) -> None:
        if self.session_id is None:
            raise ValidationError("ReplaySession.session_id must not be None.")
        if not self.dataset_id or not self.dataset_id.strip():
            raise ValidationError("ReplaySession.dataset_id must not be blank.")
        if self.started_at is None:
            raise ValidationError("ReplaySession.started_at must not be None.")
        if self.status is None:
            raise ValidationError("ReplaySession.status must not be None.")

        finished = self.status in (ReplayStatus.COMPLETED, ReplayStatus.FAILED)
        if finished and (self.ended_at is None or self.statistics is None):
            raise ValidationError(
                "ReplaySession.ended_at and statistics must be set when status is "
                "COMPLETED or FAILED."
            )
        if not finished and (self.ended_at is not None or self.statistics is not None):
            raise ValidationError(
                "ReplaySession.ended_at and statistics must be None when status is "
                "PENDING or RUNNING."
            )
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValidationError("ReplaySession.ended_at must not be before started_at.")

    @property
    def duration_seconds(self) -> float | None:
        """``ended_at - started_at`` in seconds, or ``None`` while the
        session has not ended."""
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

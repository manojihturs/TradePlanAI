"""Structured diagnostic events emitted by the Rule Framework and Strategy Engine.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule
Evaluation Pipeline", "Rule Registry") for the lifecycle these events
observe (registration, dependency-ordered execution, per-rule
evaluation, aggregate results) - this module adds no new architectural
concept, it only makes that already-documented lifecycle observable.

Every event is a frozen, immutable value object carrying only
structural/identity information - no computed trading value ever
appears in any field (see package docstring). Each event corresponds
to exactly one of Milestone 6.4's required log points:

============================  =================================
Log point (Milestone 6.4)     Event class
============================  =================================
rule registration              :class:`RuleRegistered`
dependency ordering            :class:`DependencyResolved`
unresolved dependency          :class:`DependencyMissing`
rule execution start           :class:`RuleStarted`
rule execution finish          :class:`RuleFinished`
execution skipped              :class:`RuleSkipped`
exception                      :class:`ExecutionFailed`
execution summary              :class:`ExecutionSummaryLogged`
============================  =================================
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from trading_engine.diagnostics.exceptions import DiagnosticsError


def _validate_common(event_id: uuid.UUID, occurred_at: datetime, class_name: str) -> None:
    if event_id is None:
        raise DiagnosticsError(f"{class_name}.event_id must not be None.")
    if occurred_at is None:
        raise DiagnosticsError(f"{class_name}.occurred_at must not be None.")


def _validate_non_blank(value: str, field_name: str, class_name: str) -> None:
    if not value or not value.strip():
        raise DiagnosticsError(f"{class_name}.{field_name} must not be blank.")


@dataclass(frozen=True)
class RuleRegistered:
    """A rule was successfully registered into a
    :class:`~trading_engine.rules.registry.RuleRegistry`.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the registration occurred.
        rule_id: The Rule ID that was registered.
        total_registered: How many rules are registered in that
            registry immediately after this registration (including
            this one).
    """

    event_id: uuid.UUID
    occurred_at: datetime
    rule_id: str
    total_registered: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "RuleRegistered")
        _validate_non_blank(self.rule_id, "rule_id", "RuleRegistered")
        if self.total_registered < 1:
            raise DiagnosticsError("RuleRegistered.total_registered must be at least 1.")


@dataclass(frozen=True)
class DependencyResolved:
    """A :class:`~trading_engine.rules.registry.RuleRegistry` computed
    a dependency-respecting execution order successfully.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the ordering was computed.
        execution_order: The resolved sequence of Rule IDs, in the
            order they should be evaluated.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    execution_order: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "DependencyResolved")


@dataclass(frozen=True)
class DependencyMissing:
    """A :class:`~trading_engine.rules.registry.RuleRegistry` could
    not compute an execution order because a dependency was
    unresolvable - malformed, not registered, or part of a cycle.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the failure was detected.
        rule_id: The rule whose dependency could not be resolved.
        dependency_id: The dependency Rule ID that caused the failure.
        reason: A short, human-readable explanation (e.g.
            "unsupported dependency", "missing dependency", "circular
            dependency").
    """

    event_id: uuid.UUID
    occurred_at: datetime
    rule_id: str
    dependency_id: str
    reason: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "DependencyMissing")
        _validate_non_blank(self.rule_id, "rule_id", "DependencyMissing")
        _validate_non_blank(self.dependency_id, "dependency_id", "DependencyMissing")
        _validate_non_blank(self.reason, "reason", "DependencyMissing")


@dataclass(frozen=True)
class RuleStarted:
    """A rule's ``evaluate()`` is about to be called.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When evaluation started.
        rule_id: The rule about to be evaluated.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    rule_id: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "RuleStarted")
        _validate_non_blank(self.rule_id, "rule_id", "RuleStarted")


@dataclass(frozen=True)
class RuleFinished:
    """A rule's ``evaluate()`` returned successfully.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When evaluation finished.
        rule_id: The rule that was evaluated.
        outcome_name: The ``.name`` of the
            :class:`~trading_engine.rules.outcome.RuleOutcome` value
            reached (a plain string, so this package never imports
            the ``rules`` package - see module docstring).
        duration_seconds: Wall-clock time the evaluation took.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    rule_id: str
    outcome_name: str
    duration_seconds: float

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "RuleFinished")
        _validate_non_blank(self.rule_id, "rule_id", "RuleFinished")
        _validate_non_blank(self.outcome_name, "outcome_name", "RuleFinished")
        if self.duration_seconds < 0:
            raise DiagnosticsError("RuleFinished.duration_seconds must not be negative.")


@dataclass(frozen=True)
class RuleSkipped:
    """A registered rule was not evaluated during a pipeline run.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the skip decision was made.
        rule_id: The rule that was skipped.
        reason: A short, human-readable explanation (e.g. "dry run",
            "maximum rule count reached").
    """

    event_id: uuid.UUID
    occurred_at: datetime
    rule_id: str
    reason: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "RuleSkipped")
        _validate_non_blank(self.rule_id, "rule_id", "RuleSkipped")
        _validate_non_blank(self.reason, "reason", "RuleSkipped")


@dataclass(frozen=True)
class ExecutionFailed:
    """A rule's ``evaluate()`` raised an exception.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the exception was caught.
        rule_id: The rule whose evaluation raised.
        exception_type: The raised exception's class name (e.g.
            ``"RuleExecutionError"``) - never the exception instance
            itself, to keep this event's fields plain/serialisable.
        message: The exception's ``str()`` message.
        fatal: Whether this failure stopped the pipeline (``True``)
            or was recorded and iteration continued (``False``).
    """

    event_id: uuid.UUID
    occurred_at: datetime
    rule_id: str
    exception_type: str
    message: str
    fatal: bool

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "ExecutionFailed")
        _validate_non_blank(self.rule_id, "rule_id", "ExecutionFailed")
        _validate_non_blank(self.exception_type, "exception_type", "ExecutionFailed")


@dataclass(frozen=True)
class ExecutionSummaryLogged:
    """One :class:`~trading_engine.engine.execution_summary.ExecutionSummary`
    was produced at the end of a
    :class:`~trading_engine.engine.strategy_engine.StrategyEngine` run.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the summary was produced.
        execution_id: The originating
            :class:`~trading_engine.engine.execution_report.ExecutionReport`'s
            execution id.
        total_rules: Total results summarised.
        pass_count: How many results had outcome ``PASS``.
        fail_count: How many results had outcome ``FAIL``.
        unknown_count: How many results had outcome ``UNKNOWN``.
        insufficient_evidence_count: How many results had outcome
            ``INSUFFICIENT_EVIDENCE``.
        not_applicable_count: How many results had outcome
            ``NOT_APPLICABLE``.
        duration_seconds: Wall-clock duration of the summarised run.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    execution_id: uuid.UUID
    total_rules: int
    pass_count: int
    fail_count: int
    unknown_count: int
    insufficient_evidence_count: int
    not_applicable_count: int
    duration_seconds: float

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "ExecutionSummaryLogged")
        if self.execution_id is None:
            raise DiagnosticsError("ExecutionSummaryLogged.execution_id must not be None.")
        if self.total_rules < 0:
            raise DiagnosticsError("ExecutionSummaryLogged.total_rules must not be negative.")
        if self.duration_seconds < 0:
            raise DiagnosticsError("ExecutionSummaryLogged.duration_seconds must not be negative.")


@dataclass(frozen=True)
class ReplayStarted:
    """A replay session began.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the replay started.
        session_id: The replay session's own identifier.
        total_candles: How many candles this session will replay.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    total_candles: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "ReplayStarted")
        if self.session_id is None:
            raise DiagnosticsError("ReplayStarted.session_id must not be None.")
        if self.total_candles < 0:
            raise DiagnosticsError("ReplayStarted.total_candles must not be negative.")


@dataclass(frozen=True)
class ReplayPaused:
    """A replay session was paused.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the pause occurred.
        session_id: The replay session's own identifier.
        current_index: The candle index the session was paused at.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    current_index: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "ReplayPaused")
        if self.session_id is None:
            raise DiagnosticsError("ReplayPaused.session_id must not be None.")
        if self.current_index < 0:
            raise DiagnosticsError("ReplayPaused.current_index must not be negative.")


@dataclass(frozen=True)
class ReplayResumed:
    """A paused replay session resumed.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the resume occurred.
        session_id: The replay session's own identifier.
        current_index: The candle index the session resumed from.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    current_index: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "ReplayResumed")
        if self.session_id is None:
            raise DiagnosticsError("ReplayResumed.session_id must not be None.")
        if self.current_index < 0:
            raise DiagnosticsError("ReplayResumed.current_index must not be negative.")


@dataclass(frozen=True)
class ReplayStepped:
    """A replay session advanced (or retreated) by one candle.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the step occurred.
        session_id: The replay session's own identifier.
        from_index: The candle index before the step.
        to_index: The candle index after the step.
        direction: Either ``"forward"`` or ``"backward"``.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    from_index: int
    to_index: int
    direction: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "ReplayStepped")
        if self.session_id is None:
            raise DiagnosticsError("ReplayStepped.session_id must not be None.")
        if self.from_index < 0 or self.to_index < 0:
            raise DiagnosticsError("ReplayStepped indices must not be negative.")
        if self.direction not in ("forward", "backward"):
            raise DiagnosticsError("ReplayStepped.direction must be 'forward' or 'backward'.")


@dataclass(frozen=True)
class ReplayCompleted:
    """A replay session reached the end of its candle sequence.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the session completed.
        session_id: The replay session's own identifier.
        total_candles_processed: How many candles were processed
            before completion.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    total_candles_processed: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "ReplayCompleted")
        if self.session_id is None:
            raise DiagnosticsError("ReplayCompleted.session_id must not be None.")
        if self.total_candles_processed < 0:
            raise DiagnosticsError("ReplayCompleted.total_candles_processed must not be negative.")


@dataclass(frozen=True)
class ReplayReset:
    """A replay session was reset to its initial position.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the reset occurred.
        session_id: The replay session's own identifier.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "ReplayReset")
        if self.session_id is None:
            raise DiagnosticsError("ReplayReset.session_id must not be None.")


@dataclass(frozen=True)
class MarketDataConnected:
    """A market data provider established its connection.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the connection was established.
        provider_name: The provider's own name (e.g. ``"upstox"``).
    """

    event_id: uuid.UUID
    occurred_at: datetime
    provider_name: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "MarketDataConnected")
        _validate_non_blank(self.provider_name, "provider_name", "MarketDataConnected")


@dataclass(frozen=True)
class MarketDataDisconnected:
    """A market data provider's connection ended.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the disconnection occurred.
        provider_name: The provider's own name.
        reason: A short, human-readable reason (e.g. ``"requested"``,
            ``"transport closed"``).
    """

    event_id: uuid.UUID
    occurred_at: datetime
    provider_name: str
    reason: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "MarketDataDisconnected")
        _validate_non_blank(self.provider_name, "provider_name", "MarketDataDisconnected")
        _validate_non_blank(self.reason, "reason", "MarketDataDisconnected")


@dataclass(frozen=True)
class MarketDataSubscribed:
    """A market data provider subscribed to an instrument.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the subscription was sent.
        provider_name: The provider's own name.
        instrument_token: The subscribed instrument's token.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    provider_name: str
    instrument_token: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "MarketDataSubscribed")
        _validate_non_blank(self.provider_name, "provider_name", "MarketDataSubscribed")
        _validate_non_blank(self.instrument_token, "instrument_token", "MarketDataSubscribed")


@dataclass(frozen=True)
class MarketDataReconnected:
    """A market data provider reconnected after a disconnection.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the reconnection completed.
        provider_name: The provider's own name.
        attempt: Which reconnect attempt this was (1-based).
        resubscribed_count: How many instruments were resubscribed.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    provider_name: str
    attempt: int
    resubscribed_count: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "MarketDataReconnected")
        _validate_non_blank(self.provider_name, "provider_name", "MarketDataReconnected")
        if self.attempt < 1:
            raise DiagnosticsError("MarketDataReconnected.attempt must be at least 1.")
        if self.resubscribed_count < 0:
            raise DiagnosticsError("MarketDataReconnected.resubscribed_count must not be negative.")


@dataclass(frozen=True)
class MarketDataAuthenticationFailed:
    """A market data provider's authentication attempt failed.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the failure was detected.
        provider_name: The provider's own name.
        reason: A short, human-readable reason - never the raw
            credentials or token value.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    provider_name: str
    reason: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "MarketDataAuthenticationFailed")
        _validate_non_blank(self.provider_name, "provider_name", "MarketDataAuthenticationFailed")
        _validate_non_blank(self.reason, "reason", "MarketDataAuthenticationFailed")


@dataclass(frozen=True)
class SnapshotStarted:
    """A premium snapshot capture window began.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the capture started.
        session_id: The snapshot session's own identifier.
        window_start: The capture window's start time.
        window_end: The capture window's end time.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    window_start: datetime
    window_end: datetime

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "SnapshotStarted")
        if self.session_id is None:
            raise DiagnosticsError("SnapshotStarted.session_id must not be None.")
        if self.window_end <= self.window_start:
            raise DiagnosticsError("SnapshotStarted.window_end must be after window_start.")


@dataclass(frozen=True)
class SnapshotCompleted:
    """A premium snapshot capture window closed and the snapshot was
    built.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the capture completed.
        session_id: The snapshot session's own identifier.
        captured_contract_count: How many contracts had at least one
            tick captured.
        missing_contract_count: How many requested contracts had no
            tick captured (unavailable, not treated as a failure).
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    captured_contract_count: int
    missing_contract_count: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "SnapshotCompleted")
        if self.session_id is None:
            raise DiagnosticsError("SnapshotCompleted.session_id must not be None.")
        if self.captured_contract_count < 0:
            raise DiagnosticsError(
                "SnapshotCompleted.captured_contract_count must not be negative."
            )
        if self.missing_contract_count < 0:
            raise DiagnosticsError("SnapshotCompleted.missing_contract_count must not be negative.")


@dataclass(frozen=True)
class SnapshotStored:
    """A completed premium snapshot was persisted to a repository.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the snapshot was stored.
        snapshot_id: The stored snapshot's own identifier.
        session_id: The snapshot session's own identifier.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    snapshot_id: uuid.UUID
    session_id: uuid.UUID

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "SnapshotStored")
        if self.snapshot_id is None:
            raise DiagnosticsError("SnapshotStored.snapshot_id must not be None.")
        if self.session_id is None:
            raise DiagnosticsError("SnapshotStored.session_id must not be None.")


@dataclass(frozen=True)
class RecorderStarted:
    """A market tick recorder began recording.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When recording started.
        recorder_name: The recorder's own name/label.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    recorder_name: str

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "RecorderStarted")
        _validate_non_blank(self.recorder_name, "recorder_name", "RecorderStarted")


@dataclass(frozen=True)
class RecorderStopped:
    """A market tick recorder stopped recording.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When recording stopped.
        recorder_name: The recorder's own name/label.
        records_flushed: How many records were flushed as part of
            stopping.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    recorder_name: str
    records_flushed: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "RecorderStopped")
        _validate_non_blank(self.recorder_name, "recorder_name", "RecorderStopped")
        if self.records_flushed < 0:
            raise DiagnosticsError("RecorderStopped.records_flushed must not be negative.")


@dataclass(frozen=True)
class RecorderFlushed:
    """A market tick recorder flushed its buffered records to its
    repository.

    Attributes:
        event_id: Unique identifier for this event.
        occurred_at: When the flush occurred.
        recorder_name: The recorder's own name/label.
        record_count: How many records were flushed.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    recorder_name: str
    record_count: int

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "RecorderFlushed")
        _validate_non_blank(self.recorder_name, "recorder_name", "RecorderFlushed")
        if self.record_count < 0:
            raise DiagnosticsError("RecorderFlushed.record_count must not be negative.")


#: The union of every diagnostic event type, used as
#: :class:`~trading_engine.diagnostics.sink.DiagnosticsSink.emit`'s
#: parameter type.
DiagnosticEvent = (
    RuleRegistered
    | DependencyResolved
    | DependencyMissing
    | RuleStarted
    | RuleFinished
    | RuleSkipped
    | ExecutionFailed
    | ExecutionSummaryLogged
    | ReplayStarted
    | ReplayPaused
    | ReplayResumed
    | ReplayStepped
    | ReplayCompleted
    | ReplayReset
    | MarketDataConnected
    | MarketDataDisconnected
    | MarketDataSubscribed
    | MarketDataReconnected
    | MarketDataAuthenticationFailed
    | SnapshotStarted
    | SnapshotCompleted
    | SnapshotStored
    | RecorderStarted
    | RecorderStopped
    | RecorderFlushed
)

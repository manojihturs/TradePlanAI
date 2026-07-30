"""ReplayValidationSummary: one aggregated, run-level validation summary.

Traceability
------------
"Replay Validation" here means running a historical dataset through
the already-existing full pipeline
(``application.replay_application.ReplayApplication`` ->
``application.replay_runner.ReplayRunner`` ->
``business.orchestrator.BusinessOrchestrator`` ->
``business.stages.weekly_future_stage.WeeklyFutureStage``) and
summarizing what happened - it makes no trading decision and performs
no calculation of its own, only reads an already-produced
``application.replay_result.ReplayResult``.

Per Specification Rule 1, Reference Strike/Weekly Future
High-Low/Top-Bottom Strike are computed once per session (from the
first candle) and are constant for every later candle in that same
session - so this summary reports a single value for each (the first
non-``None`` value seen across ``result.business_results``, in candle
order), not one per candle (that per-candle detail already exists via
``application.replay_report``). A session where the stage never ran at
all (e.g. no reference data supplied) reports ``None`` for all four,
which is itself a meaningful validation signal, not an error to hide.

``failures`` logs one entry per candle whose ``BusinessResult.success``
was ``False``, carrying the candle timestamp and the error text (for a
genuine stage fault, ``str(BusinessResult.error)``; for a graceful
UNRESOLVED stop, ``"UNRESOLVED"``, since ``BusinessResult.error`` is
``None`` in that case - see ``business.business_result.BusinessResult``'s
own docstring for that distinction).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

from application.replay_result import ReplayResult
from core.exceptions import ValidationError

_UNRESOLVED_LABEL = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class ReplayValidationFailure:
    """One failed candle's timestamp and error text.

    Attributes:
        candle_timestamp: The candle whose pipeline run did not succeed.
        error: ``str(BusinessResult.error)`` for a genuine stage fault,
            or ``"UNRESOLVED"`` for a graceful
            ``UnresolvedBusinessRuleError`` stop.
    """

    candle_timestamp: datetime
    error: str

    def __post_init__(self) -> None:
        if self.candle_timestamp is None:
            raise ValidationError("ReplayValidationFailure.candle_timestamp must not be None.")
        if not self.error:
            raise ValidationError("ReplayValidationFailure.error must not be blank.")


@dataclass(frozen=True, slots=True)
class ReplayValidationSummary:
    """One run-level validation summary of a :class:`~application.replay_result.ReplayResult`.

    Attributes:
        dataset_id: Which historical dataset was replayed.
        candles_processed: Total candles run through the pipeline.
        succeeded_count: How many candles' pipeline run succeeded.
        failed_count: How many did not.
        execution_time: Wall-clock duration of the run
            (``ReplaySession.duration_seconds``), or ``None`` if the
            session had not ended.
        reference_strike: The session's Reference Strike, or ``None``
            if ``WeeklyFutureStage`` never ran.
        weekly_future_high: The session's Weekly Future High, or ``None``.
        weekly_future_low: The session's Weekly Future Low, or ``None``.
        top_strike: The session's Top Strike, or ``None``.
        bottom_strike: The session's Bottom Strike, or ``None``.
        failures: One :class:`ReplayValidationFailure` per failed candle,
            in candle order.
    """

    dataset_id: str
    candles_processed: int
    succeeded_count: int
    failed_count: int
    execution_time: timedelta | None
    reference_strike: Decimal | None
    weekly_future_high: Decimal | None
    weekly_future_low: Decimal | None
    top_strike: Decimal | None
    bottom_strike: Decimal | None
    failures: tuple[ReplayValidationFailure, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.dataset_id or not self.dataset_id.strip():
            raise ValidationError("ReplayValidationSummary.dataset_id must not be blank.")
        if self.candles_processed < 0:
            raise ValidationError("ReplayValidationSummary.candles_processed must not be negative.")
        if self.succeeded_count + self.failed_count != self.candles_processed:
            raise ValidationError(
                "ReplayValidationSummary.succeeded_count + failed_count must equal "
                "candles_processed."
            )
        if len(self.failures) != self.failed_count:
            raise ValidationError(
                "ReplayValidationSummary.failures length must equal failed_count."
            )


def build_validation_summary(result: ReplayResult) -> ReplayValidationSummary:
    """Build a :class:`ReplayValidationSummary` from an already-completed
    :class:`~application.replay_result.ReplayResult`."""
    reference_strike: Decimal | None = None
    weekly_future_high: Decimal | None = None
    weekly_future_low: Decimal | None = None
    top_strike: Decimal | None = None
    bottom_strike: Decimal | None = None
    failures: list[ReplayValidationFailure] = []

    for business_result in result.business_results:
        context = business_result.context
        if reference_strike is None and context.reference_strike is not None:
            reference_strike = context.reference_strike
        if weekly_future_high is None and context.weekly_future is not None:
            weekly_future_high = context.weekly_future.high
            weekly_future_low = context.weekly_future.low
        if top_strike is None and context.selected_strike is not None:
            top_strike = context.selected_strike.top_strike
            bottom_strike = context.selected_strike.bottom_strike
        if not business_result.success:
            error_text = str(business_result.error) if business_result.error else _UNRESOLVED_LABEL
            failures.append(
                ReplayValidationFailure(candle_timestamp=context.candle_timestamp, error=error_text)
            )

    return ReplayValidationSummary(
        dataset_id=result.session.dataset_id,
        candles_processed=len(result.business_results),
        succeeded_count=result.succeeded_count,
        failed_count=result.failed_count,
        execution_time=(
            timedelta(seconds=result.session.duration_seconds)
            if result.session.duration_seconds is not None
            else None
        ),
        reference_strike=reference_strike,
        weekly_future_high=weekly_future_high,
        weekly_future_low=weekly_future_low,
        top_strike=top_strike,
        bottom_strike=bottom_strike,
        failures=tuple(failures),
    )


def render_validation_log(summary: ReplayValidationSummary) -> str:
    """Render ``summary`` as a plain multi-line log block - one line
    per field, then one line per failure."""
    lines = [
        f"dataset_id={summary.dataset_id}",
        f"candles_processed={summary.candles_processed}",
        f"succeeded_count={summary.succeeded_count}",
        f"failed_count={summary.failed_count}",
        f"execution_time_seconds={summary.execution_time.total_seconds() if summary.execution_time else None}",
        f"reference_strike={summary.reference_strike}",
        f"weekly_future_high={summary.weekly_future_high}",
        f"weekly_future_low={summary.weekly_future_low}",
        f"top_strike={summary.top_strike}",
        f"bottom_strike={summary.bottom_strike}",
    ]
    for failure in summary.failures:
        lines.append(f"FAILURE candle={failure.candle_timestamp.isoformat()} error={failure.error}")
    return "\n".join(lines)

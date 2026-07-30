"""ReplayDashboard: per-trading-day validation view over a ReplayResult.

Traceability
------------
Sprint: "Replay Validation Dashboard" (Compact Development Mode) -
observability only, no new business logic. Reads an already-completed
``application.replay_result.ReplayResult`` and groups its existing
per-candle ``business.business_result.BusinessResult`` entries by
calendar day (``candle_timestamp.date()``), since this codebase's
current session model runs an entire dataset - possibly spanning many
days - as one session/one ``ReplayResult`` (see
``replay.replay_engine.ReplayEngine``), not one session per day. No
value is recomputed - Reference Strike/Weekly Future/Top-Bottom Strike
per day are the first non-``None`` value seen among that day's
candles, mirroring ``application.replay_validation``'s own
whole-run version of the same rule.

"Execution Time" per day is the span between that day's first and
last candle timestamps (``max - min``), *not* a measured wall-clock
processing duration - no per-day timing instrumentation exists yet
(that is a separate, not-yet-requested sprint: "Pipeline
Diagnostics"). This is documented here rather than fabricated as a
real measurement, and is still meaningful for spotting an
unexpectedly short/long trading day in the data.

"Replay Status" is ``"PASSED"`` only if every candle that day
succeeded, ``"FAILED"`` if any did not - "Any Errors" lists the error
text for each failed candle that day (reusing
``application.replay_validation``'s own error-text convention:
``str(BusinessResult.error)`` for a genuine fault, ``"UNRESOLVED"``
for a graceful stop).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from application.replay_result import ReplayResult
from business.business_result import BusinessResult
from core.exceptions import ValidationError

_UNRESOLVED_LABEL = "UNRESOLVED"
_STATUS_PASSED = "PASSED"
_STATUS_FAILED = "FAILED"

CSV_HEADER = (
    "date",
    "reference_strike",
    "weekly_future_high",
    "weekly_future_low",
    "top_strike",
    "bottom_strike",
    "execution_time_seconds",
    "status",
    "errors",
)


@dataclass(frozen=True, slots=True)
class ReplayDashboardRow:
    """One trading day's validation summary.

    Attributes:
        trading_day: The calendar date this row concerns.
        reference_strike: That day's Reference Strike, or ``None`` if
            ``WeeklyFutureStage`` never ran that day.
        weekly_future_high: That day's Weekly Future High, or ``None``.
        weekly_future_low: That day's Weekly Future Low, or ``None``.
        top_strike: That day's Top Strike, or ``None``.
        bottom_strike: That day's Bottom Strike, or ``None``.
        execution_time: Span between that day's first and last candle
            timestamps - see module docstring for why this is not a
            true wall-clock measurement.
        status: ``"PASSED"`` if every candle that day succeeded,
            otherwise ``"FAILED"``.
        errors: One error string per failed candle that day, in
            candle order.
    """

    trading_day: date
    reference_strike: Decimal | None
    weekly_future_high: Decimal | None
    weekly_future_low: Decimal | None
    top_strike: Decimal | None
    bottom_strike: Decimal | None
    execution_time: timedelta
    status: str
    errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.trading_day is None:
            raise ValidationError("ReplayDashboardRow.trading_day must not be None.")
        if self.status not in (_STATUS_PASSED, _STATUS_FAILED):
            raise ValidationError(
                f"ReplayDashboardRow.status must be {_STATUS_PASSED!r} or "
                f"{_STATUS_FAILED!r}, got {self.status!r}."
            )
        if self.execution_time < timedelta():
            raise ValidationError("ReplayDashboardRow.execution_time must not be negative.")


@dataclass(frozen=True, slots=True)
class ReplayDashboardSummary:
    """Aggregate counts/timings across every :class:`ReplayDashboardRow`.

    Attributes:
        days_processed: Total distinct trading days found.
        days_passed: How many had ``status == "PASSED"``.
        days_failed: How many had ``status == "FAILED"``.
        average_execution_time: Mean of every row's ``execution_time``,
            or ``None`` if there were no rows.
        fastest_execution_time: The minimum ``execution_time``, or ``None``.
        slowest_execution_time: The maximum ``execution_time``, or ``None``.
    """

    days_processed: int
    days_passed: int
    days_failed: int
    average_execution_time: timedelta | None
    fastest_execution_time: timedelta | None
    slowest_execution_time: timedelta | None

    def __post_init__(self) -> None:
        if self.days_processed < 0:
            raise ValidationError("ReplayDashboardSummary.days_processed must not be negative.")
        if self.days_passed + self.days_failed != self.days_processed:
            raise ValidationError(
                "ReplayDashboardSummary.days_passed + days_failed must equal " "days_processed."
            )


def build_dashboard_rows(result: ReplayResult) -> tuple[ReplayDashboardRow, ...]:
    """Group ``result.business_results`` by calendar day and build one
    :class:`ReplayDashboardRow` per day, in date order."""
    days: dict[date, list[BusinessResult]] = {}
    for business_result in result.business_results:
        context = business_result.context
        trading_day = context.candle_timestamp.date()
        days.setdefault(trading_day, []).append(business_result)

    rows: list[ReplayDashboardRow] = []
    for trading_day in sorted(days):
        day_results = days[trading_day]
        timestamps = [br.context.candle_timestamp for br in day_results]

        reference_strike: Decimal | None = None
        weekly_future_high: Decimal | None = None
        weekly_future_low: Decimal | None = None
        top_strike: Decimal | None = None
        bottom_strike: Decimal | None = None
        errors: list[str] = []

        for business_result in day_results:
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
                error_text = (
                    str(business_result.error) if business_result.error else _UNRESOLVED_LABEL
                )
                errors.append(error_text)

        rows.append(
            ReplayDashboardRow(
                trading_day=trading_day,
                reference_strike=reference_strike,
                weekly_future_high=weekly_future_high,
                weekly_future_low=weekly_future_low,
                top_strike=top_strike,
                bottom_strike=bottom_strike,
                execution_time=max(timestamps) - min(timestamps),
                status=_STATUS_FAILED if errors else _STATUS_PASSED,
                errors=tuple(errors),
            )
        )
    return tuple(rows)


def build_dashboard_summary(rows: tuple[ReplayDashboardRow, ...]) -> ReplayDashboardSummary:
    """Aggregate ``rows`` into a :class:`ReplayDashboardSummary`."""
    if not rows:
        return ReplayDashboardSummary(
            days_processed=0,
            days_passed=0,
            days_failed=0,
            average_execution_time=None,
            fastest_execution_time=None,
            slowest_execution_time=None,
        )

    durations = [row.execution_time for row in rows]
    return ReplayDashboardSummary(
        days_processed=len(rows),
        days_passed=sum(1 for row in rows if row.status == _STATUS_PASSED),
        days_failed=sum(1 for row in rows if row.status == _STATUS_FAILED),
        average_execution_time=sum(durations, timedelta()) / len(durations),
        fastest_execution_time=min(durations),
        slowest_execution_time=max(durations),
    )


def write_dashboard_csv(rows: tuple[ReplayDashboardRow, ...], path: Path) -> None:
    """Write ``rows`` to a CSV file at ``path``, one row per trading
    day, header first."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADER)
        for row in rows:
            writer.writerow(
                (
                    row.trading_day.isoformat(),
                    row.reference_strike,
                    row.weekly_future_high,
                    row.weekly_future_low,
                    row.top_strike,
                    row.bottom_strike,
                    row.execution_time.total_seconds(),
                    row.status,
                    "; ".join(row.errors),
                )
            )

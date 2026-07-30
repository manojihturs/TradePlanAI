"""ReplayReportRow: per-candle Weekly Future/Strike output derived from ReplayResult.

Traceability
------------
Exposes only values already computed by
``business.stages.weekly_future_stage.WeeklyFutureStage`` and stored on
``business.pipeline_context.PipelineContext`` (``weekly_future``,
``selected_strike``) - this module performs no calculation of its own,
only reads and formats. One row per
``business.business_result.BusinessResult`` in
``application.replay_result.ReplayResult.business_results``, in candle
order.

Kept as free functions taking a ``ReplayResult`` rather than a
``ReplayResult.report_rows`` property, to avoid a circular import
(``ReplayResult`` would otherwise have to import this module and vice
versa) - ``ReplayResult`` itself is unchanged by this sprint.

CSV export uses the stdlib ``csv`` module only, matching this
project's existing no-third-party-dependency convention in the
application layer.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from application.replay_result import ReplayResult
from core.exceptions import ValidationError

CSV_HEADER = (
    "candle_timestamp",
    "success",
    "weekly_future_high",
    "weekly_future_low",
    "top_strike",
    "bottom_strike",
)


@dataclass(frozen=True, slots=True)
class ReplayReportRow:
    """One candle's Weekly Future/Strike output, or ``None`` fields if
    that candle's pipeline run never reached the ``WeeklyFutureStage``.

    Attributes:
        candle_timestamp: The candle this row concerns.
        success: The underlying ``BusinessResult.success`` for this candle.
        weekly_future_high: ``PipelineContext.weekly_future.high``, if present.
        weekly_future_low: ``PipelineContext.weekly_future.low``, if present.
        top_strike: ``PipelineContext.selected_strike.top_strike``, if present.
        bottom_strike: ``PipelineContext.selected_strike.bottom_strike``, if present.
    """

    candle_timestamp: datetime
    success: bool
    weekly_future_high: Decimal | None
    weekly_future_low: Decimal | None
    top_strike: Decimal | None
    bottom_strike: Decimal | None

    def __post_init__(self) -> None:
        if self.candle_timestamp is None:
            raise ValidationError("ReplayReportRow.candle_timestamp must not be None.")


def build_report_rows(result: ReplayResult) -> tuple[ReplayReportRow, ...]:
    """Build one :class:`ReplayReportRow` per entry in
    ``result.business_results``, in the same order."""
    rows: list[ReplayReportRow] = []
    for business_result in result.business_results:
        context = business_result.context
        weekly_future = context.weekly_future
        selected_strike = context.selected_strike
        rows.append(
            ReplayReportRow(
                candle_timestamp=context.candle_timestamp,
                success=business_result.success,
                weekly_future_high=weekly_future.high if weekly_future else None,
                weekly_future_low=weekly_future.low if weekly_future else None,
                top_strike=selected_strike.top_strike if selected_strike else None,
                bottom_strike=selected_strike.bottom_strike if selected_strike else None,
            )
        )
    return tuple(rows)


def write_report_csv(rows: tuple[ReplayReportRow, ...], path: Path) -> None:
    """Write ``rows`` to a CSV file at ``path``, one row per candle,
    header first. ``None`` values are written as empty cells."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADER)
        for row in rows:
            writer.writerow(
                (
                    row.candle_timestamp.isoformat(),
                    row.success,
                    row.weekly_future_high,
                    row.weekly_future_low,
                    row.top_strike,
                    row.bottom_strike,
                )
            )

"""ReplayViewRow: display-only, human-readable rendering of a ReplayResult.

Traceability
------------
Display-only - reads values already computed by
``business.stages.weekly_future_stage.WeeklyFutureStage`` and stored on
``business.pipeline_context.PipelineContext`` (``reference_strike``,
``weekly_future``, ``selected_strike``), and formats them as strings.
No calculation, no new business logic, no persistence or external I/O.

Kept as plain functions producing/consuming a small display-string
dataclass, not a web/GUI framework binding - matches this project's
"no invented" discipline (no framework has otherwise been introduced
in ``src/``) and keeps this layer trivially unit-testable, which a
rendered page would not be. A future real UI (web page, TUI, etc.) can
bind to ``ReplayViewRow`` without needing to re-derive formatting
rules.

Missing values (a candle whose pipeline run never reached
``WeeklyFutureStage``) render as the placeholder ``"--"`` rather than
``None``/``""``, so a table column never silently goes blank.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from application.replay_result import ReplayResult
from core.exceptions import ValidationError

MISSING_VALUE_PLACEHOLDER = "--"

VIEW_COLUMNS = (
    "Candle",
    "Reference Strike",
    "Weekly Future High",
    "Weekly Future Low",
    "Top Strike",
    "Bottom Strike",
)


def _format_decimal(value: Decimal | None) -> str:
    return MISSING_VALUE_PLACEHOLDER if value is None else str(value)


def _format_timestamp(value: datetime) -> str:
    return value.isoformat()


@dataclass(frozen=True, slots=True)
class ReplayViewRow:
    """One candle's display-ready values.

    All value fields are already-formatted strings (``"--"`` for a
    missing value) - a UI binds this row directly, with no further
    null-handling or formatting logic of its own.

    Attributes:
        candle: The candle timestamp, ISO-8601 formatted.
        reference_strike: ``PipelineContext.reference_strike``, formatted.
        weekly_future_high: ``PipelineContext.weekly_future.high``, formatted.
        weekly_future_low: ``PipelineContext.weekly_future.low``, formatted.
        top_strike: ``PipelineContext.selected_strike.top_strike``, formatted.
        bottom_strike: ``PipelineContext.selected_strike.bottom_strike``, formatted.
    """

    candle: str
    reference_strike: str
    weekly_future_high: str
    weekly_future_low: str
    top_strike: str
    bottom_strike: str

    def __post_init__(self) -> None:
        if not self.candle:
            raise ValidationError("ReplayViewRow.candle must not be blank.")

    def as_columns(self) -> tuple[str, str, str, str, str, str]:
        """This row's values in ``VIEW_COLUMNS`` order."""
        return (
            self.candle,
            self.reference_strike,
            self.weekly_future_high,
            self.weekly_future_low,
            self.top_strike,
            self.bottom_strike,
        )


def build_view_rows(result: ReplayResult) -> tuple[ReplayViewRow, ...]:
    """Build one display-ready :class:`ReplayViewRow` per
    ``result.business_results`` entry, in order."""
    rows: list[ReplayViewRow] = []
    for business_result in result.business_results:
        context = business_result.context
        weekly_future = context.weekly_future
        selected_strike = context.selected_strike
        rows.append(
            ReplayViewRow(
                candle=_format_timestamp(context.candle_timestamp),
                reference_strike=_format_decimal(context.reference_strike),
                weekly_future_high=_format_decimal(weekly_future.high if weekly_future else None),
                weekly_future_low=_format_decimal(weekly_future.low if weekly_future else None),
                top_strike=_format_decimal(selected_strike.top_strike if selected_strike else None),
                bottom_strike=_format_decimal(
                    selected_strike.bottom_strike if selected_strike else None
                ),
            )
        )
    return tuple(rows)


def render_view_table(rows: tuple[ReplayViewRow, ...]) -> str:
    """Render ``rows`` as a plain, fixed-width text table for
    console/log display - header first, then one line per row."""
    widths = [len(column) for column in VIEW_COLUMNS]
    row_columns = [row.as_columns() for row in rows]
    for columns in row_columns:
        for index, value in enumerate(columns):
            widths[index] = max(widths[index], len(value))

    def _format_line(columns: tuple[str, ...]) -> str:
        return "  ".join(value.ljust(widths[index]) for index, value in enumerate(columns))

    lines = [_format_line(VIEW_COLUMNS)]
    lines.extend(_format_line(columns) for columns in row_columns)
    return "\n".join(lines)

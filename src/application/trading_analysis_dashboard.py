"""TradingAnalysisDashboard: trader-facing view over a ReplayResult.

Traceability
------------
Sprint: "Trading Analysis Dashboard" (Delivery Mode) - the first
sprint framed as user value rather than infrastructure, but the rule
is unchanged: read ``application.replay_result.ReplayResult`` only,
never recalculate a business value. Built on top of
``application.replay_dashboard.build_dashboard_rows``, which already
does the one piece of real work here (grouping per-candle
``business.business_result.BusinessResult`` entries by calendar day,
first-non-``None``-value-per-day) - this module only reshapes that
same per-day data for a trader: renames "Reference Strike" to "ATM
Strike" (the same value - the anchor strike Weekly Future/Strike
Selection were computed against) and adds two *display-only*
subtractions (ATM vs. Weekly Future High/Low) that are elementary
arithmetic over already-computed values, not a new business rule -
no threshold, decision, or trading action is derived from them here.

"Charts" are structured (date, value) series, not rendered pixels -
no charting/GUI framework has been introduced anywhere in ``src/``,
and a plain data series is what any real front end (or a script that
plots it) would need regardless of which library renders it.

Excel export uses ``openpyxl.Workbook``, matching this repository's
own existing precedent (``strategy/multi_day_backtest.py``'s
``export_to_excel``) - not a newly introduced dependency.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from application.replay_dashboard import build_dashboard_rows
from application.replay_result import ReplayResult
from core.exceptions import ValidationError

CSV_HEADER = (
    "trading_day",
    "atm_strike",
    "weekly_future_high",
    "weekly_future_low",
    "top_strike",
    "bottom_strike",
    "diff_atm_to_high",
    "diff_atm_to_low",
)


@dataclass(frozen=True, slots=True)
class TradingAnalysisRow:
    """One trading day's trader-facing view.

    Attributes:
        trading_day: The calendar date this row concerns.
        atm_strike: The session's ATM/anchor strike (same value as
            ``business.pipeline_context.PipelineContext.reference_strike``),
            or ``None`` if ``WeeklyFutureStage`` never ran that day.
        weekly_future_high: That day's Weekly Future High, or ``None``.
        weekly_future_low: That day's Weekly Future Low, or ``None``.
        top_strike: That day's Top Strike, or ``None``.
        bottom_strike: That day's Bottom Strike, or ``None``.
        diff_atm_to_high: ``weekly_future_high - atm_strike``, or
            ``None`` if either side is missing. Display-only
            arithmetic - not a business rule.
        diff_atm_to_low: ``weekly_future_low - atm_strike``, or
            ``None`` if either side is missing.
    """

    trading_day: date
    atm_strike: Decimal | None
    weekly_future_high: Decimal | None
    weekly_future_low: Decimal | None
    top_strike: Decimal | None
    bottom_strike: Decimal | None
    diff_atm_to_high: Decimal | None
    diff_atm_to_low: Decimal | None

    def __post_init__(self) -> None:
        if self.trading_day is None:
            raise ValidationError("TradingAnalysisRow.trading_day must not be None.")

    @property
    def range(self) -> Decimal | None:
        """``weekly_future_high - weekly_future_low``, or ``None`` if
        either is missing."""
        if self.weekly_future_high is None or self.weekly_future_low is None:
            return None
        return self.weekly_future_high - self.weekly_future_low


@dataclass(frozen=True, slots=True)
class TradingAnalysisSummary:
    """Aggregate "summary card" figures across every row with enough
    data to compute them.

    Attributes:
        trading_days: Total distinct trading days in the rows this
            summary was built from (before any filtering below).
        average_range: Mean of ``TradingAnalysisRow.range`` across
            rows where it is known, or ``None`` if none are.
        largest_range: The maximum such range, or ``None``.
        smallest_range: The minimum such range, or ``None``.
        average_distance_to_top: Mean of
            ``abs(top_strike - atm_strike)`` across rows where both
            are known, or ``None``.
        average_distance_to_bottom: Mean of
            ``abs(bottom_strike - atm_strike)`` across rows where both
            are known, or ``None``.
    """

    trading_days: int
    average_range: Decimal | None
    largest_range: Decimal | None
    smallest_range: Decimal | None
    average_distance_to_top: Decimal | None
    average_distance_to_bottom: Decimal | None

    def __post_init__(self) -> None:
        if self.trading_days < 0:
            raise ValidationError("TradingAnalysisSummary.trading_days must not be negative.")


@dataclass(frozen=True, slots=True)
class ChartPoint:
    """One (date, value) point in a :class:`ChartSeries`."""

    trading_day: date
    value: Decimal | None


@dataclass(frozen=True, slots=True)
class ChartSeries:
    """A named series of :class:`ChartPoint`, ready for any charting
    library or export to plot - this module never renders pixels."""

    name: str
    points: tuple[ChartPoint, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TradingAnalysisFilter:
    """Optional predicates for :meth:`TradingAnalysisDashboard.filtered_rows`.

    Every field is optional; an unset field imposes no constraint.

    Attributes:
        start_date: Keep only rows on or after this date.
        end_date: Keep only rows on or before this date.
        atm_strike: Keep only rows whose ``atm_strike`` equals this value.
        min_range: Keep only rows whose ``range`` is at least this value.
        max_range: Keep only rows whose ``range`` is at most this value.
    """

    start_date: date | None = None
    end_date: date | None = None
    atm_strike: Decimal | None = None
    min_range: Decimal | None = None
    max_range: Decimal | None = None


def build_rows(result: ReplayResult) -> tuple[TradingAnalysisRow, ...]:
    """Build one :class:`TradingAnalysisRow` per trading day in
    ``result``, in date order, reusing
    ``application.replay_dashboard.build_dashboard_rows`` for the
    per-day grouping/value-selection itself."""
    rows = []
    for dashboard_row in build_dashboard_rows(result):
        atm = dashboard_row.reference_strike
        high = dashboard_row.weekly_future_high
        low = dashboard_row.weekly_future_low
        rows.append(
            TradingAnalysisRow(
                trading_day=dashboard_row.trading_day,
                atm_strike=atm,
                weekly_future_high=high,
                weekly_future_low=low,
                top_strike=dashboard_row.top_strike,
                bottom_strike=dashboard_row.bottom_strike,
                diff_atm_to_high=(high - atm) if high is not None and atm is not None else None,
                diff_atm_to_low=(low - atm) if low is not None and atm is not None else None,
            )
        )
    return tuple(rows)


def build_summary(rows: tuple[TradingAnalysisRow, ...]) -> TradingAnalysisSummary:
    """Aggregate ``rows`` into a :class:`TradingAnalysisSummary`."""
    ranges = [row.range for row in rows if row.range is not None]
    top_distances = [
        abs(row.top_strike - row.atm_strike)
        for row in rows
        if row.top_strike is not None and row.atm_strike is not None
    ]
    bottom_distances = [
        abs(row.bottom_strike - row.atm_strike)
        for row in rows
        if row.bottom_strike is not None and row.atm_strike is not None
    ]

    return TradingAnalysisSummary(
        trading_days=len(rows),
        average_range=(sum(ranges, Decimal(0)) / len(ranges)) if ranges else None,
        largest_range=max(ranges) if ranges else None,
        smallest_range=min(ranges) if ranges else None,
        average_distance_to_top=(
            (sum(top_distances, Decimal(0)) / len(top_distances)) if top_distances else None
        ),
        average_distance_to_bottom=(
            (sum(bottom_distances, Decimal(0)) / len(bottom_distances))
            if bottom_distances
            else None
        ),
    )


def build_chart_series(rows: tuple[TradingAnalysisRow, ...]) -> tuple[ChartSeries, ...]:
    """Build the five named chart series over ``rows``, in date order."""

    def _series(name: str, values: tuple) -> ChartSeries:  # type: ignore[type-arg]
        return ChartSeries(
            name=name,
            points=tuple(
                ChartPoint(trading_day=row.trading_day, value=value)
                for row, value in zip(rows, values, strict=True)
            ),
        )

    return (
        _series("Weekly Future High by Date", tuple(row.weekly_future_high for row in rows)),
        _series("Weekly Future Low by Date", tuple(row.weekly_future_low for row in rows)),
        _series("Top Strike by Date", tuple(row.top_strike for row in rows)),
        _series("Bottom Strike by Date", tuple(row.bottom_strike for row in rows)),
        _series("Weekly Future Range by Date", tuple(row.range for row in rows)),
    )


def filter_rows(
    rows: tuple[TradingAnalysisRow, ...], criteria: TradingAnalysisFilter
) -> tuple[TradingAnalysisRow, ...]:
    """Return only the ``rows`` matching every set field in ``criteria``."""
    filtered = []
    for row in rows:
        if criteria.start_date is not None and row.trading_day < criteria.start_date:
            continue
        if criteria.end_date is not None and row.trading_day > criteria.end_date:
            continue
        if criteria.atm_strike is not None and row.atm_strike != criteria.atm_strike:
            continue
        if criteria.min_range is not None and (row.range is None or row.range < criteria.min_range):
            continue
        if criteria.max_range is not None and (row.range is None or row.range > criteria.max_range):
            continue
        filtered.append(row)
    return tuple(filtered)


def write_csv(rows: tuple[TradingAnalysisRow, ...], path: Path) -> None:
    """Write ``rows`` to a CSV file at ``path``, one row per trading
    day, header first."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADER)
        for row in rows:
            writer.writerow(
                (
                    row.trading_day.isoformat(),
                    row.atm_strike,
                    row.weekly_future_high,
                    row.weekly_future_low,
                    row.top_strike,
                    row.bottom_strike,
                    row.diff_atm_to_high,
                    row.diff_atm_to_low,
                )
            )


def write_excel(
    rows: tuple[TradingAnalysisRow, ...], summary: TradingAnalysisSummary, path: Path
) -> None:
    """Write ``rows``/``summary`` to a 2-sheet ``.xlsx`` workbook at
    ``path`` - "Daily Analysis" and "Summary" - overwritten if it
    already exists."""
    workbook = Workbook()

    daily = workbook.active
    assert daily is not None  # a freshly constructed Workbook always has an active sheet
    daily.title = "Daily Analysis"
    daily.append(list(CSV_HEADER))
    for row in rows:
        daily.append(
            [
                row.trading_day.isoformat(),
                row.atm_strike,
                row.weekly_future_high,
                row.weekly_future_low,
                row.top_strike,
                row.bottom_strike,
                row.diff_atm_to_high,
                row.diff_atm_to_low,
            ]
        )

    summary_sheet = workbook.create_sheet("Summary")
    summary_sheet.append(["Metric", "Value"])
    summary_sheet.append(["Trading Days", summary.trading_days])
    summary_sheet.append(["Average Weekly Future Range", summary.average_range])
    summary_sheet.append(["Largest Weekly Future Range", summary.largest_range])
    summary_sheet.append(["Smallest Weekly Future Range", summary.smallest_range])
    summary_sheet.append(["Average Distance to Top Strike", summary.average_distance_to_top])
    summary_sheet.append(["Average Distance to Bottom Strike", summary.average_distance_to_bottom])

    workbook.save(str(path))


class TradingAnalysisDashboard:
    """Trader-facing facade over a single :class:`~application.replay_result.ReplayResult`.

    Built once from a ``ReplayResult``; every method below reads that
    same immutable snapshot - nothing here re-runs the replay or
    recalculates a business value.
    """

    def __init__(self, result: ReplayResult) -> None:
        self._rows = build_rows(result)

    @property
    def rows(self) -> tuple[TradingAnalysisRow, ...]:
        return self._rows

    def summary(self) -> TradingAnalysisSummary:
        return build_summary(self._rows)

    def chart_series(self) -> tuple[ChartSeries, ...]:
        return build_chart_series(self._rows)

    def filtered_rows(self, criteria: TradingAnalysisFilter) -> tuple[TradingAnalysisRow, ...]:
        return filter_rows(self._rows, criteria)

    def export_csv(self, path: Path) -> None:
        write_csv(self._rows, path)

    def export_excel(self, path: Path) -> None:
        write_excel(self._rows, self.summary(), path)

"""HistoricalDataProvider/CsvHistoricalDataProvider.

Traceability
------------
``HistoricalDataProvider`` holds every validation/assembly rule,
parameterized over the format-agnostic
:class:`~data.historical_data_source.HistoricalDataSource` Protocol -
see that module's docstring for why. ``CsvHistoricalDataProvider`` is
a thin convenience wrapper that constructs a
:class:`~data.historical_data_source.CsvHistoricalDataSource` and
delegates; it holds no validation logic of its own, so a future
Parquet/SQL/API provider only needs an equally thin wrapper around its
own source, never a second copy of the validation rules.

Required CSV columns mirror ``trading_engine/replay/history_loader.py``'s
own schema (``Date``, ``Time``, ``Open``, ``High``, ``Low``, ``Close``,
``Volume``) for consistency with that already-proven loader elsewhere
in this repository - not because of new evidence, and not imported
from it (see this sprint's Architecture Review: ``trading_engine`` is
a separate package boundary with an incompatible candle model).
Optional ``UnderlyingPrice`` and ``OpenInterest`` columns may also be
present (``OpenInterest`` added for
``trend_engine.open_interest_trend_engine.OpenInterestTrendEngine``,
2026-08-02 - Upstox's v3 historical-candle endpoint returns it as a
7th element per row for F&O instruments).

Engineering default (not a trading rule, see package docstring):
``MarketSnapshot.underlying_price`` defaults to the candle's own
``Close`` when no ``UnderlyingPrice`` column is supplied.
"""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import tzinfo as TzInfo
from decimal import Decimal, InvalidOperation
from pathlib import Path

from core.exceptions import HistoricalDataError, ValidationError
from data.historical_data_source import CsvHistoricalDataSource, HistoricalDataSource
from data.historical_data_validation import (
    HistoricalDataIssue,
    HistoricalDataIssueKind,
    HistoricalDataValidation,
)
from data.historical_dataset import HistoricalDataset
from models.market_snapshot import MarketSnapshot

_REQUIRED_COLUMNS = ("Date", "Time", "Open", "High", "Low", "Close", "Volume")
_MAX_ISSUES_IN_MESSAGE = 10


class HistoricalDataProvider:
    """Validates and assembles a
    :class:`~data.historical_dataset.HistoricalDataset` from any
    :class:`~data.historical_data_source.HistoricalDataSource`.

    Stateless, format-agnostic - no constructor dependencies.
    """

    def validate(
        self, source: HistoricalDataSource, tzinfo: TzInfo = UTC
    ) -> HistoricalDataValidation:
        """Validate ``source`` without raising, for a caller that
        wants to inspect every issue rather than catch an exception."""
        _, issues = self._parse(source, tzinfo)
        return HistoricalDataValidation(issues=issues)

    def load(
        self, source: HistoricalDataSource, symbol: str, timeframe: str, tzinfo: TzInfo = UTC
    ) -> HistoricalDataset:
        """Validate and assemble ``source`` into a
        :class:`~data.historical_dataset.HistoricalDataset`.

        Raises:
            core.exceptions.HistoricalDataError: if validation finds
                any issue - see :meth:`validate` to inspect issues
                without raising.
        """
        snapshots, issues = self._parse(source, tzinfo)
        if issues:
            raise HistoricalDataError(self._summarize(symbol, timeframe, issues))

        ordered = tuple(sorted(snapshots, key=lambda snapshot: snapshot.timestamp))
        return HistoricalDataset(
            symbol=symbol,
            timeframe=timeframe,
            date_range_start=ordered[0].timestamp.date(),
            date_range_end=ordered[-1].timestamp.date(),
            snapshots=ordered,
            metadata={"row_count": str(len(ordered))},
        )

    def _parse(
        self, source: HistoricalDataSource, tzinfo: TzInfo
    ) -> tuple[tuple[MarketSnapshot, ...], tuple[HistoricalDataIssue, ...]]:
        rows = list(source.read_rows())
        if not rows:
            return (), (
                HistoricalDataIssue(
                    kind=HistoricalDataIssueKind.SCHEMA_ERROR, detail="Source produced no rows."
                ),
            )

        missing_columns = [column for column in _REQUIRED_COLUMNS if column not in rows[0]]
        if missing_columns:
            return (), (
                HistoricalDataIssue(
                    kind=HistoricalDataIssueKind.SCHEMA_ERROR,
                    detail=f"Missing required column(s): {', '.join(missing_columns)}.",
                ),
            )

        issues: list[HistoricalDataIssue] = []
        snapshots: list[MarketSnapshot] = []
        seen_timestamps: dict[datetime, int] = {}

        for row_number, row in enumerate(rows, start=1):
            timestamp = self._parse_timestamp(row, row_number, tzinfo, issues)
            if timestamp is None:
                continue
            if timestamp in seen_timestamps:
                issues.append(
                    HistoricalDataIssue(
                        kind=HistoricalDataIssueKind.DUPLICATE_TIMESTAMP,
                        detail=(
                            f"Duplicate timestamp {timestamp.isoformat()} "
                            f"(first seen at row {seen_timestamps[timestamp]})."
                        ),
                        row_number=row_number,
                    )
                )
                continue
            seen_timestamps[timestamp] = row_number

            snapshot = self._parse_snapshot(row, row_number, timestamp, issues)
            if snapshot is not None:
                snapshots.append(snapshot)

        return tuple(snapshots), tuple(issues)

    def _parse_timestamp(
        self,
        row: dict[str, str],
        row_number: int,
        tzinfo: TzInfo,
        issues: list[HistoricalDataIssue],
    ) -> datetime | None:
        date_str = row.get("Date", "").strip()
        time_str = row.get("Time", "").strip()
        if not date_str or not time_str:
            issues.append(
                HistoricalDataIssue(
                    kind=HistoricalDataIssueKind.MISSING_TIMESTAMP,
                    detail="Date and/or Time column is blank.",
                    row_number=row_number,
                )
            )
            return None
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=tzinfo
            )
        except ValueError as exc:
            issues.append(
                HistoricalDataIssue(
                    kind=HistoricalDataIssueKind.SCHEMA_ERROR,
                    detail=f"Could not parse timestamp '{date_str} {time_str}': {exc}",
                    row_number=row_number,
                )
            )
            return None

    def _parse_snapshot(
        self,
        row: dict[str, str],
        row_number: int,
        timestamp: datetime,
        issues: list[HistoricalDataIssue],
    ) -> MarketSnapshot | None:
        try:
            open_ = Decimal(row["Open"])
            high = Decimal(row["High"])
            low = Decimal(row["Low"])
            close = Decimal(row["Close"])
            volume = int(row["Volume"])
        except (KeyError, InvalidOperation, ValueError) as exc:
            issues.append(
                HistoricalDataIssue(
                    kind=HistoricalDataIssueKind.SCHEMA_ERROR,
                    detail=f"Could not parse numeric field: {exc}",
                    row_number=row_number,
                )
            )
            return None

        underlying_raw = row.get("UnderlyingPrice", "").strip()
        underlying_price = Decimal(underlying_raw) if underlying_raw else close

        open_interest_raw = row.get("OpenInterest", "").strip()
        try:
            open_interest = int(open_interest_raw) if open_interest_raw else None
        except ValueError as exc:
            issues.append(
                HistoricalDataIssue(
                    kind=HistoricalDataIssueKind.SCHEMA_ERROR,
                    detail=f"Could not parse numeric field: {exc}",
                    row_number=row_number,
                )
            )
            return None

        try:
            return MarketSnapshot(
                timestamp=timestamp,
                underlying_price=underlying_price,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
                open_interest=open_interest,
            )
        except ValidationError as exc:
            kind = (
                HistoricalDataIssueKind.INVALID_VOLUME
                if "volume" in str(exc).lower()
                else HistoricalDataIssueKind.INVALID_OHLC
            )
            issues.append(HistoricalDataIssue(kind=kind, detail=str(exc), row_number=row_number))
            return None

    @staticmethod
    def _summarize(symbol: str, timeframe: str, issues: tuple[HistoricalDataIssue, ...]) -> str:
        shown = issues[:_MAX_ISSUES_IN_MESSAGE]
        detail = "; ".join(
            (
                f"row {issue.row_number}: {issue.kind.value}: {issue.detail}"
                if issue.row_number is not None
                else f"{issue.kind.value}: {issue.detail}"
            )
            for issue in shown
        )
        suffix = "..." if len(issues) > _MAX_ISSUES_IN_MESSAGE else ""
        return f"{len(issues)} validation issue(s) for {symbol} ({timeframe}): {detail}{suffix}"


class CsvHistoricalDataProvider:
    """Convenience wrapper: loads a CSV file straight into a
    :class:`~data.historical_dataset.HistoricalDataset`.

    Holds no validation logic of its own - delegates entirely to an
    injected :class:`HistoricalDataProvider`.
    """

    def __init__(self, provider: HistoricalDataProvider | None = None) -> None:
        self._provider = provider if provider is not None else HistoricalDataProvider()

    def load_csv(
        self, path: Path, symbol: str, timeframe: str, tzinfo: TzInfo = UTC
    ) -> HistoricalDataset:
        """Validate and load the CSV at ``path``.

        Raises:
            core.exceptions.HistoricalDataError: on a read failure or
                any validation issue.
        """
        return self._provider.load(CsvHistoricalDataSource(path), symbol, timeframe, tzinfo)

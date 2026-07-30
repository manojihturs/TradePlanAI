"""HistoryLoader: load and validate historical OHLC candles from CSV.

Traceability notes
-------------------
Pure infrastructure - reads a CSV file, validates it structurally, and
produces immutable, typed :class:`Candle` objects. No trading
mathematics, no strategy logic: nothing here decides what a candle
*means*, only whether the data is well-formed enough to replay.

Missing-row detection is deliberately **not** enforced as a load-time
failure (see :meth:`HistoryLoader.detect_missing_candles`): distinguishing
a genuine data gap from a legitimate market closure (a weekend, a
holiday) would require a market calendar this repository has no
evidenced source for - inventing one would be exactly the kind of
guessed business knowledge this project's evidence-first discipline
forbids. Missing-row detection is therefore an opt-in, informational
report over an already-loaded sequence, not a load-blocking check.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from trading_engine.replay.exceptions import HistoryLoadError

#: The CSV columns this loader requires, per Milestone B1's Task 2.
REQUIRED_COLUMNS = ("Date", "Time", "Open", "High", "Low", "Close", "Volume")

#: A gap between consecutive candles is flagged by
#: :meth:`HistoryLoader.detect_missing_candles` once it exceeds the
#: modal (most common) inter-candle interval by this factor. A pure
#: statistical heuristic over the loaded data itself - not a market
#: calendar, not a trading rule.
_GAP_DETECTION_FACTOR = 1.5


@dataclass(frozen=True)
class Candle:
    """One immutable, validated OHLC candle.

    Attributes:
        timestamp: The candle's date and time, combined from the
            source CSV's ``Date``/``Time`` columns.
        open: Opening price.
        high: Highest price. Must be the maximum of the four prices.
        low: Lowest price. Must be the minimum of the four prices.
        close: Closing price.
        volume: Traded volume. Must not be negative.
    """

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def __post_init__(self) -> None:
        if self.timestamp is None:
            raise HistoryLoadError("Candle.timestamp must not be None.")

        if self.high < self.low:
            raise HistoryLoadError(
                f"Candle at {self.timestamp}: high ({self.high}) is less than low ({self.low})."
            )

        if not (self.low <= self.open <= self.high):
            raise HistoryLoadError(
                f"Candle at {self.timestamp}: open ({self.open}) is outside "
                f"[low, high] = [{self.low}, {self.high}]."
            )

        if not (self.low <= self.close <= self.high):
            raise HistoryLoadError(
                f"Candle at {self.timestamp}: close ({self.close}) is outside "
                f"[low, high] = [{self.low}, {self.high}]."
            )

        if self.volume < 0:
            raise HistoryLoadError(
                f"Candle at {self.timestamp}: volume ({self.volume}) must not be negative."
            )


@dataclass(frozen=True)
class MissingCandleGap:
    """A detected gap between two consecutive candles, larger than the
    sequence's own modal inter-candle interval.

    A purely statistical observation over the loaded data - carries no
    judgment about whether the gap is a data error or a legitimate
    market closure (see module docstring).

    Attributes:
        after: The timestamp of the candle immediately before the gap.
        before: The timestamp of the candle immediately after the gap.
        expected_interval_seconds: The sequence's modal (most common)
            inter-candle interval, in seconds.
        actual_gap_seconds: The actual interval observed here, in
            seconds.
    """

    after: datetime
    before: datetime
    expected_interval_seconds: float
    actual_gap_seconds: float


class HistoryLoader:
    """Loads historical OHLC candles from a CSV file.

    Responsibilities: column/type/structural validation, chronological
    ordering (candles are sorted by timestamp on load), and
    duplicate-timestamp rejection. See module docstring for why
    missing-row detection is a separate, opt-in, non-blocking method.
    """

    def load(self, path: str | Path) -> tuple[Candle, ...]:
        """Load, validate, and chronologically sort every candle in
        the CSV file at ``path``.

        Raises:
            HistoryLoadError: if the file does not exist, has no
                header row, is missing a required column, contains an
                unparsable value, contains a structurally invalid
                candle, or contains a duplicate timestamp.
        """
        csv_path = Path(path)
        if not csv_path.is_file():
            raise HistoryLoadError(f"CSV file not found: {csv_path}")

        with csv_path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise HistoryLoadError(f"CSV file has no header row: {csv_path}")

            missing_columns = [
                column for column in REQUIRED_COLUMNS if column not in reader.fieldnames
            ]
            if missing_columns:
                raise HistoryLoadError(
                    f"{csv_path} is missing required column(s): {', '.join(missing_columns)}."
                )

            candles = [
                self._parse_row(row, csv_path, line_number)
                for line_number, row in enumerate(reader, start=2)
            ]

        if not candles:
            raise HistoryLoadError(f"{csv_path} contains no data rows.")

        candles.sort(key=lambda candle: candle.timestamp)
        self._reject_duplicate_timestamps(candles, csv_path)

        return tuple(candles)

    def _parse_row(self, row: dict[str, str | None], path: Path, line_number: int) -> Candle:
        date_value = row.get("Date")
        time_value = row.get("Time")
        if not date_value or not time_value:
            raise HistoryLoadError(f"{path} line {line_number}: Date and Time must not be blank.")

        try:
            timestamp = datetime.strptime(  # noqa: DTZ007 - no timezone requirement is evidenced anywhere in the domain
                f"{date_value.strip()} {time_value.strip()}", "%Y-%m-%d %H:%M:%S"
            )
        except ValueError as exc:
            raise HistoryLoadError(
                f"{path} line {line_number}: could not parse Date/Time "
                f"{date_value!r} {time_value!r} (expected YYYY-MM-DD HH:MM:SS)."
            ) from exc

        try:
            open_price = Decimal(str(row.get("Open")).strip())
            high_price = Decimal(str(row.get("High")).strip())
            low_price = Decimal(str(row.get("Low")).strip())
            close_price = Decimal(str(row.get("Close")).strip())
        except InvalidOperation as exc:
            raise HistoryLoadError(
                f"{path} line {line_number}: could not parse Open/High/Low/Close as decimal numbers."
            ) from exc

        volume_value = row.get("Volume")
        try:
            volume = int(str(volume_value).strip())
        except ValueError as exc:
            raise HistoryLoadError(
                f"{path} line {line_number}: could not parse Volume {volume_value!r} as an integer."
            ) from exc

        try:
            return Candle(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        except HistoryLoadError as exc:
            raise HistoryLoadError(f"{path} line {line_number}: {exc}") from exc

    def _reject_duplicate_timestamps(self, candles: list[Candle], path: Path) -> None:
        counts = Counter(candle.timestamp for candle in candles)
        duplicates = sorted(timestamp for timestamp, count in counts.items() if count > 1)
        if duplicates:
            formatted = ", ".join(str(timestamp) for timestamp in duplicates)
            raise HistoryLoadError(f"{path} contains duplicate timestamp(s): {formatted}.")

    def detect_missing_candles(self, candles: tuple[Candle, ...]) -> tuple[MissingCandleGap, ...]:
        """Report gaps between consecutive candles that are larger
        than the sequence's own modal inter-candle interval.

        Informational only - never raises, never blocks
        :meth:`load`. Returns an empty tuple if fewer than 3 candles
        are given (not enough data to establish a modal interval) or
        if the modal interval itself is non-positive (all candles
        share one timestamp cluster - already impossible after
        :meth:`load`'s duplicate check, but guarded here defensively
        for direct callers of this method).
        """
        if len(candles) < 3:
            return ()

        deltas = [
            (candles[index + 1].timestamp - candles[index].timestamp).total_seconds()
            for index in range(len(candles) - 1)
        ]
        modal_delta = Counter(deltas).most_common(1)[0][0]
        if modal_delta <= 0:
            return ()

        gaps = []
        for index in range(len(candles) - 1):
            actual_gap = (candles[index + 1].timestamp - candles[index].timestamp).total_seconds()
            if actual_gap > modal_delta * _GAP_DETECTION_FACTOR:
                gaps.append(
                    MissingCandleGap(
                        after=candles[index].timestamp,
                        before=candles[index + 1].timestamp,
                        expected_interval_seconds=modal_delta,
                        actual_gap_seconds=actual_gap,
                    )
                )
        return tuple(gaps)

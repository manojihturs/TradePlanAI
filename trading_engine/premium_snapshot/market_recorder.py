"""MarketRecorder: records every observed market tick to a repository.

Traceability notes
-------------------
Milestone I2's "MARKET RECORDER" task: receive every
:class:`~trading_engine.market_data.market_tick.MarketTick`, persist
Timestamp/Spot/Strike/CE Price/PE Price/Volume/OI/Bid/Ask, with a
Repository abstraction supporting both CSV and SQLite and no hard
dependency on either (same ``typing.Protocol`` pattern as
:mod:`trading_engine.premium_snapshot.premium_snapshot_repository`).

A single :class:`MarketTick` carries only one instrument's own
fields (timestamp/instrument/LTP/volume/OI/bid/ask) - it has no Spot,
Strike, or CE-vs-PE distinction, since those require combining
several concurrent instruments' observations (spot, one strike's CE,
that strike's PE) at one moment, and no document evidences how a
broker would deliver that combination pre-joined. Rather than invent
a join/tagging rule, :class:`TickRecord` carries the full field list
Milestone I2 asks for as independently optional columns, and the
caller (who already knows which instrument is which) supplies
whichever fields it has via :meth:`TickRecord.from_tick`.

Recording every tick during Paper Trading (rather than only the
Premium Snapshot Engine's own capture window) is the mechanism that
later lets Replay, Backtest, Strategy Validation, and Debugging work
from real captured data instead of invented data - consistent with
this whole package's data-capture-only scope.
"""

from __future__ import annotations

import csv
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol, runtime_checkable

from trading_engine.diagnostics.sink import DiagnosticsSink, NullDiagnosticsSink
from trading_engine.market_data.market_tick import MarketTick
from trading_engine.premium_snapshot.exceptions import (
    RecorderError,
    RepositoryError,
    SnapshotValidationError,
)
from trading_engine.premium_snapshot.premium_snapshot_events import (
    RecorderFlushed,
    RecorderStarted,
    RecorderStopped,
)

_COLUMNS = (
    "timestamp",
    "spot",
    "strike",
    "ce_price",
    "pe_price",
    "volume",
    "open_interest",
    "bid",
    "ask",
)


def _decimal_or_none(value: str) -> Decimal | None:
    return None if value in ("", "None") else Decimal(value)


def _int_or_none(value: str) -> int | None:
    return None if value in ("", "None") else int(value)


@dataclass(frozen=True)
class TickRecord:
    """One row of recorded market observation.

    Attributes:
        timestamp: When this observation was made.
        spot: The underlying's spot price, if known at record time.
        strike: The strike this record pertains to, if any.
        ce_price: The CE side's last traded price, if this record is
            (or includes) a CE observation.
        pe_price: The PE side's last traded price, if this record is
            (or includes) a PE observation.
        volume: Traded volume, if known.
        open_interest: Open interest, if known.
        bid: Best bid price, if known.
        ask: Best ask price, if known.
    """

    timestamp: datetime
    spot: Decimal | None = None
    strike: Decimal | None = None
    ce_price: Decimal | None = None
    pe_price: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            raise SnapshotValidationError("TickRecord.timestamp must not be None.")
        if self.volume is not None and self.volume < 0:
            raise SnapshotValidationError("TickRecord.volume must not be negative.")
        if self.open_interest is not None and self.open_interest < 0:
            raise SnapshotValidationError("TickRecord.open_interest must not be negative.")
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise SnapshotValidationError(
                f"TickRecord.bid ({self.bid}) must not exceed ask ({self.ask})."
            )

    @classmethod
    def from_tick(
        cls,
        tick: MarketTick,
        spot: Decimal | None = None,
        strike: Decimal | None = None,
        ce_price: Decimal | None = None,
        pe_price: Decimal | None = None,
    ) -> TickRecord:
        """Build a :class:`TickRecord` from a raw tick plus whatever
        Spot/Strike/CE/PE context the caller has - ``MarketTick``
        itself carries none of those (see module docstring)."""
        return cls(
            timestamp=tick.timestamp,
            spot=spot,
            strike=strike,
            ce_price=ce_price,
            pe_price=pe_price,
            volume=tick.volume,
            open_interest=tick.open_interest,
            bid=tick.bid,
            ask=tick.ask,
        )

    def to_row(self) -> dict[str, str]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "spot": "" if self.spot is None else str(self.spot),
            "strike": "" if self.strike is None else str(self.strike),
            "ce_price": "" if self.ce_price is None else str(self.ce_price),
            "pe_price": "" if self.pe_price is None else str(self.pe_price),
            "volume": "" if self.volume is None else str(self.volume),
            "open_interest": "" if self.open_interest is None else str(self.open_interest),
            "bid": "" if self.bid is None else str(self.bid),
            "ask": "" if self.ask is None else str(self.ask),
        }

    @classmethod
    def from_row(cls, row: dict[str, str]) -> TickRecord:
        return cls(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            spot=_decimal_or_none(row["spot"]),
            strike=_decimal_or_none(row["strike"]),
            ce_price=_decimal_or_none(row["ce_price"]),
            pe_price=_decimal_or_none(row["pe_price"]),
            volume=_int_or_none(row["volume"]),
            open_interest=_int_or_none(row["open_interest"]),
            bid=_decimal_or_none(row["bid"]),
            ask=_decimal_or_none(row["ask"]),
        )


@runtime_checkable
class TickRecordRepository(Protocol):
    """The structural contract every tick-record repository satisfies
    - append one record, flush any buffered records, and read
    everything back. No hard dependency on CSV or SQLite - both are
    interchangeable implementations of this same Protocol."""

    def append(self, record: TickRecord) -> None:
        """Add one record."""
        ...

    def flush(self) -> None:
        """Ensure every appended record is durably persisted."""
        ...

    def all_records(self) -> tuple[TickRecord, ...]:
        """Every record persisted so far, in append order."""
        ...


class InMemoryTickRecordRepository:
    """A dependency-free repository backed by a plain list. Records
    are already "durable" in memory, so :meth:`flush` is a no-op."""

    def __init__(self) -> None:
        self._records: list[TickRecord] = []

    def append(self, record: TickRecord) -> None:
        self._records.append(record)

    def flush(self) -> None:
        return None

    def all_records(self) -> tuple[TickRecord, ...]:
        return tuple(self._records)


class CsvTickRecordRepository:
    """Buffers records in memory and appends them to a CSV file on
    :meth:`flush` (and on :meth:`all_records`, which reads the file
    back)."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._buffer: list[TickRecord] = []

    def append(self, record: TickRecord) -> None:
        self._buffer.append(record)

    def flush(self) -> None:
        if not self._buffer:
            return
        is_new_file = not self._path.is_file()
        try:
            with self._path.open("a", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=_COLUMNS)
                if is_new_file:
                    writer.writeheader()
                for record in self._buffer:
                    writer.writerow(record.to_row())
        except OSError as exc:
            raise RepositoryError(f"Could not write tick records to {self._path}: {exc}") from exc
        self._buffer = []

    def all_records(self) -> tuple[TickRecord, ...]:
        if not self._path.is_file():
            return tuple(self._buffer)
        try:
            with self._path.open(newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                persisted = [TickRecord.from_row(dict(row)) for row in reader]
        except OSError as exc:
            raise RepositoryError(f"Could not read tick records from {self._path}: {exc}") from exc
        return tuple(persisted) + tuple(self._buffer)


class SqliteTickRecordRepository:
    """Buffers records in memory and writes them to a SQLite database
    file (via the standard library :mod:`sqlite3` module) on
    :meth:`flush`."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._buffer: list[TickRecord] = []
        try:
            connection = sqlite3.connect(self._path)
            try:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS tick_records ("
                    "row_order INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "timestamp TEXT, spot TEXT, strike TEXT, ce_price TEXT, "
                    "pe_price TEXT, volume TEXT, open_interest TEXT, bid TEXT, ask TEXT)"
                )
                connection.commit()
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise RepositoryError(
                f"Could not initialise SQLite database at {self._path}: {exc}"
            ) from exc

    def append(self, record: TickRecord) -> None:
        self._buffer.append(record)

    def flush(self) -> None:
        if not self._buffer:
            return
        try:
            connection = sqlite3.connect(self._path)
            try:
                connection.executemany(
                    "INSERT INTO tick_records "
                    "(timestamp, spot, strike, ce_price, pe_price, volume, open_interest, bid, ask) "
                    "VALUES (:timestamp, :spot, :strike, :ce_price, :pe_price, :volume, "
                    ":open_interest, :bid, :ask)",
                    [record.to_row() for record in self._buffer],
                )
                connection.commit()
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise RepositoryError(f"Could not write tick records to {self._path}: {exc}") from exc
        self._buffer = []

    def all_records(self) -> tuple[TickRecord, ...]:
        try:
            connection = sqlite3.connect(self._path)
            try:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute("SELECT * FROM tick_records ORDER BY row_order")
                persisted = [TickRecord.from_row(dict(row)) for row in cursor.fetchall()]
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise RepositoryError(f"Could not read tick records from {self._path}: {exc}") from exc
        return tuple(persisted) + tuple(self._buffer)


class MarketRecorder:
    """Records every observed market tick (as a :class:`TickRecord`)
    to an injected :class:`TickRecordRepository`.

    Lifecycle: :meth:`start` (required before recording), any number
    of :meth:`record` calls, :meth:`flush` (durably persists buffered
    records without stopping), and :meth:`stop` (flushes, then marks
    the recorder as not running).
    """

    def __init__(
        self,
        repository: TickRecordRepository,
        recorder_name: str = "market_recorder",
        diagnostics_sink: DiagnosticsSink | None = None,
        clock: Callable[[], datetime] = datetime.now,
        id_factory: Callable[[], uuid.UUID] = uuid.uuid4,
    ) -> None:
        self._repository = repository
        self._recorder_name = recorder_name
        self._sink: DiagnosticsSink = (
            diagnostics_sink if diagnostics_sink is not None else NullDiagnosticsSink()
        )
        self._clock = clock
        self._id_factory = id_factory
        self._running = False
        self._pending_count = 0

    def start(self) -> None:
        if self._running:
            raise RecorderError(f"Recorder {self._recorder_name!r} is already running.")
        self._running = True
        self._pending_count = 0
        self._sink.emit(
            RecorderStarted(
                event_id=self._id_factory(),
                occurred_at=self._clock(),
                recorder_name=self._recorder_name,
            )
        )

    def record(self, record: TickRecord) -> None:
        if not self._running:
            raise RecorderError(
                f"Recorder {self._recorder_name!r} is not running; call start() first."
            )
        self._repository.append(record)
        self._pending_count += 1

    def flush(self) -> int:
        """Flush buffered records and emit :class:`RecorderFlushed`.
        Returns how many records were flushed - tracked independently
        of the repository's own storage semantics, since an in-memory
        repository already considers appended records "durable" and
        would otherwise report zero on every flush."""
        self._repository.flush()
        flushed = self._pending_count
        self._pending_count = 0
        self._sink.emit(
            RecorderFlushed(
                event_id=self._id_factory(),
                occurred_at=self._clock(),
                recorder_name=self._recorder_name,
                record_count=flushed,
            )
        )
        return flushed

    def stop(self) -> int:
        """Flush, then stop the recorder. Returns how many records
        were flushed as part of stopping."""
        if not self._running:
            raise RecorderError(f"Recorder {self._recorder_name!r} is not running.")
        flushed = self.flush()
        self._running = False
        self._sink.emit(
            RecorderStopped(
                event_id=self._id_factory(),
                occurred_at=self._clock(),
                recorder_name=self._recorder_name,
                records_flushed=flushed,
            )
        )
        return flushed

    @property
    def is_running(self) -> bool:
        return self._running

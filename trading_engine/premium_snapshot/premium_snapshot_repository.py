"""PremiumSnapshotRepository: persistence for completed premium
snapshots.

Traceability notes
-------------------
Milestone I2 requires Save/Load/Latest/Historical operations with "no
hard dependency" on either CSV or SQLite. Both are Python standard
library modules (:mod:`csv`, :mod:`sqlite3`) - using them does not
violate this repository's "zero third-party dependencies" convention,
consistent with :mod:`trading_engine.replay.history_loader`'s existing
use of :mod:`csv`. The abstraction itself is a ``typing.Protocol``,
the same pattern already used for
:class:`trading_engine.diagnostics.sink.DiagnosticsSink` and
:class:`trading_engine.market_data.upstox_provider.RestTransport` -
callers inject whichever backend they want; nothing here requires
one.

Each snapshot is stored as one row: the four core contracts and the
range contracts are serialised with the standard library's
:mod:`json` module (also standard library) into per-column blobs,
keeping the on-disk schema flat and avoiding a multi-row
reconstruction problem. No trading value is computed or interpreted
here - purely mechanical (de)serialisation of already-validated
:class:`~trading_engine.premium_snapshot.premium_snapshot_models.PremiumSnapshot`
objects.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol, runtime_checkable

from trading_engine.market_data.instrument_resolver import InstrumentKey, OptionType
from trading_engine.premium_snapshot.exceptions import RepositoryError
from trading_engine.premium_snapshot.premium_snapshot_models import (
    ContractSnapshot,
    PremiumSnapshot,
)

_COLUMNS = (
    "snapshot_id",
    "session_id",
    "capture_window_start",
    "capture_window_end",
    "top_strike",
    "bottom_strike",
    "top_ce",
    "top_pe",
    "bottom_ce",
    "bottom_pe",
    "range_contracts",
)


def _contract_to_dict(contract: ContractSnapshot | None) -> dict[str, str] | None:
    if contract is None:
        return None
    return {
        "token": contract.instrument.token,
        "symbol": contract.instrument.symbol,
        "exchange": contract.instrument.exchange,
        "strike": str(contract.strike),
        "option_type": contract.option_type.name,
        "timestamp": contract.timestamp.isoformat(),
        "open": str(contract.open),
        "high": str(contract.high),
        "low": str(contract.low),
        "close": str(contract.close),
        "last_traded_price": str(contract.last_traded_price),
        "volume": str(contract.volume),
        "open_interest": str(contract.open_interest),
    }


def _dict_to_contract(data: dict[str, str] | None) -> ContractSnapshot | None:
    if data is None:
        return None
    return ContractSnapshot(
        instrument=InstrumentKey(
            token=data["token"], symbol=data["symbol"], exchange=data["exchange"]
        ),
        strike=Decimal(data["strike"]),
        option_type=OptionType[data["option_type"]],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        open=Decimal(data["open"]),
        high=Decimal(data["high"]),
        low=Decimal(data["low"]),
        close=Decimal(data["close"]),
        last_traded_price=Decimal(data["last_traded_price"]),
        volume=int(data["volume"]),
        open_interest=int(data["open_interest"]),
    )


def _snapshot_to_row(snapshot: PremiumSnapshot) -> dict[str, str]:
    return {
        "snapshot_id": str(snapshot.snapshot_id),
        "session_id": str(snapshot.session_id),
        "capture_window_start": snapshot.capture_window_start.isoformat(),
        "capture_window_end": snapshot.capture_window_end.isoformat(),
        "top_strike": str(snapshot.top_strike),
        "bottom_strike": str(snapshot.bottom_strike),
        "top_ce": json.dumps(_contract_to_dict(snapshot.top_ce)),
        "top_pe": json.dumps(_contract_to_dict(snapshot.top_pe)),
        "bottom_ce": json.dumps(_contract_to_dict(snapshot.bottom_ce)),
        "bottom_pe": json.dumps(_contract_to_dict(snapshot.bottom_pe)),
        "range_contracts": json.dumps([_contract_to_dict(c) for c in snapshot.range_contracts]),
    }


def _row_to_snapshot(row: dict[str, str]) -> PremiumSnapshot:
    try:
        return PremiumSnapshot(
            snapshot_id=uuid.UUID(row["snapshot_id"]),
            session_id=uuid.UUID(row["session_id"]),
            capture_window_start=datetime.fromisoformat(row["capture_window_start"]),
            capture_window_end=datetime.fromisoformat(row["capture_window_end"]),
            top_strike=Decimal(row["top_strike"]),
            bottom_strike=Decimal(row["bottom_strike"]),
            top_ce=_dict_to_contract(json.loads(row["top_ce"])),
            top_pe=_dict_to_contract(json.loads(row["top_pe"])),
            bottom_ce=_dict_to_contract(json.loads(row["bottom_ce"])),
            bottom_pe=_dict_to_contract(json.loads(row["bottom_pe"])),
            range_contracts=tuple(
                contract
                for contract in (_dict_to_contract(c) for c in json.loads(row["range_contracts"]))
                if contract is not None
            ),
        )
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise RepositoryError(
            f"Could not reconstruct a PremiumSnapshot from a stored row: {exc}"
        ) from exc


@runtime_checkable
class PremiumSnapshotRepository(Protocol):
    """The structural contract every premium snapshot repository
    satisfies - Save, Load, Latest, Historical, per Milestone I2."""

    def save(self, snapshot: PremiumSnapshot) -> None:
        """Persist one snapshot."""
        ...

    def load(self, snapshot_id: uuid.UUID) -> PremiumSnapshot | None:
        """Load one snapshot by id, or ``None`` if not found."""
        ...

    def latest(self, session_id: uuid.UUID) -> PremiumSnapshot | None:
        """The most recently saved snapshot for a session, or
        ``None`` if none exist."""
        ...

    def historical(self, session_id: uuid.UUID) -> tuple[PremiumSnapshot, ...]:
        """Every snapshot saved for a session, in save order."""
        ...


@dataclass
class InMemoryPremiumSnapshotRepository:
    """A dependency-free repository backed by a plain list. The
    default choice for tests and for callers with no persistence
    requirement."""

    _snapshots: list[PremiumSnapshot]

    def __init__(self) -> None:
        self._snapshots = []

    def save(self, snapshot: PremiumSnapshot) -> None:
        self._snapshots.append(snapshot)

    def load(self, snapshot_id: uuid.UUID) -> PremiumSnapshot | None:
        for snapshot in self._snapshots:
            if snapshot.snapshot_id == snapshot_id:
                return snapshot
        return None

    def latest(self, session_id: uuid.UUID) -> PremiumSnapshot | None:
        matches = [s for s in self._snapshots if s.session_id == session_id]
        return matches[-1] if matches else None

    def historical(self, session_id: uuid.UUID) -> tuple[PremiumSnapshot, ...]:
        return tuple(s for s in self._snapshots if s.session_id == session_id)


class CsvPremiumSnapshotRepository:
    """Persists snapshots as one flattened row per snapshot in a CSV
    file, appending on every :meth:`save`."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def save(self, snapshot: PremiumSnapshot) -> None:
        is_new_file = not self._path.is_file()
        try:
            with self._path.open("a", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=_COLUMNS)
                if is_new_file:
                    writer.writeheader()
                writer.writerow(_snapshot_to_row(snapshot))
        except OSError as exc:
            raise RepositoryError(f"Could not write snapshot to {self._path}: {exc}") from exc

    def _read_all(self) -> list[PremiumSnapshot]:
        if not self._path.is_file():
            return []
        try:
            with self._path.open(newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                return [_row_to_snapshot(dict(row)) for row in reader]
        except OSError as exc:
            raise RepositoryError(f"Could not read snapshots from {self._path}: {exc}") from exc

    def load(self, snapshot_id: uuid.UUID) -> PremiumSnapshot | None:
        for snapshot in self._read_all():
            if snapshot.snapshot_id == snapshot_id:
                return snapshot
        return None

    def latest(self, session_id: uuid.UUID) -> PremiumSnapshot | None:
        matches = [s for s in self._read_all() if s.session_id == session_id]
        return matches[-1] if matches else None

    def historical(self, session_id: uuid.UUID) -> tuple[PremiumSnapshot, ...]:
        return tuple(s for s in self._read_all() if s.session_id == session_id)


class SqlitePremiumSnapshotRepository:
    """Persists snapshots as one flattened row per snapshot in a
    SQLite database file, via the standard library :mod:`sqlite3`
    module."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        try:
            connection = sqlite3.connect(self._path)
            try:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS premium_snapshots ("
                    "snapshot_id TEXT PRIMARY KEY, session_id TEXT, "
                    "capture_window_start TEXT, capture_window_end TEXT, "
                    "top_strike TEXT, bottom_strike TEXT, "
                    "top_ce TEXT, top_pe TEXT, bottom_ce TEXT, bottom_pe TEXT, "
                    "range_contracts TEXT, save_order INTEGER)"
                )
                connection.commit()
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise RepositoryError(
                f"Could not initialise SQLite database at {self._path}: {exc}"
            ) from exc

    def save(self, snapshot: PremiumSnapshot) -> None:
        row = _snapshot_to_row(snapshot)
        try:
            connection = sqlite3.connect(self._path)
            try:
                cursor = connection.execute(
                    "SELECT COALESCE(MAX(save_order), -1) FROM premium_snapshots"
                )
                next_order = cursor.fetchone()[0] + 1
                connection.execute(
                    "INSERT OR REPLACE INTO premium_snapshots "
                    "(snapshot_id, session_id, capture_window_start, capture_window_end, "
                    "top_strike, bottom_strike, top_ce, top_pe, bottom_ce, bottom_pe, "
                    "range_contracts, save_order) "
                    "VALUES (:snapshot_id, :session_id, :capture_window_start, :capture_window_end, "
                    ":top_strike, :bottom_strike, :top_ce, :top_pe, :bottom_ce, :bottom_pe, "
                    ":range_contracts, :save_order)",
                    {**row, "save_order": next_order},
                )
                connection.commit()
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise RepositoryError(f"Could not save snapshot to {self._path}: {exc}") from exc

    def _query(self, where: str, params: tuple[str, ...]) -> list[PremiumSnapshot]:
        try:
            connection = sqlite3.connect(self._path)
            try:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute(
                    f"SELECT * FROM premium_snapshots WHERE {where} ORDER BY save_order", params
                )
                return [_row_to_snapshot(dict(row)) for row in cursor.fetchall()]
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise RepositoryError(f"Could not read snapshots from {self._path}: {exc}") from exc

    def load(self, snapshot_id: uuid.UUID) -> PremiumSnapshot | None:
        matches = self._query("snapshot_id = ?", (str(snapshot_id),))
        return matches[0] if matches else None

    def latest(self, session_id: uuid.UUID) -> PremiumSnapshot | None:
        matches = self._query("session_id = ?", (str(session_id),))
        return matches[-1] if matches else None

    def historical(self, session_id: uuid.UUID) -> tuple[PremiumSnapshot, ...]:
        return tuple(self._query("session_id = ?", (str(session_id),)))

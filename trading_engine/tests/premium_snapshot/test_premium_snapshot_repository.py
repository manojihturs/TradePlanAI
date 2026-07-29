"""Tests for PremiumSnapshotRepository: InMemory, CSV, SQLite
implementations - Save/Load/Latest/Historical."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from trading_engine.market_data.instrument_resolver import OptionType
from trading_engine.premium_snapshot.exceptions import RepositoryError
from trading_engine.premium_snapshot.premium_snapshot_models import (
    ContractSnapshot,
    PremiumSnapshot,
)
from trading_engine.premium_snapshot.premium_snapshot_repository import (
    CsvPremiumSnapshotRepository,
    InMemoryPremiumSnapshotRepository,
    SqlitePremiumSnapshotRepository,
    _row_to_snapshot,
)


def _snapshot(
    session_id: uuid.UUID, window_start: datetime, top_ce_instrument, with_range: bool = False
) -> PremiumSnapshot:
    contract = ContractSnapshot(
        instrument=top_ce_instrument,
        strike=Decimal(24000),
        option_type=OptionType.CALL,
        timestamp=window_start,
        open=Decimal(100),
        high=Decimal(110),
        low=Decimal(95),
        close=Decimal(105),
        last_traded_price=Decimal(105),
        volume=1000,
        open_interest=5000,
    )
    return PremiumSnapshot(
        snapshot_id=uuid.uuid4(),
        session_id=session_id,
        capture_window_start=window_start,
        capture_window_end=window_start + timedelta(minutes=5),
        top_strike=Decimal(24000),
        bottom_strike=Decimal(23900),
        top_ce=contract,
        top_pe=None,
        bottom_ce=None,
        bottom_pe=None,
        range_contracts=(contract,) if with_range else (),
    )


@pytest.fixture(params=["in_memory", "csv", "sqlite"])
def repository(request: pytest.FixtureRequest, tmp_path: Path):
    if request.param == "in_memory":
        return InMemoryPremiumSnapshotRepository()
    if request.param == "csv":
        return CsvPremiumSnapshotRepository(tmp_path / "snapshots.csv")
    return SqlitePremiumSnapshotRepository(tmp_path / "snapshots.db")


class TestSaveAndLoad:
    def test_save_then_load_round_trips(
        self, repository, session_id: uuid.UUID, window_start: datetime, top_ce_instrument
    ) -> None:
        snapshot = _snapshot(session_id, window_start, top_ce_instrument, with_range=True)
        repository.save(snapshot)
        loaded = repository.load(snapshot.snapshot_id)
        assert loaded is not None
        assert loaded.snapshot_id == snapshot.snapshot_id
        assert loaded.session_id == session_id
        assert loaded.top_ce is not None
        assert loaded.top_ce.close == Decimal(105)
        assert loaded.top_pe is None
        assert len(loaded.range_contracts) == 1

    def test_load_missing_returns_none(self, repository) -> None:
        assert repository.load(uuid.uuid4()) is None


class TestLatestAndHistorical:
    def test_latest_returns_most_recently_saved(
        self, repository, session_id: uuid.UUID, window_start: datetime, top_ce_instrument
    ) -> None:
        first = _snapshot(session_id, window_start, top_ce_instrument)
        second = _snapshot(session_id, window_start + timedelta(minutes=10), top_ce_instrument)
        repository.save(first)
        repository.save(second)
        latest = repository.latest(session_id)
        assert latest is not None
        assert latest.snapshot_id == second.snapshot_id

    def test_latest_with_no_snapshots_returns_none(self, repository, session_id: uuid.UUID) -> None:
        assert repository.latest(session_id) is None

    def test_historical_returns_all_for_session_in_order(
        self, repository, session_id: uuid.UUID, window_start: datetime, top_ce_instrument
    ) -> None:
        other_session = uuid.uuid4()
        first = _snapshot(session_id, window_start, top_ce_instrument)
        other = _snapshot(other_session, window_start, top_ce_instrument)
        second = _snapshot(session_id, window_start + timedelta(minutes=10), top_ce_instrument)
        repository.save(first)
        repository.save(other)
        repository.save(second)
        history = repository.historical(session_id)
        assert [s.snapshot_id for s in history] == [first.snapshot_id, second.snapshot_id]

    def test_historical_with_no_snapshots_returns_empty(
        self, repository, session_id: uuid.UUID
    ) -> None:
        assert repository.historical(session_id) == ()


class TestCsvSpecific:
    def test_reads_from_existing_file(
        self, tmp_path: Path, session_id: uuid.UUID, window_start: datetime, top_ce_instrument
    ) -> None:
        path = tmp_path / "snapshots.csv"
        repo1 = CsvPremiumSnapshotRepository(path)
        snapshot = _snapshot(session_id, window_start, top_ce_instrument)
        repo1.save(snapshot)

        repo2 = CsvPremiumSnapshotRepository(path)
        loaded = repo2.load(snapshot.snapshot_id)
        assert loaded is not None

    def test_load_when_file_absent_returns_none(self, tmp_path: Path) -> None:
        repo = CsvPremiumSnapshotRepository(tmp_path / "missing.csv")
        assert repo.load(uuid.uuid4()) is None

    def test_write_failure_raises_repository_error(
        self, tmp_path: Path, session_id: uuid.UUID, window_start: datetime, top_ce_instrument
    ) -> None:
        directory_as_file = tmp_path / "not_writable_dir"
        directory_as_file.mkdir()
        repo = CsvPremiumSnapshotRepository(directory_as_file)
        snapshot = _snapshot(session_id, window_start, top_ce_instrument)
        with pytest.raises(RepositoryError, match="Could not write snapshot"):
            repo.save(snapshot)

    def test_read_failure_raises_repository_error(
        self,
        tmp_path: Path,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        path = tmp_path / "snapshots.csv"
        repo = CsvPremiumSnapshotRepository(path)
        repo.save(_snapshot(session_id, window_start, top_ce_instrument))

        def raise_oserror(*args: object, **kwargs: object) -> None:
            raise OSError("boom")

        monkeypatch.setattr(Path, "open", raise_oserror)
        with pytest.raises(RepositoryError, match="Could not read snapshots"):
            repo.load(uuid.uuid4())


class TestRowToSnapshotMalformedData:
    def test_missing_key_raises_repository_error(self) -> None:
        with pytest.raises(RepositoryError, match="Could not reconstruct a PremiumSnapshot"):
            _row_to_snapshot({"snapshot_id": str(uuid.uuid4())})

    def test_invalid_json_raises_repository_error(
        self, session_id: uuid.UUID, window_start: datetime
    ) -> None:
        row = {
            "snapshot_id": str(uuid.uuid4()),
            "session_id": str(session_id),
            "capture_window_start": window_start.isoformat(),
            "capture_window_end": (window_start + timedelta(minutes=5)).isoformat(),
            "top_strike": "24000",
            "bottom_strike": "23900",
            "top_ce": "not valid json",
            "top_pe": "null",
            "bottom_ce": "null",
            "bottom_pe": "null",
            "range_contracts": "[]",
        }
        with pytest.raises(RepositoryError, match="Could not reconstruct a PremiumSnapshot"):
            _row_to_snapshot(row)


class TestSqliteSpecific:
    def test_reads_from_existing_database(
        self, tmp_path: Path, session_id: uuid.UUID, window_start: datetime, top_ce_instrument
    ) -> None:
        path = tmp_path / "snapshots.db"
        repo1 = SqlitePremiumSnapshotRepository(path)
        snapshot = _snapshot(session_id, window_start, top_ce_instrument)
        repo1.save(snapshot)

        repo2 = SqlitePremiumSnapshotRepository(path)
        loaded = repo2.load(snapshot.snapshot_id)
        assert loaded is not None

    def test_init_failure_raises_repository_error(self, tmp_path: Path) -> None:
        directory_as_file = tmp_path / "not_a_db"
        directory_as_file.mkdir()
        with pytest.raises(RepositoryError, match="Could not initialise SQLite database"):
            SqlitePremiumSnapshotRepository(directory_as_file)

    def test_save_failure_raises_repository_error(
        self,
        tmp_path: Path,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        repo = SqlitePremiumSnapshotRepository(tmp_path / "snapshots.db")

        def raise_sqlite_error(*args: object, **kwargs: object) -> None:
            raise sqlite3.Error("boom")

        monkeypatch.setattr(sqlite3, "connect", raise_sqlite_error)
        with pytest.raises(RepositoryError, match="Could not save snapshot"):
            repo.save(_snapshot(session_id, window_start, top_ce_instrument))

    def test_query_failure_raises_repository_error(
        self, tmp_path: Path, session_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = SqlitePremiumSnapshotRepository(tmp_path / "snapshots.db")

        def raise_sqlite_error(*args: object, **kwargs: object) -> None:
            raise sqlite3.Error("boom")

        monkeypatch.setattr(sqlite3, "connect", raise_sqlite_error)
        with pytest.raises(RepositoryError, match="Could not read snapshots"):
            repo.latest(session_id)

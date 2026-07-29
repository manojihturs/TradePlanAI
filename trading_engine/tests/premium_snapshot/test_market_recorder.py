"""Tests for MarketRecorder and its CSV/SQLite/InMemory TickRecordRepository
implementations: tick recording, snapshot retrieval, diagnostics,
failure handling."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from trading_engine.diagnostics.sink import InMemoryDiagnosticsSink
from trading_engine.premium_snapshot.exceptions import (
    RecorderError,
    RepositoryError,
    SnapshotValidationError,
)
from trading_engine.premium_snapshot.market_recorder import (
    CsvTickRecordRepository,
    InMemoryTickRecordRepository,
    MarketRecorder,
    SqliteTickRecordRepository,
    TickRecord,
)
from trading_engine.tests.premium_snapshot.conftest import make_tick


class TestTickRecord:
    def test_valid_construction(self, window_start: datetime) -> None:
        record = TickRecord(timestamp=window_start, spot=Decimal(24000))
        assert record.spot == Decimal(24000)

    def test_none_timestamp_raises(self) -> None:
        with pytest.raises(SnapshotValidationError, match="timestamp must not be None"):
            TickRecord(timestamp=None)  # type: ignore[arg-type]

    def test_negative_volume_raises(self, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="volume must not be negative"):
            TickRecord(timestamp=window_start, volume=-1)

    def test_negative_open_interest_raises(self, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="open_interest must not be negative"):
            TickRecord(timestamp=window_start, open_interest=-1)

    def test_bid_above_ask_raises(self, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="bid .* must not exceed ask"):
            TickRecord(timestamp=window_start, bid=Decimal(10), ask=Decimal(5))

    def test_from_tick_carries_context(self, top_ce_instrument, window_start: datetime) -> None:
        tick = make_tick(top_ce_instrument, window_start, "105", volume=50, open_interest=100)
        record = TickRecord.from_tick(
            tick, spot=Decimal(24000), strike=Decimal(24000), ce_price=Decimal(105)
        )
        assert record.timestamp == window_start
        assert record.ce_price == Decimal(105)
        assert record.volume == 50
        assert record.open_interest == 100

    def test_row_round_trip(self, window_start: datetime) -> None:
        record = TickRecord(
            timestamp=window_start,
            spot=Decimal(24000),
            strike=Decimal(24000),
            ce_price=Decimal(105),
            pe_price=None,
            volume=50,
            open_interest=100,
            bid=Decimal(104),
            ask=Decimal(106),
        )
        restored = TickRecord.from_row(record.to_row())
        assert restored == record


@pytest.fixture(params=["in_memory", "csv", "sqlite"])
def repository(request: pytest.FixtureRequest, tmp_path: Path):
    if request.param == "in_memory":
        return InMemoryTickRecordRepository()
    if request.param == "csv":
        return CsvTickRecordRepository(tmp_path / "ticks.csv")
    return SqliteTickRecordRepository(tmp_path / "ticks.db")


class TestRepositoryAppendAndFlush:
    def test_append_then_flush_then_read_back(self, repository, window_start: datetime) -> None:
        record = TickRecord(
            timestamp=window_start, spot=Decimal(24000), volume=10, open_interest=20
        )
        repository.append(record)
        repository.flush()
        records = repository.all_records()
        assert len(records) == 1
        assert records[0].spot == Decimal(24000)

    def test_all_records_before_flush_still_visible(
        self, repository, window_start: datetime
    ) -> None:
        record = TickRecord(timestamp=window_start)
        repository.append(record)
        assert len(repository.all_records()) == 1

    def test_multiple_records_preserve_order(self, repository, window_start: datetime) -> None:
        for i in range(3):
            repository.append(TickRecord(timestamp=window_start + timedelta(seconds=i), volume=i))
        repository.flush()
        records = repository.all_records()
        assert [r.volume for r in records] == [0, 1, 2]

    def test_flush_with_no_records_is_a_no_op(self, repository) -> None:
        repository.flush()
        assert repository.all_records() == ()


class TestCsvRepositorySpecific:
    def test_write_failure_raises_repository_error(
        self, tmp_path: Path, window_start: datetime
    ) -> None:
        directory_as_file = tmp_path / "not_writable_dir"
        directory_as_file.mkdir()
        repo = CsvTickRecordRepository(directory_as_file)
        repo.append(TickRecord(timestamp=window_start))
        with pytest.raises(RepositoryError, match="Could not write tick records"):
            repo.flush()

    def test_persisted_and_buffered_both_visible(
        self, tmp_path: Path, window_start: datetime
    ) -> None:
        path = tmp_path / "ticks.csv"
        repo = CsvTickRecordRepository(path)
        repo.append(TickRecord(timestamp=window_start, volume=1))
        repo.flush()
        repo.append(TickRecord(timestamp=window_start + timedelta(seconds=1), volume=2))
        records = repo.all_records()
        assert [r.volume for r in records] == [1, 2]

    def test_read_failure_raises_repository_error(
        self, tmp_path: Path, window_start: datetime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "ticks.csv"
        repo = CsvTickRecordRepository(path)
        repo.append(TickRecord(timestamp=window_start))
        repo.flush()

        def raise_oserror(*args: object, **kwargs: object) -> None:
            raise OSError("boom")

        monkeypatch.setattr(Path, "open", raise_oserror)
        with pytest.raises(RepositoryError, match="Could not read tick records"):
            repo.all_records()


class TestSqliteRepositorySpecific:
    def test_init_failure_raises_repository_error(self, tmp_path: Path) -> None:
        directory_as_file = tmp_path / "not_a_db"
        directory_as_file.mkdir()
        with pytest.raises(RepositoryError, match="Could not initialise SQLite database"):
            SqliteTickRecordRepository(directory_as_file)

    def test_reopening_reads_previously_flushed_records(
        self, tmp_path: Path, window_start: datetime
    ) -> None:
        path = tmp_path / "ticks.db"
        repo1 = SqliteTickRecordRepository(path)
        repo1.append(TickRecord(timestamp=window_start, volume=7))
        repo1.flush()

        repo2 = SqliteTickRecordRepository(path)
        assert len(repo2.all_records()) == 1

    def test_flush_failure_raises_repository_error(
        self, tmp_path: Path, window_start: datetime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = SqliteTickRecordRepository(tmp_path / "ticks.db")
        repo.append(TickRecord(timestamp=window_start))

        def raise_sqlite_error(*args: object, **kwargs: object) -> None:
            raise sqlite3.Error("boom")

        monkeypatch.setattr(sqlite3, "connect", raise_sqlite_error)
        with pytest.raises(RepositoryError, match="Could not write tick records"):
            repo.flush()

    def test_read_failure_raises_repository_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = SqliteTickRecordRepository(tmp_path / "ticks.db")

        def raise_sqlite_error(*args: object, **kwargs: object) -> None:
            raise sqlite3.Error("boom")

        monkeypatch.setattr(sqlite3, "connect", raise_sqlite_error)
        with pytest.raises(RepositoryError, match="Could not read tick records"):
            repo.all_records()


class TestMarketRecorderLifecycle:
    def test_record_without_start_raises(self, window_start: datetime) -> None:
        recorder = MarketRecorder(InMemoryTickRecordRepository())
        with pytest.raises(RecorderError, match="not running"):
            recorder.record(TickRecord(timestamp=window_start))

    def test_start_then_record_then_stop(self, window_start: datetime) -> None:
        repository = InMemoryTickRecordRepository()
        recorder = MarketRecorder(repository)
        recorder.start()
        assert recorder.is_running is True
        recorder.record(TickRecord(timestamp=window_start, volume=1))
        recorder.record(TickRecord(timestamp=window_start + timedelta(seconds=1), volume=2))
        flushed = recorder.stop()
        assert flushed == 2
        assert recorder.is_running is False
        assert len(repository.all_records()) == 2

    def test_double_start_raises(self) -> None:
        recorder = MarketRecorder(InMemoryTickRecordRepository())
        recorder.start()
        with pytest.raises(RecorderError, match="already running"):
            recorder.start()

    def test_stop_without_start_raises(self) -> None:
        recorder = MarketRecorder(InMemoryTickRecordRepository())
        with pytest.raises(RecorderError, match="not running"):
            recorder.stop()

    def test_flush_without_pending_records_reports_zero(self) -> None:
        recorder = MarketRecorder(InMemoryTickRecordRepository())
        recorder.start()
        assert recorder.flush() == 0

    def test_restart_after_stop(self, window_start: datetime) -> None:
        recorder = MarketRecorder(InMemoryTickRecordRepository())
        recorder.start()
        recorder.stop()
        recorder.start()
        assert recorder.is_running is True


class TestMarketRecorderDiagnostics:
    def test_started_stopped_flushed_events_emitted(self, window_start: datetime) -> None:
        sink = InMemoryDiagnosticsSink()
        recorder = MarketRecorder(
            InMemoryTickRecordRepository(),
            recorder_name="paper_trading_recorder",
            diagnostics_sink=sink,
        )
        recorder.start()
        recorder.record(TickRecord(timestamp=window_start))
        recorder.flush()
        recorder.stop()

        events = sink.events()
        # start, explicit flush(), stop()'s own internal flush(), stop
        assert len(events) == 4
        from trading_engine.diagnostics.events import (
            RecorderFlushed,
            RecorderStarted,
            RecorderStopped,
        )

        assert isinstance(events[0], RecorderStarted)
        assert events[0].recorder_name == "paper_trading_recorder"
        assert isinstance(events[1], RecorderFlushed)
        assert events[1].record_count == 1
        assert isinstance(events[2], RecorderFlushed)
        assert events[2].record_count == 0
        assert isinstance(events[3], RecorderStopped)
        assert events[3].records_flushed == 0

    def test_no_sink_uses_null_sink_without_error(self, window_start: datetime) -> None:
        recorder = MarketRecorder(InMemoryTickRecordRepository())
        recorder.start()
        recorder.record(TickRecord(timestamp=window_start))
        recorder.stop()

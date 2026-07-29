"""Tests for the 6 premium snapshot diagnostic event dataclasses
(Milestone I2).

A dedicated file, separate from ``test_events.py``, ``test_replay_events.py``,
and ``test_market_data_events.py``. No existing test file is modified
to add this.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest

from trading_engine.diagnostics.events import (
    RecorderFlushed,
    RecorderStarted,
    RecorderStopped,
    SnapshotCompleted,
    SnapshotStarted,
    SnapshotStored,
)
from trading_engine.diagnostics.exceptions import DiagnosticsError


class TestSnapshotStarted:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = SnapshotStarted(
            valid_uuid,
            valid_datetime,
            valid_uuid,
            valid_datetime,
            valid_datetime + timedelta(minutes=5),
        )
        assert event.session_id == valid_uuid

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="session_id must not be None"):
            SnapshotStarted(valid_uuid, valid_datetime, None, valid_datetime, valid_datetime)  # type: ignore[arg-type]

    def test_window_end_not_after_start_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="window_end must be after window_start"):
            SnapshotStarted(valid_uuid, valid_datetime, valid_uuid, valid_datetime, valid_datetime)


class TestSnapshotCompleted:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = SnapshotCompleted(valid_uuid, valid_datetime, valid_uuid, 4, 0)
        assert event.captured_contract_count == 4
        assert event.missing_contract_count == 0

    def test_negative_captured_count_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="captured_contract_count must not be negative"):
            SnapshotCompleted(valid_uuid, valid_datetime, valid_uuid, -1, 0)

    def test_negative_missing_count_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="missing_contract_count must not be negative"):
            SnapshotCompleted(valid_uuid, valid_datetime, valid_uuid, 0, -1)

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="SnapshotCompleted.session_id must not be None"):
            SnapshotCompleted(valid_uuid, valid_datetime, None, 0, 0)  # type: ignore[arg-type]


class TestSnapshotStored:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = SnapshotStored(valid_uuid, valid_datetime, valid_uuid, valid_uuid)
        assert event.snapshot_id == valid_uuid

    def test_none_snapshot_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="snapshot_id must not be None"):
            SnapshotStored(valid_uuid, valid_datetime, None, valid_uuid)  # type: ignore[arg-type]

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="SnapshotStored.session_id must not be None"):
            SnapshotStored(valid_uuid, valid_datetime, valid_uuid, None)  # type: ignore[arg-type]


class TestRecorderStarted:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RecorderStarted(valid_uuid, valid_datetime, "market_recorder")
        assert event.recorder_name == "market_recorder"

    def test_blank_recorder_name_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="recorder_name must not be blank"):
            RecorderStarted(valid_uuid, valid_datetime, "")


class TestRecorderStopped:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RecorderStopped(valid_uuid, valid_datetime, "market_recorder", 42)
        assert event.records_flushed == 42

    def test_negative_records_flushed_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="records_flushed must not be negative"):
            RecorderStopped(valid_uuid, valid_datetime, "market_recorder", -1)


class TestRecorderFlushed:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RecorderFlushed(valid_uuid, valid_datetime, "market_recorder", 10)
        assert event.record_count == 10

    def test_negative_record_count_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="record_count must not be negative"):
            RecorderFlushed(valid_uuid, valid_datetime, "market_recorder", -1)

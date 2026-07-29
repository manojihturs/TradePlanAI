"""Tests for the 6 replay diagnostic event dataclasses (Milestone B1).

A dedicated file, separate from ``test_events.py`` (Milestone 6.4). No
existing test file is modified to add this.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from trading_engine.diagnostics.events import (
    ReplayCompleted,
    ReplayPaused,
    ReplayReset,
    ReplayResumed,
    ReplayStarted,
    ReplayStepped,
)
from trading_engine.diagnostics.exceptions import DiagnosticsError


class TestReplayStarted:
    def test_valid_construction(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = ReplayStarted(valid_uuid, valid_datetime, another_uuid, 100)
        assert event.total_candles == 100

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="session_id must not be None"):
            ReplayStarted(valid_uuid, valid_datetime, None, 100)  # type: ignore[arg-type]

    def test_negative_total_candles_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="total_candles must not be negative"):
            ReplayStarted(valid_uuid, valid_datetime, another_uuid, -1)


class TestReplayPaused:
    def test_valid_construction(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = ReplayPaused(valid_uuid, valid_datetime, another_uuid, 5)
        assert event.current_index == 5

    def test_negative_current_index_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="current_index must not be negative"):
            ReplayPaused(valid_uuid, valid_datetime, another_uuid, -1)

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="session_id must not be None"):
            ReplayPaused(valid_uuid, valid_datetime, None, 0)  # type: ignore[arg-type]


class TestReplayResumed:
    def test_valid_construction(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = ReplayResumed(valid_uuid, valid_datetime, another_uuid, 5)
        assert event.current_index == 5

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="session_id must not be None"):
            ReplayResumed(valid_uuid, valid_datetime, None, 0)  # type: ignore[arg-type]

    def test_negative_current_index_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="current_index must not be negative"):
            ReplayResumed(valid_uuid, valid_datetime, another_uuid, -1)


class TestReplayStepped:
    def test_valid_construction(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = ReplayStepped(valid_uuid, valid_datetime, another_uuid, 0, 1, "forward")
        assert event.direction == "forward"

    def test_backward_direction_is_valid(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = ReplayStepped(valid_uuid, valid_datetime, another_uuid, 1, 0, "backward")
        assert event.direction == "backward"

    def test_invalid_direction_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="direction must be"):
            ReplayStepped(valid_uuid, valid_datetime, another_uuid, 0, 1, "sideways")

    def test_negative_index_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="indices must not be negative"):
            ReplayStepped(valid_uuid, valid_datetime, another_uuid, -1, 0, "forward")

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="session_id must not be None"):
            ReplayStepped(valid_uuid, valid_datetime, None, 0, 1, "forward")  # type: ignore[arg-type]


class TestReplayCompleted:
    def test_valid_construction(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = ReplayCompleted(valid_uuid, valid_datetime, another_uuid, 10)
        assert event.total_candles_processed == 10

    def test_negative_total_processed_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="total_candles_processed must not be negative"):
            ReplayCompleted(valid_uuid, valid_datetime, another_uuid, -1)

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="session_id must not be None"):
            ReplayCompleted(valid_uuid, valid_datetime, None, 0)  # type: ignore[arg-type]


class TestReplayReset:
    def test_valid_construction(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = ReplayReset(valid_uuid, valid_datetime, another_uuid)
        assert event.session_id == another_uuid

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="session_id must not be None"):
            ReplayReset(valid_uuid, valid_datetime, None)  # type: ignore[arg-type]

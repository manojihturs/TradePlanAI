"""Tests for the diagnostics sinks."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

import pytest

from trading_engine.diagnostics.events import RuleStarted
from trading_engine.diagnostics.sink import (
    DEFAULT_LOGGER_NAME,
    DiagnosticsSink,
    InMemoryDiagnosticsSink,
    NullDiagnosticsSink,
    StandardLoggingDiagnosticsSink,
)


def _event(valid_uuid: uuid.UUID, valid_datetime: datetime) -> RuleStarted:
    return RuleStarted(valid_uuid, valid_datetime, "STRIKE-001")


class TestNullDiagnosticsSink:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(NullDiagnosticsSink(), DiagnosticsSink)

    def test_emit_is_a_true_no_op(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        sink = NullDiagnosticsSink()
        result = sink.emit(_event(valid_uuid, valid_datetime))
        assert result is None


class TestInMemoryDiagnosticsSink:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(InMemoryDiagnosticsSink(), DiagnosticsSink)

    def test_starts_empty(self) -> None:
        sink = InMemoryDiagnosticsSink()
        assert sink.events() == ()
        assert len(sink) == 0

    def test_emit_appends_in_order(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        first = RuleStarted(valid_uuid, valid_datetime, "STRIKE-001")
        second = RuleStarted(another_uuid, valid_datetime, "TREND-001")
        sink.emit(first)
        sink.emit(second)
        assert sink.events() == (first, second)
        assert len(sink) == 2

    def test_events_returns_a_tuple_not_the_live_list(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        sink.emit(_event(valid_uuid, valid_datetime))
        snapshot = sink.events()
        sink.emit(_event(valid_uuid, valid_datetime))
        assert len(snapshot) == 1
        assert len(sink.events()) == 2


class TestStandardLoggingDiagnosticsSink:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(StandardLoggingDiagnosticsSink(), DiagnosticsSink)

    def test_emit_logs_at_info_level(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime, caplog: pytest.LogCaptureFixture
    ) -> None:
        sink = StandardLoggingDiagnosticsSink()
        with caplog.at_level(logging.INFO, logger=DEFAULT_LOGGER_NAME):
            sink.emit(_event(valid_uuid, valid_datetime))
        assert any("RuleStarted" in record.getMessage() for record in caplog.records)

    def test_uses_default_logger_name(self) -> None:
        sink = StandardLoggingDiagnosticsSink()
        assert sink._logger.name == DEFAULT_LOGGER_NAME

    def test_custom_logger_name(self) -> None:
        sink = StandardLoggingDiagnosticsSink(logger_name="custom.logger")
        assert sink._logger.name == "custom.logger"

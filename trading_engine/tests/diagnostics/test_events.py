"""Tests for the diagnostics event dataclasses."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime

import pytest

from trading_engine.diagnostics.events import (
    DependencyMissing,
    DependencyResolved,
    ExecutionFailed,
    ExecutionSummaryLogged,
    RuleFinished,
    RuleRegistered,
    RuleSkipped,
    RuleStarted,
)
from trading_engine.diagnostics.exceptions import DiagnosticsError


class TestRuleRegistered:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RuleRegistered(valid_uuid, valid_datetime, "STRIKE-001", 1)
        assert event.rule_id == "STRIKE-001"
        assert event.total_registered == 1

    def test_none_event_id_raises(self, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="event_id must not be None"):
            RuleRegistered(None, valid_datetime, "STRIKE-001", 1)  # type: ignore[arg-type]

    def test_blank_rule_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="rule_id must not be blank"):
            RuleRegistered(valid_uuid, valid_datetime, "   ", 1)

    def test_total_registered_below_one_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="total_registered must be at least 1"):
            RuleRegistered(valid_uuid, valid_datetime, "STRIKE-001", 0)

    def test_immutability(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RuleRegistered(valid_uuid, valid_datetime, "STRIKE-001", 1)
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.rule_id = "TREND-001"  # type: ignore[misc]

    def test_hashable(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        hash(RuleRegistered(valid_uuid, valid_datetime, "STRIKE-001", 1))


class TestDependencyResolved:
    def test_valid_construction_with_defaults(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = DependencyResolved(valid_uuid, valid_datetime)
        assert event.execution_order == ()

    def test_valid_construction_with_order(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = DependencyResolved(valid_uuid, valid_datetime, ("TREND-001", "TREND-002"))
        assert event.execution_order == ("TREND-001", "TREND-002")

    def test_none_occurred_at_raises(self, valid_uuid: uuid.UUID) -> None:
        with pytest.raises(DiagnosticsError, match="occurred_at must not be None"):
            DependencyResolved(valid_uuid, None)  # type: ignore[arg-type]


class TestDependencyMissing:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = DependencyMissing(
            valid_uuid, valid_datetime, "TREND-002", "TREND-001", "missing dependency"
        )
        assert event.reason == "missing dependency"

    def test_blank_dependency_id_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="dependency_id must not be blank"):
            DependencyMissing(valid_uuid, valid_datetime, "TREND-002", "", "missing dependency")

    def test_blank_reason_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="reason must not be blank"):
            DependencyMissing(valid_uuid, valid_datetime, "TREND-002", "TREND-001", "")


class TestRuleStarted:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RuleStarted(valid_uuid, valid_datetime, "STRIKE-001")
        assert event.rule_id == "STRIKE-001"

    def test_blank_rule_id_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="rule_id must not be blank"):
            RuleStarted(valid_uuid, valid_datetime, "")


class TestRuleFinished:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RuleFinished(valid_uuid, valid_datetime, "STRIKE-001", "UNKNOWN", 0.01)
        assert event.outcome_name == "UNKNOWN"
        assert event.duration_seconds == 0.01

    def test_blank_outcome_name_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="outcome_name must not be blank"):
            RuleFinished(valid_uuid, valid_datetime, "STRIKE-001", "", 0.0)

    def test_negative_duration_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="duration_seconds must not be negative"):
            RuleFinished(valid_uuid, valid_datetime, "STRIKE-001", "UNKNOWN", -0.1)

    def test_zero_duration_is_valid(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RuleFinished(valid_uuid, valid_datetime, "STRIKE-001", "UNKNOWN", 0.0)
        assert event.duration_seconds == 0.0


class TestRuleSkipped:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = RuleSkipped(valid_uuid, valid_datetime, "STRIKE-001", "dry run")
        assert event.reason == "dry run"

    def test_blank_reason_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="reason must not be blank"):
            RuleSkipped(valid_uuid, valid_datetime, "STRIKE-001", "")


class TestExecutionFailed:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = ExecutionFailed(
            valid_uuid, valid_datetime, "STRIKE-001", "RuleExecutionError", "boom", True
        )
        assert event.fatal is True

    def test_blank_exception_type_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="exception_type must not be blank"):
            ExecutionFailed(valid_uuid, valid_datetime, "STRIKE-001", "", "boom", True)

    def test_non_fatal_is_valid(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = ExecutionFailed(
            valid_uuid, valid_datetime, "STRIKE-001", "ValueError", "boom", False
        )
        assert event.fatal is False


class TestExecutionSummaryLogged:
    def test_valid_construction(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        event = ExecutionSummaryLogged(
            event_id=valid_uuid,
            occurred_at=valid_datetime,
            execution_id=another_uuid,
            total_rules=3,
            pass_count=1,
            fail_count=1,
            unknown_count=1,
            insufficient_evidence_count=0,
            not_applicable_count=0,
            duration_seconds=1.5,
        )
        assert event.total_rules == 3

    def test_none_execution_id_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="execution_id must not be None"):
            ExecutionSummaryLogged(
                event_id=valid_uuid,
                occurred_at=valid_datetime,
                execution_id=None,  # type: ignore[arg-type]
                total_rules=0,
                pass_count=0,
                fail_count=0,
                unknown_count=0,
                insufficient_evidence_count=0,
                not_applicable_count=0,
                duration_seconds=0.0,
            )

    def test_negative_total_rules_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="total_rules must not be negative"):
            ExecutionSummaryLogged(
                event_id=valid_uuid,
                occurred_at=valid_datetime,
                execution_id=another_uuid,
                total_rules=-1,
                pass_count=0,
                fail_count=0,
                unknown_count=0,
                insufficient_evidence_count=0,
                not_applicable_count=0,
                duration_seconds=0.0,
            )

    def test_negative_duration_raises(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="duration_seconds must not be negative"):
            ExecutionSummaryLogged(
                event_id=valid_uuid,
                occurred_at=valid_datetime,
                execution_id=another_uuid,
                total_rules=0,
                pass_count=0,
                fail_count=0,
                unknown_count=0,
                insufficient_evidence_count=0,
                not_applicable_count=0,
                duration_seconds=-1.0,
            )

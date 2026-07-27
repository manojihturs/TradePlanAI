"""Tests for ExecutionReport and ExecutionSummary."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timedelta

import pytest

from trading_engine.domain.rule_reference import RuleReference
from trading_engine.engine.exceptions import PipelineExecutionError
from trading_engine.engine.execution_report import ExecutionReport
from trading_engine.engine.execution_summary import ExecutionSummary
from trading_engine.rules.outcome import RuleExecutionResult, RuleOutcome


def _result(rule: RuleReference, outcome: RuleOutcome) -> RuleExecutionResult:
    return RuleExecutionResult(uuid.uuid4(), rule, outcome, "test reason")


class TestExecutionReportConstructorValidation:
    def test_valid_construction_with_defaults(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        report = ExecutionReport(valid_uuid, valid_datetime, valid_datetime)
        assert report.rules_executed == ()
        assert report.results == ()
        assert report.warnings == ()
        assert report.errors == ()

    def test_valid_construction_with_all_fields(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime, sample_rule_reference: RuleReference
    ) -> None:
        end = valid_datetime + timedelta(seconds=5)
        result = _result(sample_rule_reference, RuleOutcome.PASS)
        report = ExecutionReport(
            valid_uuid,
            valid_datetime,
            end,
            rules_executed=("STRIKE-001",),
            results=(result,),
            warnings=("w",),
            errors=("e",),
        )
        assert report.results == (result,)
        assert report.warnings == ("w",)
        assert report.errors == ("e",)


class TestExecutionReportInvalidConstructorValues:
    def test_none_execution_id_raises(self, valid_datetime: datetime) -> None:
        with pytest.raises(PipelineExecutionError, match="execution_id must not be None"):
            ExecutionReport(None, valid_datetime, valid_datetime)  # type: ignore[arg-type]

    def test_none_start_time_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(PipelineExecutionError, match="start_time must not be None"):
            ExecutionReport(valid_uuid, None, valid_datetime)  # type: ignore[arg-type]

    def test_none_end_time_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(PipelineExecutionError, match="end_time must not be None"):
            ExecutionReport(valid_uuid, valid_datetime, None)  # type: ignore[arg-type]

    def test_end_time_before_start_time_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        earlier = valid_datetime - timedelta(seconds=1)
        with pytest.raises(PipelineExecutionError, match="must not precede start_time"):
            ExecutionReport(valid_uuid, valid_datetime, earlier)


class TestExecutionReportDuration:
    def test_duration_is_end_minus_start(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        end = valid_datetime + timedelta(seconds=10)
        report = ExecutionReport(valid_uuid, valid_datetime, end)
        assert report.duration == timedelta(seconds=10)

    def test_zero_duration_is_valid(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        report = ExecutionReport(valid_uuid, valid_datetime, valid_datetime)
        assert report.duration == timedelta(0)


class TestExecutionReportImmutability:
    def test_cannot_reassign_results(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        report = ExecutionReport(valid_uuid, valid_datetime, valid_datetime)
        with pytest.raises(dataclasses.FrozenInstanceError):
            report.results = ()  # type: ignore[misc]


class TestExecutionReportHashability:
    def test_is_hashable(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        hash(ExecutionReport(valid_uuid, valid_datetime, valid_datetime))


class TestExecutionSummaryFromReport:
    def test_counts_each_outcome(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime, sample_rule_reference: RuleReference
    ) -> None:
        end = valid_datetime + timedelta(seconds=2)
        results = (
            _result(sample_rule_reference, RuleOutcome.PASS),
            _result(sample_rule_reference, RuleOutcome.PASS),
            _result(sample_rule_reference, RuleOutcome.FAIL),
            _result(sample_rule_reference, RuleOutcome.UNKNOWN),
            _result(sample_rule_reference, RuleOutcome.INSUFFICIENT_EVIDENCE),
            _result(sample_rule_reference, RuleOutcome.NOT_APPLICABLE),
        )
        report = ExecutionReport(valid_uuid, valid_datetime, end, results=results)
        summary = ExecutionSummary.from_report(report)

        assert summary.total_rules == 6
        assert summary.pass_count == 2
        assert summary.fail_count == 1
        assert summary.unknown_count == 1
        assert summary.insufficient_evidence_count == 1
        assert summary.not_applicable_count == 1
        assert summary.duration == timedelta(seconds=2)

    def test_empty_results_produce_all_zero_counts(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        report = ExecutionReport(valid_uuid, valid_datetime, valid_datetime)
        summary = ExecutionSummary.from_report(report)
        assert summary.total_rules == 0
        assert summary.pass_count == 0

    def test_none_report_raises(self) -> None:
        with pytest.raises(PipelineExecutionError, match="report.*must not be None"):
            ExecutionSummary.from_report(None)  # type: ignore[arg-type]


class TestExecutionSummaryConstructorValidation:
    def test_negative_count_raises(self) -> None:
        with pytest.raises(PipelineExecutionError, match="must not be negative"):
            ExecutionSummary(1, -1, 0, 0, 0, 0, timedelta(0))

    def test_negative_total_rules_raises(self) -> None:
        with pytest.raises(PipelineExecutionError, match="must not be negative"):
            ExecutionSummary(-1, 0, 0, 0, 0, 0, timedelta(0))

    def test_counts_not_summing_to_total_raises(self) -> None:
        with pytest.raises(PipelineExecutionError, match="must sum to total_rules"):
            ExecutionSummary(10, 1, 1, 1, 1, 1, timedelta(0))

    def test_consistent_counts_succeed(self) -> None:
        summary = ExecutionSummary(3, 1, 1, 1, 0, 0, timedelta(seconds=1))
        assert summary.total_rules == 3


class TestExecutionSummaryImmutability:
    def test_cannot_reassign_pass_count(self) -> None:
        summary = ExecutionSummary(1, 1, 0, 0, 0, 0, timedelta(0))
        with pytest.raises(dataclasses.FrozenInstanceError):
            summary.pass_count = 99  # type: ignore[misc]

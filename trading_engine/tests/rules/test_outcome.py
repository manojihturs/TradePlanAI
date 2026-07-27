"""Tests for RuleOutcome and RuleExecutionResult."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime

import pytest

from trading_engine.domain.evidence_reference import EvidenceReference
from trading_engine.domain.rule_reference import RuleReference
from trading_engine.rules.exceptions import RuleExecutionError
from trading_engine.rules.outcome import RuleExecutionResult, RuleOutcome


class TestRuleOutcomeEnum:
    def test_member_set(self) -> None:
        expected = {"PASS", "FAIL", "UNKNOWN", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE"}
        assert {member.name for member in RuleOutcome} == expected

    def test_is_not_bool_like(self) -> None:
        # Explicit per Milestone 4.2: "Do not use bool."
        assert not isinstance(RuleOutcome.PASS, bool)
        assert not isinstance(RuleOutcome.FAIL, bool)

    def test_invalid_member_name_raises(self) -> None:
        with pytest.raises(KeyError):
            RuleOutcome["NOT_A_MEMBER"]


class TestConstructorValidation:
    def test_valid_construction_with_defaults(
        self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference
    ) -> None:
        result = RuleExecutionResult(
            result_id=valid_uuid,
            rule=sample_rule_reference,
            outcome=RuleOutcome.UNKNOWN,
            reason="No mathematics known yet.",
        )
        assert result.outcome is RuleOutcome.UNKNOWN
        assert result.evidence_used == ()
        assert result.executed_at is None

    def test_valid_construction_with_all_fields(
        self,
        valid_uuid: uuid.UUID,
        sample_rule_reference: RuleReference,
        sample_evidence_reference: EvidenceReference,
        valid_datetime: datetime,
    ) -> None:
        result = RuleExecutionResult(
            result_id=valid_uuid,
            rule=sample_rule_reference,
            outcome=RuleOutcome.PASS,
            reason="Condition held.",
            evidence_used=(sample_evidence_reference,),
            executed_at=valid_datetime,
        )
        assert result.evidence_used == (sample_evidence_reference,)
        assert result.executed_at == valid_datetime


class TestInvalidConstructorValues:
    def test_none_result_id_raises(self, sample_rule_reference: RuleReference) -> None:
        with pytest.raises(RuleExecutionError, match="result_id must not be None"):
            RuleExecutionResult(
                result_id=None,  # type: ignore[arg-type]
                rule=sample_rule_reference,
                outcome=RuleOutcome.UNKNOWN,
                reason="x",
            )

    def test_none_rule_raises(self, valid_uuid: uuid.UUID) -> None:
        with pytest.raises(RuleExecutionError, match="rule must not be None"):
            RuleExecutionResult(
                result_id=valid_uuid,
                rule=None,  # type: ignore[arg-type]
                outcome=RuleOutcome.UNKNOWN,
                reason="x",
            )

    def test_blank_reason_raises(
        self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference
    ) -> None:
        with pytest.raises(RuleExecutionError, match="reason must not be blank"):
            RuleExecutionResult(
                result_id=valid_uuid,
                rule=sample_rule_reference,
                outcome=RuleOutcome.UNKNOWN,
                reason="   ",
            )


class TestEquality:
    def test_equal_values_are_equal(
        self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference
    ) -> None:
        a = RuleExecutionResult(valid_uuid, sample_rule_reference, RuleOutcome.PASS, "same")
        b = RuleExecutionResult(valid_uuid, sample_rule_reference, RuleOutcome.PASS, "same")
        assert a == b

    def test_different_outcome_not_equal(
        self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference
    ) -> None:
        a = RuleExecutionResult(valid_uuid, sample_rule_reference, RuleOutcome.PASS, "r")
        b = RuleExecutionResult(valid_uuid, sample_rule_reference, RuleOutcome.FAIL, "r")
        assert a != b


class TestImmutability:
    def test_cannot_reassign_outcome(
        self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference
    ) -> None:
        result = RuleExecutionResult(valid_uuid, sample_rule_reference, RuleOutcome.PASS, "r")
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.outcome = RuleOutcome.FAIL  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference) -> None:
        hash(RuleExecutionResult(valid_uuid, sample_rule_reference, RuleOutcome.PASS, "r"))


class TestSerialization:
    def test_asdict_structure(
        self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference
    ) -> None:
        as_dict = dataclasses.asdict(
            RuleExecutionResult(valid_uuid, sample_rule_reference, RuleOutcome.PASS, "r")
        )
        assert as_dict["outcome"] is RuleOutcome.PASS


class TestStringRepresentation:
    def test_repr_contains_outcome(
        self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference
    ) -> None:
        result = RuleExecutionResult(valid_uuid, sample_rule_reference, RuleOutcome.PASS, "r")
        assert "PASS" in repr(result)


class TestEdgeCases:
    def test_every_outcome_value_constructible(
        self, valid_uuid: uuid.UUID, sample_rule_reference: RuleReference
    ) -> None:
        for outcome in RuleOutcome:
            RuleExecutionResult(valid_uuid, sample_rule_reference, outcome, "r")

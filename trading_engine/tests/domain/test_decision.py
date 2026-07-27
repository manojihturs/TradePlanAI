"""Tests for RuleEvaluationResult and Decision."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.decision import Decision, RuleEvaluationResult
from trading_engine.domain.evidence_reference import EvidenceLevel, EvidenceReference
from trading_engine.domain.rule_reference import (
    ConfidenceLevel,
    RuleCategory,
    RuleReference,
    RuleStatus,
)


@pytest.fixture
def sample_rule() -> RuleReference:
    return RuleReference(
        "STRIKE-001", RuleCategory.STRIKE, RuleStatus.DRAFT, ConfidenceLevel.MEDIUM, 2
    )


@pytest.fixture
def sample_evidence() -> EvidenceReference:
    return EvidenceReference("EVID-001", EvidenceLevel.ORIGINAL_TRANSCRIPT, "statement")


@pytest.fixture
def sample_result(
    valid_uuid: uuid.UUID,
    valid_datetime: datetime,
    sample_rule: RuleReference,
    sample_evidence: EvidenceReference,
) -> RuleEvaluationResult:
    return RuleEvaluationResult(
        valid_uuid, sample_rule, (sample_evidence,), "strike selected", valid_datetime
    )


class TestConstructorValidationResult:
    def test_valid_construction_succeeds(
        self, sample_result: RuleEvaluationResult, sample_rule: RuleReference
    ) -> None:
        assert sample_result.rule == sample_rule
        assert sample_result.outcome_description == "strike selected"
        assert sample_result.outcome_value is None

    def test_outcome_value_can_be_supplied(
        self,
        valid_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_rule: RuleReference,
        sample_evidence: EvidenceReference,
    ) -> None:
        result = RuleEvaluationResult(
            valid_uuid, sample_rule, (sample_evidence,), "desc", valid_datetime, outcome_value=42
        )
        assert result.outcome_value == 42


class TestInvalidConstructorValuesResult:
    def test_none_result_id_raises(
        self,
        valid_datetime: datetime,
        sample_rule: RuleReference,
        sample_evidence: EvidenceReference,
    ) -> None:
        with pytest.raises(DomainValidationError, match="result_id must not be None"):
            RuleEvaluationResult(None, sample_rule, (sample_evidence,), "desc", valid_datetime)  # type: ignore[arg-type]

    def test_blank_outcome_description_raises(
        self,
        valid_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_rule: RuleReference,
        sample_evidence: EvidenceReference,
    ) -> None:
        with pytest.raises(DomainValidationError, match="outcome_description must not be blank"):
            RuleEvaluationResult(valid_uuid, sample_rule, (sample_evidence,), "", valid_datetime)

    def test_whitespace_outcome_description_raises(
        self,
        valid_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_rule: RuleReference,
        sample_evidence: EvidenceReference,
    ) -> None:
        with pytest.raises(DomainValidationError, match="outcome_description must not be blank"):
            RuleEvaluationResult(valid_uuid, sample_rule, (sample_evidence,), "   ", valid_datetime)


class TestEqualityResult:
    def test_equal_values_are_equal(
        self,
        sample_result: RuleEvaluationResult,
        valid_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_rule: RuleReference,
        sample_evidence: EvidenceReference,
    ) -> None:
        other = RuleEvaluationResult(
            valid_uuid, sample_rule, (sample_evidence,), "strike selected", valid_datetime
        )
        assert sample_result == other


class TestImmutabilityResult:
    def test_cannot_reassign_outcome_description(self, sample_result: RuleEvaluationResult) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_result.outcome_description = "changed"  # type: ignore[misc]


class TestHashabilityResult:
    def test_is_hashable_with_default_outcome_value(
        self, sample_result: RuleEvaluationResult
    ) -> None:
        hash(sample_result)

    def test_is_hashable_with_hashable_outcome_value(
        self,
        valid_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_rule: RuleReference,
        sample_evidence: EvidenceReference,
    ) -> None:
        result = RuleEvaluationResult(
            valid_uuid, sample_rule, (sample_evidence,), "desc", valid_datetime, outcome_value=42
        )
        hash(result)


class TestCopyUpdateResult:
    def test_replace_produces_new_instance(self, sample_result: RuleEvaluationResult) -> None:
        updated = dataclasses.replace(sample_result, outcome_description="new description")
        assert updated is not sample_result
        assert updated.outcome_description == "new description"
        assert sample_result.outcome_description == "strike selected"


class TestSerializationResult:
    def test_asdict_structure(self, sample_result: RuleEvaluationResult) -> None:
        as_dict = dataclasses.asdict(sample_result)
        assert as_dict["outcome_description"] == "strike selected"
        assert as_dict["rule"]["rule_id"] == "STRIKE-001"


class TestStringRepresentationResult:
    def test_repr_contains_outcome_description(self, sample_result: RuleEvaluationResult) -> None:
        assert "strike selected" in repr(sample_result)


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------


class TestConstructorValidationDecision:
    def test_valid_construction_with_no_results(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID
    ) -> None:
        decision = Decision(valid_uuid, another_uuid)
        assert decision.results == ()
        assert decision.created_at is None

    def test_valid_construction_with_results(
        self,
        valid_uuid: uuid.UUID,
        another_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_result: RuleEvaluationResult,
    ) -> None:
        decision = Decision(valid_uuid, another_uuid, (sample_result,), valid_datetime)
        assert decision.results == (sample_result,)
        assert decision.created_at == valid_datetime


class TestInvalidConstructorValuesDecision:
    def test_none_decision_id_raises(self, another_uuid: uuid.UUID) -> None:
        with pytest.raises(DomainValidationError, match="decision_id must not be None"):
            Decision(None, another_uuid)  # type: ignore[arg-type]

    def test_none_session_id_raises(self, valid_uuid: uuid.UUID) -> None:
        with pytest.raises(DomainValidationError, match="session_id must not be None"):
            Decision(valid_uuid, None)  # type: ignore[arg-type]


class TestEqualityDecision:
    def test_equal_values_are_equal(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        assert Decision(valid_uuid, another_uuid) == Decision(valid_uuid, another_uuid)

    def test_different_results_not_equal(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, sample_result: RuleEvaluationResult
    ) -> None:
        empty = Decision(valid_uuid, another_uuid)
        populated = Decision(valid_uuid, another_uuid, (sample_result,))
        assert empty != populated


class TestImmutabilityDecision:
    def test_cannot_reassign_results(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        decision = Decision(valid_uuid, another_uuid)
        with pytest.raises(dataclasses.FrozenInstanceError):
            decision.results = ()  # type: ignore[misc]


class TestHashabilityDecision:
    def test_is_hashable_when_empty(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        hash(Decision(valid_uuid, another_uuid))

    def test_is_hashable_with_results(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, sample_result: RuleEvaluationResult
    ) -> None:
        hash(Decision(valid_uuid, another_uuid, (sample_result,)))


class TestCopyUpdateDecision:
    def test_replace_produces_new_instance(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, sample_result: RuleEvaluationResult
    ) -> None:
        original = Decision(valid_uuid, another_uuid)
        updated = dataclasses.replace(original, results=(sample_result,))
        assert updated is not original
        assert updated.results == (sample_result,)
        assert original.results == ()


class TestSerializationDecision:
    def test_asdict_structure(
        self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID, sample_result: RuleEvaluationResult
    ) -> None:
        as_dict = dataclasses.asdict(Decision(valid_uuid, another_uuid, (sample_result,)))
        assert len(as_dict["results"]) == 1


class TestStringRepresentationDecision:
    def test_repr_contains_class_name(self, valid_uuid: uuid.UUID, another_uuid: uuid.UUID) -> None:
        assert "Decision" in repr(Decision(valid_uuid, another_uuid))


class TestEdgeCasesDecision:
    def test_decision_aggregates_multiple_results_without_synthesis(
        self,
        valid_uuid: uuid.UUID,
        another_uuid: uuid.UUID,
        valid_datetime: datetime,
        sample_rule: RuleReference,
        sample_evidence: EvidenceReference,
    ) -> None:
        result_a = RuleEvaluationResult(
            uuid.uuid4(), sample_rule, (sample_evidence,), "a", valid_datetime
        )
        result_b = RuleEvaluationResult(
            uuid.uuid4(), sample_rule, (sample_evidence,), "b", valid_datetime
        )
        decision = Decision(valid_uuid, another_uuid, (result_a, result_b))
        # Purely a collection - no combination/synthesis attribute exists.
        assert decision.results == (result_a, result_b)
        assert not hasattr(decision, "combined_outcome")

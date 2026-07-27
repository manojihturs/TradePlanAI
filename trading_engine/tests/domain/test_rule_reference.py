"""Tests for RuleReference, RuleCategory, RuleStatus, ConfidenceLevel."""

from __future__ import annotations

import dataclasses

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.rule_reference import (
    ConfidenceLevel,
    RuleCategory,
    RuleReference,
    RuleStatus,
)


def _make(**overrides: object) -> RuleReference:
    defaults: dict[str, object] = {
        "rule_id": "STRIKE-001",
        "category": RuleCategory.STRIKE,
        "status": RuleStatus.DRAFT,
        "confidence": ConfidenceLevel.MEDIUM,
        "evidence_count": 2,
    }
    defaults.update(overrides)
    return RuleReference(**defaults)  # type: ignore[arg-type]


class TestConstructorValidation:
    def test_valid_construction_succeeds(self) -> None:
        ref = _make()
        assert ref.rule_id == "STRIKE-001"
        assert ref.category is RuleCategory.STRIKE
        assert ref.status is RuleStatus.DRAFT
        assert ref.confidence is ConfidenceLevel.MEDIUM
        assert ref.evidence_count == 2

    def test_evidence_count_defaults_to_zero(self) -> None:
        ref = RuleReference(
            "OPPONENT-002",
            RuleCategory.OPPONENT,
            RuleStatus.AWAITING_EVIDENCE,
            ConfidenceLevel.UNKNOWN,
        )
        assert ref.evidence_count == 0

    @pytest.mark.parametrize(
        "rule_id",
        [
            "STRIKE-001",
            "TREND-003",
            "OPPONENT-002",
            "WEEKLY_FUTURE-010",
            "A-000",
        ],
    )
    def test_accepts_valid_rule_id_patterns(self, rule_id: str) -> None:
        ref = _make(rule_id=rule_id)
        assert ref.rule_id == rule_id


class TestInvalidConstructorValues:
    def test_blank_rule_id_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="must not be blank"):
            _make(rule_id="")

    def test_whitespace_only_rule_id_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="must not be blank"):
            _make(rule_id="   ")

    @pytest.mark.parametrize(
        "bad_id",
        [
            "strike-001",  # lowercase category
            "STRIKE001",  # missing hyphen
            "STRIKE-1",  # not 3 digits
            "STRIKE-0001",  # 4 digits
            "STRIKE_001",  # underscore instead of hyphen before number
            "bad id",
        ],
    )
    def test_malformed_rule_id_raises(self, bad_id: str) -> None:
        with pytest.raises(DomainValidationError, match="does not match"):
            _make(rule_id=bad_id)

    def test_negative_evidence_count_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="must not be negative"):
            _make(evidence_count=-1)


class TestEquality:
    def test_equal_values_are_equal(self) -> None:
        assert _make() == _make()

    def test_different_rule_id_not_equal(self) -> None:
        assert _make(rule_id="STRIKE-001") != _make(rule_id="TREND-001")

    def test_different_evidence_count_not_equal(self) -> None:
        assert _make(evidence_count=1) != _make(evidence_count=2)

    def test_not_equal_to_other_type(self) -> None:
        assert _make() != "STRIKE-001"


class TestImmutability:
    def test_cannot_reassign_field(self) -> None:
        ref = _make()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ref.rule_id = "TREND-001"  # type: ignore[misc]

    def test_cannot_reassign_evidence_count(self) -> None:
        ref = _make()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ref.evidence_count = 5  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(self) -> None:
        hash(_make())  # must not raise

    def test_equal_instances_have_equal_hash(self) -> None:
        assert hash(_make()) == hash(_make())

    def test_usable_as_dict_key(self) -> None:
        d = {_make(): "value"}
        assert d[_make()] == "value"

    def test_usable_in_set(self) -> None:
        s = {_make(rule_id="STRIKE-001"), _make(rule_id="STRIKE-001"), _make(rule_id="TREND-001")}
        assert len(s) == 2


class TestCopyUpdate:
    def test_dataclasses_replace_produces_new_instance_with_change(self) -> None:
        original = _make(evidence_count=2)
        updated = dataclasses.replace(original, evidence_count=3)
        assert updated is not original
        assert updated.evidence_count == 3
        assert original.evidence_count == 2  # original untouched


class TestEnumBehaviour:
    def test_rule_category_members_match_bible_taxonomy(self) -> None:
        expected = {
            "CORE",
            "PHILOSOPHY",
            "WEEKLY_FUTURE",
            "FIRST_CANDLE",
            "STRIKE",
            "TREND",
            "STATE",
            "CONTROL_ZONE",
            "FLOW",
            "OPPONENT",
            "ENTRY",
            "EXIT",
            "REVERSAL",
            "DECAY",
            "PREMIUM",
            "RISK",
            "VALIDATION",
            "MATH",
            "UNKNOWN",
        }
        assert {member.name for member in RuleCategory} == expected

    def test_rule_status_members(self) -> None:
        expected = {"AWAITING_EVIDENCE", "DRAFT", "UNDER_REVIEW", "VALIDATED", "SUPERSEDED"}
        assert {member.name for member in RuleStatus} == expected

    def test_confidence_level_members(self) -> None:
        expected = {"UNKNOWN", "LOW", "MEDIUM", "HIGH", "CONFIRMED"}
        assert {member.name for member in ConfidenceLevel} == expected

    def test_enum_members_are_distinct(self) -> None:
        assert RuleCategory.STRIKE != RuleCategory.TREND
        assert RuleStatus.DRAFT != RuleStatus.VALIDATED
        assert ConfidenceLevel.LOW != ConfidenceLevel.HIGH

    def test_invalid_enum_value_raises(self) -> None:
        with pytest.raises(ValueError):
            RuleCategory("NOT_A_CATEGORY")


class TestSerialization:
    def test_asdict_roundtrip_structure(self) -> None:
        ref = _make()
        as_dict = dataclasses.asdict(ref)
        assert as_dict["rule_id"] == "STRIKE-001"
        assert as_dict["category"] is RuleCategory.STRIKE
        assert as_dict["evidence_count"] == 2


class TestStringRepresentation:
    def test_repr_contains_class_name_and_rule_id(self) -> None:
        text = repr(_make())
        assert "RuleReference" in text
        assert "STRIKE-001" in text


class TestEdgeCases:
    def test_evidence_count_zero_is_valid(self) -> None:
        ref = _make(evidence_count=0)
        assert ref.evidence_count == 0

    def test_large_evidence_count_is_valid(self) -> None:
        ref = _make(evidence_count=1_000_000)
        assert ref.evidence_count == 1_000_000

    def test_all_categories_constructible(self) -> None:
        for category in RuleCategory:
            _make(category=category)

    def test_all_statuses_constructible(self) -> None:
        for status in RuleStatus:
            _make(status=status)

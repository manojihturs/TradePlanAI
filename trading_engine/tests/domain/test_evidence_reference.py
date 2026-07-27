"""Tests for EvidenceReference, EvidenceLevel."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from trading_engine.domain import DomainValidationError
from trading_engine.domain.evidence_reference import EvidenceLevel, EvidenceReference


def _make(**overrides: object) -> EvidenceReference:
    defaults: dict[str, object] = {
        "evidence_id": "EVID-007",
        "level": EvidenceLevel.ORIGINAL_TRANSCRIPT,
        "description": "TR-001 transcript, first-candle strike selection statement",
        "source_path": Path("research/transcripts/TR-001.md"),
    }
    defaults.update(overrides)
    return EvidenceReference(**defaults)  # type: ignore[arg-type]


class TestConstructorValidation:
    def test_valid_construction_succeeds(self) -> None:
        ref = _make()
        assert ref.evidence_id == "EVID-007"
        assert ref.level is EvidenceLevel.ORIGINAL_TRANSCRIPT
        assert ref.source_path == Path("research/transcripts/TR-001.md")

    def test_source_path_defaults_to_none(self) -> None:
        ref = EvidenceReference(
            "EVID-001", EvidenceLevel.HYPOTHESIS, "unsaved conversational statement"
        )
        assert ref.source_path is None

    def test_none_source_path_is_a_legitimate_documented_state(self) -> None:
        # Per docs/TRACEABILITY_MATRIX.md: EVID-001..006 legitimately
        # have no saved source file. This must not raise.
        ref = _make(source_path=None)
        assert ref.source_path is None


class TestInvalidConstructorValues:
    def test_blank_evidence_id_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="evidence_id must not be blank"):
            _make(evidence_id="")

    def test_whitespace_only_evidence_id_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="evidence_id must not be blank"):
            _make(evidence_id="   ")

    def test_blank_description_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="description must not be blank"):
            _make(description="")

    def test_whitespace_only_description_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="description must not be blank"):
            _make(description="   ")


class TestEquality:
    def test_equal_values_are_equal(self) -> None:
        assert _make() == _make()

    def test_different_evidence_id_not_equal(self) -> None:
        assert _make(evidence_id="EVID-001") != _make(evidence_id="EVID-002")

    def test_different_source_path_not_equal(self) -> None:
        assert _make(source_path=Path("a.md")) != _make(source_path=Path("b.md"))


class TestImmutability:
    def test_cannot_reassign_field(self) -> None:
        ref = _make()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ref.evidence_id = "EVID-999"  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(self) -> None:
        hash(_make())

    def test_equal_instances_have_equal_hash(self) -> None:
        assert hash(_make()) == hash(_make())

    def test_hashable_with_none_source_path(self) -> None:
        hash(_make(source_path=None))


class TestCopyUpdate:
    def test_replace_produces_new_instance(self) -> None:
        original = _make(description="original description")
        updated = dataclasses.replace(original, description="updated description")
        assert updated is not original
        assert updated.description == "updated description"
        assert original.description == "original description"


class TestEnumBehaviour:
    def test_evidence_level_values_match_knowledge_sources(self) -> None:
        assert EvidenceLevel.ORIGINAL_TRANSCRIPT.value == 1
        assert EvidenceLevel.MANUAL_OBSERVATION.value == 2
        assert EvidenceLevel.EXISTING_IMPLEMENTATION.value == 3
        assert EvidenceLevel.HYPOTHESIS.value == 4

    def test_levels_are_ordered_by_value_as_documented(self) -> None:
        # research/KNOWLEDGE_SOURCES.md: higher numbered levels do not
        # override lower ones - just verifying the numeric ordering
        # exists as documented, not that any override logic exists.
        levels = [e.value for e in EvidenceLevel]
        assert levels == sorted(levels)

    def test_invalid_enum_value_raises(self) -> None:
        with pytest.raises(ValueError):
            EvidenceLevel(99)


class TestSerialization:
    def test_asdict_structure(self) -> None:
        as_dict = dataclasses.asdict(_make())
        assert as_dict["evidence_id"] == "EVID-007"
        assert as_dict["level"] is EvidenceLevel.ORIGINAL_TRANSCRIPT


class TestStringRepresentation:
    def test_repr_contains_evidence_id(self) -> None:
        assert "EVID-007" in repr(_make())


class TestEdgeCases:
    def test_all_evidence_levels_constructible(self) -> None:
        for level in EvidenceLevel:
            _make(level=level)

    def test_long_description_accepted(self) -> None:
        long_description = "x" * 5000
        ref = _make(description=long_description)
        assert ref.description == long_description

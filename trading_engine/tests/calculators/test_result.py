"""Tests for CalculationStatus and CalculationResult."""

from __future__ import annotations

import dataclasses
import uuid

import pytest

from trading_engine.calculators.exceptions import CalculationError
from trading_engine.calculators.result import CalculationResult, CalculationStatus


class TestCalculationStatusEnum:
    def test_member_set(self) -> None:
        expected = {"SUCCESS", "FAILURE", "NOT_IMPLEMENTED", "INVALID_CONTEXT"}
        assert {member.name for member in CalculationStatus} == expected

    def test_invalid_member_name_raises(self) -> None:
        with pytest.raises(KeyError):
            CalculationStatus["NOT_A_MEMBER"]


class TestConstructorValidation:
    def test_valid_construction_with_defaults(self, valid_uuid: uuid.UUID) -> None:
        result = CalculationResult(
            calculation_id=valid_uuid,
            calculator_id="STRIKE-001-CALCULATOR",
            success=False,
            status=CalculationStatus.NOT_IMPLEMENTED,
        )
        assert result.success is False
        assert result.metadata == {}
        assert result.warnings == ()
        assert result.errors == ()
        assert result.computed_values == {}

    def test_valid_construction_with_all_fields(self, valid_uuid: uuid.UUID) -> None:
        result = CalculationResult(
            calculation_id=valid_uuid,
            calculator_id="X",
            success=True,
            status=CalculationStatus.SUCCESS,
            metadata={"duration_ms": 3},
            warnings=("w",),
            errors=(),
            computed_values={"value": 1},
        )
        assert result.metadata == {"duration_ms": 3}
        assert result.computed_values == {"value": 1}


class TestInvalidConstructorValues:
    def test_none_calculation_id_raises(self) -> None:
        with pytest.raises(CalculationError, match="calculation_id must not be None"):
            CalculationResult(
                calculation_id=None,  # type: ignore[arg-type]
                calculator_id="X",
                success=True,
                status=CalculationStatus.SUCCESS,
            )

    def test_blank_calculator_id_raises(self, valid_uuid: uuid.UUID) -> None:
        with pytest.raises(CalculationError, match="calculator_id must not be blank"):
            CalculationResult(
                calculation_id=valid_uuid,
                calculator_id="   ",
                success=True,
                status=CalculationStatus.SUCCESS,
            )


class TestEquality:
    def test_equal_values_are_equal(self, valid_uuid: uuid.UUID) -> None:
        a = CalculationResult(valid_uuid, "X", True, CalculationStatus.SUCCESS)
        b = CalculationResult(valid_uuid, "X", True, CalculationStatus.SUCCESS)
        assert a == b

    def test_different_status_not_equal(self, valid_uuid: uuid.UUID) -> None:
        a = CalculationResult(valid_uuid, "X", True, CalculationStatus.SUCCESS)
        b = CalculationResult(valid_uuid, "X", True, CalculationStatus.FAILURE)
        assert a != b


class TestImmutability:
    def test_cannot_reassign_success(self, valid_uuid: uuid.UUID) -> None:
        result = CalculationResult(valid_uuid, "X", True, CalculationStatus.SUCCESS)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.success = False  # type: ignore[misc]


class TestSerialization:
    def test_asdict_structure(self, valid_uuid: uuid.UUID) -> None:
        as_dict = dataclasses.asdict(
            CalculationResult(valid_uuid, "X", True, CalculationStatus.SUCCESS)
        )
        assert as_dict["status"] is CalculationStatus.SUCCESS


class TestStringRepresentation:
    def test_repr_contains_calculator_id(self, valid_uuid: uuid.UUID) -> None:
        result = CalculationResult(
            valid_uuid, "STRIKE-001-CALCULATOR", True, CalculationStatus.SUCCESS
        )
        assert "STRIKE-001-CALCULATOR" in repr(result)


class TestEdgeCases:
    def test_not_implemented_status_with_success_false_is_the_common_case(
        self, valid_uuid: uuid.UUID
    ) -> None:
        result = CalculationResult(valid_uuid, "X", False, CalculationStatus.NOT_IMPLEMENTED)
        assert result.success is False
        assert result.status is CalculationStatus.NOT_IMPLEMENTED

    def test_every_status_value_constructible(self, valid_uuid: uuid.UUID) -> None:
        for status in CalculationStatus:
            CalculationResult(valid_uuid, "X", True, status)

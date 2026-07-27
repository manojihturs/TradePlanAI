"""Tests for EngineConfiguration."""

from __future__ import annotations

import dataclasses

import pytest

from trading_engine.engine.engine_configuration import EngineConfiguration
from trading_engine.engine.exceptions import EngineConfigurationError, EngineError


class TestConstructorValidation:
    def test_default_construction_succeeds(self) -> None:
        config = EngineConfiguration()
        assert config.fail_fast is False
        assert config.continue_on_error is True
        assert config.maximum_rule_count is None
        assert config.logging_enabled is False
        assert config.dry_run is False

    def test_valid_construction_with_explicit_values(self) -> None:
        config = EngineConfiguration(
            fail_fast=True,
            continue_on_error=False,
            maximum_rule_count=5,
            logging_enabled=True,
            dry_run=True,
        )
        assert config.fail_fast is True
        assert config.maximum_rule_count == 5
        assert config.dry_run is True


class TestInvalidConstructorValues:
    def test_fail_fast_and_continue_on_error_both_true_raises(self) -> None:
        with pytest.raises(EngineConfigurationError, match="cannot both be True"):
            EngineConfiguration(fail_fast=True, continue_on_error=True)

    def test_zero_maximum_rule_count_raises(self) -> None:
        with pytest.raises(EngineConfigurationError, match="positive integer"):
            EngineConfiguration(maximum_rule_count=0)

    def test_negative_maximum_rule_count_raises(self) -> None:
        with pytest.raises(EngineConfigurationError, match="positive integer"):
            EngineConfiguration(maximum_rule_count=-1)

    def test_engine_configuration_error_is_an_engine_error(self) -> None:
        assert issubclass(EngineConfigurationError, EngineError)


class TestEquality:
    def test_equal_values_are_equal(self) -> None:
        assert EngineConfiguration() == EngineConfiguration()

    def test_different_dry_run_not_equal(self) -> None:
        assert EngineConfiguration(dry_run=True) != EngineConfiguration(dry_run=False)


class TestImmutability:
    def test_cannot_reassign_fail_fast(self) -> None:
        config = EngineConfiguration()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.fail_fast = True  # type: ignore[misc]


class TestHashability:
    def test_is_hashable(self) -> None:
        hash(EngineConfiguration())


class TestSerialization:
    def test_asdict_structure(self) -> None:
        as_dict = dataclasses.asdict(EngineConfiguration(maximum_rule_count=3))
        assert as_dict["maximum_rule_count"] == 3


class TestStringRepresentation:
    def test_repr_contains_class_name(self) -> None:
        assert "EngineConfiguration" in repr(EngineConfiguration())


class TestEdgeCases:
    def test_maximum_rule_count_of_one_is_valid(self) -> None:
        config = EngineConfiguration(maximum_rule_count=1)
        assert config.maximum_rule_count == 1

    def test_both_fail_fast_and_continue_on_error_false_is_valid(self) -> None:
        config = EngineConfiguration(fail_fast=False, continue_on_error=False)
        assert config.fail_fast is False
        assert config.continue_on_error is False

"""Tests for application.replay_configuration."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from application.replay_configuration import ReplayConfiguration
from core.exceptions import ValidationError


def _config(**overrides: object) -> ReplayConfiguration:
    defaults: dict[str, object] = {
        "start_date": date(2026, 7, 1),
        "end_date": date(2026, 7, 31),
        "symbols": ("NIFTY",),
        "timeframe": "5m",
    }
    defaults.update(overrides)
    return ReplayConfiguration(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_valid_construction(self) -> None:
        config = _config()

        assert config.symbols == ("NIFTY",)
        assert config.replay_speed == Decimal(1)

    def test_defaults(self) -> None:
        config = ReplayConfiguration(start_date=date(2026, 7, 1), end_date=date(2026, 7, 1))

        assert config.symbols == ()
        assert config.timeframe == ""


class TestValidation:
    def test_none_start_date_raises(self) -> None:
        with pytest.raises(ValidationError, match="start_date must not be None"):
            _config(start_date=None)

    def test_none_end_date_raises(self) -> None:
        with pytest.raises(ValidationError, match="end_date must not be None"):
            _config(end_date=None)

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValidationError, match="end_date must not be before start_date"):
            _config(start_date=date(2026, 7, 31), end_date=date(2026, 7, 1))

    def test_zero_replay_speed_raises(self) -> None:
        with pytest.raises(ValidationError, match="replay_speed must be greater than 0"):
            _config(replay_speed=Decimal(0))

    def test_negative_replay_speed_raises(self) -> None:
        with pytest.raises(ValidationError, match="replay_speed must be greater than 0"):
            _config(replay_speed=Decimal(-1))

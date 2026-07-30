"""Tests for data.historical_dataset."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from data.historical_dataset import HistoricalDataset
from models.market_snapshot import MarketSnapshot


def _snapshot(second: int) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 20, second, tzinfo=UTC),
        underlying_price=Decimal(24000),
    )


def _dataset(**overrides: object) -> HistoricalDataset:
    defaults: dict[str, object] = {
        "symbol": "NIFTY",
        "timeframe": "1m",
        "date_range_start": date(2026, 7, 30),
        "date_range_end": date(2026, 7, 30),
        "snapshots": (_snapshot(0), _snapshot(1)),
    }
    defaults.update(overrides)
    return HistoricalDataset(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_valid_construction(self) -> None:
        dataset = _dataset()

        assert dataset.key == "NIFTY@1m"
        assert dataset.metadata == {}


class TestValidation:
    def test_blank_symbol_raises(self) -> None:
        with pytest.raises(ValidationError, match="symbol must not be blank"):
            _dataset(symbol="  ")

    def test_blank_timeframe_raises(self) -> None:
        with pytest.raises(ValidationError, match="timeframe must not be blank"):
            _dataset(timeframe="  ")

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValidationError, match="date_range_end must not be before"):
            _dataset(date_range_start=date(2026, 7, 30), date_range_end=date(2026, 7, 1))

    def test_empty_snapshots_raises(self) -> None:
        with pytest.raises(ValidationError, match="snapshots must not be empty"):
            _dataset(snapshots=())

    def test_out_of_order_snapshots_raises(self) -> None:
        with pytest.raises(ValidationError, match="chronological order"):
            _dataset(snapshots=(_snapshot(5), _snapshot(1)))

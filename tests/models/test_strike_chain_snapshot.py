"""Tests for models.strike_chain_snapshot."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.strike_chain_snapshot import StrikeChainSnapshot

_TIMESTAMP = datetime(2026, 7, 30, 9, 25, 0, tzinfo=UTC)


def _snapshot(timestamp: datetime = _TIMESTAMP, price: str = "100") -> MarketSnapshot:
    return MarketSnapshot(timestamp=timestamp, underlying_price=Decimal(price))


class TestValidConstruction:
    def test_valid_pair(self) -> None:
        pair = StrikeChainSnapshot(strike=Decimal(24000), ce=_snapshot(), pe=_snapshot())

        assert pair.strike == Decimal(24000)
        assert pair.ce.timestamp == _TIMESTAMP
        assert pair.pe.timestamp == _TIMESTAMP


class TestInvalidConstruction:
    def test_non_positive_strike_raises(self) -> None:
        with pytest.raises(ValidationError, match="strike must be greater than 0"):
            StrikeChainSnapshot(strike=Decimal(0), ce=_snapshot(), pe=_snapshot())

    def test_none_ce_raises(self) -> None:
        with pytest.raises(ValidationError, match="ce must not be None"):
            StrikeChainSnapshot(strike=Decimal(24000), ce=None, pe=_snapshot())  # type: ignore[arg-type]

    def test_none_pe_raises(self) -> None:
        with pytest.raises(ValidationError, match="pe must not be None"):
            StrikeChainSnapshot(strike=Decimal(24000), ce=_snapshot(), pe=None)  # type: ignore[arg-type]

    def test_mismatched_timestamps_raises(self) -> None:
        other_timestamp = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)
        with pytest.raises(ValidationError, match="must share the same timestamp"):
            StrikeChainSnapshot(
                strike=Decimal(24000),
                ce=_snapshot(_TIMESTAMP),
                pe=_snapshot(other_timestamp),
            )

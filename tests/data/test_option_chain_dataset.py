"""Tests for data.option_chain_dataset."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from data.option_chain_dataset import OptionChainCandle, OptionChainDataset
from models.market_snapshot import MarketSnapshot
from models.strike_chain_snapshot import StrikeChainSnapshot

_TIMESTAMP = datetime(2026, 7, 30, 9, 25, 0, tzinfo=UTC)


def _pair(strike: int, timestamp: datetime = _TIMESTAMP) -> StrikeChainSnapshot:
    snapshot = MarketSnapshot(timestamp=timestamp, underlying_price=Decimal(strike))
    return StrikeChainSnapshot(strike=Decimal(strike), ce=snapshot, pe=snapshot)


class TestOptionChainCandleValidConstruction:
    def test_valid_candle(self) -> None:
        candle = OptionChainCandle(timestamp=_TIMESTAMP, strikes=(_pair(24000), _pair(24050)))

        assert candle.timestamp == _TIMESTAMP
        assert len(candle.strikes) == 2


class TestOptionChainCandleInvalidConstruction:
    def test_none_timestamp_raises(self) -> None:
        with pytest.raises(ValidationError, match="timestamp must not be None"):
            OptionChainCandle(timestamp=None, strikes=(_pair(24000),))  # type: ignore[arg-type]

    def test_empty_strikes_raises(self) -> None:
        with pytest.raises(ValidationError, match="strikes must not be empty"):
            OptionChainCandle(timestamp=_TIMESTAMP, strikes=())

    def test_mismatched_strike_timestamp_raises(self) -> None:
        other = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)
        with pytest.raises(ValidationError, match="does not match"):
            OptionChainCandle(timestamp=_TIMESTAMP, strikes=(_pair(24000, other),))

    def test_duplicate_strike_raises(self) -> None:
        with pytest.raises(ValidationError, match="must not repeat a strike"):
            OptionChainCandle(timestamp=_TIMESTAMP, strikes=(_pair(24000), _pair(24000)))


class TestOptionChainDatasetValidConstruction:
    def test_valid_dataset(self) -> None:
        candle1 = OptionChainCandle(timestamp=_TIMESTAMP, strikes=(_pair(24000),))
        candle2 = OptionChainCandle(
            timestamp=_TIMESTAMP + timedelta(minutes=5),
            strikes=(_pair(24000, _TIMESTAMP + timedelta(minutes=5)),),
        )
        dataset = OptionChainDataset(session_date=date(2026, 7, 30), candles=(candle1, candle2))

        assert dataset.session_date == date(2026, 7, 30)
        assert len(dataset.candles) == 2


class TestOptionChainDatasetInvalidConstruction:
    def test_none_session_date_raises(self) -> None:
        candle = OptionChainCandle(timestamp=_TIMESTAMP, strikes=(_pair(24000),))
        with pytest.raises(ValidationError, match="session_date must not be None"):
            OptionChainDataset(session_date=None, candles=(candle,))  # type: ignore[arg-type]

    def test_empty_candles_raises(self) -> None:
        with pytest.raises(ValidationError, match="candles must not be empty"):
            OptionChainDataset(session_date=date(2026, 7, 30), candles=())

    def test_out_of_order_candles_raises(self) -> None:
        early = OptionChainCandle(timestamp=_TIMESTAMP, strikes=(_pair(24000),))
        earlier_still = OptionChainCandle(
            timestamp=_TIMESTAMP - timedelta(minutes=5),
            strikes=(_pair(24000, _TIMESTAMP - timedelta(minutes=5)),),
        )
        with pytest.raises(ValidationError, match="chronological order"):
            OptionChainDataset(session_date=date(2026, 7, 30), candles=(early, earlier_still))

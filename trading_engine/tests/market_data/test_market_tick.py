"""Tests for MarketTick."""

from __future__ import annotations

import dataclasses
from datetime import datetime
from decimal import Decimal

import pytest

from trading_engine.market_data.exceptions import MarketDataValidationError
from trading_engine.market_data.instrument_resolver import InstrumentKey
from trading_engine.market_data.market_tick import MarketTick


class TestConstructorValidation:
    def test_valid_construction(
        self, base_timestamp: datetime, sample_instrument: InstrumentKey
    ) -> None:
        tick = MarketTick(base_timestamp, sample_instrument, Decimal("125.5"), 1000, 5000)
        assert tick.last_traded_price == Decimal("125.5")

    def test_valid_construction_with_bid_ask(
        self, base_timestamp: datetime, sample_instrument: InstrumentKey
    ) -> None:
        tick = MarketTick(
            base_timestamp,
            sample_instrument,
            Decimal("125.5"),
            1000,
            5000,
            bid=Decimal(125),
            ask=Decimal(126),
        )
        assert tick.bid == Decimal(125)
        assert tick.ask == Decimal(126)

    def test_none_timestamp_raises(self, sample_instrument: InstrumentKey) -> None:
        with pytest.raises(MarketDataValidationError, match="timestamp must not be None"):
            MarketTick(None, sample_instrument, Decimal(100), 0, 0)  # type: ignore[arg-type]

    def test_none_instrument_raises(self, base_timestamp: datetime) -> None:
        with pytest.raises(MarketDataValidationError, match="instrument must not be None"):
            MarketTick(base_timestamp, None, Decimal(100), 0, 0)  # type: ignore[arg-type]

    def test_zero_price_raises(
        self, base_timestamp: datetime, sample_instrument: InstrumentKey
    ) -> None:
        with pytest.raises(
            MarketDataValidationError, match="last_traded_price must be greater than 0"
        ):
            MarketTick(base_timestamp, sample_instrument, Decimal(0), 0, 0)

    def test_negative_volume_raises(
        self, base_timestamp: datetime, sample_instrument: InstrumentKey
    ) -> None:
        with pytest.raises(MarketDataValidationError, match="volume must not be negative"):
            MarketTick(base_timestamp, sample_instrument, Decimal(100), -1, 0)

    def test_negative_open_interest_raises(
        self, base_timestamp: datetime, sample_instrument: InstrumentKey
    ) -> None:
        with pytest.raises(MarketDataValidationError, match="open_interest must not be negative"):
            MarketTick(base_timestamp, sample_instrument, Decimal(100), 0, -1)

    def test_bid_above_ask_raises(
        self, base_timestamp: datetime, sample_instrument: InstrumentKey
    ) -> None:
        with pytest.raises(MarketDataValidationError, match="must not exceed ask"):
            MarketTick(
                base_timestamp,
                sample_instrument,
                Decimal(100),
                0,
                0,
                bid=Decimal(105),
                ask=Decimal(100),
            )

    def test_bid_equal_to_ask_is_valid(
        self, base_timestamp: datetime, sample_instrument: InstrumentKey
    ) -> None:
        tick = MarketTick(
            base_timestamp,
            sample_instrument,
            Decimal(100),
            0,
            0,
            bid=Decimal(100),
            ask=Decimal(100),
        )
        assert tick.bid == tick.ask

    def test_only_bid_given_is_valid(
        self, base_timestamp: datetime, sample_instrument: InstrumentKey
    ) -> None:
        tick = MarketTick(base_timestamp, sample_instrument, Decimal(100), 0, 0, bid=Decimal(99))
        assert tick.ask is None

    def test_immutability(self, base_timestamp: datetime, sample_instrument: InstrumentKey) -> None:
        tick = MarketTick(base_timestamp, sample_instrument, Decimal(100), 0, 0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            tick.last_traded_price = Decimal(200)  # type: ignore[misc]

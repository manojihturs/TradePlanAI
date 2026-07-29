"""Shared fixtures for the premium snapshot test suite."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from trading_engine.market_data.instrument_resolver import InstrumentKey
from trading_engine.market_data.market_tick import MarketTick


@pytest.fixture
def window_start() -> datetime:
    return datetime(2026, 7, 3, 9, 15, 0)  # noqa: DTZ001


@pytest.fixture
def window_end(window_start: datetime) -> datetime:
    return window_start + timedelta(minutes=5)


@pytest.fixture
def session_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def top_ce_instrument() -> InstrumentKey:
    return InstrumentKey(token="NSE_FO|1", symbol="NIFTY24070124000CE", exchange="NSE_FO")


@pytest.fixture
def top_pe_instrument() -> InstrumentKey:
    return InstrumentKey(token="NSE_FO|2", symbol="NIFTY24070124000PE", exchange="NSE_FO")


@pytest.fixture
def bottom_ce_instrument() -> InstrumentKey:
    return InstrumentKey(token="NSE_FO|3", symbol="NIFTY24070123900CE", exchange="NSE_FO")


@pytest.fixture
def bottom_pe_instrument() -> InstrumentKey:
    return InstrumentKey(token="NSE_FO|4", symbol="NIFTY24070123900PE", exchange="NSE_FO")


def make_tick(
    instrument: InstrumentKey,
    timestamp: datetime,
    price: str,
    volume: int = 100,
    open_interest: int = 500,
) -> MarketTick:
    return MarketTick(
        timestamp=timestamp,
        instrument=instrument,
        last_traded_price=Decimal(price),
        volume=volume,
        open_interest=open_interest,
    )

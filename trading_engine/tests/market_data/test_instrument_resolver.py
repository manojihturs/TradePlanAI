"""Tests for InstrumentKey, OptionType, and InstrumentResolver."""

from __future__ import annotations

import dataclasses
from datetime import date
from decimal import Decimal

import pytest

from trading_engine.market_data.exceptions import (
    InstrumentResolutionError,
    MarketDataValidationError,
)
from trading_engine.market_data.instrument_resolver import (
    InstrumentKey,
    InstrumentResolver,
    OptionType,
)


class TestInstrumentKeyValidation:
    def test_valid_construction(self) -> None:
        key = InstrumentKey(token="T1", symbol="NIFTY", exchange="NSE_INDEX")
        assert key.token == "T1"

    def test_blank_token_raises(self) -> None:
        with pytest.raises(MarketDataValidationError, match="token must not be blank"):
            InstrumentKey(token="   ", symbol="NIFTY", exchange="NSE_INDEX")

    def test_blank_symbol_raises(self) -> None:
        with pytest.raises(MarketDataValidationError, match="symbol must not be blank"):
            InstrumentKey(token="T1", symbol="", exchange="NSE_INDEX")

    def test_blank_exchange_raises(self) -> None:
        with pytest.raises(MarketDataValidationError, match="exchange must not be blank"):
            InstrumentKey(token="T1", symbol="NIFTY", exchange="")

    def test_immutable_and_hashable(self) -> None:
        key = InstrumentKey(token="T1", symbol="NIFTY", exchange="NSE_INDEX")
        with pytest.raises(dataclasses.FrozenInstanceError):
            key.token = "T2"  # type: ignore[misc]
        hash(key)


class TestOptionType:
    def test_member_set(self) -> None:
        assert {member.name for member in OptionType} == {"CALL", "PUT"}


class TestResolveSpot:
    def test_registers_and_resolves(self) -> None:
        resolver = InstrumentResolver()
        key = InstrumentKey(token="T1", symbol="NIFTY", exchange="NSE_INDEX")
        resolver.register_spot("NIFTY", key)
        assert resolver.resolve_spot("NIFTY") is key

    def test_unregistered_symbol_raises(self) -> None:
        resolver = InstrumentResolver()
        with pytest.raises(InstrumentResolutionError, match="No spot instrument"):
            resolver.resolve_spot("BANKNIFTY")


class TestResolveOption:
    def test_registers_and_resolves(self) -> None:
        resolver = InstrumentResolver()
        key = InstrumentKey(token="T2", symbol="NIFTY24070124000CE", exchange="NSE_FO")
        expiry = date(2026, 7, 3)
        resolver.register_option("NIFTY", expiry, Decimal(24000), OptionType.CALL, key)
        resolved = resolver.resolve_option("NIFTY", expiry, Decimal(24000), OptionType.CALL)
        assert resolved is key

    def test_unregistered_combination_raises(self) -> None:
        resolver = InstrumentResolver()
        with pytest.raises(InstrumentResolutionError, match="No option instrument"):
            resolver.resolve_option("NIFTY", date(2026, 7, 3), Decimal(24000), OptionType.PUT)

    def test_call_and_put_are_distinct(self) -> None:
        resolver = InstrumentResolver()
        expiry = date(2026, 7, 3)
        call_key = InstrumentKey(token="CE", symbol="NIFTY-CE", exchange="NSE_FO")
        put_key = InstrumentKey(token="PE", symbol="NIFTY-PE", exchange="NSE_FO")
        resolver.register_option("NIFTY", expiry, Decimal(24000), OptionType.CALL, call_key)
        resolver.register_option("NIFTY", expiry, Decimal(24000), OptionType.PUT, put_key)
        assert resolver.resolve_option("NIFTY", expiry, Decimal(24000), OptionType.CALL) is call_key
        assert resolver.resolve_option("NIFTY", expiry, Decimal(24000), OptionType.PUT) is put_key


class TestOptionChain:
    def test_returns_every_registered_instrument_for_underlying_and_expiry(self) -> None:
        resolver = InstrumentResolver()
        expiry = date(2026, 7, 3)
        call_key = InstrumentKey(token="CE", symbol="NIFTY-CE", exchange="NSE_FO")
        put_key = InstrumentKey(token="PE", symbol="NIFTY-PE", exchange="NSE_FO")
        resolver.register_option("NIFTY", expiry, Decimal(24000), OptionType.CALL, call_key)
        resolver.register_option("NIFTY", expiry, Decimal(23900), OptionType.PUT, put_key)
        chain = resolver.option_chain("NIFTY", expiry)
        assert set(chain) == {call_key, put_key}

    def test_excludes_other_underlyings_and_expiries(self) -> None:
        resolver = InstrumentResolver()
        expiry = date(2026, 7, 3)
        other_expiry = date(2026, 7, 10)
        nifty_key = InstrumentKey(token="A", symbol="NIFTY-CE", exchange="NSE_FO")
        banknifty_key = InstrumentKey(token="B", symbol="BANKNIFTY-CE", exchange="NSE_FO")
        other_expiry_key = InstrumentKey(token="C", symbol="NIFTY-CE2", exchange="NSE_FO")
        resolver.register_option("NIFTY", expiry, Decimal(24000), OptionType.CALL, nifty_key)
        resolver.register_option(
            "BANKNIFTY", expiry, Decimal(50000), OptionType.CALL, banknifty_key
        )
        resolver.register_option(
            "NIFTY", other_expiry, Decimal(24000), OptionType.CALL, other_expiry_key
        )
        chain = resolver.option_chain("NIFTY", expiry)
        assert chain == (nifty_key,)

    def test_empty_when_nothing_registered(self) -> None:
        resolver = InstrumentResolver()
        assert resolver.option_chain("NIFTY", date(2026, 7, 3)) == ()

"""Tests for the MarketDataProvider protocol and ConnectionState."""

from __future__ import annotations

from trading_engine.market_data.market_data_provider import ConnectionState, MarketDataProvider
from trading_engine.market_data.upstox_provider import UpstoxProvider


class TestConnectionState:
    def test_member_set(self) -> None:
        expected = {"DISCONNECTED", "CONNECTING", "CONNECTED", "RECONNECTING"}
        assert {member.name for member in ConnectionState} == expected


class TestProtocolConformance:
    def test_upstox_provider_satisfies_protocol(self, provider: UpstoxProvider) -> None:
        assert isinstance(provider, MarketDataProvider)

    def test_default_state_is_disconnected(self, provider: UpstoxProvider) -> None:
        assert provider.state == ConnectionState.DISCONNECTED

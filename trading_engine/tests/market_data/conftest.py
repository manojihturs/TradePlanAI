"""Shared fixtures and test doubles for the market data test suite."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import pytest

from trading_engine.diagnostics.sink import InMemoryDiagnosticsSink
from trading_engine.market_data.instrument_resolver import InstrumentKey
from trading_engine.market_data.upstox_provider import (
    UpstoxCredentials,
    UpstoxProvider,
)


@pytest.fixture
def base_timestamp() -> datetime:
    return datetime(2026, 7, 3, 9, 15, 0)  # noqa: DTZ001


@pytest.fixture
def sample_instrument() -> InstrumentKey:
    return InstrumentKey(token="NSE_FO|12345", symbol="NIFTY24070124000CE", exchange="NSE_FO")


@pytest.fixture
def another_instrument() -> InstrumentKey:
    return InstrumentKey(token="NSE_FO|67890", symbol="NIFTY24070123900PE", exchange="NSE_FO")


@pytest.fixture
def spot_instrument() -> InstrumentKey:
    return InstrumentKey(token="NSE_INDEX|26000", symbol="NIFTY", exchange="NSE_INDEX")


@pytest.fixture
def credentials() -> UpstoxCredentials:
    return UpstoxCredentials(
        client_id="test-client-id",
        client_secret="test-secret",
        redirect_uri="https://example.test/callback",
    )


class FakeRestTransport:
    """A configurable, network-free test double for ``RestTransport``."""

    def __init__(
        self,
        response: Mapping[str, Any] | None = None,
        raise_exception: Exception | None = None,
    ) -> None:
        self.response = (
            response if response is not None else {"access_token": "token-1", "expires_in": 3600}
        )
        self.raise_exception = raise_exception
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def post(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append((path, payload))
        if self.raise_exception is not None:
            raise self.raise_exception
        return self.response


class FakeWebSocketTransport:
    """A configurable, network-free test double for ``WebSocketTransport``."""

    def __init__(self) -> None:
        self._open = False
        self.opened_urls: list[str] = []
        self.sent_messages: list[str] = []
        self.close_count = 0

    def open(self, url: str) -> None:
        self.opened_urls.append(url)
        self._open = True

    def close(self) -> None:
        self.close_count += 1
        self._open = False

    def send(self, message: str) -> None:
        self.sent_messages.append(message)

    def is_open(self) -> bool:
        return self._open


@pytest.fixture
def rest_transport() -> FakeRestTransport:
    return FakeRestTransport()


@pytest.fixture
def websocket_transport() -> FakeWebSocketTransport:
    return FakeWebSocketTransport()


@pytest.fixture
def provider(
    rest_transport: FakeRestTransport,
    websocket_transport: FakeWebSocketTransport,
    credentials: UpstoxCredentials,
) -> UpstoxProvider:
    return UpstoxProvider(
        rest_transport=rest_transport,
        websocket_transport=websocket_transport,
        credentials=credentials,
        token_endpoint="/token",
        websocket_url="wss://example.test/feed",
    )


@pytest.fixture
def connected_provider(provider: UpstoxProvider) -> UpstoxProvider:
    provider.authenticate("auth-code-1")
    provider.connect()
    return provider


@pytest.fixture
def sink() -> InMemoryDiagnosticsSink:
    return InMemoryDiagnosticsSink()


@pytest.fixture
def provider_with_sink(
    rest_transport: FakeRestTransport,
    websocket_transport: FakeWebSocketTransport,
    credentials: UpstoxCredentials,
    sink: InMemoryDiagnosticsSink,
) -> UpstoxProvider:
    return UpstoxProvider(
        rest_transport=rest_transport,
        websocket_transport=websocket_transport,
        credentials=credentials,
        token_endpoint="/token",
        websocket_url="wss://example.test/feed",
        diagnostics_sink=sink,
    )


@pytest.fixture
def connected_provider_with_sink(provider_with_sink: UpstoxProvider) -> UpstoxProvider:
    provider_with_sink.authenticate("auth-code-1")
    provider_with_sink.connect()
    return provider_with_sink

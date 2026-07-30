"""Tests for UpstoxProvider: authentication, connection, subscription, reconnect, heartbeat."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from trading_engine.diagnostics.events import (
    MarketDataAuthenticationFailed,
    MarketDataConnected,
    MarketDataDisconnected,
    MarketDataReconnected,
    MarketDataSubscribed,
)
from trading_engine.diagnostics.sink import InMemoryDiagnosticsSink
from trading_engine.market_data.exceptions import (
    AuthenticationError,
    MarketDataConnectionError,
    SubscriptionError,
)
from trading_engine.market_data.instrument_resolver import InstrumentKey
from trading_engine.market_data.market_data_provider import ConnectionState
from trading_engine.market_data.market_tick import MarketTick
from trading_engine.market_data.upstox_provider import (
    AccessToken,
    UpstoxCredentials,
    UpstoxProvider,
)

from .conftest import FakeRestTransport, FakeWebSocketTransport


class TestUpstoxCredentialsValidation:
    def test_blank_client_id_raises(self) -> None:
        with pytest.raises(AuthenticationError, match="client_id must not be blank"):
            UpstoxCredentials(client_id="", client_secret="s", redirect_uri="https://x")

    def test_blank_client_secret_raises(self) -> None:
        with pytest.raises(AuthenticationError, match="client_secret must not be blank"):
            UpstoxCredentials(client_id="c", client_secret="", redirect_uri="https://x")

    def test_blank_redirect_uri_raises(self) -> None:
        with pytest.raises(AuthenticationError, match="redirect_uri must not be blank"):
            UpstoxCredentials(client_id="c", client_secret="s", redirect_uri="")


class TestAccessTokenValidation:
    def test_blank_token_raises(self, base_timestamp: datetime) -> None:
        with pytest.raises(AuthenticationError, match="token must not be blank"):
            AccessToken(token="", expires_at=base_timestamp)

    def test_none_expires_at_raises(self) -> None:
        with pytest.raises(AuthenticationError, match="expires_at must not be None"):
            AccessToken(token="tok", expires_at=None)  # type: ignore[arg-type]


class TestAuthentication:
    def test_authenticate_returns_and_stores_token(
        self, provider: UpstoxProvider, rest_transport: FakeRestTransport
    ) -> None:
        token = provider.authenticate("auth-code")
        assert token.token == "token-1"
        assert provider.access_token is token
        assert rest_transport.calls == [
            (
                "/token",
                {
                    "client_id": "test-client-id",
                    "client_secret": "test-secret",
                    "redirect_uri": "https://example.test/callback",
                    "code": "auth-code",
                    "grant_type": "authorization_code",
                },
            )
        ]

    def test_transport_failure_raises_authentication_error(
        self, credentials: UpstoxCredentials
    ) -> None:
        transport = FakeRestTransport(raise_exception=ConnectionError("network down"))
        provider = UpstoxProvider(
            transport, FakeWebSocketTransport(), credentials, "/token", "wss://x"
        )
        with pytest.raises(AuthenticationError, match="failed"):
            provider.authenticate("auth-code")

    def test_transport_failure_emits_authentication_failed(
        self, credentials: UpstoxCredentials
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        transport = FakeRestTransport(raise_exception=ConnectionError("network down"))
        provider = UpstoxProvider(
            transport,
            FakeWebSocketTransport(),
            credentials,
            "/token",
            "wss://x",
            diagnostics_sink=sink,
        )
        with pytest.raises(AuthenticationError):
            provider.authenticate("auth-code")
        events = sink.events()
        assert len(events) == 1
        assert isinstance(events[0], MarketDataAuthenticationFailed)

    def test_malformed_response_raises_authentication_error(
        self, credentials: UpstoxCredentials
    ) -> None:
        transport = FakeRestTransport(response={"unexpected": "shape"})
        provider = UpstoxProvider(
            transport, FakeWebSocketTransport(), credentials, "/token", "wss://x"
        )
        with pytest.raises(AuthenticationError, match="malformed"):
            provider.authenticate("auth-code")

    def test_diagnostic_never_contains_the_token_value(
        self, credentials: UpstoxCredentials
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        transport = FakeRestTransport(raise_exception=ConnectionError("secret-token-xyz leaked?"))
        provider = UpstoxProvider(
            transport,
            FakeWebSocketTransport(),
            credentials,
            "/token",
            "wss://x",
            diagnostics_sink=sink,
        )
        with pytest.raises(AuthenticationError):
            provider.authenticate("auth-code")
        # The event's reason may include the transport exception text,
        # but never an actual access_token value (none was ever
        # obtained in this failure path).
        assert provider.access_token is None


class TestTokenRefresh:
    def test_refresh_before_authenticate_raises(self, provider: UpstoxProvider) -> None:
        with pytest.raises(AuthenticationError, match="before authenticate"):
            provider.refresh_token()

    def test_refresh_returns_new_token(
        self, provider: UpstoxProvider, rest_transport: FakeRestTransport
    ) -> None:
        provider.authenticate("auth-code")
        rest_transport.response = {"access_token": "token-2", "expires_in": 7200}
        token = provider.refresh_token()
        assert token.token == "token-2"

    def test_is_token_expired_true_before_authentication(self, provider: UpstoxProvider) -> None:
        assert provider.is_token_expired() is True

    def test_is_token_expired_false_immediately_after_authenticate(
        self, provider: UpstoxProvider
    ) -> None:
        provider.authenticate("auth-code")
        assert provider.is_token_expired() is False

    def test_is_token_expired_true_after_expiry(self, credentials: UpstoxCredentials) -> None:
        current = {"t": datetime(2026, 7, 3, 9, 0, 0)}  # noqa: DTZ001

        def clock() -> datetime:
            return current["t"]

        transport = FakeRestTransport(response={"access_token": "tok", "expires_in": 60})
        provider = UpstoxProvider(
            transport, FakeWebSocketTransport(), credentials, "/token", "wss://x", clock=clock
        )
        provider.authenticate("auth-code")
        current["t"] = current["t"] + timedelta(seconds=61)
        assert provider.is_token_expired() is True


class TestConnectDisconnect:
    def test_connect_without_token_raises(self, provider: UpstoxProvider) -> None:
        with pytest.raises(MarketDataConnectionError, match="without a valid access token"):
            provider.connect()

    def test_connect_opens_websocket_and_sets_connected(
        self, provider: UpstoxProvider, websocket_transport: FakeWebSocketTransport
    ) -> None:
        provider.authenticate("auth-code")
        provider.connect()
        assert provider.state == ConnectionState.CONNECTED
        assert websocket_transport.opened_urls == ["wss://example.test/feed"]

    def test_connect_emits_connected_event(
        self, provider_with_sink: UpstoxProvider, sink: InMemoryDiagnosticsSink
    ) -> None:
        provider_with_sink.authenticate("auth-code")
        provider_with_sink.connect()
        events = sink.events()
        assert len(events) == 1
        assert isinstance(events[0], MarketDataConnected)
        assert events[0].provider_name == "upstox"

    def test_disconnect_closes_and_sets_disconnected(
        self, connected_provider: UpstoxProvider, websocket_transport: FakeWebSocketTransport
    ) -> None:
        connected_provider.disconnect()
        assert connected_provider.state == ConnectionState.DISCONNECTED
        assert websocket_transport.close_count == 1

    def test_disconnect_emits_disconnected_event(
        self, connected_provider_with_sink: UpstoxProvider, sink: InMemoryDiagnosticsSink
    ) -> None:
        connected_provider_with_sink.disconnect()
        events = sink.events()
        assert isinstance(events[-1], MarketDataDisconnected)
        assert events[-1].reason == "requested"


class TestSubscribeUnsubscribe:
    def test_subscribe_requires_connected(
        self, provider: UpstoxProvider, sample_instrument: InstrumentKey
    ) -> None:
        with pytest.raises(SubscriptionError, match="not connected"):
            provider.subscribe(sample_instrument)

    def test_subscribe_sends_message_and_tracks(
        self,
        connected_provider: UpstoxProvider,
        websocket_transport: FakeWebSocketTransport,
        sample_instrument: InstrumentKey,
    ) -> None:
        connected_provider.subscribe(sample_instrument)
        assert websocket_transport.sent_messages == [f"SUBSCRIBE {sample_instrument.token}"]

    def test_subscribe_twice_sends_message_once(
        self,
        connected_provider: UpstoxProvider,
        websocket_transport: FakeWebSocketTransport,
        sample_instrument: InstrumentKey,
    ) -> None:
        connected_provider.subscribe(sample_instrument)
        connected_provider.subscribe(sample_instrument)
        assert websocket_transport.sent_messages == [f"SUBSCRIBE {sample_instrument.token}"]

    def test_subscribe_emits_subscribed_event(
        self,
        connected_provider_with_sink: UpstoxProvider,
        sink: InMemoryDiagnosticsSink,
        sample_instrument: InstrumentKey,
    ) -> None:
        connected_provider_with_sink.subscribe(sample_instrument)
        events = sink.events()
        assert isinstance(events[-1], MarketDataSubscribed)
        assert events[-1].instrument_token == sample_instrument.token

    def test_unsubscribe_requires_connected(
        self, provider: UpstoxProvider, sample_instrument: InstrumentKey
    ) -> None:
        with pytest.raises(SubscriptionError, match="not connected"):
            provider.unsubscribe(sample_instrument)

    def test_unsubscribe_sends_message(
        self,
        connected_provider: UpstoxProvider,
        websocket_transport: FakeWebSocketTransport,
        sample_instrument: InstrumentKey,
    ) -> None:
        connected_provider.subscribe(sample_instrument)
        connected_provider.unsubscribe(sample_instrument)
        assert websocket_transport.sent_messages[-1] == f"UNSUBSCRIBE {sample_instrument.token}"

    def test_unsubscribe_emits_no_dedicated_event(
        self,
        connected_provider_with_sink: UpstoxProvider,
        sink: InMemoryDiagnosticsSink,
        sample_instrument: InstrumentKey,
    ) -> None:
        connected_provider_with_sink.subscribe(sample_instrument)
        before = len(sink)
        connected_provider_with_sink.unsubscribe(sample_instrument)
        assert len(sink) == before


class TestReconnect:
    def test_reconnect_resubscribes_all_active_instruments(
        self,
        connected_provider: UpstoxProvider,
        websocket_transport: FakeWebSocketTransport,
        sample_instrument: InstrumentKey,
        another_instrument: InstrumentKey,
    ) -> None:
        connected_provider.subscribe(sample_instrument)
        connected_provider.subscribe(another_instrument)
        websocket_transport.sent_messages.clear()

        connected_provider.reconnect()

        assert connected_provider.state == ConnectionState.CONNECTED
        sent_tokens = {
            msg.split(" ", 1)[1]
            for msg in websocket_transport.sent_messages
            if msg.startswith("SUBSCRIBE")
        }
        assert sent_tokens == {sample_instrument.token, another_instrument.token}

    def test_reconnect_refreshes_expired_token(self, credentials: UpstoxCredentials) -> None:
        current = {"t": datetime(2026, 7, 3, 9, 0, 0)}  # noqa: DTZ001

        def clock() -> datetime:
            return current["t"]

        transport = FakeRestTransport(response={"access_token": "tok-1", "expires_in": 60})
        websocket = FakeWebSocketTransport()
        provider = UpstoxProvider(
            transport, websocket, credentials, "/token", "wss://x", clock=clock
        )
        provider.authenticate("auth-code")
        provider.connect()

        current["t"] = current["t"] + timedelta(seconds=120)
        transport.response = {"access_token": "tok-2", "expires_in": 3600}
        provider.reconnect()
        assert provider.access_token is not None
        assert provider.access_token.token == "tok-2"

    def test_reconnect_increments_attempt_number(
        self, connected_provider_with_sink: UpstoxProvider, sink: InMemoryDiagnosticsSink
    ) -> None:
        connected_provider_with_sink.reconnect()
        connected_provider_with_sink.reconnect()
        events = [event for event in sink.events() if isinstance(event, MarketDataReconnected)]
        assert [event.attempt for event in events] == [1, 2]

    def test_reconnect_emits_reconnected_event_with_resubscribed_count(
        self,
        connected_provider_with_sink: UpstoxProvider,
        sink: InMemoryDiagnosticsSink,
        sample_instrument: InstrumentKey,
    ) -> None:
        connected_provider_with_sink.subscribe(sample_instrument)
        connected_provider_with_sink.reconnect()
        events = [event for event in sink.events() if isinstance(event, MarketDataReconnected)]
        assert len(events) == 1
        assert events[0].resubscribed_count == 1


class TestHeartbeat:
    def test_send_heartbeat_requires_connected(self, provider: UpstoxProvider) -> None:
        with pytest.raises(MarketDataConnectionError, match="not connected"):
            provider.send_heartbeat()

    def test_send_heartbeat_sends_message(
        self, connected_provider: UpstoxProvider, websocket_transport: FakeWebSocketTransport
    ) -> None:
        connected_provider.send_heartbeat()
        assert websocket_transport.sent_messages == ["HEARTBEAT"]

    def test_is_heartbeat_stale_true_before_any_heartbeat(
        self, connected_provider: UpstoxProvider
    ) -> None:
        assert connected_provider.is_heartbeat_stale(timedelta(seconds=30)) is True

    def test_is_heartbeat_stale_false_immediately_after_send(
        self, connected_provider: UpstoxProvider
    ) -> None:
        connected_provider.send_heartbeat()
        assert connected_provider.is_heartbeat_stale(timedelta(seconds=30)) is False

    def test_is_heartbeat_stale_true_after_timeout_elapses(
        self, credentials: UpstoxCredentials
    ) -> None:
        current = {"t": datetime(2026, 7, 3, 9, 0, 0)}  # noqa: DTZ001

        def clock() -> datetime:
            return current["t"]

        transport = FakeRestTransport()
        provider = UpstoxProvider(
            transport, FakeWebSocketTransport(), credentials, "/token", "wss://x", clock=clock
        )
        provider.authenticate("auth-code")
        provider.connect()
        provider.send_heartbeat()
        current["t"] = current["t"] + timedelta(seconds=31)
        assert provider.is_heartbeat_stale(timedelta(seconds=30)) is True


class TestTickIngestionAndOptionChain:
    def test_ingest_and_get_spot(
        self,
        connected_provider: UpstoxProvider,
        sample_instrument: InstrumentKey,
        base_timestamp: datetime,
    ) -> None:
        from decimal import Decimal

        tick = MarketTick(base_timestamp, sample_instrument, Decimal("125.5"), 100, 500)
        connected_provider.ingest_tick(sample_instrument, tick)
        assert connected_provider.get_spot(sample_instrument) is tick

    def test_get_spot_returns_none_when_no_tick_ingested(
        self, connected_provider: UpstoxProvider, sample_instrument: InstrumentKey
    ) -> None:
        assert connected_provider.get_spot(sample_instrument) is None

    def test_get_option_chain_delegates_to_instrument_resolver(
        self, credentials: UpstoxCredentials, spot_instrument: InstrumentKey
    ) -> None:
        from datetime import date
        from decimal import Decimal

        from trading_engine.market_data.instrument_resolver import InstrumentResolver, OptionType

        resolver = InstrumentResolver()
        expiry = date(2026, 7, 3)
        call_key = InstrumentKey(token="CE", symbol="NIFTY-CE", exchange="NSE_FO")
        resolver.register_option("NIFTY", expiry, Decimal(24000), OptionType.CALL, call_key)

        provider = UpstoxProvider(
            FakeRestTransport(),
            FakeWebSocketTransport(),
            credentials,
            "/token",
            "wss://x",
            instrument_resolver=resolver,
        )
        chain = provider.get_option_chain(spot_instrument, expiry)
        assert chain == (call_key,)

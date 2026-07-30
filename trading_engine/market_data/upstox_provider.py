"""UpstoxProvider: a MarketDataProvider implementation over injected REST/WebSocket transports.

Traceability notes
-------------------
See ``trading_engine/market_data/__init__.py``'s "Traceability
limitation" note: no document in this repository evidences Upstox's
actual endpoint paths, authentication payload shape, or message
format. This class therefore never hardcodes a literal Upstox URL,
field name, or wire-message format - every endpoint path and the
transport itself are supplied by the caller via
:class:`RestTransport`/:class:`WebSocketTransport` (dependency
injection, mirroring this codebase's existing pattern - e.g.
:attr:`trading_engine.rules.context.RuleExecutionContext.clock`).

What IS implemented here - authentication/token-refresh scheduling,
connection state management, subscription tracking, reconnect with
resubscribe, and heartbeat timing - is general REST+WebSocket
broker-integration *mechanism*, equally applicable to any such broker,
not a trading-strategy rule. No calculation, threshold, or trading
decision of any kind appears anywhere in this module.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Protocol, runtime_checkable

from trading_engine.diagnostics.events import (
    MarketDataAuthenticationFailed,
    MarketDataConnected,
    MarketDataDisconnected,
    MarketDataReconnected,
    MarketDataSubscribed,
)
from trading_engine.diagnostics.sink import DiagnosticsSink, NullDiagnosticsSink
from trading_engine.market_data.exceptions import (
    AuthenticationError,
    MarketDataConnectionError,
    SubscriptionError,
)
from trading_engine.market_data.instrument_resolver import InstrumentKey, InstrumentResolver
from trading_engine.market_data.market_data_provider import ConnectionState
from trading_engine.market_data.market_tick import MarketTick
from trading_engine.market_data.subscription_manager import SubscriptionManager


@runtime_checkable
class RestTransport(Protocol):
    """The structural contract for whatever performs this provider's
    REST calls (authentication, token refresh). Injected - never
    implemented in this package, since no real HTTP client is a
    dependency of ``trading_engine`` (see
    ``docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md``'s "zero
    third-party dependencies" placement)."""

    def post(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """POST ``payload`` to ``path`` and return the parsed response body."""
        ...


@runtime_checkable
class WebSocketTransport(Protocol):
    """The structural contract for whatever performs this provider's
    WebSocket I/O. Injected, for the same reason as :class:`RestTransport`."""

    def open(self, url: str) -> None:
        """Open a connection to ``url``."""
        ...

    def close(self) -> None:
        """Close the connection."""
        ...

    def send(self, message: str) -> None:
        """Send ``message`` over the open connection."""
        ...

    def is_open(self) -> bool:
        """Whether the connection is currently open."""
        ...


@dataclass(frozen=True)
class UpstoxCredentials:
    """Caller-supplied OAuth2-style credentials.

    Attributes:
        client_id: The application's client identifier.
        client_secret: The application's client secret.
        redirect_uri: The registered redirect URI.
    """

    client_id: str
    client_secret: str
    redirect_uri: str

    def __post_init__(self) -> None:
        if not self.client_id or not self.client_id.strip():
            raise AuthenticationError("UpstoxCredentials.client_id must not be blank.")
        if not self.client_secret or not self.client_secret.strip():
            raise AuthenticationError("UpstoxCredentials.client_secret must not be blank.")
        if not self.redirect_uri or not self.redirect_uri.strip():
            raise AuthenticationError("UpstoxCredentials.redirect_uri must not be blank.")


@dataclass(frozen=True)
class AccessToken:
    """A parsed authentication token.

    Attributes:
        token: The access token string. Never logged or included in
            any diagnostic event.
        expires_at: When this token stops being valid.
    """

    token: str
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.token or not self.token.strip():
            raise AuthenticationError("AccessToken.token must not be blank.")
        if self.expires_at is None:
            raise AuthenticationError("AccessToken.expires_at must not be None.")


class UpstoxProvider:
    """A :class:`~trading_engine.market_data.market_data_provider.MarketDataProvider`
    implementation coordinating authentication, connection lifecycle,
    subscriptions, reconnection, and heartbeats over injected transports.

    Rule References
        None - infrastructure only.
    """

    def __init__(
        self,
        rest_transport: RestTransport,
        websocket_transport: WebSocketTransport,
        credentials: UpstoxCredentials,
        token_endpoint: str,
        websocket_url: str,
        subscription_manager: SubscriptionManager | None = None,
        instrument_resolver: InstrumentResolver | None = None,
        diagnostics_sink: DiagnosticsSink | None = None,
        clock: Callable[[], datetime] = datetime.now,
        provider_name: str = "upstox",
    ) -> None:
        self._rest = rest_transport
        self._websocket = websocket_transport
        self._credentials = credentials
        self._token_endpoint = token_endpoint
        self._websocket_url = websocket_url
        self._subscriptions = (
            subscription_manager if subscription_manager is not None else SubscriptionManager()
        )
        self._instrument_resolver = (
            instrument_resolver if instrument_resolver is not None else InstrumentResolver()
        )
        self._sink: DiagnosticsSink = (
            diagnostics_sink if diagnostics_sink is not None else NullDiagnosticsSink()
        )
        self._clock = clock
        self._provider_name = provider_name

        self._state = ConnectionState.DISCONNECTED
        self._access_token: AccessToken | None = None
        self._reconnect_attempts = 0
        self._last_heartbeat_at: datetime | None = None
        self._ticks: dict[InstrumentKey, MarketTick] = {}

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def access_token(self) -> AccessToken | None:
        """The currently held :class:`AccessToken`, or ``None`` if
        never authenticated."""
        return self._access_token

    def authenticate(self, authorization_code: str) -> AccessToken:
        """Exchange ``authorization_code`` for an :class:`AccessToken`
        via the injected :class:`RestTransport`.

        Raises:
            AuthenticationError: if the transport call fails or the
                response cannot be parsed. Emits
                :class:`~trading_engine.diagnostics.events.MarketDataAuthenticationFailed`
                first.
        """
        payload = {
            "client_id": self._credentials.client_id,
            "client_secret": self._credentials.client_secret,
            "redirect_uri": self._credentials.redirect_uri,
            "code": authorization_code,
            "grant_type": "authorization_code",
        }
        return self._exchange_for_token(payload, "authentication")

    def refresh_token(self) -> AccessToken:
        """Refresh the current :class:`AccessToken` via the injected
        :class:`RestTransport`.

        Raises:
            AuthenticationError: if no token has ever been obtained,
                the transport call fails, or the response cannot be
                parsed.
        """
        if self._access_token is None:
            raise AuthenticationError("Cannot refresh a token before authenticate() succeeds.")

        payload = {
            "client_id": self._credentials.client_id,
            "client_secret": self._credentials.client_secret,
            "refresh_token": self._access_token.token,
            "grant_type": "refresh_token",
        }
        return self._exchange_for_token(payload, "token refresh")

    def _exchange_for_token(self, payload: Mapping[str, Any], operation: str) -> AccessToken:
        try:
            response = self._rest.post(self._token_endpoint, payload)
        except Exception as exc:
            self._emit_auth_failed(f"{operation} transport call failed: {exc}")
            raise AuthenticationError(f"{operation} failed: {exc}") from exc

        try:
            token_value = str(response["access_token"])
            expires_in_seconds = int(response["expires_in"])
        except (KeyError, TypeError, ValueError) as exc:
            self._emit_auth_failed(f"{operation} response was malformed: {exc}")
            raise AuthenticationError(f"{operation} response was malformed: {exc}") from exc

        token = AccessToken(
            token=token_value,
            expires_at=self._clock() + timedelta(seconds=expires_in_seconds),
        )
        self._access_token = token
        return token

    def _emit_auth_failed(self, reason: str) -> None:
        self._sink.emit(
            MarketDataAuthenticationFailed(
                event_id=uuid.uuid4(),
                occurred_at=self._clock(),
                provider_name=self._provider_name,
                reason=reason,
            )
        )

    def is_token_expired(self) -> bool:
        """Whether the held :class:`AccessToken` is missing or has
        expired according to the injected clock."""
        if self._access_token is None:
            return True
        return self._clock() >= self._access_token.expires_at

    def connect(self) -> None:
        """Open the WebSocket connection.

        Raises:
            MarketDataConnectionError: if no valid, unexpired access
                token is held - call :meth:`authenticate`/
                :meth:`refresh_token` first.
        """
        if self.is_token_expired():
            raise MarketDataConnectionError(
                "Cannot connect without a valid access token; "
                "call authenticate() or refresh_token() first."
            )

        self._state = ConnectionState.CONNECTING
        self._websocket.open(self._websocket_url)
        self._state = ConnectionState.CONNECTED
        self._reconnect_attempts = 0
        self._sink.emit(
            MarketDataConnected(
                event_id=uuid.uuid4(),
                occurred_at=self._clock(),
                provider_name=self._provider_name,
            )
        )

    def disconnect(self) -> None:
        """Deliberately close the WebSocket connection."""
        self._websocket.close()
        self._state = ConnectionState.DISCONNECTED
        self._sink.emit(
            MarketDataDisconnected(
                event_id=uuid.uuid4(),
                occurred_at=self._clock(),
                provider_name=self._provider_name,
                reason="requested",
            )
        )

    def subscribe(self, instrument: InstrumentKey) -> None:
        """Subscribe to ``instrument``.

        Raises:
            SubscriptionError: if not currently connected.
        """
        if self._state != ConnectionState.CONNECTED:
            raise SubscriptionError("Cannot subscribe while not connected.")

        newly_added = self._subscriptions.subscribe(instrument)
        if newly_added:
            self._websocket.send(self._build_subscribe_message(instrument))
            self._sink.emit(
                MarketDataSubscribed(
                    event_id=uuid.uuid4(),
                    occurred_at=self._clock(),
                    provider_name=self._provider_name,
                    instrument_token=instrument.token,
                )
            )

    def unsubscribe(self, instrument: InstrumentKey) -> None:
        """Unsubscribe from ``instrument``.

        No dedicated diagnostic event exists for this action -
        Milestone I1's diagnostics list names Connected, Disconnected,
        Subscribed, Reconnect, and Authentication Failed only,
        mirroring Milestone B1's precedent of leaving an analogous
        action (``ReplayController.stop()``) without a dedicated event
        when the spec's event list does not name one.

        Raises:
            SubscriptionError: if not currently connected.
        """
        if self._state != ConnectionState.CONNECTED:
            raise SubscriptionError("Cannot unsubscribe while not connected.")

        removed = self._subscriptions.unsubscribe(instrument)
        if removed:
            self._websocket.send(self._build_unsubscribe_message(instrument))

    def reconnect(self) -> None:
        """Reconnect after an unplanned disconnection: refresh the
        token if expired, reopen the WebSocket, and resubscribe every
        previously-active instrument.
        """
        self._state = ConnectionState.RECONNECTING
        self._reconnect_attempts += 1

        if self._websocket.is_open():
            self._websocket.close()

        if self.is_token_expired():
            self.refresh_token()

        self._websocket.open(self._websocket_url)

        resubscribed = 0
        for instrument in self._subscriptions.active_subscriptions():
            self._websocket.send(self._build_subscribe_message(instrument))
            resubscribed += 1

        self._state = ConnectionState.CONNECTED
        self._sink.emit(
            MarketDataReconnected(
                event_id=uuid.uuid4(),
                occurred_at=self._clock(),
                provider_name=self._provider_name,
                attempt=self._reconnect_attempts,
                resubscribed_count=resubscribed,
            )
        )

    def send_heartbeat(self) -> None:
        """Send one heartbeat message and record the send time.

        Raises:
            MarketDataConnectionError: if not currently connected.
        """
        if self._state != ConnectionState.CONNECTED:
            raise MarketDataConnectionError("Cannot send a heartbeat while not connected.")

        self._websocket.send(self._build_heartbeat_message())
        self._last_heartbeat_at = self._clock()

    def is_heartbeat_stale(self, timeout: timedelta) -> bool:
        """Whether more than ``timeout`` has elapsed since the last
        successful :meth:`send_heartbeat` call (or no heartbeat has
        ever been sent)."""
        if self._last_heartbeat_at is None:
            return True
        return (self._clock() - self._last_heartbeat_at) > timeout

    def ingest_tick(self, instrument: InstrumentKey, tick: MarketTick) -> None:
        """Record ``tick`` as the latest observation for ``instrument``.

        The caller (not this class) is responsible for parsing a raw
        transport message into a :class:`MarketTick` - no wire format
        is evidenced, so no parser is implemented here.
        """
        self._ticks[instrument] = tick

    def get_spot(self, instrument: InstrumentKey) -> MarketTick | None:
        return self._ticks.get(instrument)

    def get_option_chain(
        self, underlying: InstrumentKey, expiry: date
    ) -> tuple[InstrumentKey, ...]:
        """Return every registered option instrument for
        ``underlying``'s symbol and ``expiry``.

        Delegates entirely to the injected
        :class:`~trading_engine.market_data.instrument_resolver.InstrumentResolver`
        - this provider holds no chain-discovery logic of its own; the
        resolver must have been populated by the caller in advance
        (see ``trading_engine/market_data/__init__.py``'s traceability
        note on why no real data source is implemented here).
        """
        return self._instrument_resolver.option_chain(underlying.symbol, expiry)

    def _build_subscribe_message(self, instrument: InstrumentKey) -> str:
        return f"SUBSCRIBE {instrument.token}"

    def _build_unsubscribe_message(self, instrument: InstrumentKey) -> str:
        return f"UNSUBSCRIBE {instrument.token}"

    def _build_heartbeat_message(self) -> str:
        return "HEARTBEAT"

# Market Data Implementation Report

Milestone I1. `trading_engine/market_data/` — infrastructure connecting
the trading engine to a live broker. No trading strategy, no Weekly
Future calculation, no Winner/Entry/Exit logic anywhere in this
package.

## Files

```
trading_engine/market_data/
    __init__.py
    exceptions.py               -- MarketDataError, MarketDataConnectionError,
                                    AuthenticationError, SubscriptionError,
                                    InstrumentResolutionError, MarketDataValidationError
    market_data_provider.py      -- ConnectionState, MarketDataProvider (Protocol)
    market_tick.py                 -- MarketTick
    instrument_resolver.py          -- OptionType, InstrumentKey, InstrumentResolver
    subscription_manager.py          -- SubscriptionManager
    upstox_provider.py                -- RestTransport, WebSocketTransport (Protocols),
                                          UpstoxCredentials, AccessToken, UpstoxProvider
```

5 new diagnostic events added additively to the existing, reused
`trading_engine/diagnostics/events.py`: `MarketDataConnected`,
`MarketDataDisconnected`, `MarketDataSubscribed`,
`MarketDataReconnected`, `MarketDataAuthenticationFailed`.

## The central design decision: no hardcoded Upstox specifics

`research/specification/REALTIME_TRADING_SPECIFICATION.md` Section 13
confirmed zero broker-API mentions anywhere in this repository — no
endpoint path, authentication payload shape, or WebSocket message
format is evidenced. `UpstoxProvider` therefore never hardcodes a
literal Upstox URL, field name, or wire format. Every endpoint
(`token_endpoint`, `websocket_url`) and the transport itself
(`RestTransport`, `WebSocketTransport` — injected Protocols) are
supplied by the caller. This is the same dependency-injection pattern
already established throughout this codebase
(`RuleExecutionContext.clock`, `RuleRegistry.execution_order`'s
`dependency_resolver`).

What this class DOES implement is general REST+WebSocket
broker-integration *mechanism* — authentication/token-refresh
scheduling, connection state management, subscription tracking,
reconnect-with-resubscribe, heartbeat timing — equally applicable to
any such broker. This is ordinary software engineering knowledge, not
a trading-strategy rule, and is therefore not subject to this
repository's evidence-first discipline the way Weekly Future/Strike
mathematics are. No calculation, threshold, or trading decision of any
kind appears anywhere in this package.

## Responsibilities

- **`MarketDataProvider`** (Protocol) — `connect`, `disconnect`,
  `subscribe`, `unsubscribe`, `get_spot`, `get_option_chain`, plus a
  `state` property. `ConnectionState` (DISCONNECTED/CONNECTING/
  CONNECTED/RECONNECTING) is the shared lifecycle enum.
- **`UpstoxProvider`** — authentication (`authenticate`, exchanging an
  authorization code for an `AccessToken`), token refresh
  (`refresh_token`, `is_token_expired`), connection management
  (`connect`/`disconnect`), subscription lifecycle (`subscribe`/
  `unsubscribe`, delegating tracking to `SubscriptionManager`),
  reconnect (`reconnect` — refreshes an expired token if needed,
  reopens the WebSocket, resubscribes every previously-active
  instrument), and heartbeat (`send_heartbeat`/`is_heartbeat_stale`).
- **`InstrumentResolver`** — a pure lookup table (spot symbol → 
  `InstrumentKey`; underlying+expiry+strike+`OptionType` →
  `InstrumentKey`; plus `option_chain(underlying, expiry)`). Never
  fetches or invents instrument-master data itself — populated
  entirely by the caller, since no real instrument-master format is
  evidenced anywhere.
- **`MarketTick`** — one immutable, structurally-validated live price
  observation (timestamp, instrument, LTP, volume, OI, bid, ask).
  Distinct from `trading_engine.replay.history_loader.Candle`, which
  represents an already-closed historical OHLC bar, not a live tick.
- **`SubscriptionManager`** — idempotent subscribe/unsubscribe
  tracking, `active_subscriptions()` for reconnect-time resubscription.

## Deliberate gaps, stated plainly

- **`unsubscribe()` emits no dedicated diagnostic event.** Milestone
  I1's diagnostics list names Connected, Disconnected, Subscribed,
  Reconnect, and Authentication Failed only — mirroring Milestone
  B1's precedent (`ReplayController.stop()` likewise emits nothing
  beyond what its own milestone's event list named).
- **`get_option_chain()` never fetches real chain data.** It delegates
  entirely to the injected `InstrumentResolver`, which itself is a
  pure lookup table with no data source of its own — see above.
- **No real message-parsing logic exists.** `UpstoxProvider.ingest_tick()`
  accepts an already-constructed `MarketTick` — parsing a raw
  WebSocket message into one is left to the caller, since no wire
  format is evidenced.
- **No token-refresh scheduling/background thread exists.** `is_token_expired()`
  and `refresh_token()` are provided as callable checks; nothing calls
  them automatically. This codebase has no concurrent execution
  anywhere yet (see `trading_engine.diagnostics.sink.InMemoryDiagnosticsSink`'s
  own docstring on this point) — a scheduler is a future extension
  point, not built here.

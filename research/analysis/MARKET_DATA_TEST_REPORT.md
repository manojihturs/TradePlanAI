# Market Data Test Report

Milestone I1. Companion to `research/analysis/MARKET_DATA_IMPLEMENTATION.md`.

## Coverage

| Package | Statements | Missed | Coverage |
|---|---:|---:|---:|
| `trading_engine/market_data/` | 281 | 0 | **100%** |
| Whole `trading_engine` suite (all 7 packages) | 1,648 | 0 | **100%** |

746 tests passing overall (86 new for `trading_engine/market_data/`,
5 new for the market-data diagnostic events), zero regressions in the
655 pre-existing tests.

## Test files

```
trading_engine/tests/market_data/
    __init__.py
    conftest.py                     -- FakeRestTransport, FakeWebSocketTransport
                                        (network-free test doubles), fixtures
    test_instrument_resolver.py      -- InstrumentKey validation, spot/option
                                          resolution, option_chain filtering
    test_market_tick.py               -- structural validation (price, volume,
                                          OI, bid/ask ordering)
    test_subscription_manager.py       -- idempotent subscribe/unsubscribe,
                                           active_subscriptions, clear
    test_market_data_provider.py        -- ConnectionState, Protocol conformance
    test_upstox_provider.py              -- authentication, token refresh,
                                             connect/disconnect, subscribe/
                                             unsubscribe, reconnect, heartbeat,
                                             tick ingestion, option chain delegation

trading_engine/tests/diagnostics/
    test_market_data_events.py       -- the 5 new event dataclasses' validation
```

No real network call happens anywhere in this test suite —
`FakeRestTransport`/`FakeWebSocketTransport` are the only
implementations of `RestTransport`/`WebSocketTransport` used, exactly
matching how `trading_engine/replay/` tests use fakes for
`RuleExecutionContext.clock`.

## Test scenarios (mapped to Milestone I1's Task 7 checklist)

| Required scenario | Covered by |
|---|---|
| Connection lifecycle | `TestConnectDisconnect` — connect requires a valid token, opens the transport, sets CONNECTED, emits `MarketDataConnected`; disconnect closes the transport, sets DISCONNECTED, emits `MarketDataDisconnected` |
| Subscription lifecycle | `TestSubscribeUnsubscribe` — subscribe/unsubscribe both require CONNECTED; subscribing twice sends only one wire message (idempotent); `unsubscribe()` deliberately emits no event (see implementation report) |
| Instrument lookup | `TestResolveSpot`, `TestResolveOption`, `TestOptionChain` in `test_instrument_resolver.py` — register-then-resolve round trips, unregistered lookups raise, CALL/PUT are distinct, chain filtering excludes other underlyings/expiries |
| Tick parsing | `TestTickIngestionAndOptionChain` — `ingest_tick`/`get_spot` round trip; `get_spot` returns `None` before any tick is ingested (per module docstring, no real parser exists — this tests the ingestion/storage contract, not a wire-format parser) |
| Reconnect | `TestReconnect` — resubscribes every active instrument, refreshes an expired token first, increments the attempt counter across repeated calls, emits `MarketDataReconnected` with an accurate `resubscribed_count` |
| Diagnostics | Distributed across `TestConnectDisconnect`/`TestSubscribeUnsubscribe`/`TestReconnect`/`TestAuthentication` (provider-level emission) plus `test_market_data_events.py` (event-level validation) |

Additional coverage beyond the checklist: authentication failure paths
(transport exception, malformed response) both raise
`AuthenticationError` and emit `MarketDataAuthenticationFailed`;
`is_token_expired()`/`is_heartbeat_stale()` are tested against an
injected, fully controllable clock rather than real wall-clock time
(matching this codebase's established clock-injection pattern), so
expiry/staleness transitions are deterministic, not timing-dependent.

## Known limitations

1. **No real Upstox endpoint/message-format knowledge is encoded
   anywhere.** Every test constructs `UpstoxProvider` with fake,
   test-local endpoint strings (`"/token"`, `"wss://example.test/feed"`)
   — this suite validates the provider's *mechanism* (state machine,
   scheduling, retry/resubscribe logic), not compatibility with
   Upstox's actual, real API, which remains entirely unevidenced in
   this repository (see `MARKET_DATA_IMPLEMENTATION.md`).
2. **No token-refresh scheduling is tested because none exists** —
   `is_token_expired()` is a callable check, not an automatic timer;
   see the implementation report's "Deliberate gaps" section.
3. **No concurrency/thread-safety testing** — this codebase has no
   concurrent execution anywhere yet (consistent with
   `InMemoryDiagnosticsSink`'s own "not thread-safe" docstring note);
   `UpstoxProvider` was not designed or tested for concurrent access.
4. **Tick parsing from a raw wire message is untested because it does
   not exist** — `ingest_tick()` accepts an already-valid `MarketTick`;
   no test exercises turning a raw string/bytes WebSocket payload into
   one, since no such format is evidenced.

## Quality Gate Report

| Gate | Result |
|---|---|
| `pytest` | **746 passed** (91 new, 0 regressions) |
| Coverage | **100%** — 1,648/1,648 statements, 0 missed |
| `mypy --strict` | Clean — 58 source files |
| `ruff check` | Clean |
| `black --check` | Clean |

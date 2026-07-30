"""Market Data Infrastructure: connecting the engine to a live broker feed.

Traceability notes
-------------------
Milestone I1 (Phase I1). Reuses, without modifying, the existing
:mod:`trading_engine.diagnostics` package (extended additively with 5
new market-data event types, mirroring Milestone B1's precedent of
extending diagnostics for a new subsystem rather than building a
parallel mechanism).

This package contains **no trading strategy, no Weekly Future
calculation, no Winner logic, no Entry logic, and no Exit logic** -
see ``research/analysis/REALTIME_TRADING_SPECIFICATION.md`` Section 13
("Upstox Integration") and
``research/implementation/IMPLEMENTATION_BLUEPRINT.md`` for why this
package exists (connectivity plumbing only) and what it deliberately
does not attempt.

Traceability limitation, stated plainly
    No document in this repository evidences Upstox's actual REST/WebSocket
    endpoint paths, authentication payload shape, or market-data message
    format - `research/analysis/REALTIME_TRADING_SPECIFICATION.md`
    Section 13 confirmed zero broker-API mentions anywhere in the
    repository. :class:`~trading_engine.market_data.upstox_provider.UpstoxProvider`
    therefore never hardcodes a literal Upstox URL or payload field
    name; every endpoint and the wire transport itself are supplied by
    the caller (dependency injection via
    :class:`~trading_engine.market_data.upstox_provider.RestTransport`/
    :class:`~trading_engine.market_data.upstox_provider.WebSocketTransport`).
    What this package DOES implement - authentication/token-refresh
    scheduling, connection state management, subscription tracking,
    reconnect-with-resubscribe, and heartbeat timing - is general
    broker-integration *mechanism* (equally applicable to any REST+WebSocket
    broker), not a trading-strategy rule, and is not subject to this
    repository's evidence-first discipline for trading mathematics.
"""

from __future__ import annotations

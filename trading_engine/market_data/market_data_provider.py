"""MarketDataProvider: the structural contract every broker connection satisfies.

Traceability notes
-------------------
Per ``research/implementation/INTERFACE_MAP.md``'s ``IMarketDataProvider``.
A ``typing.Protocol``, matching this codebase's existing contract style
(:class:`trading_engine.rules.protocols.Rule`,
:class:`trading_engine.calculators.protocols.Calculator`,
:class:`trading_engine.diagnostics.sink.DiagnosticsSink`) - any object
with the right methods qualifies, without a forced inheritance
relationship.
"""

from __future__ import annotations

from datetime import date
from enum import Enum, auto
from typing import Protocol, runtime_checkable

from trading_engine.market_data.instrument_resolver import InstrumentKey
from trading_engine.market_data.market_tick import MarketTick


class ConnectionState(Enum):
    """The lifecycle states a :class:`MarketDataProvider` can be in."""

    #: Never connected, or a deliberate :meth:`MarketDataProvider.disconnect` completed.
    DISCONNECTED = auto()

    #: A connection attempt is in progress.
    CONNECTING = auto()

    #: Connected and able to subscribe/receive ticks.
    CONNECTED = auto()

    #: A reconnect attempt is in progress after an unplanned disconnection.
    RECONNECTING = auto()


@runtime_checkable
class MarketDataProvider(Protocol):
    """The structural contract every market data provider implementation satisfies.

    Rule References
        None - infrastructure only. Never reads a tick's price/volume
        for any trading-meaningful purpose.
    """

    @property
    def state(self) -> ConnectionState:
        """This provider's current :class:`ConnectionState`."""
        ...

    def connect(self) -> None:
        """Establish the connection."""
        ...

    def disconnect(self) -> None:
        """Deliberately end the connection."""
        ...

    def subscribe(self, instrument: InstrumentKey) -> None:
        """Begin receiving ticks for ``instrument``."""
        ...

    def unsubscribe(self, instrument: InstrumentKey) -> None:
        """Stop receiving ticks for ``instrument``."""
        ...

    def get_spot(self, instrument: InstrumentKey) -> MarketTick | None:
        """Return the most recently observed tick for ``instrument``,
        or ``None`` if none has been observed yet."""
        ...

    def get_option_chain(
        self, underlying: InstrumentKey, expiry: date
    ) -> tuple[InstrumentKey, ...]:
        """Return every known option instrument for one
        underlying/expiry pair."""
        ...

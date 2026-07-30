"""Exceptions raised by the market data infrastructure.

Traceability notes
-------------------
Mirrors the per-package exception style already established by
``trading_engine.domain.DomainValidationError``,
``trading_engine.rules.exceptions.RuleFrameworkError``,
``trading_engine.engine.exceptions.EngineError``,
``trading_engine.calculators.exceptions.CalculatorFrameworkError``,
``trading_engine.diagnostics.exceptions.DiagnosticsError``, and
``trading_engine.replay.exceptions.ReplayError`` - one base exception
per package.
"""

from __future__ import annotations


class MarketDataError(Exception):
    """Base class for every exception raised by
    :mod:`trading_engine.market_data`.

    Never raised directly - always one of the subclasses below.
    """


class MarketDataConnectionError(MarketDataError):
    """Raised when a connection-related operation cannot proceed - a
    connect/reconnect attempt failing, or an operation (subscribe,
    heartbeat) requiring a connected state that has not been reached.
    """


class AuthenticationError(MarketDataError):
    """Raised when authentication or token refresh fails, or a
    provider's authentication response cannot be parsed.

    Never carries the raw credentials or token value in its message -
    see :class:`~trading_engine.diagnostics.events.MarketDataAuthenticationFailed`'s
    own docstring for the same constraint on the diagnostic event.
    """


class SubscriptionError(MarketDataError):
    """Raised when a subscribe/unsubscribe operation cannot proceed."""


class InstrumentResolutionError(MarketDataError):
    """Raised when an instrument cannot be resolved - no matching
    entry exists for the requested spot symbol, or option
    underlying/expiry/strike/type combination.
    """


class MarketDataValidationError(MarketDataError):
    """Raised when a market-data value object (:class:`~trading_engine.market_data.instrument_resolver.InstrumentKey`,
    :class:`~trading_engine.market_data.market_tick.MarketTick`) is
    constructed with structurally invalid data - a blank identifier,
    a non-positive price, a negative volume/open-interest.

    Distinct from :class:`InstrumentResolutionError`: that means "this
    otherwise-valid lookup key has no registered instrument"; this
    means "the data itself is malformed."
    """

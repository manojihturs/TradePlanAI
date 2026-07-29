"""Exception hierarchy for the strategy engine.

Traceability
------------
Mirrors the per-package exception convention already established in
this repository's ``trading_engine`` codebase (one base exception per
concern, e.g. ``trading_engine.market_data.exceptions.MarketDataError``)
- an engineering convention, not a business rule.
"""

from __future__ import annotations


class StrategyEngineError(Exception):
    """Base class for every exception raised by this package.

    Never raised directly - always one of the subclasses below.
    """


class ValidationError(StrategyEngineError):
    """Raised when a model/value object is constructed with
    structurally invalid data (e.g. a non-positive strike price)."""


class EventBusError(StrategyEngineError):
    """Raised when the event bus is used incorrectly - e.g.
    unsubscribing a handler that was never subscribed."""


class TradeManagerError(StrategyEngineError):
    """Raised when the trade manager is used incorrectly - e.g.
    closing a trade that is not active."""


class StateMachineError(StrategyEngineError):
    """Raised when an illegal state transition is attempted."""


class ReplayError(StrategyEngineError):
    """Raised when the replay engine cannot process its historical
    data source."""


class UnresolvedBusinessRuleError(StrategyEngineError):
    """Raised by any interface/abstract method whose underlying
    business rule is still MISSING INFORMATION per
    ``research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md``
    Section 20 (e.g. the Weekly Future formula, the ATM strike
    selection rule, the Stop Loss rule). Deliberately distinct from
    ``NotImplementedError`` so callers can catch "this rule is a
    known, tracked gap" specifically, rather than a generic
    not-yet-implemented condition.
    """

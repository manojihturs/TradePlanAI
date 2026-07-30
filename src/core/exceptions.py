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


class AmbiguousWinnerError(StrategyEngineError):
    """Raised if a Winner evaluation ever finds both CE and PE
    genuinely touching their own reference levels on the same candle.

    Specification Rule 3 (v1.1) states this scenario "does not
    occur" and explicitly instructs against inventing tie-break
    logic. Rather than guess a winner, this exception makes the
    supposedly-impossible case fail loudly instead of silently -
    matching ``research/architecture/TEST_STRATEGY.md`` Section 2.7's
    own "asserted absent" testing convention for this exact case.
    """


class HistoricalDataError(StrategyEngineError):
    """Raised when a historical market-data source cannot be read, or
    fails validation (missing/duplicate timestamps, invalid OHLC,
    invalid volume, schema errors) - see
    ``data.historical_data_validation.HistoricalDataValidation`` for
    the itemized report; ``data.historical_data_provider.HistoricalDataProvider.validate``
    returns that report directly without raising, for a caller that
    wants to inspect issues rather than catch this exception.
    """


class ApplicationError(StrategyEngineError):
    """Raised by ``application.replay_application.ReplayApplication``
    when a composition-root step fails (dataset load, replay
    execution, report writing) - always wraps the original exception
    via ``raise ... from exc`` so the underlying cause is preserved;
    this class only adds a stage-labeled message, it does not attempt
    any recovery.
    """


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

"""Exceptions raised by the replay engine.

Traceability notes
-------------------
Mirrors the per-package exception style already established by
``trading_engine.domain.DomainValidationError``,
``trading_engine.rules.exceptions.RuleFrameworkError``,
``trading_engine.engine.exceptions.EngineError``,
``trading_engine.calculators.exceptions.CalculatorFrameworkError``, and
``trading_engine.diagnostics.exceptions.DiagnosticsError`` - one base
exception per package.
"""

from __future__ import annotations


class ReplayError(Exception):
    """Base class for every exception raised by
    :mod:`trading_engine.replay`.

    Never raised directly - always one of the subclasses below.
    """


class HistoryLoadError(ReplayError):
    """Raised when historical OHLC data cannot be loaded or fails
    structural validation - a missing/malformed column, an
    unparsable value, a structurally invalid candle (e.g. High less
    than Low), or a duplicate timestamp.

    Never represents a trading-mathematics judgment about the data
    (e.g. this exception has no opinion on whether a gap between
    candles is a legitimate market closure or a data error) - only
    structural loadability.
    """


class ReplayStateError(ReplayError):
    """Raised when a replay operation is invalid for the session's
    current state - e.g. seeking out of bounds, stepping past either
    end of the candle sequence, resuming a session that is not
    paused, or pausing a session that is not running.
    """

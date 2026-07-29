"""Exceptions raised by the diagnostics package.

Traceability notes
-------------------
Mirrors the per-package exception style already established by
``trading_engine.domain.DomainValidationError``,
``trading_engine.rules.exceptions.RuleFrameworkError``,
``trading_engine.engine.exceptions.EngineError``, and
``trading_engine.calculators.exceptions.CalculatorFrameworkError`` -
one base exception per package, raised only for structural validation
failures within that package's own value objects.
"""

from __future__ import annotations


class DiagnosticsError(ValueError):
    """Raised when a diagnostic event is constructed with structurally
    invalid data (e.g. a blank Rule ID, a ``None`` timestamp).

    Never represents a trading-rule outcome or a Rule Framework
    failure - only a malformed diagnostic event.
    """

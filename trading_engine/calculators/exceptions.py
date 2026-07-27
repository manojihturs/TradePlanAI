"""Exceptions raised by the Calculator Framework.

Traceability notes
-------------------
Mirrors the exception shape of :mod:`trading_engine.rules.exceptions`
at a different layer: these represent misuse of the Calculator
Framework itself (a duplicate registration, a malformed calculator, a
malformed context/result) - never a trading-mathematics failure, since
no calculator in this milestone performs any mathematics.
"""

from __future__ import annotations


class CalculatorFrameworkError(Exception):
    """Base class for every exception raised by
    :mod:`trading_engine.calculators`.

    Never raised directly - always one of the subclasses below.
    """


class DuplicateCalculatorError(CalculatorFrameworkError):
    """Raised when :class:`~trading_engine.calculators.registry.CalculatorRegistry`
    is asked to register a Calculator ID that is already registered.

    A second registration under the same ID is always a caller error -
    there is no "re-register to update" operation in this framework,
    matching :class:`trading_engine.rules.exceptions.DuplicateRuleError`'s
    treatment of Rule IDs.
    """


class CalculatorRegistrationError(CalculatorFrameworkError):
    """Raised when a calculator cannot be registered because it fails
    structural validation - e.g. it does not satisfy the
    :class:`~trading_engine.calculators.protocols.Calculator` protocol,
    or its ``id()``/``name()``/``description()`` is blank.

    Also raised by :meth:`~trading_engine.calculators.registry.CalculatorRegistry.get`
    when no calculator is registered under the requested Calculator ID.
    """


class CalculationError(CalculatorFrameworkError):
    """Raised when a :class:`~trading_engine.calculators.context.CalculationContext`
    or :class:`~trading_engine.calculators.result.CalculationResult` is
    constructed with structurally invalid data.

    Does not represent a mathematical failure - no calculator in this
    milestone computes anything (each raises ``NotImplementedError``
    from :meth:`~trading_engine.calculators.protocols.Calculator.calculate`
    instead, per the Milestone 4.3A instruction).
    """

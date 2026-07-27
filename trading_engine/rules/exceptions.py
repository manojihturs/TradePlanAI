"""Exceptions raised by the Rule Framework.

Traceability notes
-------------------
These are framework-level errors, distinct from
:class:`trading_engine.domain.DomainValidationError`: a
``DomainValidationError`` means a domain value object's own structural
invariant failed (e.g. a Strike price <= 0); the exceptions here mean
the Rule Framework itself was used incorrectly (a duplicate
registration, a malformed rule, a malformed execution result) - no
trading-rule outcome is represented by any of these.
"""

from __future__ import annotations


class RuleFrameworkError(Exception):
    """Base class for every exception raised by :mod:`trading_engine.rules`.

    Never raised directly - always one of the subclasses below. Exists
    so callers can catch every Rule Framework failure with one
    ``except RuleFrameworkError`` without also swallowing unrelated
    Python exceptions.
    """


class DuplicateRuleError(RuleFrameworkError):
    """Raised when :class:`~trading_engine.rules.registry.RuleRegistry`
    is asked to register a Rule ID that is already registered.

    See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule
    Registry"): Rule IDs are permanent and unique once assigned in
    ``docs/RULE_INDEX.md``, so a second registration under the same ID
    is always a caller error, never a legitimate update - there is no
    "re-register to update" operation in this framework.
    """


class RuleRegistrationError(RuleFrameworkError):
    """Raised when a rule cannot be registered because it fails
    structural validation - e.g. it does not satisfy the
    :class:`~trading_engine.rules.protocols.Rule` protocol, or its
    ``id()`` is blank.

    Also raised by :meth:`~trading_engine.rules.registry.RuleRegistry.get`
    when no rule is registered under the requested Rule ID.
    """


class RuleExecutionError(RuleFrameworkError):
    """Raised when a :class:`~trading_engine.rules.context.RuleExecutionContext`
    or :class:`~trading_engine.rules.outcome.RuleExecutionResult` is
    constructed with structurally invalid data.

    Does not represent a trading-rule failure (that is expressed by
    :attr:`~trading_engine.rules.outcome.RuleOutcome.FAIL`, a normal,
    successfully-produced result) - only a framework-level defect, such
    as a missing required field.
    """

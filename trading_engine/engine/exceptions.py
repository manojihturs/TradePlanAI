"""Exceptions raised by the Strategy Engine Skeleton.

Traceability notes
-------------------
Distinct from :mod:`trading_engine.rules.exceptions`: those represent
misuse of the Rule Framework itself (a duplicate registration, a
malformed rule); the exceptions here represent misuse of the
*orchestration layer* built on top of it - an engine that was never
validly set up (:class:`EngineConfigurationError`), or a pipeline run
that could not complete for a reason outside any individual rule's
control (:class:`PipelineExecutionError`).
"""

from __future__ import annotations


class EngineError(Exception):
    """Base class for every exception raised by
    :mod:`trading_engine.engine`.

    Never raised directly - always one of the subclasses below.
    """


class EngineConfigurationError(EngineError):
    """Raised when a :class:`~trading_engine.engine.strategy_engine.StrategyEngine`
    or :class:`~trading_engine.engine.engine_configuration.EngineConfiguration`
    is constructed with structurally invalid or contradictory data -
    e.g. a ``None`` RuleRegistry, or a ``maximum_rule_count`` that is
    not a positive integer.

    Raised at *setup* time, before any rule is evaluated - never as a
    consequence of a rule's own outcome.
    """


class PipelineExecutionError(EngineError):
    """Raised when a pipeline run cannot complete or produce a valid
    result - e.g. a ``None`` RuleExecutionContext was supplied to
    :meth:`~trading_engine.engine.strategy_engine.StrategyEngine.run`,
    an unexpected (non-Rule-Framework) exception escaped a rule's
    ``evaluate()`` call, or an
    :class:`~trading_engine.engine.execution_report.ExecutionReport`/
    :class:`~trading_engine.engine.execution_summary.ExecutionSummary`
    was assembled with internally inconsistent data.

    Does not represent a rule's own :class:`~trading_engine.rules.outcome.RuleOutcome`
    (e.g. ``FAIL`` or ``UNKNOWN``) - those are normal, successfully
    produced results, not pipeline failures.
    """

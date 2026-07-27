"""ExecutionReport: the structured output of one StrategyEngine run.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Decision
Objects"): "a structured collection of Rule Results ... no synthesis
logic." ExecutionReport is the Milestone 4.3 orchestration-layer
counterpart of that idea, scoped to one engine run rather than one
Decision - it carries run bookkeeping (execution id, timing) plus the
raw collected results, warnings, and errors, and performs no synthesis
across them (no P&L, no signals - explicitly out of scope per the
Milestone 4.3 instruction).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from trading_engine.engine.exceptions import PipelineExecutionError
from trading_engine.rules.outcome import RuleExecutionResult


@dataclass(frozen=True)
class ExecutionReport:
    """The complete, structured record of one
    :class:`~trading_engine.engine.strategy_engine.StrategyEngine` run.

    Rule References
        None directly - a structural container referencing whichever
        rules were evaluated via :attr:`results`.

    Attributes:
        execution_id: Unique identifier for this run.
        start_time: When this run began.
        end_time: When this run ended. Must not precede ``start_time``.
        rules_executed: The Rule ID(s) actually evaluated during this
            run, in evaluation order (not necessarily every registered
            rule - see ``maximum_rule_count``/``dry_run`` in
            :class:`~trading_engine.engine.engine_configuration.EngineConfiguration`).
        results: The RuleExecutionResult(s) produced during this run.
        warnings: Non-fatal notices recorded during this run (e.g. a
            rule count limit was reached).
        errors: Fatal-but-recorded problems encountered during this
            run (e.g. a Rule Framework exception that stopped
            evaluation early).
    """

    execution_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    rules_executed: tuple[str, ...] = field(default_factory=tuple)
    results: tuple[RuleExecutionResult, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.execution_id is None:
            raise PipelineExecutionError("ExecutionReport.execution_id must not be None.")

        if self.start_time is None:
            raise PipelineExecutionError("ExecutionReport.start_time must not be None.")

        if self.end_time is None:
            raise PipelineExecutionError("ExecutionReport.end_time must not be None.")

        if self.end_time < self.start_time:
            raise PipelineExecutionError("ExecutionReport.end_time must not precede start_time.")

    @property
    def duration(self) -> timedelta:
        """The wall-clock duration of this run (``end_time - start_time``)."""
        return self.end_time - self.start_time

    # TODO (RULE_ENGINE_ARCHITECTURE): Whether/how an ExecutionReport
    # feeds a future Decision Object is unspecified - Decision Objects
    # (docs/architecture/RULE_ENGINE_ARCHITECTURE.md) and
    # ExecutionReport currently exist independently, at different
    # layers (domain vs. engine orchestration).

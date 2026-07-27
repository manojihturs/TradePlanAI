"""StrategyEngine: top-level orchestration entry point.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule
Evaluation Pipeline"). StrategyEngine is the Milestone 4.3
orchestration shell around that Pipeline: it accepts an already-built
:class:`~trading_engine.rules.registry.RuleRegistry` and
:class:`~trading_engine.rules.context.RuleExecutionContext`, delegates
iteration/evaluation/collection entirely to
:class:`~trading_engine.engine.execution_pipeline.ExecutionPipeline`,
and assembles the result into an
:class:`~trading_engine.engine.execution_report.ExecutionReport`.

Architecture Rule
    StrategyEngine may orchestrate. Rules may evaluate. Only future
    calculator modules may perform mathematics. This class never
    mixes those responsibilities.
"""

from __future__ import annotations

import uuid

from trading_engine.engine.engine_configuration import EngineConfiguration
from trading_engine.engine.exceptions import EngineConfigurationError, PipelineExecutionError
from trading_engine.engine.execution_pipeline import ExecutionPipeline
from trading_engine.engine.execution_report import ExecutionReport
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.registry import RuleRegistry


class StrategyEngine:
    """Coordinates a RuleRegistry and an ExecutionPipeline to produce
    an ExecutionReport for one RuleExecutionContext.

    Rule References
        None directly - a generic orchestrator over whichever rules
        the supplied RuleRegistry contains.

    Contains no business logic: no ``if strike`` / ``if trend`` / ``if
    reversal`` or other rule-specific branch exists anywhere in this
    class. It does not read Strike, TrendPoint, Opponent, Edge, or
    Reversal data directly - only the generic
    :class:`~trading_engine.rules.protocols.Rule` contract and the
    RuleExecutionContext wrapper.

    Attributes:
        registry: The RuleRegistry this engine orchestrates.
        configuration: The EngineConfiguration governing this engine's
            behaviour.
    """

    def __init__(
        self,
        registry: RuleRegistry,
        configuration: EngineConfiguration | None = None,
    ) -> None:
        if registry is None:
            raise EngineConfigurationError("StrategyEngine.registry must not be None.")

        self.registry = registry
        self.configuration = configuration if configuration is not None else EngineConfiguration()
        self._pipeline = ExecutionPipeline()

    def run(self, context: RuleExecutionContext) -> ExecutionReport:
        """Execute every registered rule (per
        :meth:`~trading_engine.rules.registry.RuleRegistry.execution_order`)
        against ``context`` and return the resulting ExecutionReport.

        Raises:
            PipelineExecutionError: if ``context`` is ``None``, or if
                the underlying ExecutionPipeline could not complete
                (see :meth:`~trading_engine.engine.execution_pipeline.ExecutionPipeline.run`).
        """
        if context is None:
            raise PipelineExecutionError("StrategyEngine.run(context) must not be None.")

        start_time = context.clock()
        outcome = self._pipeline.run(
            rules=self.registry.execution_order(),
            context=context,
            configuration=self.configuration,
        )
        end_time = context.clock()

        return ExecutionReport(
            execution_id=uuid.uuid4(),
            start_time=start_time,
            end_time=end_time,
            rules_executed=outcome.rules_executed,
            results=outcome.results,
            warnings=outcome.warnings,
            errors=outcome.errors,
        )

    # TODO (RULE_ENGINE_ARCHITECTURE): Applying "resulting Session
    # State updates" (Rule Evaluation Pipeline step 5) is unimplemented
    # - no rule in docs/RULE_INDEX.md defines what a Session State
    # update looks like yet. StrategyEngine.run() does not mutate or
    # return an updated SessionState.

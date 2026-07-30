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

from trading_engine.diagnostics.events import ExecutionSummaryLogged
from trading_engine.diagnostics.sink import (
    DiagnosticsSink,
    NullDiagnosticsSink,
    StandardLoggingDiagnosticsSink,
)
from trading_engine.engine.engine_configuration import EngineConfiguration
from trading_engine.engine.exceptions import EngineConfigurationError, PipelineExecutionError
from trading_engine.engine.execution_pipeline import ExecutionPipeline
from trading_engine.engine.execution_report import ExecutionReport
from trading_engine.engine.execution_summary import ExecutionSummary
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

        sink = self._resolve_diagnostics_sink()

        start_time = context.clock()
        outcome = self._pipeline.run(
            rules=self.registry.execution_order(diagnostics_sink=sink),
            context=context,
            configuration=self.configuration,
            diagnostics_sink=sink,
        )
        end_time = context.clock()

        report = ExecutionReport(
            execution_id=uuid.uuid4(),
            start_time=start_time,
            end_time=end_time,
            rules_executed=outcome.rules_executed,
            results=outcome.results,
            warnings=outcome.warnings,
            errors=outcome.errors,
        )

        summary = ExecutionSummary.from_report(report)
        sink.emit(
            ExecutionSummaryLogged(
                event_id=uuid.uuid4(),
                occurred_at=context.clock(),
                execution_id=report.execution_id,
                total_rules=summary.total_rules,
                pass_count=summary.pass_count,
                fail_count=summary.fail_count,
                unknown_count=summary.unknown_count,
                insufficient_evidence_count=summary.insufficient_evidence_count,
                not_applicable_count=summary.not_applicable_count,
                duration_seconds=summary.duration.total_seconds(),
            )
        )

        return report

    def _resolve_diagnostics_sink(self) -> DiagnosticsSink:
        """Resolve the sink this run should emit diagnostic events to.

        Returns
        :class:`~trading_engine.diagnostics.sink.NullDiagnosticsSink`
        whenever ``configuration.logging_enabled`` is ``False`` - the
        single place this guarantee is enforced for every event this
        class itself emits (:class:`~trading_engine.diagnostics.events.ExecutionSummaryLogged`).
        :meth:`~trading_engine.engine.execution_pipeline.ExecutionPipeline.run`
        and
        :meth:`~trading_engine.rules.registry.RuleRegistry.execution_order`
        each additionally enforce the same guarantee themselves for
        the events they emit, so the flag is respected even if this
        engine's own pipeline/registry are used independently of this
        method.
        """
        if not self.configuration.logging_enabled:
            return NullDiagnosticsSink()
        if self.configuration.diagnostics_sink is not None:
            return self.configuration.diagnostics_sink
        return StandardLoggingDiagnosticsSink()

    # TODO (RULE_ENGINE_ARCHITECTURE): Applying "resulting Session
    # State updates" (Rule Evaluation Pipeline step 5) is unimplemented
    # - no rule in docs/RULE_INDEX.md defines what a Session State
    # update looks like yet. StrategyEngine.run() does not mutate or
    # return an updated SessionState.

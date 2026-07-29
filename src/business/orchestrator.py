"""BusinessOrchestrator: builds and runs a BusinessPipeline.

Traceability
------------
A thin composition-root wrapper around
:class:`~business.business_pipeline.BusinessPipeline` - registering
stages and running them are kept as two separate steps (``register``
then ``run``) so a caller can build the same orchestrator once (e.g.
at session start) and execute it repeatedly (once per candle), rather
than re-registering stages on every run. No business rule is
referenced here; ``register`` accepts any object structurally
satisfying :class:`~business.business_pipeline.PipelineStage`.
"""

from __future__ import annotations

from business.business_pipeline import BusinessPipeline, PipelineStage
from business.business_result import BusinessResult
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError


class BusinessOrchestrator:
    """Registers business-engine adapters and executes them as one
    ordered pipeline.

    Constructor-injected :class:`~business.execution_context.ExecutionContext`
    only - no globals, no singletons.
    """

    def __init__(self, execution: ExecutionContext) -> None:
        if execution is None:
            raise ValidationError("BusinessOrchestrator.execution must not be None.")
        self._execution = execution
        self._stages: list[PipelineStage] = []

    def register(self, stage: PipelineStage) -> None:
        """Append ``stage`` to the end of the execution order.

        Registration order is execution order - matching
        ``BUSINESS_RULE_INTEGRATION_GUIDE.md``'s own recommended
        sequence (Weekly Future -> Strike Selection -> TP Engine ->
        Qualification Engine, with Stop Loss/Trailing Stop pluggable
        independently) - but this class does not enforce or know that
        sequence; the caller is responsible for registering stages in
        the order they should run.
        """
        if stage is None:
            raise ValidationError("BusinessOrchestrator.register(stage) must not be None.")
        self._stages.append(stage)

    def build_pipeline(self) -> BusinessPipeline:
        """Return a :class:`~business.business_pipeline.BusinessPipeline`
        over every stage registered so far, in registration order."""
        return BusinessPipeline(tuple(self._stages))

    def run(self, context: PipelineContext) -> BusinessResult:
        """Build a pipeline from the currently registered stages and
        execute it once against ``context``.

        Equivalent to ``self.build_pipeline().execute(context, self._execution)``
        - provided as the orchestrator's own top-level entry point so
        callers don't need to hold a separate
        :class:`~business.business_pipeline.BusinessPipeline`
        reference for a single run.
        """
        return self.build_pipeline().execute(context, self._execution)

"""BusinessPipeline: executes an ordered sequence of business stages.

Traceability
------------
This module coordinates - it does not implement - business rules. A
:class:`PipelineStage` is an *adapter* around one of the six blocked
interfaces (``interfaces.weekly_future_calculator.WeeklyFutureCalculator``,
``interfaces.strike_selector.StrikeSelector``,
``interfaces.tp_engine.TPEngine``,
``interfaces.qualification_engine.QualificationEngine``,
``interfaces.stop_loss_engine.StopLossEngine``,
``interfaces.trailing_stop_engine.TrailingStopEngine``) or an
already-built engine (``winner_engine.winner_engine.WinnerEngine``,
etc.) - this pipeline calls only :meth:`PipelineStage.is_ready` and
:meth:`PipelineStage.run`, and never inspects, branches on, or
constructs any business-domain value itself.

``core.exceptions.UnresolvedBusinessRuleError`` is treated as an
expected outcome (a stage whose business rule is not yet available),
not a fault: the pipeline stops cleanly, records why, and returns a
``BusinessResult`` with ``success=False`` and ``error=None``. Any
other exception a stage raises is treated as a genuine fault, wrapped
in :class:`~business.business_errors.StageExecutionError`, and also
stops the pipeline - the distinction between these two stop reasons is
readable from ``BusinessResult.error`` (``None`` for the former,
populated for the latter) and from the diagnostics trail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from business.business_errors import StageExecutionError
from business.business_result import BusinessResult
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.events import Event
from core.exceptions import StrategyEngineError, UnresolvedBusinessRuleError, ValidationError


@dataclass(frozen=True, slots=True)
class StageOutcome:
    """What a single :class:`PipelineStage` run produced.

    Attributes:
        context: The updated :class:`~business.pipeline_context.PipelineContext`.
        events: Domain events the stage itself constructed (e.g. a
            ``WeeklyFutureCalculatedEvent``), for the pipeline to
            forward to the injected event bus. The pipeline never
            constructs an event itself - only forwards what the stage
            (which owns the business rule) already built.
        warnings: Non-fatal notes from this stage's own run.
    """

    context: PipelineContext
    events: tuple[Event, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.context is None:
            raise ValidationError("StageOutcome.context must not be None.")


@runtime_checkable
class PipelineStage(Protocol):
    """The structural contract every business-engine adapter satisfies.

    A ``typing.Protocol``, matching this project's established
    preference for structural typing over inheritance (see
    ``core.events.Event``, ``core.protocols.EventBusProtocol``).
    """

    @property
    def name(self) -> str:
        """A short, stable identifier for this stage (e.g.
        ``"weekly_future"``), used in
        :class:`~business.business_result.BusinessResult`'s
        ``completed_stages``/``skipped_stages``/``diagnostics``."""
        ...  # pragma: no cover

    def is_ready(self, context: PipelineContext) -> bool:
        """Whether ``context`` already carries this stage's required
        prerequisite fields (e.g. a Strike Selection stage requires
        ``context.weekly_future`` to be populated). Must not raise -
        a stage that cannot determine readiness should return
        ``False``."""
        ...  # pragma: no cover

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Execute this stage's business engine and return the
        resulting :class:`StageOutcome`.

        Raises:
            core.exceptions.UnresolvedBusinessRuleError: if this
                stage's underlying business rule is not yet resolved
                - the expected outcome for every stage backed by one
                of the six still-blocked interfaces today.
        """
        ...  # pragma: no cover


class BusinessPipeline:
    """Executes a fixed, ordered sequence of :class:`PipelineStage`
    instances, threading a single :class:`~business.pipeline_context.PipelineContext`
    through them.

    Constructor-injected stage list only - no globals, no singletons,
    matching every other engine in this codebase.
    """

    def __init__(self, stages: tuple[PipelineStage, ...]) -> None:
        self._stages = stages

    @property
    def stages(self) -> tuple[PipelineStage, ...]:
        return self._stages

    def execute(self, context: PipelineContext, execution: ExecutionContext) -> BusinessResult:
        """Run every registered stage in order, stopping at the first
        one that is not ready, raises
        :class:`~core.exceptions.UnresolvedBusinessRuleError`, or
        raises any other :class:`~core.exceptions.StrategyEngineError`.

        Never raises itself - every stage-level exception is caught
        and reflected in the returned :class:`~business.business_result.BusinessResult`.
        """
        start = execution.clock()
        current = context
        completed: list[str] = []
        skipped: list[str] = []
        warnings: list[str] = []
        diagnostics: list[str] = []
        error: StageExecutionError | None = None
        success = True
        halted = False

        for stage in self._stages:
            if halted:
                skipped.append(stage.name)
                diagnostics.append(f"{stage.name}: skipped - pipeline already halted")
                continue

            if not stage.is_ready(current):
                skipped.append(stage.name)
                diagnostics.append(f"{stage.name}: skipped - prerequisites not met")
                success = False
                halted = True
                continue

            try:
                outcome = stage.run(current, execution)
            except UnresolvedBusinessRuleError as exc:
                skipped.append(stage.name)
                diagnostics.append(f"{stage.name}: UNRESOLVED - {exc}")
                success = False
                halted = True
                continue
            except StrategyEngineError as exc:
                skipped.append(stage.name)
                error = StageExecutionError(f"{stage.name} raised {type(exc).__name__}: {exc}")
                diagnostics.append(f"{stage.name}: FAILED - {type(exc).__name__}: {exc}")
                success = False
                halted = True
                continue

            current = outcome.context
            warnings.extend(outcome.warnings)
            completed.append(stage.name)
            diagnostics.append(f"{stage.name}: completed")

            if execution.event_bus is not None:
                for published_event in outcome.events:
                    execution.event_bus.publish(published_event)

        elapsed = execution.clock() - start
        return BusinessResult(
            success=success,
            context=current,
            completed_stages=tuple(completed),
            skipped_stages=tuple(skipped),
            warnings=tuple(warnings),
            execution_time=elapsed,
            diagnostics=tuple(diagnostics),
            error=error,
        )

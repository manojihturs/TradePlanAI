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

Logging (Sprint: "Logging", Delivery Mode): a genuine stage fault (not
an expected ``UnresolvedBusinessRuleError`` stop) is logged at
``ERROR`` via the standard library :mod:`logging` module before being
wrapped in ``StageExecutionError`` - observability only, this does not
change which exceptions are treated as faults vs. expected outcomes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from business.business_errors import StageExecutionError
from business.business_result import BusinessResult
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from business.stage_diagnostics import StageDiagnostic
from core.events import Event
from core.exceptions import StrategyEngineError, UnresolvedBusinessRuleError, ValidationError

logger = logging.getLogger(__name__)


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

        Every stage in :attr:`stages` - including one skipped because
        the pipeline already halted - gets exactly one
        :class:`~business.stage_diagnostics.StageDiagnostic` in the
        returned result's ``stage_diagnostics``, timed via
        ``execution.clock()`` (never ``datetime.now()``), so a caller
        can see where the run's time actually went without this
        pipeline recomputing or inventing any business value.
        """
        start = execution.clock()
        current = context
        completed: list[str] = []
        skipped: list[str] = []
        warnings: list[str] = []
        diagnostics: list[str] = []
        stage_diagnostics: list[StageDiagnostic] = []
        error: StageExecutionError | None = None
        success = True
        halted = False

        for stage in self._stages:
            stage_start = execution.clock()

            if halted:
                stage_diagnostics.append(
                    self._failed_diagnostic(
                        stage.name, stage_start, execution.clock(), "pipeline already halted"
                    )
                )
                skipped.append(stage.name)
                diagnostics.append(f"{stage.name}: skipped - pipeline already halted")
                continue

            if not stage.is_ready(current):
                stage_diagnostics.append(
                    self._failed_diagnostic(
                        stage.name, stage_start, execution.clock(), "prerequisites not met"
                    )
                )
                skipped.append(stage.name)
                diagnostics.append(f"{stage.name}: skipped - prerequisites not met")
                success = False
                halted = True
                continue

            try:
                outcome = stage.run(current, execution)
            except UnresolvedBusinessRuleError as exc:
                stage_diagnostics.append(
                    self._failed_diagnostic(
                        stage.name, stage_start, execution.clock(), f"UNRESOLVED - {exc}"
                    )
                )
                skipped.append(stage.name)
                diagnostics.append(f"{stage.name}: UNRESOLVED - {exc}")
                success = False
                halted = True
                continue
            except StrategyEngineError as exc:
                reason = f"FAILED - {type(exc).__name__}: {exc}"
                logger.error("Stage %s failed: %s", stage.name, exc)
                stage_diagnostics.append(
                    self._failed_diagnostic(stage.name, stage_start, execution.clock(), reason)
                )
                skipped.append(stage.name)
                error = StageExecutionError(f"{stage.name} raised {type(exc).__name__}: {exc}")
                diagnostics.append(f"{stage.name}: {reason}")
                success = False
                halted = True
                continue

            stage_end = execution.clock()
            stage_diagnostics.append(
                StageDiagnostic(
                    stage_name=stage.name,
                    start_time=stage_start,
                    end_time=stage_end,
                    duration=stage_end - stage_start,
                    success=True,
                )
            )
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
            stage_diagnostics=tuple(stage_diagnostics),
            error=error,
        )

    @staticmethod
    def _failed_diagnostic(
        stage_name: str,
        start_time: datetime,
        end_time: datetime,
        failure_reason: str,
    ) -> StageDiagnostic:
        """Build a ``success=False`` :class:`~business.stage_diagnostics.StageDiagnostic`
        - a tiny helper only to avoid repeating this construction at
        every skip/halt branch in :meth:`execute`."""
        return StageDiagnostic(
            stage_name=stage_name,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=False,
            failure_reason=failure_reason,
        )

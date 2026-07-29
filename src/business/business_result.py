"""BusinessResult: the outcome of a single BusinessPipeline execution.

Traceability
------------
Field set matches the instruction's own list (Success, Failure,
Warnings, Execution Time, Completed Stages, Skipped Stages,
Diagnostics) - "Failure" is represented as ``success is False`` plus
an optional ``error`` (present only for a genuine stage fault, absent
when the pipeline stopped gracefully on an
:class:`~core.exceptions.UnresolvedBusinessRuleError`, since that is
an expected outcome, not a fault - see ``business_pipeline.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from business.business_errors import BusinessOrchestrationError
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class BusinessResult:
    """The outcome of one :meth:`~business.business_pipeline.BusinessPipeline.execute`
    call.

    Attributes:
        success: ``True`` only if every registered stage ran to
            completion.
        context: The final :class:`~business.pipeline_context.PipelineContext`,
            as of wherever execution stopped.
        completed_stages: Names of stages that ran to completion, in
            order.
        skipped_stages: Names of stages that did not run - either
            because their prerequisites were unmet, they raised
            :class:`~core.exceptions.UnresolvedBusinessRuleError`, or
            they were never reached because an earlier stage stopped
            the pipeline.
        warnings: Non-fatal notes surfaced by stages themselves.
        execution_time: Wall-clock duration of the run, per the
            injected :data:`~core.protocols.Clock`.
        diagnostics: Pipeline-level trace, one entry per stage
            outcome (completed / skipped / unresolved / faulted).
        error: The wrapped fault, if the pipeline stopped due to a
            stage raising anything other than
            ``UnresolvedBusinessRuleError``. ``None`` on success and
            on a graceful UNRESOLVED stop.
    """

    success: bool
    context: PipelineContext
    completed_stages: tuple[str, ...] = field(default_factory=tuple)
    skipped_stages: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    execution_time: timedelta = timedelta()
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    error: BusinessOrchestrationError | None = None

    def __post_init__(self) -> None:
        if self.context is None:
            raise ValidationError("BusinessResult.context must not be None.")
        if self.execution_time is None:
            raise ValidationError("BusinessResult.execution_time must not be None.")
        if self.execution_time < timedelta():
            raise ValidationError("BusinessResult.execution_time must not be negative.")
        if self.success and self.error is not None:
            raise ValidationError("BusinessResult.error must be None when success is True.")

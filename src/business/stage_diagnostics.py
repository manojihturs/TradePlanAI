"""StageDiagnostic: one PipelineStage's own execution record.

Traceability
------------
Sprint: "Pipeline Diagnostics" (Compact Development Mode) -
observability only, no business logic. Kept in its own module (not
inside ``business_pipeline.py`` alongside ``StageOutcome``, and not
inside ``business_result.py``) because both of those modules need to
reference it - ``business_pipeline.BusinessPipeline.execute`` builds
it, ``business_result.BusinessResult`` carries it - and either
direction would otherwise be a circular import.

Every field is measured, not invented: ``start_time``/``end_time``
come from the same injected ``business.execution_context.ExecutionContext.clock``
every other timestamp in this package already uses (never
``datetime.now()`` directly), and ``duration`` is their difference.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class StageDiagnostic:
    """One :class:`~business.business_pipeline.PipelineStage`'s own
    execution record for a single :meth:`~business.business_pipeline.BusinessPipeline.execute`
    call.

    Attributes:
        stage_name: The stage's own ``PipelineStage.name``.
        start_time: When this stage began (its readiness check plus
            its own ``run``, if reached).
        end_time: When this stage finished - completed, skipped, or
            faulted.
        duration: ``end_time - start_time``.
        success: ``True`` only if the stage ran to completion.
        failure_reason: Why the stage did not complete - unmet
            prerequisites, an ``UnresolvedBusinessRuleError``, or a
            genuine fault's message. ``None`` when ``success`` is
            ``True``.
    """

    stage_name: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    success: bool
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.stage_name or not self.stage_name.strip():
            raise ValidationError("StageDiagnostic.stage_name must not be blank.")
        if self.start_time is None:
            raise ValidationError("StageDiagnostic.start_time must not be None.")
        if self.end_time is None:
            raise ValidationError("StageDiagnostic.end_time must not be None.")
        if self.end_time < self.start_time:
            raise ValidationError("StageDiagnostic.end_time must not be before start_time.")
        if self.success and self.failure_reason is not None:
            raise ValidationError(
                "StageDiagnostic.failure_reason must be None when success is True."
            )
        if not self.success and self.failure_reason is None:
            raise ValidationError(
                "StageDiagnostic.failure_reason must be set when success is False."
            )

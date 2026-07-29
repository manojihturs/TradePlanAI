"""Exceptions raised by the Business Orchestration Layer.

Traceability
------------
Mirrors this codebase's per-package exception convention
(``core.exceptions.StrategyEngineError`` as the root, one subclass per
concern - see ``core/exceptions.py``'s own traceability note). Nothing
here encodes a business rule; every exception concerns pipeline
mechanics only (stage ordering, prerequisite checks, unexpected stage
failures).
"""

from __future__ import annotations

from core.exceptions import StrategyEngineError


class BusinessOrchestrationError(StrategyEngineError):
    """Base class for every exception raised by :mod:`business`.

    Never raised directly - always one of the subclasses below.
    """


class StagePrerequisiteError(BusinessOrchestrationError):
    """Raised when a stage is asked to run without its required
    :class:`~business.pipeline_context.PipelineContext` fields
    present.

    ``BusinessPipeline`` itself never raises this - it checks
    :meth:`~business.business_pipeline.PipelineStage.is_ready` first
    and skips the stage instead (see ``business_pipeline.py``). This
    exception exists for a :class:`~business.business_pipeline.PipelineStage`
    adapter's own defensive use, if it is invoked directly outside the
    pipeline (e.g. in a unit test) without its prerequisites met.
    """


class StageExecutionError(BusinessOrchestrationError):
    """Raised (wrapping the original exception) when a registered
    stage fails with anything other than
    :class:`~core.exceptions.UnresolvedBusinessRuleError`.

    ``UnresolvedBusinessRuleError`` is treated as an expected,
    business-evidence-gap outcome (the pipeline stops gracefully and
    records it as such - see ``business_pipeline.py``). Every other
    exception is a genuine stage-execution fault and is wrapped in
    this type so :class:`~business.business_result.BusinessResult`
    always carries a single, uniform error type.
    """

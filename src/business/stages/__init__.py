"""PipelineStage adapters wrapping real business engines for BusinessOrchestrator.

Traceability
------------
Pure orchestration glue - each stage here reads
``business.pipeline_context.PipelineContext``, delegates to an
already-implemented business engine, and writes the result back into
context. No stage performs a calculation itself.
"""

from __future__ import annotations

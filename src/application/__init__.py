"""Application layer: wires historical replay into the Business Orchestration Layer.

Traceability
------------
Pure integration - no trading logic. Drives ``replay.replay_engine.ReplayEngine``
candle-by-candle into ``business.orchestrator.BusinessOrchestrator``, records
whatever events the registered ``business.business_pipeline.PipelineStage``
adapters produce, and reports the outcome. Deliberately does not
duplicate ``BusinessPipeline`` (stage execution/failure handling) or
``BusinessResult`` (per-run outcome) - see ``ReplayRunner``'s own
docstring for why.
"""

from __future__ import annotations

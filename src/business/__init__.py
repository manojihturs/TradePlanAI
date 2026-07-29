"""Business Orchestration Layer.

Traceability
------------
Coordinates business engines in sequence - it does not implement any
business rule itself. Built per the "Implement Business Orchestration
Layer" instruction: the six blocked business engines
(``WeeklyFutureCalculator``, ``StrikeSelector``, ``TPEngine``,
``QualificationEngine``, ``StopLossEngine``, ``TrailingStopEngine``,
see ``src/interfaces/``) are injected as :class:`~business.business_pipeline.PipelineStage`
adapters; this package only sequences their execution, propagates
context between them, and stops cleanly when a stage's prerequisites
are unmet or it raises :class:`~core.exceptions.UnresolvedBusinessRuleError`.
No trading calculation, formula, or threshold is defined anywhere in
this package.
"""

from __future__ import annotations

"""MultiTimeframeConfirmationStage: PipelineStage adapter for
MultiTimeframeUTBotConfirmation.

Traceability
------------
Product Owner (2026-08-02, chat): "try higher timeframe 15mins,
30mins and one hour then confirm the trend" - confirmed the 5-minute
UT Bot signal (``business.stages.ut_bot_trend_stage.UTBotTrendStage``)
should still be what triggers entries; 15m/30m/1h only confirm or
revoke it, they don't replace it. This stage must run AFTER
``UTBotTrendStage`` in the same orchestrator (reads whatever
``PipelineContext.trend`` that stage already set this candle) - if
the three higher timeframes don't all agree with each other AND with
that 5-minute trend, this stage clears ``PipelineContext.trend`` back
to ``None`` via ``PipelineContext.with_trend(None)``, which makes
``business.stages.qualification_stage.QualificationStage`` not-ready
for this candle (its own ``is_ready`` requires ``trend is not None``)
- entries are silently skipped, not forced or overridden.

Reads ``PipelineContext.underlying_index_candles`` (added 2026-08-02,
distinct from ``candles`` - see that field's own docstring for why).
"""

from __future__ import annotations

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from trend_engine.multi_timeframe_confirmation import MultiTimeframeUTBotConfirmation


class MultiTimeframeConfirmationStage:
    """Confirms (or revokes) whatever trend
    ``business.stages.ut_bot_trend_stage.UTBotTrendStage`` already set
    on ``PipelineContext.trend`` this candle, using
    ``MultiTimeframeUTBotConfirmation``.

    Constructor-injected confirmation engine only - no globals, no
    singletons. Stateful across calls by design - construct a fresh
    instance per trading session.
    """

    def __init__(self, confirmation: MultiTimeframeUTBotConfirmation) -> None:
        self._confirmation = confirmation

    @property
    def name(self) -> str:
        return "multi_timeframe_confirmation"

    def is_ready(self, context: PipelineContext) -> bool:
        """Ready once this candle's underlying index series is
        present - a no-op (not an unmet prerequisite) if
        ``context.trend`` is already unset, since there is nothing to
        confirm or revoke."""
        return len(context.underlying_index_candles) > 0

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Confirm or revoke ``context.trend`` via the injected
        ``MultiTimeframeUTBotConfirmation``."""
        _ = execution
        confirmed = self._confirmation.update(context.underlying_index_candles)

        if context.trend is None:
            return StageOutcome(context=context)
        if confirmed is None or confirmed is not context.trend:
            return StageOutcome(context=context.with_trend(None))
        return StageOutcome(context=context)

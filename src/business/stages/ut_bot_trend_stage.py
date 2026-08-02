"""UTBotTrendStage: PipelineStage adapter for UTBotEngine.

Traceability
------------
Product Owner decision (2026-08-02, chat): backtest both trend
approaches over the past week's real Upstox data before choosing.
``research/scratch_compare_trend_methods.py`` ran both against
27-31 July 2026 - ``trend_engine.open_interest_trend_engine.OpenInterestTrendEngine``
could not run at all (Upstox's historical-candle endpoint returned no
Open Interest for any option contract that week, despite documenting
support for it), while ``trend_engine.ut_bot_engine.UTBotEngine``
produced real Buy/Sell flips every session. Product Owner chose UT Bot
for the live paper-trading launch on that basis - OI-trend remains
implemented for later, live-only use if Upstox's live market-quote
feed is confirmed to return real OI (untested).

Maps ``UTBotEngine.current_position`` (BUY/SELL, persisting across
candles between flips - see that property's own docstring) onto
``core.enums.TrendDirection`` (BUY -> BULLISH, SELL -> BEARISH),
writing it to ``PipelineContext.trend`` via the same field
``business.stages.trend_stage.TrendStage``/
``business.stages.qualification_stage.QualificationStage`` already
use.

Reads ``PipelineContext.underlying_index_candles[-1]`` as this
candle's underlying index OHLC - a field distinct from ``candles``
(which ``business.stages.orb_stage.ORBStage`` uses for the anchor
strike's own CE stream instead), added 2026-08-02 specifically to
avoid the two data sources colliding on one field. The caller is
responsible for threading the index's own candle series into
``underlying_index_candles`` each candle.
"""

from __future__ import annotations

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.enums import TrendDirection
from models.market_snapshot import MarketSnapshot
from trend_engine.ut_bot_engine import UTBotEngine, UTBotSignal

_SIGNAL_TO_TREND = {
    UTBotSignal.BUY: TrendDirection.BULLISH,
    UTBotSignal.SELL: TrendDirection.BEARISH,
}


class UTBotTrendStage:
    """Runs ``UTBotEngine`` against this candle's underlying index
    OHLC, and updates ``PipelineContext.trend`` from the engine's
    persisted Buy/Sell position.

    Constructor-injected engine only - no globals, no singletons.
    Stateful across calls (running ATR/trailing stop/position) by
    design - construct a fresh instance per trading session.
    """

    def __init__(self, engine: UTBotEngine) -> None:
        self._engine = engine

    @property
    def name(self) -> str:
        return "ut_bot_trend"

    def is_ready(self, context: PipelineContext) -> bool:
        """Ready once this candle's underlying index candle has been
        threaded into ``PipelineContext.underlying_index_candles``
        (the caller's own responsibility - see module docstring)."""
        return len(context.underlying_index_candles) > 0

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Feed this candle's underlying index OHLC to ``UTBotEngine``
        and update ``PipelineContext.trend`` from its current
        position, if any flip has fired yet."""
        _ = execution
        index_candle: MarketSnapshot = context.underlying_index_candles[-1]
        self._engine.update(index_candle)

        position = self._engine.current_position
        if position is None:
            return StageOutcome(context=context)
        return StageOutcome(context=context.with_trend(_SIGNAL_TO_TREND[position]))

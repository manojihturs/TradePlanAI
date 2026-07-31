"""ExitStage: PipelineStage adapter for ExitEngine.

Traceability
------------
Backtest harness wiring (Specification Section 11, Target/Competitor
legs confirmed and implemented - see ``exit_engine.exit_engine.ExitEngine``).
Follows the same adapter pattern already established by
``business.stages.orb_stage.ORBStage`` - performs no calculation of
its own, only reads ``PipelineContext.chain_snapshot`` for the
currently-active position's Target/Competitor strikes, invokes the
already-implemented engine unchanged, and writes a closed position
back via ``PipelineContext.with_exited_position``.

No-op when no trade is active - a no-op, not a skip, since there is
nothing for this stage to evaluate; ``is_ready`` returns ``True``
regardless, and ``run`` simply returns ``context`` unchanged (checked
via the shared ``position_manager.position_manager.PositionManager``,
the same instance ``entry_engine.entry_engine.EntryEngine`` uses, so
open-trade state is consistent across both).

Stop Loss/Trailing Stop: the injected ``ExitEngine`` requires real
``StopLossEngine``/``TrailingStopEngine`` instances at construction -
per this harness's own scoping decision (see
``backtest.null_engines``), those are ``NeverTriggersStopLoss``/
``NeverTriggersTrailingStop`` stand-ins, so this stage - like
``ExitEngine`` itself - can only ever close a position via the
Target or Competitor legs.
"""

from __future__ import annotations

from decimal import Decimal

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.enums import TradeDirection
from core.exceptions import ValidationError
from exit_engine.exit_engine import ExitEngine
from models.market_snapshot import MarketSnapshot
from models.strike_chain_snapshot import StrikeChainSnapshot
from position_manager.position_manager import PositionManager


class ExitStage:
    """Runs ``ExitEngine`` against the currently-active position (if
    any), and stores a closed position in context if one resulted.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(self, exit_engine: ExitEngine, position_manager: PositionManager) -> None:
        self._exit_engine = exit_engine
        self._position_manager = position_manager

    @property
    def name(self) -> str:
        return "exit"

    def is_ready(self, context: PipelineContext) -> bool:
        """Always ready - a candle with no active position and no
        chain snapshot is a legitimate no-op, not an unmet
        prerequisite."""
        _ = context
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Invoke ``ExitEngine`` if a trade is active, and store the
        closed position, if any, back into context.

        Raises:
            core.exceptions.ValidationError: if a trade is active but
                its Target or Competitor strike is missing from
                ``context.chain_snapshot``.
        """
        position = self._position_manager.current_position()
        if position is None:
            return StageOutcome(context=context)

        target_side = position.entry_side
        competitor_side = (
            TradeDirection.PE if position.entry_side is TradeDirection.CE else TradeDirection.CE
        )
        target_snapshot = self._snapshot_for(
            context.chain_snapshot, position.target_level, target_side
        )
        competitor_snapshot = self._snapshot_for(
            context.chain_snapshot, position.competitor_monitor_strike, competitor_side
        )

        closed = self._exit_engine.evaluate(
            context.candle_timestamp, target_snapshot, competitor_snapshot
        )
        if closed is None:
            return StageOutcome(context=context)

        updated = context.with_exited_position(closed)
        return StageOutcome(context=updated)

    @staticmethod
    def _snapshot_for(
        chain_snapshot: tuple[StrikeChainSnapshot, ...], strike: Decimal, side: TradeDirection
    ) -> MarketSnapshot:
        for pair in chain_snapshot:
            if pair.strike == strike:
                return pair.ce if side is TradeDirection.CE else pair.pe
        raise ValidationError(
            f"No StrikeChainSnapshot found for strike {strike} in PipelineContext.chain_snapshot."
        )

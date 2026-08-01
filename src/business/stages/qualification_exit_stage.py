"""QualificationExitStage: PipelineStage adapter for
QualificationExitEngine.

Traceability
------------
Sprint 11. Follows the same adapter pattern already established by
``business.stages.exit_stage.ExitStage`` - performs no calculation of
its own, only reads ``PipelineContext.chain_snapshot`` for the active
position's own anchor strike, invokes the already-implemented engine
unchanged, and writes a closed position back via
``PipelineContext.with_qualification_exited_position``.

No-op when no trade is active, mirroring ``ExitStage``'s own
documented precedent exactly - ``is_ready`` returns ``True``
regardless, and ``run`` simply returns ``context`` unchanged.
"""

from __future__ import annotations

from decimal import Decimal

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.enums import AnchorRole, TradeDirection
from core.exceptions import ValidationError
from models.strike import StrikeSelection
from models.strike_chain_snapshot import StrikeChainSnapshot
from qualification_engine.qualification_exit_engine import QualificationExitEngine
from qualification_engine.qualification_position_manager import QualificationPositionManager


class QualificationExitStage:
    """Runs ``QualificationExitEngine`` against the currently-active
    qualified position (if any), and stores a closed position in
    context if one resulted.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(
        self,
        exit_engine: QualificationExitEngine,
        position_manager: QualificationPositionManager,
    ) -> None:
        self._exit_engine = exit_engine
        self._position_manager = position_manager

    @property
    def name(self) -> str:
        return "qualification_exit"

    def is_ready(self, context: PipelineContext) -> bool:
        """Always ready - a candle with no active qualified position
        is a legitimate no-op, not an unmet prerequisite."""
        _ = context
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Invoke ``QualificationExitEngine`` if a qualified trade is
        active, and store the closed position, if any, back into
        context.

        Raises:
            core.exceptions.ValidationError: if a trade is active but
                its anchor strike is missing from
                ``context.chain_snapshot`` or Strike Selection has not
                yet run.
        """
        position = self._position_manager.active_position()
        if position is None:
            return StageOutcome(context=context)
        if context.qualified_position is not None and (
            context.qualified_position.position_id == position.position_id
        ):
            # This position was opened by QualificationStage THIS SAME
            # candle. Its confirming crossing (opposite side touching
            # the confirm-column level) is numerically identical to
            # competitor_exit_level by construction - checking exit on
            # the same candle's data would always immediately close it
            # via Competitor Hit, which the confirmed evidence's own
            # trade logs contradict (many trades run 5-45 minutes
            # before resolving). Exit monitoring starts the candle
            # after entry, mirroring how the confirmed Rule 2 flow
            # never checks Target/Competitor against the same strike's
            # own entry-triggering candle either.
            return StageOutcome(context=context)
        if context.selected_strike is None:
            raise ValidationError(
                "QualificationExitStage requires PipelineContext.selected_strike "
                "to resolve the active position's anchor strike."
            )

        anchor_strike = self._anchor_strike_for(position.anchor_role, context.selected_strike)
        pair = self._find_chain_snapshot(context.chain_snapshot, anchor_strike)
        own_snapshot = pair.ce if position.side is TradeDirection.CE else pair.pe
        competitor_snapshot = pair.pe if position.side is TradeDirection.CE else pair.ce

        closed = self._exit_engine.evaluate(
            context.candle_timestamp, own_snapshot, competitor_snapshot
        )
        if closed is None:
            return StageOutcome(context=context)

        return StageOutcome(context=context.with_qualification_exited_position(closed))

    @staticmethod
    def _anchor_strike_for(anchor_role: AnchorRole, selected_strike: StrikeSelection) -> Decimal:
        return (
            selected_strike.top_strike
            if anchor_role is AnchorRole.TOP
            else selected_strike.bottom_strike
        )

    @staticmethod
    def _find_chain_snapshot(
        chain_snapshot: tuple[StrikeChainSnapshot, ...], strike: Decimal
    ) -> StrikeChainSnapshot:
        for pair in chain_snapshot:
            if pair.strike == strike:
                return pair
        raise ValidationError(
            f"No StrikeChainSnapshot found for anchor strike {strike} "
            "in PipelineContext.chain_snapshot."
        )

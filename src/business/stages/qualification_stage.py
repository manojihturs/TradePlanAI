"""QualificationStage: PipelineStage adapter for QualificationEngine.

Traceability
------------
Sprint 11 - pipeline wiring for the confirmed
``qualification_engine.qualification_engine.QualificationEngine``
mechanism (QUAL-007, resolved 2026-08-01). Follows the same adapter
pattern already established by ``business.stages.winner_stage.WinnerStage``
- performs no calculation of its own, only reads
``PipelineContext.chain_snapshot`` for the Top and Bottom anchors' own
CE/PE pairs, invokes the already-implemented engine unchanged, and
writes the result back via ``PipelineContext.with_qualified_position``.

Checks Top before Bottom on each candle - an engineering default for
the case where both anchors would independently qualify on the exact
same candle, which no evidence addresses either way (mirrors
``exit_engine.exit_engine.ExitEngine``'s own documented precedent for
an analogous unresolved-precedence gap). Only one position may be
open at a time (Rule 4/QUAL-009, already enforced by
``qualification_engine.qualification_position_manager.QualificationPositionManager.open``),
so this ordering only matters on the rare candle where both anchors
qualify simultaneously and no trade is yet active.

Trend: this stage requires ``PipelineContext.trend`` to already be
populated - see that field's own docstring. Not ready (a no-op, not
an error) when trend is absent, since computing trend automatically
remains UNRESOLVED evidence this package does not attempt to invent.
"""

from __future__ import annotations

from decimal import Decimal

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.enums import AnchorRole
from core.exceptions import ValidationError
from models.strike_chain_snapshot import StrikeChainSnapshot
from qualification_engine.qualification_engine import QualificationEngine
from qualification_engine.qualification_position_manager import QualificationPositionManager


class QualificationStage:
    """Runs ``QualificationEngine`` for the Top and Bottom anchors (in
    that order), and opens/stores a position if either qualifies.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(
        self,
        qualification_engine: QualificationEngine,
        position_manager: QualificationPositionManager,
    ) -> None:
        self._qualification_engine = qualification_engine
        self._position_manager = position_manager

    @property
    def name(self) -> str:
        return "qualification"

    def is_ready(self, context: PipelineContext) -> bool:
        """Ready once a reference ladder, this candle's chain
        snapshot, Strike Selection, and an externally-supplied trend
        are all present."""
        return (
            len(context.reference_data) > 0
            and len(context.chain_snapshot) > 0
            and context.selected_strike is not None
            and context.trend is not None
        )

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Invoke ``QualificationEngine`` for Top then Bottom, and
        store/open a position from whichever first qualifies.

        Raises:
            core.exceptions.ValidationError: if the Top or Bottom
                strike is not present in ``context.chain_snapshot``.
        """
        assert context.selected_strike is not None  # guaranteed by is_ready
        assert context.trend is not None  # guaranteed by is_ready

        for anchor_role, strike in (
            (AnchorRole.TOP, context.selected_strike.top_strike),
            (AnchorRole.BOTTOM, context.selected_strike.bottom_strike),
        ):
            pair = self._find_chain_snapshot(context.chain_snapshot, strike)
            signal = self._qualification_engine.evaluate(
                anchor_role,
                context.trend,
                context.reference_data,
                pair.ce,
                pair.pe,
                context.candle_timestamp,
            )
            if signal is None:
                continue
            position = self._position_manager.open(signal)
            if position is None:
                return StageOutcome(context=context)
            return StageOutcome(context=context.with_qualified_position(position))

        return StageOutcome(context=context)

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

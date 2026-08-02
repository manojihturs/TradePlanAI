"""QualificationStage: PipelineStage adapter for QualificationEngine.

Traceability
------------
Sprint 11 - pipeline wiring for the confirmed
``qualification_engine.qualification_engine.QualificationEngine``
mechanism (QUAL-007, resolved 2026-08-01). Follows the same adapter
pattern already established by ``business.stages.winner_stage.WinnerStage``
- performs no calculation of its own, only reads
``PipelineContext.chain_snapshot`` for one anchor's own CE/PE pair,
invokes the already-implemented engine unchanged, and writes the
result back via ``PipelineContext.with_qualified_position_top``/
``with_qualified_position_bottom``.

Scoped to a single ``anchor_role`` (2026-08-01 correction) - Top and
Bottom are confirmed to each hold their own independent active trade
simultaneously (Product Owner-confirmed: "Yes, one Top + one Bottom
max at a time"), evidenced by real overlapping trades in
``research/incoming/daily_data_2026-07-31.md`` (30-July: both a Top
and a Bottom trade ran concurrently from 10:40 and again from 13:10).
A single stage instance trying both anchors against one shared
position manager was a modelling error, not a business rule - it
silently starved Bottom of its own entries whenever Top happened to
qualify first. ``backtest.runner.BacktestRunner`` now registers two
instances of this stage, one per anchor, each with its own injected
``QualificationPositionManager``.

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
    """Runs ``QualificationEngine`` for a single anchor (Top or
    Bottom), and opens/stores a position if it qualifies.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(
        self,
        anchor_role: AnchorRole,
        qualification_engine: QualificationEngine,
        position_manager: QualificationPositionManager,
    ) -> None:
        self._anchor_role = anchor_role
        self._qualification_engine = qualification_engine
        self._position_manager = position_manager

    @property
    def name(self) -> str:
        return f"qualification_{self._anchor_role.value.lower()}"

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
        """Invoke ``QualificationEngine`` for this stage's own anchor,
        and store/open a position if it qualifies.

        Raises:
            core.exceptions.ValidationError: if this anchor's strike
                is not present in ``context.chain_snapshot``.
        """
        assert context.selected_strike is not None  # guaranteed by is_ready
        assert context.trend is not None  # guaranteed by is_ready

        strike = (
            context.selected_strike.top_strike
            if self._anchor_role is AnchorRole.TOP
            else context.selected_strike.bottom_strike
        )
        pair = self._find_chain_snapshot(context.chain_snapshot, strike)
        signal = self._qualification_engine.evaluate(
            self._anchor_role,
            context.trend,
            context.reference_data,
            pair.ce,
            pair.pe,
            context.candle_timestamp,
        )
        if signal is None:
            return StageOutcome(context=context)

        position = self._position_manager.open(signal)
        if position is None:
            return StageOutcome(context=context)

        updated = (
            context.with_qualified_position_top(position)
            if self._anchor_role is AnchorRole.TOP
            else context.with_qualified_position_bottom(position)
        )
        return StageOutcome(context=updated)

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

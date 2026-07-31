"""WinnerStage: PipelineStage adapter for WinnerEngine.

Traceability
------------
Backtest harness wiring (research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md
Section 9, already implemented and confirmed - see
``winner_engine.winner_engine.WinnerEngine``). Follows the same
adapter pattern already established by ``business.stages.orb_stage.ORBStage``
and ``business.stages.weekly_future_stage.WeeklyFutureStage`` -
performs no calculation of its own, only reads
``PipelineContext.chain_snapshot`` for the anchor strike's CE/PE pair,
invokes the already-implemented engine unchanged, and writes the
result back via ``PipelineContext.with_winner``.

Event publication: per Rule 3 (v1.1, CONFIRMED), a detected Winner
"immediately generates Entry Signal." ``winner_engine.winner_engine.WinnerEngine.evaluate``
already publishes the resulting ``WinnerDetectedEvent`` to its own
injected event bus internally (not merely returning it), and
``entry_engine.entry_engine.EntryEngine`` already subscribes itself to
that same bus for ``WinnerDetectedEvent`` at construction (see its own
module docstring) - so Entry fires synchronously, inside
``evaluate()``, before this stage's ``run`` even returns. This stage
therefore does NOT also return the event via ``StageOutcome.events`` -
``business.business_pipeline.BusinessPipeline.execute`` would publish
it a second time, double-triggering ``EntryEngine``.
"""

from __future__ import annotations

from decimal import Decimal

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel
from models.strike_chain_snapshot import StrikeChainSnapshot
from winner_engine.winner_engine import WinnerEngine


class WinnerStage:
    """Runs ``WinnerEngine`` for the injected anchor strike, and
    stores/publishes the result if a Winner is detected.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(self, anchor_strike: Decimal, winner_engine: WinnerEngine) -> None:
        self._anchor_strike = anchor_strike
        self._winner_engine = winner_engine

    @property
    def name(self) -> str:
        return "winner"

    def is_ready(self, context: PipelineContext) -> bool:
        """Ready once a reference ladder and this candle's chain
        snapshot are both present."""
        return len(context.reference_data) > 0 and len(context.chain_snapshot) > 0

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Invoke ``WinnerEngine`` and store/publish the result.

        Raises:
            core.exceptions.ValidationError: if the anchor strike is
                not present in ``context.reference_data`` or
                ``context.chain_snapshot``.
            strategy_engine.core.exceptions.AmbiguousWinnerError:
                propagated unchanged from ``WinnerEngine.evaluate`` if
                both sides genuinely touch the same candle
                (Specification Rule 3 - "does not occur," treated as
                a genuine fault, not guessed around).
        """
        level = self._find_level(context.reference_data)
        pair = self._find_chain_snapshot(context.chain_snapshot)
        winner = self._winner_engine.evaluate(
            context.session_id,
            context.candle_timestamp,
            self._anchor_strike,
            level,
            pair.ce,
            pair.pe,
        )
        if winner is None:
            return StageOutcome(context=context)

        updated = context.with_winner(winner)
        return StageOutcome(context=updated)

    def _find_level(self, reference_data: tuple[ReferenceLevel, ...]) -> ReferenceLevel:
        for level in reference_data:
            if level.strike == self._anchor_strike:
                return level
        raise ValidationError(
            f"No ReferenceLevel found for anchor strike {self._anchor_strike} "
            "in PipelineContext.reference_data."
        )

    def _find_chain_snapshot(
        self, chain_snapshot: tuple[StrikeChainSnapshot, ...]
    ) -> StrikeChainSnapshot:
        for pair in chain_snapshot:
            if pair.strike == self._anchor_strike:
                return pair
        raise ValidationError(
            f"No StrikeChainSnapshot found for anchor strike {self._anchor_strike} "
            "in PipelineContext.chain_snapshot."
        )

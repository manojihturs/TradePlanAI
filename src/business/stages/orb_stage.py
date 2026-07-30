"""ORBStage: PipelineStage adapter for ORBEngine.

Traceability
------------
Phase 2, Sprint: "ORB Pipeline Integration" (Compact Development
Mode). Placed in ``business.stages`` (an existing package, since
``business.business_pipeline`` already lives in ``src/business/``),
not the prompt's literally-named ``src/business_pipeline/stages/`` -
the same deliberate deviation already made (and explained) for
``business.stages.weekly_future_stage.WeeklyFutureStage``.

Reads ``PipelineContext.reference_data`` (for the strike's already-
built ``ReferenceLevel``) and ``PipelineContext.candles`` (every
candle from the replay's own driver dataset observed so far this
session, threaded in by
``application.replay_runner.ReplayRunner``'s candle-accumulation
loop), invokes the already-implemented
``orb_engine.orb_engine.ORBEngine`` unchanged, and writes its result
back via ``PipelineContext.with_orb_result`` - an already-existing
field, no new calculation. Performs no calculation of its own.

``PipelineContext.candles`` and ``PipelineContext.reference_data``
are deliberately separate data sources - the reference ladder comes
from ``ReferenceBuilder``, itself built from separately-supplied
first-candle CE/PE data (real captured data, per
``reference_builder.reference_builder.ReferenceBuilder``'s own
docstring), not from the replay's driver dataset at all. So every
candle in ``PipelineContext.candles`` is legitimately "after the
opening range" from ``ORBEngine``'s point of view - no slicing off a
first candle is needed or performed here.

Error propagation: relies on ``business.business_pipeline.BusinessPipeline``'s
existing fault-absorption design (a stage fault is caught, wrapped in
``business.business_errors.StageExecutionError``, recorded on
``BusinessResult.error``, never re-raised) - the same precedent
``WeeklyFutureStage`` already established, not a new error-handling
layer.

The anchor strike and side (CE/PE) are constructor-injected, not
derived - the same evidence-gap reasoning as ``WeeklyFutureStage``'s
own anchor strike (selection itself remains unresolved evidence).
"""

from __future__ import annotations

from decimal import Decimal

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.enums import OptionType
from core.exceptions import ValidationError
from interfaces.orb_engine import ORBEngine
from models.reference_level import ReferenceLevel


class ORBStage:
    """Runs ``ORBEngine`` for the injected anchor strike/side, and
    stores the result in context.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(
        self,
        anchor_strike: Decimal,
        side: OptionType,
        orb_engine: ORBEngine,
    ) -> None:
        self._anchor_strike = anchor_strike
        self._side = side
        self._orb_engine = orb_engine

    @property
    def name(self) -> str:
        return "orb"

    def is_ready(self, context: PipelineContext) -> bool:
        """Ready once a reference ladder is present in context - the
        same prerequisite ``WeeklyFutureStage`` uses. ``context.candles``
        may legitimately be empty (``ORBEngine`` yields ``ORBStatus.NONE``
        in that case)."""
        return len(context.reference_data) > 0

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Invoke ``ORBEngine`` and store its result back into context.

        Raises:
            core.exceptions.ValidationError: if the anchor strike is
                not present in ``context.reference_data``.
        """
        level = self._find_level(context.reference_data)
        orb_result = self._orb_engine.calculate(
            context.session_id, level, self._side, context.candles, context.candle_timestamp
        )
        updated = context.with_orb_result(orb_result)
        return StageOutcome(context=updated)

    def _find_level(self, reference_data: tuple[ReferenceLevel, ...]) -> ReferenceLevel:
        for level in reference_data:
            if level.strike == self._anchor_strike:
                return level
        raise ValidationError(
            f"No ReferenceLevel found for anchor strike {self._anchor_strike} "
            "in PipelineContext.reference_data."
        )

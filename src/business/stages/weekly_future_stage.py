"""WeeklyFutureStage: PipelineStage adapter for WeeklyFutureCalculator + StrikeSelector.

Traceability
------------
Reads ``PipelineContext.reference_data`` (threaded in by
``application.replay_runner.ReplayRunner``'s ReferenceBuilder
integration), invokes the already-implemented
``weekly_future.weekly_future_calculator.WeeklyFutureCalculator`` and
``strike_selector.strike_selector.StrikeSelector`` in sequence, and
writes their results back into context via
``PipelineContext.with_weekly_future``/``with_selected_strike`` -
already-existing fields, no new ``PipelineContext`` fields added.
Performs no calculation of its own.

Error propagation: ``business.business_pipeline.BusinessPipeline``'s
own documented design (see its module docstring) is that a stage
fault is caught once, wrapped in
``business.business_errors.StageExecutionError``, and recorded on
``BusinessResult.error`` - it is deliberately **not** re-raised out
of ``BusinessPipeline.execute()``/``BusinessOrchestrator.run()``, so
that one faulty candle/stage never aborts an entire replay. This
stage relies on that existing, already-established behaviour rather
than introducing a second error-wrapping layer that would contradict
it. ``application.replay_application.ReplayApplication`` still wraps
*its own* setup/execution failures (e.g. a broken event bus) in
``core.exceptions.ApplicationError`` - unchanged and unaffected by
this stage.

The anchor strike (which strike in the 13-level ladder to run the
formula against) is constructor-injected, not derived here - which
strike is "anchor" is itself still unresolved evidence (see
``research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md``
v1.0 §1), so this stage does not guess it.
"""

from __future__ import annotations

from decimal import Decimal

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError
from interfaces.strike_selector import StrikeSelector
from interfaces.weekly_future_calculator import WeeklyFutureCalculator
from models.reference_level import ReferenceLevel


class WeeklyFutureStage:
    """Runs ``WeeklyFutureCalculator`` then ``StrikeSelector`` for the
    injected anchor strike, and stores both results in context.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(
        self,
        anchor_strike: Decimal,
        weekly_future_calculator: WeeklyFutureCalculator,
        strike_selector: StrikeSelector,
    ) -> None:
        self._anchor_strike = anchor_strike
        self._weekly_future_calculator = weekly_future_calculator
        self._strike_selector = strike_selector

    @property
    def name(self) -> str:
        return "weekly_future"

    def is_ready(self, context: PipelineContext) -> bool:
        """Ready once a reference ladder is present in context."""
        return len(context.reference_data) > 0

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Invoke ``WeeklyFutureCalculator`` then ``StrikeSelector``,
        and store both outputs back into context.

        Raises:
            core.exceptions.ValidationError: if the anchor strike is
                not present in ``context.reference_data``.
        """
        level = self._find_level(context.reference_data)
        weekly_future = self._weekly_future_calculator.calculate(
            context.session_id, level, context.candle_timestamp
        )
        strike_selection = self._strike_selector.select(
            context.session_id, weekly_future, context.candle_timestamp
        )
        updated = context.with_weekly_future(weekly_future).with_selected_strike(strike_selection)
        return StageOutcome(context=updated)

    def _find_level(self, reference_data: tuple[ReferenceLevel, ...]) -> ReferenceLevel:
        for level in reference_data:
            if level.strike == self._anchor_strike:
                return level
        raise ValidationError(
            f"No ReferenceLevel found for anchor strike {self._anchor_strike} "
            "in PipelineContext.reference_data."
        )

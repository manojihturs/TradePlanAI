"""BacktestRunner: drives an OptionChainDataset through the confirmed pipeline.

Traceability
------------
Mirrors ``application.replay_runner.ReplayRunner``'s structure (builds
the reference ladder once via ``reference_builder.reference_builder.ReferenceBuilder``,
then threads one ``business.pipeline_context.PipelineContext`` per
candle through a ``business.orchestrator.BusinessOrchestrator``) but
drives a :class:`~data.option_chain_dataset.OptionChainDataset`
(every ladder strike's CE/PE simultaneously) instead of
``ReplayRunner``'s single-instrument ``data.historical_dataset.HistoricalDataset``
- see that module's own docstring on why deriving one from the other
is not possible with the data shapes that exist today.

Scope, per ``docs/BUSINESS_LOGIC_FLOW.md``: Weekly Future -> Strike
Selection -> ORB (one side, diagnostic only - confirmed to have zero
influence on Winner/Entry/Exit) -> Winner Detection -> Entry -> Exit
(Target/Competitor legs only, via ``backtest.null_engines`` stand-ins
for the still-blocked Stop Loss/Trailing Stop). Decision Engine
synthesis is not wired in - it remains a blocked stub with no
implementation to wire.

Sprint 11 (2026-08-01) additively wires in the confirmed
``qualification_engine.qualification_engine.QualificationEngine``
mechanism (QUAL-007) alongside the above, as a genuinely separate,
independently-confirmed mechanism - not a replacement for the
Winner/Entry/Exit flow. Runs on its own
``qualification_engine.qualification_position_manager.QualificationPositionManager``,
so open-trade state does not interact with the Rule-2-based
``position_manager.position_manager.PositionManager`` at all. Requires
a ``core.enums.TrendDirection`` supplied by the caller for the whole
run - trend computation itself remains UNRESOLVED evidence this
package does not invent; the Product Owner has said they compute it
manually for now, so the caller (``run_upstox_backtest.py``, for a
live run) is expected to hardcode it per session, the same way
``ANCHOR_STRIKE``/``SESSION_DATE`` already are. QUAL-011's
end-of-session forced close is applied once after the candle loop, on
any qualified position still open.

The anchor strike's own CE stream (extracted from each candle's
``chain_snapshot``) accumulates into ``PipelineContext.candles`` for
``business.stages.orb_stage.ORBStage``, matching ``ReplayRunner``'s
own candle-accumulation convention.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from backtest.fixture import BacktestFixture
from backtest.null_engines import NeverTriggersStopLoss, NeverTriggersTrailingStop
from business.business_result import BusinessResult
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.exit_stage import ExitStage
from business.stages.orb_stage import ORBStage
from business.stages.qualification_exit_stage import QualificationExitStage
from business.stages.qualification_stage import QualificationStage
from business.stages.weekly_future_stage import WeeklyFutureStage
from business.stages.winner_stage import WinnerStage
from core.enums import OptionType, TrendDirection
from core.protocols import IdFactory
from entry_engine.entry_engine import EntryEngine
from events.event_bus import EventBus
from exit_engine.exit_engine import ExitEngine
from models.market_snapshot import MarketSnapshot
from models.qualified_position import QualifiedPosition
from orb_engine.orb_engine import ORBEngine
from position_manager.position_manager import PositionManager
from qualification_engine.qualification_engine import QualificationEngine
from qualification_engine.qualification_exit_engine import QualificationExitEngine
from qualification_engine.qualification_position_manager import QualificationPositionManager
from qualification_engine.qualification_trailing_stop import (
    NeverTriggersQualificationTrailingStop,
)
from reference_builder.reference_builder import ReferenceBuilder
from strike_selector.strike_selector import StrikeSelector
from trade_history.trade_history import TradeHistory
from trade_manager.trade_manager import TradeManager
from weekly_future.weekly_future_calculator import WeeklyFutureCalculator
from winner_engine.winner_engine import WinnerEngine


class _SimulatedClock:
    """A ``core.protocols.Clock`` that returns whichever candle
    timestamp the runner most recently set, not wall-clock time.

    Every timestamped side effect during a backtest (trade
    opened/closed times, Winner ``occurred_at``) must reflect
    simulated market time, not real execution time - otherwise trade
    durations would measure how long this process took to run, not
    how long a position was actually open in the simulated session.
    """

    def __init__(self, initial: datetime) -> None:
        self._current = initial

    def set(self, timestamp: datetime) -> None:
        self._current = timestamp

    def __call__(self) -> datetime:
        return self._current


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """The full outcome of one backtest run.

    Attributes:
        session_id: The synthetic session this run concerns.
        business_results: One :class:`~business.business_result.BusinessResult`
            per candle processed, in order.
        trade_history: Every completed trade (Target/Competitor exits
            only - see module docstring). ``TradeRecord.pnl`` is
            always ``None``; P&L is not confirmed business logic.
        qualification_positions: Every completed
            :class:`~models.qualified_position.QualifiedPosition` from
            the separate, Sprint-11 QualificationEngine-based flow
            (QUAL-007) - independent of ``trade_history`` above, which
            covers only the older Rule-2/Winner-based flow.
    """

    session_id: uuid.UUID
    business_results: tuple[BusinessResult, ...] = field(default_factory=tuple)
    trade_history: TradeHistory = field(default_factory=TradeHistory)
    qualification_positions: tuple[QualifiedPosition, ...] = field(default_factory=tuple)


class BacktestRunner:
    """Runs the confirmed pipeline over one
    :class:`~backtest.fixture.BacktestFixture`, one candle at a time -
    data-source-agnostic, whether ``fixture`` came from
    ``backtest.synthetic_data.build_synthetic_fixture`` (not real
    market data) or a real source.

    Constructor-injected id_factory only, for deterministic testing -
    no other globals/singletons.
    """

    def __init__(self, id_factory: IdFactory = uuid.uuid4) -> None:
        self._id_factory = id_factory

    def run(self, fixture: BacktestFixture, trend: TrendDirection) -> BacktestResult:
        """Build the reference ladder once, then run the confirmed
        pipeline candle by candle over ``fixture.dataset``.

        Args:
            fixture: The candle data to run over.
            trend: The underlying's directional bias for this whole
                run, supplied by the caller - see module docstring
                for why this package does not compute it.
        """
        session_id = self._id_factory()

        reference_data = ReferenceBuilder().build(session_id, fixture.reference_inputs)

        clock = _SimulatedClock(fixture.dataset.candles[0].timestamp)
        bus = EventBus()
        trade_manager = TradeManager(bus=bus, clock=clock, id_factory=self._id_factory)
        position_manager = PositionManager(trade_manager)
        trade_history = TradeHistory()

        # EntryEngine subscribes itself to `bus` on construction (see its own
        # docstring) - not held onto, since nothing here calls it directly.
        EntryEngine(
            bus=bus,
            position_manager=position_manager,
            reference_levels=reference_data,
            clock=clock,
            id_factory=self._id_factory,
        )
        winner_engine = WinnerEngine(bus=bus, clock=clock, id_factory=self._id_factory)
        exit_engine = ExitEngine(
            position_manager=position_manager,
            reference_levels=reference_data,
            stop_loss_engine=NeverTriggersStopLoss(),
            trailing_stop_engine=NeverTriggersTrailingStop(),
            trade_history=trade_history,
        )

        qualification_engine = QualificationEngine(id_factory=self._id_factory)
        qualification_position_manager = QualificationPositionManager(
            bus=bus, clock=clock, id_factory=self._id_factory
        )
        qualification_exit_engine = QualificationExitEngine(
            position_manager=qualification_position_manager,
            trailing_stop=NeverTriggersQualificationTrailingStop(),
        )

        # Two separate orchestrators, not one combined registration list:
        # a fault in the legacy flow (e.g. AmbiguousWinnerError) halts
        # ITS OWN orchestrator's remaining stages
        # (business.business_pipeline.BusinessPipeline.execute's own
        # documented halt-on-fault behaviour), which would otherwise
        # silently skip the qualification stages too if they shared one
        # orchestrator - defeating the whole point of these being
        # "genuinely separate, independently-confirmed" mechanisms (see
        # this module's own docstring). The qualification orchestrator
        # runs on the legacy orchestrator's resulting context (so it
        # still sees weekly_future/selected_strike/reference_data), but
        # with its own independent halt state.
        legacy_execution = ExecutionContext(mode=ExecutionMode.REPLAY, event_bus=bus)
        legacy_orchestrator = BusinessOrchestrator(legacy_execution)
        legacy_orchestrator.register(
            WeeklyFutureStage(
                anchor_strike=fixture.anchor_strike,
                weekly_future_calculator=WeeklyFutureCalculator(),
                strike_selector=StrikeSelector(),
            )
        )
        legacy_orchestrator.register(
            ORBStage(
                anchor_strike=fixture.anchor_strike,
                side=OptionType.CALL,
                orb_engine=ORBEngine(),
            )
        )
        legacy_orchestrator.register(
            WinnerStage(anchor_strike=fixture.anchor_strike, winner_engine=winner_engine)
        )
        legacy_orchestrator.register(
            ExitStage(exit_engine=exit_engine, position_manager=position_manager)
        )

        qualification_execution = ExecutionContext(mode=ExecutionMode.REPLAY, event_bus=bus)
        qualification_orchestrator = BusinessOrchestrator(qualification_execution)
        qualification_orchestrator.register(
            QualificationStage(
                qualification_engine=qualification_engine,
                position_manager=qualification_position_manager,
            )
        )
        qualification_orchestrator.register(
            QualificationExitStage(
                exit_engine=qualification_exit_engine,
                position_manager=qualification_position_manager,
            )
        )

        business_results: list[BusinessResult] = []
        anchor_ce_candles: list[MarketSnapshot] = []
        qualification_positions: list[QualifiedPosition] = []

        for candle in fixture.dataset.candles:
            clock.set(candle.timestamp)
            anchor_pair = next(
                pair for pair in candle.strikes if pair.strike == fixture.anchor_strike
            )
            anchor_ce_candles.append(anchor_pair.ce)

            context = PipelineContext(
                session_id=session_id,
                candle_timestamp=candle.timestamp,
                reference_data=reference_data,
                candles=tuple(anchor_ce_candles),
                chain_snapshot=candle.strikes,
                trend=trend,
            )
            legacy_result = legacy_orchestrator.run(context)
            qualification_result = qualification_orchestrator.run(legacy_result.context)
            result = self._merge_results(legacy_result, qualification_result)
            business_results.append(result)
            if result.context.qualification_exited_position is not None:
                qualification_positions.append(result.context.qualification_exited_position)

        forced_close = qualification_position_manager.force_close_session_end()
        if forced_close is not None:
            qualification_positions.append(forced_close)

        return BacktestResult(
            session_id=session_id,
            business_results=tuple(business_results),
            trade_history=trade_history,
            qualification_positions=tuple(qualification_positions),
        )

    @staticmethod
    def _merge_results(legacy: BusinessResult, qualification: BusinessResult) -> BusinessResult:
        """Combine one candle's legacy-flow and qualification-flow
        results into a single :class:`~business.business_result.BusinessResult`,
        preserving the existing one-result-per-candle shape callers
        already expect, while keeping the two orchestrators'
        success/halt state genuinely independent (see the caller's own
        comment for why they are separate orchestrators at all).
        """
        return BusinessResult(
            success=legacy.success and qualification.success,
            context=qualification.context,
            completed_stages=legacy.completed_stages + qualification.completed_stages,
            skipped_stages=legacy.skipped_stages + qualification.skipped_stages,
            warnings=legacy.warnings + qualification.warnings,
            execution_time=legacy.execution_time + qualification.execution_time,
            diagnostics=legacy.diagnostics + qualification.diagnostics,
            stage_diagnostics=legacy.stage_diagnostics + qualification.stage_diagnostics,
            error=legacy.error if legacy.error is not None else qualification.error,
        )

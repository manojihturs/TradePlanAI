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
for the still-blocked Stop Loss/Trailing Stop). Qualification and
Decision Engine synthesis are not wired in - both remain blocked
stubs with no implementation to wire.

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
from business.stages.weekly_future_stage import WeeklyFutureStage
from business.stages.winner_stage import WinnerStage
from core.enums import OptionType
from core.protocols import IdFactory
from entry_engine.entry_engine import EntryEngine
from events.event_bus import EventBus
from exit_engine.exit_engine import ExitEngine
from models.market_snapshot import MarketSnapshot
from orb_engine.orb_engine import ORBEngine
from position_manager.position_manager import PositionManager
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
    """

    session_id: uuid.UUID
    business_results: tuple[BusinessResult, ...] = field(default_factory=tuple)
    trade_history: TradeHistory = field(default_factory=TradeHistory)


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

    def run(self, fixture: BacktestFixture) -> BacktestResult:
        """Build the reference ladder once, then run the confirmed
        pipeline candle by candle over ``fixture.dataset``.
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

        orchestrator = BusinessOrchestrator(
            ExecutionContext(mode=ExecutionMode.REPLAY, event_bus=bus)
        )
        orchestrator.register(
            WeeklyFutureStage(
                anchor_strike=fixture.anchor_strike,
                weekly_future_calculator=WeeklyFutureCalculator(),
                strike_selector=StrikeSelector(),
            )
        )
        orchestrator.register(
            ORBStage(
                anchor_strike=fixture.anchor_strike,
                side=OptionType.CALL,
                orb_engine=ORBEngine(),
            )
        )
        orchestrator.register(
            WinnerStage(anchor_strike=fixture.anchor_strike, winner_engine=winner_engine)
        )
        orchestrator.register(ExitStage(exit_engine=exit_engine, position_manager=position_manager))

        business_results: list[BusinessResult] = []
        anchor_ce_candles: list[MarketSnapshot] = []

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
            )
            business_results.append(orchestrator.run(context))

        return BacktestResult(
            session_id=session_id,
            business_results=tuple(business_results),
            trade_history=trade_history,
        )

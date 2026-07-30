"""ReplayController: coordinates loading, clocking, and (optionally) strategy execution.

Traceability notes
-------------------
Reuses, and never modifies the business behaviour of,
:class:`~trading_engine.engine.strategy_engine.StrategyEngine` (per
Milestone B1's explicit "Existing Architecture: reuse StrategyEngine
... Do NOT modify their business behaviour" instruction). This class
is pure orchestration glue: it advances a
:class:`~trading_engine.replay.replay_clock.ReplayClock`, and - only
if the caller supplies BOTH a ``strategy_engine`` and a
``context_factory`` - calls ``strategy_engine.run()`` once per step.

The ``context_factory`` (a caller-supplied
``Callable[[Candle], RuleExecutionContext]``) is the deliberate
boundary of this milestone's scope: converting a raw OHLC
:class:`~trading_engine.replay.history_loader.Candle` into a
:class:`~trading_engine.rules.context.RuleExecutionContext` requires
building domain objects (a Strike, a MarketContext) from that candle -
a conversion with no evidenced formula anywhere in this repository
(see ``research/analysis/WEEKLY_FUTURE_VERIFICATION.md``). Rather than
inventing that conversion, this milestone leaves it entirely to the
caller via dependency injection - if neither is supplied, replay still
works fully as pure position-advancement infrastructure, with no
StrategyEngine interaction at all.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path

from trading_engine.diagnostics.events import (
    ReplayCompleted,
    ReplayPaused,
    ReplayReset,
    ReplayResumed,
    ReplayStarted,
    ReplayStepped,
)
from trading_engine.diagnostics.sink import DiagnosticsSink, NullDiagnosticsSink
from trading_engine.engine.execution_report import ExecutionReport
from trading_engine.engine.strategy_engine import StrategyEngine
from trading_engine.replay.history_loader import Candle, HistoryLoader
from trading_engine.replay.replay_clock import ReplayClock
from trading_engine.replay.replay_session import ReplaySession
from trading_engine.rules.context import RuleExecutionContext

#: The shape of a caller-supplied Candle -> RuleExecutionContext
#: converter - see module docstring for why this milestone does not
#: implement one itself.
ContextFactory = Callable[[Candle], RuleExecutionContext]


class ReplayController:
    """Coordinates a :class:`~trading_engine.replay.history_loader.HistoryLoader`-produced
    candle sequence, a :class:`~trading_engine.replay.replay_clock.ReplayClock`,
    a :class:`~trading_engine.replay.replay_session.ReplaySession`, and
    (optionally) a :class:`~trading_engine.engine.strategy_engine.StrategyEngine`.

    Rule References
        None - infrastructure only. Never reads a candle's OHLC
        values itself, and never branches on
        :class:`~trading_engine.rules.outcome.RuleOutcome` or any
        other trading-meaningful value.

    Attributes:
        clock: The underlying :class:`ReplayClock`.
        session: The :class:`ReplaySession` wrapping ``clock``.
    """

    def __init__(
        self,
        candles: tuple[Candle, ...],
        strategy_engine: StrategyEngine | None = None,
        context_factory: ContextFactory | None = None,
        diagnostics_sink: DiagnosticsSink | None = None,
        playback_speed: float = 1.0,
    ) -> None:
        self.clock = ReplayClock(candles, playback_speed=playback_speed)
        self.session = ReplaySession(self.clock)
        self._strategy_engine = strategy_engine
        self._context_factory = context_factory
        self._sink: DiagnosticsSink = (
            diagnostics_sink if diagnostics_sink is not None else NullDiagnosticsSink()
        )
        self._execution_reports: list[ExecutionReport] = []

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        strategy_engine: StrategyEngine | None = None,
        context_factory: ContextFactory | None = None,
        diagnostics_sink: DiagnosticsSink | None = None,
        playback_speed: float = 1.0,
    ) -> ReplayController:
        """Build a controller by loading candles from a CSV file via
        :class:`~trading_engine.replay.history_loader.HistoryLoader`."""
        candles = HistoryLoader().load(path)
        return cls(
            candles,
            strategy_engine=strategy_engine,
            context_factory=context_factory,
            diagnostics_sink=diagnostics_sink,
            playback_speed=playback_speed,
        )

    @property
    def current_position(self) -> int:
        """The current candle's index."""
        return self.clock.current_index

    @property
    def current_candle(self) -> Candle:
        """The candle at the current position."""
        return self.clock.current_candle()

    @property
    def is_complete(self) -> bool:
        """Whether replay has reached the end of the candle sequence."""
        return self.clock.is_complete()

    def execution_reports(self) -> tuple[ExecutionReport, ...]:
        """Every :class:`~trading_engine.engine.execution_report.ExecutionReport`
        produced so far (empty if no ``strategy_engine``/``context_factory``
        was supplied)."""
        return tuple(self._execution_reports)

    def start(self) -> Candle:
        """Begin replay at the first candle."""
        candle = self.clock.start()
        self._sink.emit(
            ReplayStarted(
                event_id=uuid.uuid4(),
                occurred_at=candle.timestamp,
                session_id=self.session.session_id,
                total_candles=self.clock.total_candles,
            )
        )
        self._maybe_run_strategy(candle)
        return candle

    def step(self) -> Candle:
        """Advance one candle forward."""
        from_index = self.clock.current_index
        candle = self.clock.step_forward()
        self._sink.emit(
            ReplayStepped(
                event_id=uuid.uuid4(),
                occurred_at=candle.timestamp,
                session_id=self.session.session_id,
                from_index=from_index,
                to_index=self.clock.current_index,
                direction="forward",
            )
        )
        self._maybe_run_strategy(candle)
        if self.clock.is_complete():
            self._emit_completed()
        return candle

    def step_backward(self) -> Candle:
        """Retreat one candle backward. Does not invoke the strategy
        engine - only forward steps represent new market data being
        observed."""
        from_index = self.clock.current_index
        candle = self.clock.step_backward()
        self._sink.emit(
            ReplayStepped(
                event_id=uuid.uuid4(),
                occurred_at=candle.timestamp,
                session_id=self.session.session_id,
                from_index=from_index,
                to_index=self.clock.current_index,
                direction="backward",
            )
        )
        return candle

    def seek(self, index: int) -> Candle:
        """Move directly to ``index``."""
        return self.clock.seek(index)

    def pause(self) -> None:
        """Pause replay."""
        self.clock.pause()
        self._sink.emit(
            ReplayPaused(
                event_id=uuid.uuid4(),
                occurred_at=self.clock.current_candle().timestamp,
                session_id=self.session.session_id,
                current_index=self.clock.current_index,
            )
        )

    def resume(self) -> None:
        """Resume a paused replay."""
        self.clock.resume()
        self._sink.emit(
            ReplayResumed(
                event_id=uuid.uuid4(),
                occurred_at=self.clock.current_candle().timestamp,
                session_id=self.session.session_id,
                current_index=self.clock.current_index,
            )
        )

    def stop(self) -> None:
        """Deliberately, non-resumably halt replay.

        No dedicated diagnostic event exists for this action -
        Milestone B1's Task 6 names exactly six replay event types,
        and ``ReplayStopped`` is not among them; see
        ``research/analysis/REPLAY_ENGINE_TEST_REPORT.md``'s "Known
        limitations" for this deliberate, spec-faithful gap.
        """
        self.clock.stop()

    def restart(self) -> Candle:
        """Reset and immediately start again - emits ``ReplayReset``
        then ``ReplayStarted``, in that order."""
        self.reset()
        return self.start()

    def reset(self) -> None:
        """Return to the first candle, ``NOT_STARTED`` state, and
        clear any accumulated execution reports."""
        self.clock.reset()
        self._execution_reports.clear()
        self._sink.emit(
            ReplayReset(
                event_id=uuid.uuid4(),
                occurred_at=self.clock.current_candle().timestamp,
                session_id=self.session.session_id,
            )
        )

    def _maybe_run_strategy(self, candle: Candle) -> None:
        if self._strategy_engine is None or self._context_factory is None:
            return
        context = self._context_factory(candle)
        report = self._strategy_engine.run(context)
        self._execution_reports.append(report)

    def _emit_completed(self) -> None:
        self._sink.emit(
            ReplayCompleted(
                event_id=uuid.uuid4(),
                occurred_at=self.clock.current_candle().timestamp,
                session_id=self.session.session_id,
                total_candles_processed=self.session.statistics().processed_candles,
            )
        )

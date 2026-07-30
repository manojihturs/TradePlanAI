"""Tests for ReplayController."""

from __future__ import annotations

import uuid
from pathlib import Path

from trading_engine.diagnostics.sink import InMemoryDiagnosticsSink
from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.session_state import SessionState
from trading_engine.engine.strategy_engine import StrategyEngine
from trading_engine.replay.history_loader import Candle
from trading_engine.replay.replay_clock import ReplayState
from trading_engine.replay.replay_controller import ReplayController
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.outcome import RuleOutcome
from trading_engine.rules.registry import RuleRegistry

from ..rules.conftest import FakeRule, make_rule_reference
from .conftest import write_csv


def _context_factory(candle: Candle) -> RuleExecutionContext:
    # A minimal, evidence-free conversion used only by tests - real
    # replay callers must supply their own, per the module docstring's
    # explanation of why this milestone does not implement one.
    market_context = MarketContext(
        context_id=uuid.uuid4(), session_id=uuid.uuid4(), timestamp=candle.timestamp
    )
    session_state = SessionState(session_id=uuid.uuid4())
    return RuleExecutionContext(market_context, session_state)


class TestConstruction:
    def test_wraps_candles_into_clock_and_session(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        assert controller.clock.total_candles == 5
        assert controller.session.clock is controller.clock

    def test_from_csv_loads_and_wraps(
        self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]
    ) -> None:
        csv_path = write_csv(tmp_path / "candles.csv", valid_csv_rows)
        controller = ReplayController.from_csv(csv_path)
        assert controller.clock.total_candles == 3


class TestBasicNavigation:
    def test_current_position_and_candle(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        assert controller.current_position == 0
        assert controller.current_candle == sample_candles[0]

    def test_start_moves_state_to_running(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        assert controller.clock.state == ReplayState.RUNNING

    def test_step_advances_position(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        controller.step()
        assert controller.current_position == 1
        assert controller.current_candle == sample_candles[1]

    def test_step_backward(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        controller.step()
        controller.step_backward()
        assert controller.current_position == 0

    def test_seek(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        controller.seek(3)
        assert controller.current_position == 3

    def test_is_complete_after_stepping_to_the_end(
        self, sample_candles: tuple[Candle, ...]
    ) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        for _ in range(len(sample_candles) - 1):
            controller.step()
        assert controller.is_complete is True


class TestPauseResumeStopRestartReset:
    def test_pause_and_resume(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        controller.pause()
        assert controller.clock.state == ReplayState.PAUSED
        controller.resume()
        assert controller.clock.state == ReplayState.RUNNING

    def test_stop_sets_stopped_state(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        controller.stop()
        assert controller.clock.state == ReplayState.STOPPED

    def test_reset_returns_to_start_and_clears_reports(
        self, sample_candles: tuple[Candle, ...]
    ) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        controller.step()
        controller.reset()
        assert controller.current_position == 0
        assert controller.clock.state == ReplayState.NOT_STARTED
        assert controller.execution_reports() == ()

    def test_restart_resets_then_starts(self, sample_candles: tuple[Candle, ...]) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        controller.step()
        controller.step()
        controller.restart()
        assert controller.current_position == 0
        assert controller.clock.state == ReplayState.RUNNING


class TestStrategyEngineIntegration:
    def test_no_strategy_engine_means_no_execution_reports(
        self, sample_candles: tuple[Candle, ...]
    ) -> None:
        controller = ReplayController(sample_candles)
        controller.start()
        controller.step()
        assert controller.execution_reports() == ()

    def test_context_factory_without_engine_produces_no_reports(
        self, sample_candles: tuple[Candle, ...]
    ) -> None:
        controller = ReplayController(sample_candles, context_factory=_context_factory)
        controller.start()
        assert controller.execution_reports() == ()

    def test_engine_without_context_factory_produces_no_reports(
        self, sample_candles: tuple[Candle, ...]
    ) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS))
        engine = StrategyEngine(registry)
        controller = ReplayController(sample_candles, strategy_engine=engine)
        controller.start()
        assert controller.execution_reports() == ()

    def test_both_supplied_runs_the_engine_on_start_and_each_step(
        self, sample_candles: tuple[Candle, ...]
    ) -> None:
        registry = RuleRegistry()
        registry.register(FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS))
        engine = StrategyEngine(registry)
        controller = ReplayController(
            sample_candles, strategy_engine=engine, context_factory=_context_factory
        )
        controller.start()
        controller.step()
        controller.step()
        assert len(controller.execution_reports()) == 3


class TestDiagnosticsEmission:
    def test_start_emits_replay_started(self, sample_candles: tuple[Candle, ...]) -> None:
        sink = InMemoryDiagnosticsSink()
        controller = ReplayController(sample_candles, diagnostics_sink=sink)
        controller.start()
        events = sink.events()
        assert len(events) == 1
        assert type(events[0]).__name__ == "ReplayStarted"

    def test_step_emits_replay_stepped(self, sample_candles: tuple[Candle, ...]) -> None:
        sink = InMemoryDiagnosticsSink()
        controller = ReplayController(sample_candles, diagnostics_sink=sink)
        controller.start()
        controller.step()
        events = sink.events()
        assert type(events[-1]).__name__ == "ReplayStepped"
        assert events[-1].direction == "forward"

    def test_step_backward_emits_replay_stepped_backward(
        self, sample_candles: tuple[Candle, ...]
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        controller = ReplayController(sample_candles, diagnostics_sink=sink)
        controller.start()
        controller.step()
        controller.step_backward()
        events = sink.events()
        assert events[-1].direction == "backward"

    def test_pause_resume_emit_paused_and_resumed(self, sample_candles: tuple[Candle, ...]) -> None:
        sink = InMemoryDiagnosticsSink()
        controller = ReplayController(sample_candles, diagnostics_sink=sink)
        controller.start()
        controller.pause()
        controller.resume()
        event_types = [type(event).__name__ for event in sink.events()]
        assert event_types == ["ReplayStarted", "ReplayPaused", "ReplayResumed"]

    def test_reaching_the_end_emits_replay_completed(
        self, sample_candles: tuple[Candle, ...]
    ) -> None:
        sink = InMemoryDiagnosticsSink()
        controller = ReplayController(sample_candles, diagnostics_sink=sink)
        controller.start()
        for _ in range(len(sample_candles) - 1):
            controller.step()
        event_types = [type(event).__name__ for event in sink.events()]
        assert event_types[-1] == "ReplayCompleted"

    def test_reset_emits_replay_reset(self, sample_candles: tuple[Candle, ...]) -> None:
        sink = InMemoryDiagnosticsSink()
        controller = ReplayController(sample_candles, diagnostics_sink=sink)
        controller.start()
        controller.reset()
        event_types = [type(event).__name__ for event in sink.events()]
        assert event_types[-1] == "ReplayReset"

    def test_stop_emits_no_dedicated_event(self, sample_candles: tuple[Candle, ...]) -> None:
        # Deliberate per module docstring: Task 6's event list names no
        # "ReplayStopped" event.
        sink = InMemoryDiagnosticsSink()
        controller = ReplayController(sample_candles, diagnostics_sink=sink)
        controller.start()
        before = len(sink)
        controller.stop()
        assert len(sink) == before

    def test_no_sink_configured_does_not_raise(self, sample_candles: tuple[Candle, ...]) -> None:
        # Default diagnostics_sink=None resolves internally to
        # NullDiagnosticsSink - every operation must still work.
        controller = ReplayController(sample_candles)
        controller.start()
        controller.step()
        controller.pause()
        controller.resume()
        controller.reset()

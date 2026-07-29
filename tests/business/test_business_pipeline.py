"""Tests for business.business_pipeline."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from business.business_errors import StageExecutionError
from business.business_pipeline import BusinessPipeline, PipelineStage, StageOutcome
from business.execution_context import ExecutionContext, ExecutionMode
from business.pipeline_context import PipelineContext
from core.enums import EventPriority
from core.events import MarketOpenEvent
from core.exceptions import (
    EventBusError,
    UnresolvedBusinessRuleError,
    ValidationError,
)


def _ts(offset_seconds: int = 0) -> datetime:
    return datetime(2026, 7, 30, 9, 20, offset_seconds, tzinfo=UTC)


def _context() -> PipelineContext:
    return PipelineContext(session_id=uuid.uuid4(), candle_timestamp=_ts())


class _RecordingBus:
    def __init__(self) -> None:
        self.published: list[object] = []

    def publish(self, event: object) -> None:
        self.published.append(event)

    def subscribe(self, event_type: object, handler: object) -> None:  # pragma: no cover
        raise NotImplementedError

    def unsubscribe(self, event_type: object, handler: object) -> None:  # pragma: no cover
        raise NotImplementedError

    def subscribe_all(self, handler: object) -> None:  # pragma: no cover
        raise NotImplementedError

    def unsubscribe_all(self, handler: object) -> None:  # pragma: no cover
        raise NotImplementedError


class _AlwaysReadyStage:
    """A stage that always runs successfully, appending a diagnostic."""

    def __init__(self, name: str, events: tuple[object, ...] = ()) -> None:
        self._name = name
        self._events = events

    @property
    def name(self) -> str:
        return self._name

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        return StageOutcome(
            context=context.with_diagnostic(f"{self._name} ran"),
            events=self._events,  # type: ignore[arg-type]
            warnings=(f"{self._name} warning",),
        )


class _NeverReadyStage:
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def is_ready(self, context: PipelineContext) -> bool:
        return False

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        raise AssertionError("run() must not be called when is_ready() is False")


class _UnresolvedStage:
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        raise UnresolvedBusinessRuleError(f"{self._name} rule is MISSING INFORMATION.")


class _FaultingStage:
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        raise EventBusError(f"{self._name} misused the bus.")


class TestProtocolConformance:
    def test_ready_stage_satisfies_protocol(self) -> None:
        assert isinstance(_AlwaysReadyStage("weekly_future"), PipelineStage)

    def test_plain_object_does_not_satisfy_protocol(self) -> None:
        assert not isinstance(object(), PipelineStage)


class TestStageOutcomeValidation:
    def test_none_context_raises(self) -> None:
        with pytest.raises(ValidationError, match="context must not be None"):
            StageOutcome(context=None)  # type: ignore[arg-type]


class TestAllStagesComplete:
    def test_success_runs_every_stage_in_order(self) -> None:
        pipeline = BusinessPipeline(
            (_AlwaysReadyStage("weekly_future"), _AlwaysReadyStage("strike_selection"))
        )
        execution = ExecutionContext(mode=ExecutionMode.REPLAY, clock=lambda: _ts())

        result = pipeline.execute(_context(), execution)

        assert result.success is True
        assert result.completed_stages == ("weekly_future", "strike_selection")
        assert result.skipped_stages == ()
        assert result.error is None
        assert result.warnings == ("weekly_future warning", "strike_selection warning")
        assert result.context.diagnostics == ("weekly_future ran", "strike_selection ran")
        assert "weekly_future: completed" in result.diagnostics
        assert "strike_selection: completed" in result.diagnostics

    def test_empty_pipeline_succeeds_trivially(self) -> None:
        pipeline = BusinessPipeline(())

        result = pipeline.execute(_context(), ExecutionContext(mode=ExecutionMode.LIVE))

        assert result.success is True
        assert result.completed_stages == ()
        assert result.skipped_stages == ()


class TestPrerequisitesNotMet:
    def test_stops_and_skips_remaining_stages(self) -> None:
        pipeline = BusinessPipeline(
            (
                _AlwaysReadyStage("weekly_future"),
                _NeverReadyStage("strike_selection"),
                _AlwaysReadyStage("tp_engine"),
            )
        )

        result = pipeline.execute(_context(), ExecutionContext(mode=ExecutionMode.LIVE))

        assert result.success is False
        assert result.completed_stages == ("weekly_future",)
        assert result.skipped_stages == ("strike_selection", "tp_engine")
        assert result.error is None
        assert any("prerequisites not met" in d for d in result.diagnostics)


class TestUnresolvedBusinessRule:
    def test_stops_gracefully_without_error(self) -> None:
        pipeline = BusinessPipeline(
            (_UnresolvedStage("weekly_future"), _AlwaysReadyStage("strike_selection"))
        )

        result = pipeline.execute(_context(), ExecutionContext(mode=ExecutionMode.LIVE))

        assert result.success is False
        assert result.completed_stages == ()
        assert result.skipped_stages == ("weekly_future", "strike_selection")
        assert result.error is None
        assert any("UNRESOLVED" in d for d in result.diagnostics)


class TestUnexpectedStageFault:
    def test_wraps_fault_in_stage_execution_error(self) -> None:
        pipeline = BusinessPipeline(
            (_FaultingStage("weekly_future"), _AlwaysReadyStage("strike_selection"))
        )

        result = pipeline.execute(_context(), ExecutionContext(mode=ExecutionMode.LIVE))

        assert result.success is False
        assert result.completed_stages == ()
        assert result.skipped_stages == ("weekly_future", "strike_selection")
        assert isinstance(result.error, StageExecutionError)
        assert "EventBusError" in str(result.error)
        assert any("FAILED" in d for d in result.diagnostics)


class TestEventForwarding:
    def test_stage_events_are_published_to_the_bus(self) -> None:
        event = MarketOpenEvent(
            event_id=uuid.uuid4(),
            occurred_at=_ts(),
            session_id=uuid.uuid4(),
            priority=EventPriority.NORMAL,
        )
        bus = _RecordingBus()
        pipeline = BusinessPipeline((_AlwaysReadyStage("weekly_future", events=(event,)),))
        execution = ExecutionContext(mode=ExecutionMode.LIVE, event_bus=bus)

        pipeline.execute(_context(), execution)

        assert bus.published == [event]

    def test_no_bus_injected_does_not_raise(self) -> None:
        event = MarketOpenEvent(
            event_id=uuid.uuid4(),
            occurred_at=_ts(),
            session_id=uuid.uuid4(),
            priority=EventPriority.NORMAL,
        )
        pipeline = BusinessPipeline((_AlwaysReadyStage("weekly_future", events=(event,)),))
        execution = ExecutionContext(mode=ExecutionMode.LIVE, event_bus=None)

        result = pipeline.execute(_context(), execution)

        assert result.success is True


class TestExecutionTime:
    def test_execution_time_reflects_injected_clock(self) -> None:
        ticks = iter([_ts(0), _ts(5)])
        pipeline = BusinessPipeline((_AlwaysReadyStage("weekly_future"),))
        execution = ExecutionContext(mode=ExecutionMode.LIVE, clock=lambda: next(ticks))

        result = pipeline.execute(_context(), execution)

        assert result.execution_time == timedelta(seconds=5)


class TestStagesProperty:
    def test_stages_property_exposes_registration_order(self) -> None:
        stage_a = _AlwaysReadyStage("weekly_future")
        stage_b = _AlwaysReadyStage("strike_selection")

        pipeline = BusinessPipeline((stage_a, stage_b))

        assert pipeline.stages == (stage_a, stage_b)

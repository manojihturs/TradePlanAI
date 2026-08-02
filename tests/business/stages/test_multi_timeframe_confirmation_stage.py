"""Tests for business.stages.multi_timeframe_confirmation_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from business.business_pipeline import BusinessPipeline
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.multi_timeframe_confirmation_stage import MultiTimeframeConfirmationStage
from core.enums import TrendDirection
from models.market_snapshot import MarketSnapshot

_TIMESTAMP = datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)


def _candle() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_TIMESTAMP,
        underlying_price=Decimal(100),
        open=Decimal(100),
        high=Decimal(101),
        low=Decimal(99),
        close=Decimal(100),
    )


def _context(
    candles: tuple[MarketSnapshot, ...], trend: TrendDirection | None = None
) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(), candle_timestamp=_TIMESTAMP, candles=candles, trend=trend
    )


class _FakeConfirmation:
    def __init__(self, result: TrendDirection | None) -> None:
        self._result = result
        self.calls: list[tuple[MarketSnapshot, ...]] = []

    def update(self, candles: tuple[MarketSnapshot, ...]) -> TrendDirection | None:
        self.calls.append(candles)
        return self._result


def _stage(result: TrendDirection | None) -> MultiTimeframeConfirmationStage:
    return MultiTimeframeConfirmationStage(_FakeConfirmation(result))  # type: ignore[arg-type]


class TestIsReady:
    def test_ready_when_candles_present(self) -> None:
        stage = _stage(None)

        assert stage.is_ready(_context((_candle(),))) is True

    def test_not_ready_when_candles_empty(self) -> None:
        stage = _stage(None)

        assert stage.is_ready(_context(())) is False


class TestRun:
    def test_no_op_when_context_trend_is_already_none(self) -> None:
        stage = _stage(TrendDirection.BULLISH)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context((_candle(),), trend=None)

        outcome = stage.run(context, execution)

        assert outcome.context is context

    def test_confirmed_matching_trend_is_kept(self) -> None:
        stage = _stage(TrendDirection.BULLISH)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context((_candle(),), trend=TrendDirection.BULLISH)

        outcome = stage.run(context, execution)

        assert outcome.context.trend is TrendDirection.BULLISH

    def test_no_confirmation_clears_trend(self) -> None:
        stage = _stage(None)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context((_candle(),), trend=TrendDirection.BULLISH)

        outcome = stage.run(context, execution)

        assert outcome.context.trend is None

    def test_confirmed_opposite_trend_clears_trend(self) -> None:
        stage = _stage(TrendDirection.BEARISH)
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context((_candle(),), trend=TrendDirection.BULLISH)

        outcome = stage.run(context, execution)

        assert outcome.context.trend is None


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        stage = _stage(TrendDirection.BULLISH)
        orchestrator.register(stage)
        context = _context((_candle(),), trend=TrendDirection.BULLISH)

        result = orchestrator.run(context)

        assert result.success is True
        assert result.completed_stages == ("multi_timeframe_confirmation",)

    def test_pipeline_stages_property_includes_the_stage(self) -> None:
        stage = _stage(None)
        pipeline = BusinessPipeline((stage,))

        assert pipeline.stages == (stage,)

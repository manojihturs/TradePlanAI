"""Tests for business.stages.ut_bot_trend_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from business.business_pipeline import BusinessPipeline
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.ut_bot_trend_stage import UTBotTrendStage
from core.enums import TrendDirection
from models.market_snapshot import MarketSnapshot
from trend_engine.ut_bot_engine import UTBotEngine

_START = datetime(2026, 7, 30, 9, 15, 0, tzinfo=UTC)


def _candle(index: int, high: str, low: str, close: str) -> MarketSnapshot:
    timestamp = _START + timedelta(minutes=5 * index)
    return MarketSnapshot(
        timestamp=timestamp,
        underlying_price=Decimal(close),
        open=Decimal(close),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
    )


def _context(candles: tuple[MarketSnapshot, ...]) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(), candle_timestamp=_START, underlying_index_candles=candles
    )


def _stage() -> UTBotTrendStage:
    return UTBotTrendStage(UTBotEngine(key_value=Decimal(1), atr_period=1))


class TestIsReady:
    def test_ready_when_candles_present(self) -> None:
        stage = _stage()
        context = _context((_candle(0, "110", "90", "100"),))

        assert stage.is_ready(context) is True

    def test_not_ready_when_candles_empty(self) -> None:
        stage = _stage()
        context = _context(())

        assert stage.is_ready(context) is False


class TestRun:
    def test_seed_candle_leaves_trend_unset(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context((_candle(0, "100", "90", "95"),))

        outcome = stage.run(context, execution)

        assert outcome.context.trend is None

    def test_sell_flip_sets_bearish_trend(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        stage.run(_context((_candle(0, "100", "90", "95"),)), execution)

        outcome = stage.run(_context((_candle(1, "80", "70", "75"),)), execution)

        assert outcome.context.trend is TrendDirection.BEARISH

    def test_buy_flip_sets_bullish_trend(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        stage.run(_context((_candle(0, "100", "90", "95"),)), execution)
        stage.run(_context((_candle(1, "80", "70", "75"),)), execution)

        outcome = stage.run(_context((_candle(2, "115", "105", "110"),)), execution)

        assert outcome.context.trend is TrendDirection.BULLISH

    def test_no_flip_candle_preserves_trend_already_on_context(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        stage.run(_context((_candle(0, "100", "90", "95"),)), execution)
        stage.run(_context((_candle(1, "80", "70", "75"),)), execution)

        no_flip_context = _context((_candle(2, "65", "55", "60"),)).with_trend(
            TrendDirection.BEARISH
        )
        outcome = stage.run(no_flip_context, execution)

        assert outcome.context.trend is TrendDirection.BEARISH


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())
        context = _context((_candle(0, "100", "90", "95"),))

        result = orchestrator.run(context)

        assert result.success is True
        assert result.completed_stages == ("ut_bot_trend",)

    def test_pipeline_stages_property_includes_the_stage(self) -> None:
        stage = _stage()
        pipeline = BusinessPipeline((stage,))

        assert pipeline.stages == (stage,)

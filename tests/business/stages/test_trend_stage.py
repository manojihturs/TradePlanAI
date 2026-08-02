"""Tests for business.stages.trend_stage."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from business.business_pipeline import BusinessPipeline
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from business.stages.trend_stage import TrendStage
from core.enums import TrendDirection
from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.strike_chain_snapshot import StrikeChainSnapshot
from trend_engine.open_interest_trend_engine import OpenInterestTrendEngine

_STRIKE = Decimal(24200)
_TIMESTAMP = datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)
_LATER_TIMESTAMP = datetime(2026, 7, 30, 9, 25, 0, tzinfo=UTC)


def _snapshot(
    timestamp: datetime, underlying_price: Decimal, open_interest: int | None
) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=timestamp, underlying_price=underlying_price, open_interest=open_interest
    )


def _chain_snapshot(
    timestamp: datetime,
    underlying_price: Decimal,
    call_oi: int | None,
    put_oi: int | None,
) -> tuple[StrikeChainSnapshot, ...]:
    return (
        StrikeChainSnapshot(
            strike=_STRIKE,
            ce=_snapshot(timestamp, underlying_price, call_oi),
            pe=_snapshot(timestamp, underlying_price, put_oi),
        ),
    )


def _context(
    chain_snapshot: tuple[StrikeChainSnapshot, ...], timestamp: datetime = _TIMESTAMP
) -> PipelineContext:
    return PipelineContext(
        session_id=uuid.uuid4(), candle_timestamp=timestamp, chain_snapshot=chain_snapshot
    )


def _stage() -> TrendStage:
    return TrendStage(OpenInterestTrendEngine())


class TestIsReady:
    def test_ready_when_chain_snapshot_present(self) -> None:
        stage = _stage()
        context = _context(_chain_snapshot(_TIMESTAMP, Decimal(24000), 1000, 1000))

        assert stage.is_ready(context) is True

    def test_not_ready_when_chain_snapshot_empty(self) -> None:
        stage = _stage()
        context = _context(())

        assert stage.is_ready(context) is False


class TestRun:
    def test_first_candle_captures_baseline_and_no_signal_at_own_open(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(_chain_snapshot(_TIMESTAMP, Decimal(24000), 1000, 1000))

        outcome = stage.run(context, execution)

        assert outcome.context.trend is None

    def test_bullish_signal_updates_trend(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        opening = _context(_chain_snapshot(_TIMESTAMP, Decimal(24000), 1000, 1000))
        stage.run(opening, execution)

        later = _context(
            _chain_snapshot(_LATER_TIMESTAMP, Decimal(24050), 1000, 1200), _LATER_TIMESTAMP
        )
        outcome = stage.run(later, execution)

        assert outcome.context.trend is TrendDirection.BULLISH

    def test_no_signal_candle_preserves_trend_already_on_context(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        stage.run(_context(_chain_snapshot(_TIMESTAMP, Decimal(24000), 1000, 1000)), execution)

        # This candle's own Price/OI combination gives no signal (price
        # unchanged from session open), but the input context already
        # carries an established trend from an earlier candle - the
        # stage must not clear it.
        flat_candle_with_established_trend = _context(
            _chain_snapshot(_LATER_TIMESTAMP, Decimal(24000), 1000, 1000), _LATER_TIMESTAMP
        ).with_trend(TrendDirection.BULLISH)

        outcome = stage.run(flat_candle_with_established_trend, execution)

        assert outcome.context.trend is TrendDirection.BULLISH

    def test_missing_call_oi_raises(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(_chain_snapshot(_TIMESTAMP, Decimal(24000), None, 1000))

        with pytest.raises(ValidationError, match="requires open_interest"):
            stage.run(context, execution)

    def test_missing_put_oi_raises(self) -> None:
        stage = _stage()
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        context = _context(_chain_snapshot(_TIMESTAMP, Decimal(24000), 1000, None))

        with pytest.raises(ValidationError, match="requires open_interest"):
            stage.run(context, execution)


class TestBusinessPipelineIntegration:
    def test_successful_run_through_orchestrator(self) -> None:
        execution = ExecutionContext(mode=ExecutionMode.REPLAY)
        orchestrator = BusinessOrchestrator(execution)
        orchestrator.register(_stage())
        context = _context(_chain_snapshot(_TIMESTAMP, Decimal(24000), 1000, 1000))

        result = orchestrator.run(context)

        assert result.success is True
        assert result.completed_stages == ("trend",)

    def test_pipeline_stages_property_includes_the_stage(self) -> None:
        stage = _stage()
        pipeline = BusinessPipeline((stage,))

        assert pipeline.stages == (stage,)

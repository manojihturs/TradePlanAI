"""Replay Engine: infrastructure for replaying historical OHLC candles.

Traceability notes
-------------------
Milestone B1. Reuses, without modifying the business behaviour of,
:class:`trading_engine.engine.strategy_engine.StrategyEngine`,
:class:`trading_engine.engine.execution_pipeline.ExecutionPipeline`,
:class:`trading_engine.rules.registry.RuleRegistry`,
:class:`trading_engine.engine.engine_configuration.EngineConfiguration`,
and the :mod:`trading_engine.diagnostics` package (extended with six
new replay-specific event types, additive only).

This package contains **no trading mathematics, no strategy logic, no
business rules, no P&L calculation, no trade execution, no order
management, and no risk management**. It answers only "given a
sequence of historical candles, what candle are we looking at, and how
do we move through them" - see
``research/analysis/REPLAY_ENGINE_ARCHITECTURE.md`` for the full
architecture and explicit extension points (including how a future
milestone would wire real Candle -> RuleExecutionContext conversion,
once that conversion is evidenced rather than guessed).
"""

from __future__ import annotations

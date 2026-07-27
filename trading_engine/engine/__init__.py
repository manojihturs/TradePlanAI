"""Strategy Engine Skeleton: orchestration only.

See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule
Evaluation Pipeline", "Decision Objects") for the architecture this
package implements the orchestration shell of.

Architecture Rule (Milestone 4.3)
    :class:`~trading_engine.engine.strategy_engine.StrategyEngine` may
    orchestrate. Rules (see :mod:`trading_engine.rules`) may evaluate.
    Only future calculator modules may perform mathematics. This
    package never mixes those responsibilities - nothing here contains
    an ``if strike`` / ``if trend`` / ``if reversal`` or any other
    business-logic branch.

This package contains **no trading mathematics, no strategy
decisions, no replay, no backtesting, and no broker integration**. It
coordinates the existing :mod:`trading_engine.rules` framework only:
given a populated
:class:`~trading_engine.rules.registry.RuleRegistry` and a
:class:`~trading_engine.rules.context.RuleExecutionContext`, it calls
each registered rule's ``evaluate()`` and collects the results into a
structured report - nothing more.
"""

from __future__ import annotations

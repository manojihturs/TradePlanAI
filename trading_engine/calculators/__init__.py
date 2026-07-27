"""Calculator Framework: the mathematical layer's contracts and scaffolding.

See ``docs/architecture/DOMAIN_ARCHITECTURE.md`` and
``docs/RULE_INDEX.md`` for the business rules this framework exists to
eventually delegate mathematics to. This package defines **how** a
future rule implementation would delegate a calculation - contract
(:mod:`.protocols`), an optional shared base
(:mod:`.base`), result/context shapes (:mod:`.result`, :mod:`.context`),
registration (:mod:`.registry`), this framework's own exceptions
(:mod:`.exceptions`), and five placeholder calculators
(:mod:`.strike_calculator`, :mod:`.trend_calculator`,
:mod:`.opponent_calculator`, :mod:`.reversal_calculator`,
:mod:`.edge_calculator`) that compile and register successfully but
raise ``NotImplementedError`` when actually asked to calculate.

This package contains **no trading mathematics of any kind**. Every
one of the 6 confirmed rules in ``docs/RULE_INDEX.md`` still has
``Mathematical Definition: Unknown`` or ``Partially Known`` - this
framework only makes it possible for a future rule to call a
calculator instead of embedding a formula inline, once that formula is
known (a later milestone).

Architecture Rule (carried forward from Milestone 4.3, see
``trading_engine/engine/__init__.py``)
    StrategyEngine may orchestrate. Rules may evaluate. Only future
    calculator modules may perform mathematics. No calculator in this
    package performs mathematics yet - each raises
    ``NotImplementedError`` - and no calculator knows about the
    StrategyEngine, the Rule Registry, or the Execution Pipeline.
"""

from __future__ import annotations

"""Post-market workflow package.

Modular, single-responsibility modules that together implement the
daily end-of-day validation checklist: data loading, trade review,
rejected-signal review, API/data health, strategy validation, health
scoring, report generation, and archiving. Each module reads only the
already-exported artifacts from Module 11 (``strategy/live_paper_trading.py``)
- nothing here imports from or modifies the ``strategy/`` package, the
live trading loop, or any business rule. Orchestrated by
``run_post_market_workflow.py`` at the repository root.

Kept intentionally decoupled (plain dataclasses passed module to
module) so a future real-time monitoring module can reuse
``data_health`` and ``strategy_validation``'s check functions against
a live, in-progress session rather than only a completed one.
"""

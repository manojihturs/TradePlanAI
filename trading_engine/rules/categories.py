"""Rule category taxonomy, re-exported for the Rule Framework.

Traceability notes
-------------------
Per Milestone 4.2's instruction to "use the existing Rule Bible
taxonomy, no new categories": :class:`RuleCategory` is **not**
redefined here. It is re-exported directly from
:mod:`trading_engine.domain.rule_reference`, the Milestone 4.1 module
that already mirrors ``docs/TRADINGVIEW_STRATEGY_BIBLE.md``'s
"Category Taxonomy (fixed)" exactly. Defining a second copy in this
package would create two sources of truth that could silently drift
apart; this module exists only so callers of :mod:`trading_engine.rules`
can import the category enum from within the ``rules`` package without
reaching into ``domain`` directly.
"""

from __future__ import annotations

from trading_engine.domain.rule_reference import RuleCategory

__all__ = ["RuleCategory"]

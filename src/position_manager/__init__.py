"""PositionManager: builds and tracks the single active TradePosition.

Depends on ``core``, ``models``, and ``trade_manager``. The
single-active-trade gate itself (Specification Section 10, Rule 4)
is not re-implemented here - it is delegated, unmodified, to
``trade_manager.trade_manager.TradeManager`` (Sprint 1), per this
sprint's own instruction not to modify Sprint 1 infrastructure.
"""

from __future__ import annotations

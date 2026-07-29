"""EntryEngine: opens a trade immediately after WinnerDetectedEvent.

Depends on ``core``, ``models``, and ``position_manager``. Does not
re-implement the single-active-trade gate (delegated to
``position_manager.position_manager.PositionManager``, which itself
delegates to the unmodified Sprint 1 ``trade_manager.trade_manager.TradeManager``).
"""

from __future__ import annotations

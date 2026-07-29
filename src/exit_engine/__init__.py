"""ExitEngine: monitors the active TradePosition and closes it on any
of the four confirmed exit conditions.

Depends on ``core``, ``models``, ``interfaces``, ``position_manager``,
and optionally ``trade_history``. Does not create a separate
Competitor Engine - the competitor exit strike is already computed by
``position_manager.position_manager.PositionManager`` (Specification
Rule 2) and read straight off the ``TradePosition``.
"""

from __future__ import annotations

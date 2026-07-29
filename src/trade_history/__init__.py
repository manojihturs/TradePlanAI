"""TradeHistory: maintains completed trades.

Depends on ``core`` and ``models``. PnL calculation is explicitly NOT
implemented - see ``trade_history.trade_history.TradeRecord.pnl``.
"""

from __future__ import annotations

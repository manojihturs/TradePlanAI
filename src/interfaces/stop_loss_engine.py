"""StopLossEngine: interface only.

Traceability
------------
Specification Section 11, Section 20 item 4 (Critical): "Exit when:
... OR Stop Loss ..." with no SL price, basis, or placement rule
stated anywhere. This interface defines only the method shape a
future implementation must satisfy. Do NOT implement.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from models.market_snapshot import MarketSnapshot
from models.trade_position import TradePosition


@runtime_checkable
class StopLossEngine(Protocol):
    """Evaluates whether an active :class:`~models.trade_position.TradePosition`
    has hit its Stop Loss (Specification Section 11)."""

    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        """Whether the Stop Loss condition is currently met.

        Raises:
            core.exceptions.UnresolvedBusinessRuleError: always, until
                the Stop Loss rule (Specification Section 20 item 4)
                is resolved and a real implementation replaces the
                stub.
        """
        ...  # pragma: no cover

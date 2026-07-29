"""TrailingStopEngine: interface only.

Traceability
------------
Specification Section 13, Section 20 items 9-10 (High): "Trailing
stop must guarantee minimum +3 premium points to cover brokerage,
exchange charges, tax." Trail activation trigger, trail step/distance,
and the brokerage/exchange/tax figures needed to compute "+3 net" are
all MISSING INFORMATION. This interface defines only the method shape
a future implementation must satisfy. Do NOT implement.

Added in Sprint 3 - not part of Sprint 1's original five interfaces,
but required by ``exit_engine.exit_engine.ExitEngine``'s fourth exit
condition ("TrailingStopEngine reports exit"). Mirrors
``interfaces.stop_loss_engine.StopLossEngine``'s shape exactly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from models.market_snapshot import MarketSnapshot
from models.trade_position import TradePosition


@runtime_checkable
class TrailingStopEngine(Protocol):
    """Evaluates whether an active :class:`~models.trade_position.TradePosition`
    has hit its Trailing Stop (Specification Section 13)."""

    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        """Whether the Trailing Stop condition is currently met.

        Raises:
            core.exceptions.UnresolvedBusinessRuleError: always, until
                the Trailing Stop mechanics (Specification Section 20
                items 9-10) are resolved and a real implementation
                replaces the stub.
        """
        ...  # pragma: no cover

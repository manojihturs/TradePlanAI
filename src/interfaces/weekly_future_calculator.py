"""WeeklyFutureCalculator: interface only.

Traceability
------------
Specification Section 4, Section 20 item 1 (Critical): "Calculate
Weekly Future High. Weekly Future Low." No formula, inputs, or
worked example exists in the Specification - this interface defines
only the method shape a future implementation must satisfy. Do NOT
implement.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from models.market_snapshot import MarketSnapshot
from models.weekly_future import WeeklyFuture


@runtime_checkable
class WeeklyFutureCalculator(Protocol):
    """Computes the session's Weekly Future High/Low from the first
    5-minute candle (Specification Rule 1 confirms *which* candle;
    the formula itself is MISSING INFORMATION)."""

    def calculate(self, first_five_minute_candle: MarketSnapshot) -> WeeklyFuture:
        """Compute the Weekly Future High/Low.

        Raises:
            core.exceptions.UnresolvedBusinessRuleError: always, until
                the formula (Specification Section 20 item 1) is
                resolved and a real implementation replaces the stub.
        """
        ...  # pragma: no cover

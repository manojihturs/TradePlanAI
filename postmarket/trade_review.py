"""Post-market workflow: Daily Trade Review.

Single responsibility: turn the loaded session's trades into a review
row per trade, computing strike distance from ATM and flagging trades
at distance >= 4 (per Investigations #5-#8's finding that ratio
divergence and variance grow sharply from that point on). Performs no
network or file I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from postmarket.data_sources import SessionData

BOUNDARY_DISTANCE_THRESHOLD = 4


@dataclass(frozen=True)
class TradeReviewRow:
    entry_time: str
    exit_time: str
    side: str
    strike: int
    distance_from_atm: Optional[int]
    anchor: str
    entry: float
    target: float
    stop: float
    exit_reason: str
    pnl_rupees: Optional[float]
    flagged_boundary: bool


def _distance(strike: int, atm: Optional[int], strike_gap: int = 50) -> Optional[int]:
    if atm is None:
        return None
    return abs(strike - atm) // strike_gap


def build_trade_review(session: SessionData, strike_gap: int = 50) -> List[TradeReviewRow]:
    """Build the Daily Trade Review rows for every executed trade.

    Args:
        session: The loaded session data.
        strike_gap: Distance between adjacent tradable strikes (used
            only to compute strike distance from ATM).

    Returns:
        One ``TradeReviewRow`` per trade in ``session.trades``, in
        entry-time order. Rows at distance >= ``BOUNDARY_DISTANCE_THRESHOLD``
        have ``flagged_boundary=True``.
    """
    anchor_by_strike = {r.strike: r.anchor for r in session.level_usage}

    rows: List[TradeReviewRow] = []
    for t in session.trades:
        dist = _distance(t.strike, session.atm, strike_gap)
        rows.append(TradeReviewRow(
            entry_time=t.entry_time.strftime("%H:%M") if t.entry_time else "",
            exit_time=t.exit_time.strftime("%H:%M") if t.exit_time else "",
            side=t.side,
            strike=t.strike,
            distance_from_atm=dist,
            anchor=anchor_by_strike.get(t.strike, "UNKNOWN"),
            entry=t.entry_premium,
            target=t.target,
            stop=t.stop_loss,
            exit_reason=t.exit_reason,
            pnl_rupees=t.pnl_rupees,
            flagged_boundary=(dist is not None and dist >= BOUNDARY_DISTANCE_THRESHOLD),
        ))
    return rows

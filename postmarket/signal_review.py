"""Post-market workflow: Rejected Signal Review.

Single responsibility: summarise the session's rejected signals -
total count, rejection reasons, strike-distance distribution, and any
repeated rejection pattern (the same strike/side rejected for the same
reason 3+ times in one session). Performs no network or file I/O.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from postmarket.data_sources import SessionData

REPEATED_PATTERN_THRESHOLD = 3


@dataclass(frozen=True)
class SignalReviewSummary:
    total_rejected: int
    reason_counts: Dict[str, int]
    distance_distribution: Dict[str, int]
    repeated_patterns: List[Tuple[int, str, str, int]]  # strike, side, reason, count


def _distance(strike: int, atm: Optional[int], strike_gap: int = 50) -> Optional[int]:
    if atm is None:
        return None
    return abs(strike - atm) // strike_gap


def build_signal_review(session: SessionData, strike_gap: int = 50) -> SignalReviewSummary:
    """Summarise rejected signals for the session.

    Args:
        session: The loaded session data.
        strike_gap: Distance between adjacent tradable strikes.

    Returns:
        A ``SignalReviewSummary`` with counts, distribution, and any
        repeated strike/side/reason pattern occurring
        ``REPEATED_PATTERN_THRESHOLD`` or more times.
    """
    reason_counts: Counter = Counter()
    distance_counts: Counter = Counter()
    pattern_counts: Counter = Counter()

    for r in session.rejected_signals:
        reason_counts[r.reason] += 1
        dist = _distance(r.strike, session.atm, strike_gap)
        distance_counts[str(dist) if dist is not None else "unknown"] += 1
        pattern_counts[(r.strike, r.side, r.reason)] += 1

    repeated = [
        (strike, side, reason, count)
        for (strike, side, reason), count in pattern_counts.items()
        if count >= REPEATED_PATTERN_THRESHOLD
    ]
    repeated.sort(key=lambda t: -t[3])

    return SignalReviewSummary(
        total_rejected=len(session.rejected_signals),
        reason_counts=dict(reason_counts),
        distance_distribution=dict(distance_counts),
        repeated_patterns=repeated,
    )

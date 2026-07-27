"""Post-market workflow: Strategy Validation.

Single responsibility: check the session's trades and level usage for
the anomaly patterns identified across Investigations #5-#8 - premium
scale divergence, target/stop inversion, boundary-strike trades,
unexpected level-state transitions, duplicate trades, and structurally
invalid mapping (target <= stop). This module only inspects already-
loaded session data; it never touches strategy/ package internals and
never modifies anything.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List, Optional

from postmarket.data_sources import SessionData, TradeRecord

BOUNDARY_DISTANCE_THRESHOLD = 4
SCALE_RATIO_WARN_THRESHOLD = 3.0  # matches Investigation #5's "materially mismatched" cutoff


@dataclass(frozen=True)
class ValidationFinding:
    category: str
    description: str
    severity: str  # "INFO" | "WARNING" | "CRITICAL"


def _distance(strike: int, atm: Optional[int], strike_gap: int = 50) -> Optional[int]:
    if atm is None:
        return None
    return abs(strike - atm) // strike_gap


def _check_inversion(t: TradeRecord) -> Optional[ValidationFinding]:
    if t.target <= t.stop_loss:
        return ValidationFinding(
            category="target_stop_inversion",
            description=(
                f"strike={t.strike} {t.side}: target ({t.target}) <= stop ({t.stop_loss}) "
                f"- structurally invalid mapping for this entry"
            ),
            severity="CRITICAL",
        )
    return None


def _check_boundary(t: TradeRecord, atm: Optional[int], strike_gap: int) -> Optional[ValidationFinding]:
    dist = _distance(t.strike, atm, strike_gap)
    if dist is not None and dist >= BOUNDARY_DISTANCE_THRESHOLD:
        return ValidationFinding(
            category="boundary_strike_trade",
            description=(
                f"strike={t.strike} {t.side}: distance {dist} from ATM >= "
                f"{BOUNDARY_DISTANCE_THRESHOLD} - per Investigations #5-#8, mapping "
                f"ratio variance grows sharply from this distance onward"
            ),
            severity="WARNING",
        )
    return None


SCALE_ASYMMETRY_WARN_THRESHOLD = 5.0


def _check_scale_asymmetry(t: TradeRecord) -> Optional[ValidationFinding]:
    """Flag a trade whose Target-side and Stop-side rung gaps are wildly
    asymmetric.

    The exported Trade Log does not retain the real-time market premium
    at entry (only the mapped values Module 3/4 actually traded), so a
    direct mapped-vs-real-market ratio check (as done live in
    Investigations #5/#7/#8) is not possible from this file alone. This
    is a same-data proxy: the up-gap (target - entry) and down-gap
    (entry - stop) come from the same ladder and are normally within a
    similar order of magnitude; a large asymmetry between them is
    consistent with the scale-divergence pattern found in those
    investigations.
    """
    up_gap = t.target - t.entry_premium
    down_gap = t.entry_premium - t.stop_loss
    if up_gap <= 0 or down_gap <= 0:
        return None  # already reported by _check_inversion
    ratio = max(up_gap, down_gap) / min(up_gap, down_gap)
    if ratio >= SCALE_ASYMMETRY_WARN_THRESHOLD:
        return ValidationFinding(
            category="premium_scale_anomaly",
            description=(
                f"strike={t.strike} {t.side}: target-gap={up_gap:.2f} vs "
                f"stop-gap={down_gap:.2f} (ratio {ratio:.2f}x) - asymmetric rung "
                f"spacing consistent with the scale-divergence pattern from "
                f"Investigations #5/#7/#8"
            ),
            severity="WARNING",
        )
    return None


def _check_duplicates(trades: List[TradeRecord]) -> List[ValidationFinding]:
    findings = []
    seen = Counter((t.strike, t.side, t.entry_time) for t in trades)
    for (strike, side, entry_time), count in seen.items():
        if count > 1:
            findings.append(ValidationFinding(
                category="duplicate_trade",
                description=(
                    f"strike={strike} {side} entry_time={entry_time}: "
                    f"{count} trades recorded with identical strike/side/entry_time"
                ),
                severity="CRITICAL",
            ))
    return findings


def _check_level_state_transitions(session: SessionData) -> List[ValidationFinding]:
    findings = []
    valid_states = {"ACTIVE", "USED", "DISABLED"}
    for lvl in session.level_usage:
        if lvl.final_state not in valid_states:
            findings.append(ValidationFinding(
                category="unexpected_level_state",
                description=(
                    f"strike={lvl.strike} {lvl.anchor}/{lvl.side}: "
                    f"unrecognised final state '{lvl.final_state}'"
                ),
                severity="WARNING",
            ))
    return findings


def build_strategy_validation(session: SessionData, strike_gap: int = 50) -> List[ValidationFinding]:
    """Run all strategy-validation checks against one session.

    Args:
        session: The loaded session data.
        strike_gap: Distance between adjacent tradable strikes.

    Returns:
        Every ``ValidationFinding`` produced by the checks, most-severe
        first. An empty list means no anomalies were detected.
    """
    findings: List[ValidationFinding] = []

    for t in session.trades:
        inv = _check_inversion(t)
        if inv:
            findings.append(inv)
        boundary = _check_boundary(t, session.atm, strike_gap)
        if boundary:
            findings.append(boundary)
        scale = _check_scale_asymmetry(t)
        if scale:
            findings.append(scale)

    findings.extend(_check_duplicates(session.trades))
    findings.extend(_check_level_state_transitions(session))

    severity_rank = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    findings.sort(key=lambda f: severity_rank.get(f.severity, 3))
    return findings

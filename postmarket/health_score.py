"""Post-market workflow: Daily Health Score.

Single responsibility: combine the other modules' findings into three
component health labels (Engine, Data Feed, Strategy) and one overall
status - PASS, REVIEW, or FAIL. Performs no I/O; pure aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from postmarket.data_health import DataHealthReport
from postmarket.strategy_validation import ValidationFinding

Status = str  # "PASS" | "REVIEW" | "FAIL"


@dataclass(frozen=True)
class HealthScore:
    engine_health: Status
    data_feed_health: Status
    strategy_health: Status
    overall_status: Status
    explanation: str


def _worse(a: Status, b: Status) -> Status:
    rank = {"PASS": 0, "REVIEW": 1, "FAIL": 2}
    return a if rank[a] >= rank[b] else b


def compute_health_score(
    data_health: DataHealthReport,
    strategy_findings: List[ValidationFinding],
    engine_had_unhandled_error: bool = False,
) -> HealthScore:
    """Compute the Daily Health Score from prior modules' outputs.

    Args:
        data_health: Output of ``data_health.build_data_health_report``.
        strategy_findings: Output of
            ``strategy_validation.build_strategy_validation``.
        engine_had_unhandled_error: Whether the run log recorded an
            unhandled exception outside the normal poll-failure
            handling (currently always False, since
            ``run_live_paper_trading.py`` has no other failure path
            that survives to write a log line - reserved for future
            engine-level checks).

    Returns:
        A ``HealthScore`` with PASS/REVIEW/FAIL per component and
        overall, plus a short explanation when overall is not PASS.
    """
    engine_health: Status = "FAIL" if engine_had_unhandled_error else "PASS"

    if not data_health.reconnect_events:
        data_feed_health: Status = "PASS"
    elif data_health.recovered_all and not any(
        e.likely_missed_candles for e in data_health.reconnect_events
    ):
        data_feed_health = "REVIEW"
    else:
        data_feed_health = "FAIL"

    critical = [f for f in strategy_findings if f.severity == "CRITICAL"]
    warning = [f for f in strategy_findings if f.severity == "WARNING"]
    if critical:
        strategy_health: Status = "FAIL"
    elif warning:
        strategy_health = "REVIEW"
    else:
        strategy_health = "PASS"

    overall = _worse(_worse(engine_health, data_feed_health), strategy_health)

    reasons = []
    if engine_health != "PASS":
        reasons.append("engine recorded an unhandled error")
    if data_feed_health != "PASS":
        n = len(data_health.reconnect_events)
        missed = sum(1 for e in data_health.reconnect_events if e.likely_missed_candles)
        reasons.append(f"{n} API reconnect event(s), {missed} with likely missed candles")
    if strategy_health != "PASS":
        reasons.append(f"{len(critical)} critical / {len(warning)} warning strategy finding(s)")

    explanation = "; ".join(reasons) if reasons else ""

    return HealthScore(
        engine_health=engine_health, data_feed_health=data_feed_health,
        strategy_health=strategy_health, overall_status=overall, explanation=explanation,
    )

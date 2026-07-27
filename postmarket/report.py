"""Post-market workflow: Report Generation.

Single responsibility: render the other modules' outputs into (a) a
full human-readable text report and (b) a short Telegram summary.
Performs no I/O - callers write the returned strings and send the
returned Telegram text themselves.
"""

from __future__ import annotations

from dataclasses import dataclass

from postmarket.data_health import DataHealthReport
from postmarket.data_sources import SessionData
from postmarket.health_score import HealthScore
from postmarket.signal_review import SignalReviewSummary
from postmarket.strategy_validation import ValidationFinding
from postmarket.trade_review import TradeReviewRow
from typing import List


@dataclass(frozen=True)
class PostMarketReport:
    full_text: str
    telegram_text: str


def _format_trade_review(rows: List[TradeReviewRow]) -> str:
    if not rows:
        return "No trades executed today."
    lines = [
        f"{'Entry':>6} {'Exit':>6} {'Side':>4} {'Strike':>7} {'Dist':>5} {'Anchor':>7} "
        f"{'Entry':>8} {'Target':>8} {'Stop':>8} {'Reason':>10} {'PnL':>10}  Flag"
    ]
    for r in rows:
        dist = "?" if r.distance_from_atm is None else str(r.distance_from_atm)
        pnl = "" if r.pnl_rupees is None else f"{r.pnl_rupees:.2f}"
        flag = "<< BOUNDARY (dist>=4)" if r.flagged_boundary else ""
        lines.append(
            f"{r.entry_time:>6} {r.exit_time:>6} {r.side:>4} {r.strike:>7} {dist:>5} "
            f"{r.anchor:>7} {r.entry:>8.2f} {r.target:>8.2f} {r.stop:>8.2f} "
            f"{r.exit_reason:>10} {pnl:>10}  {flag}"
        )
    return "\n".join(lines)


def _format_signal_review(summary: SignalReviewSummary) -> str:
    lines = [f"Total rejected: {summary.total_rejected}"]
    if summary.reason_counts:
        lines.append("By reason:")
        for reason, count in sorted(summary.reason_counts.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {reason}: {count}")
    if summary.distance_distribution:
        lines.append("By strike distance from ATM:")
        for dist, count in sorted(summary.distance_distribution.items()):
            lines.append(f"  distance {dist}: {count}")
    if summary.repeated_patterns:
        lines.append("Repeated rejection patterns (same strike/side/reason, 3+ times):")
        for strike, side, reason, count in summary.repeated_patterns:
            lines.append(f"  strike={strike} {side} reason='{reason}': {count} times")
    else:
        lines.append("No repeated rejection patterns detected.")
    return "\n".join(lines)


def _format_data_health(report: DataHealthReport) -> str:
    if not report.reconnect_events:
        return "No API reconnect events detected."
    lines = []
    for e in report.reconnect_events:
        ts = e.timestamp.strftime("%H:%M:%S") if e.timestamp else "unknown"
        gap = f"{e.seconds_to_next_success:.0f}s" if e.seconds_to_next_success is not None else "unrecovered"
        missed = "YES" if e.likely_missed_candles else "no"
        lines.append(
            f"  {ts}  recovery={gap}  likely_missed_candles={missed}  msg={e.message}"
        )
    return "\n".join(lines)


def _format_strategy_validation(findings: List[ValidationFinding]) -> str:
    if not findings:
        return "No strategy anomalies detected."
    lines = []
    for f in findings:
        lines.append(f"  [{f.severity}] {f.category}: {f.description}")
    return "\n".join(lines)


def build_report(
    session: SessionData,
    trade_rows: List[TradeReviewRow],
    signal_summary: SignalReviewSummary,
    data_health: DataHealthReport,
    strategy_findings: List[ValidationFinding],
    health: HealthScore,
) -> PostMarketReport:
    """Render the full post-market report and its Telegram summary.

    Args:
        session: The loaded session data.
        trade_rows: Output of ``trade_review.build_trade_review``.
        signal_summary: Output of ``signal_review.build_signal_review``.
        data_health: Output of ``data_health.build_data_health_report``.
        strategy_findings: Output of
            ``strategy_validation.build_strategy_validation``.
        health: Output of ``health_score.compute_health_score``.

    Returns:
        A ``PostMarketReport`` with the full text report and a short
        Telegram summary.
    """
    trades = session.trades
    wins = sum(1 for t in trades if t.pnl_rupees is not None and t.pnl_rupees > 0)
    losses = sum(1 for t in trades if t.pnl_rupees is not None and t.pnl_rupees <= 0)
    win_pct = (wins / len(trades) * 100.0) if trades else 0.0
    net_pnl = session.daily_summary.get("Running PnL (Rs)", 0.0)
    available_capital = session.daily_summary.get("Available Capital (Rs)")

    full_text = f"""\
=========================================================
Post-Market Report — {session.session_date.isoformat()}
=========================================================

1. TRADE REVIEW
---------------
{_format_trade_review(trade_rows)}

2. REJECTED SIGNAL REVIEW
--------------------------
{_format_signal_review(signal_summary)}

3. API & DATA HEALTH
----------------------
{_format_data_health(data_health)}

4. STRATEGY VALIDATION
------------------------
{_format_strategy_validation(strategy_findings)}

5. DAILY HEALTH SCORE
------------------------
Engine Health:     {health.engine_health}
Data Feed Health:  {health.data_feed_health}
Strategy Health:   {health.strategy_health}
Overall Status:    {health.overall_status}
{("Explanation: " + health.explanation) if health.explanation else ""}

=========================================================
Trades: {len(trades)}  Wins: {wins}  Losses: {losses}  Win Rate: {win_pct:.1f}%
Net P&L: Rs {net_pnl}
Available Capital: Rs {available_capital}
=========================================================
"""

    telegram_lines = [
        f"Daily Summary — {session.session_date.isoformat()}",
        "",
        f"Trades: {len(trades)}",
        f"Win Rate: {win_pct:.1f}% ({wins}W/{losses}L)",
        f"Net P&L: Rs {net_pnl}",
        f"Capital: Rs {available_capital}",
        f"Warnings: {len(data_health.reconnect_events)} API reconnect(s)",
        f"Investigations: {len(strategy_findings)} strategy finding(s)",
        f"Health Score: Engine={health.engine_health} Data={health.data_feed_health} "
        f"Strategy={health.strategy_health}",
        f"Overall: {health.overall_status}",
    ]
    if health.overall_status != "PASS" and health.explanation:
        telegram_lines.append(f"Reason: {health.explanation}")
    telegram_text = "\n".join(telegram_lines)

    return PostMarketReport(full_text=full_text, telegram_text=telegram_text)

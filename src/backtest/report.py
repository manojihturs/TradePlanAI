"""summarize_backtest: a trade-count/timing summary over a completed backtest run.

Traceability
------------
Deliberately does NOT report P&L, win rate, drawdown, or expectancy -
``trade_history.trade_history.TradeRecord.pnl`` is always ``None``
("Specification Section 20 gives no P&L/scoring formula anywhere,"
see that module's own docstring), and no entry-price rule exists
either (Specification Section 11, MISSING INFORMATION). Reporting a
dollar figure or a "win rate" derived from anything other than the
confirmed exit-reason label would imply a business judgment
(what counts as a win) this project has no evidence for. This module
reports only what the confirmed model actually tracks: how many
trades occurred, how each one ended (by the four named
``core.enums.ExitReason`` values), and how long each stayed open.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from core.enums import ExitReason
from trade_history.trade_history import TradeRecord


@dataclass(frozen=True, slots=True)
class BacktestSummary:
    """A descriptive summary of a completed backtest run's trades.

    Attributes:
        total_trades: How many trades completed (opened and closed).
        exit_reason_counts: How many trades ended with each
            :class:`~core.enums.ExitReason` - only ``TARGET_HIT``/
            ``COMPETITOR_HIT`` are possible while Stop Loss/Trailing
            Stop remain the never-firing stand-ins in
            ``backtest.null_engines``.
        average_duration: The mean ``exit_time - entry_time`` across
            every trade, or ``None`` if there were no trades.
        candles_processed: How many candles the run evaluated.
    """

    total_trades: int
    exit_reason_counts: dict[ExitReason, int] = field(default_factory=dict)
    average_duration: timedelta | None = None
    candles_processed: int = 0


def summarize_backtest(trades: tuple[TradeRecord, ...], candles_processed: int) -> BacktestSummary:
    """Build a :class:`BacktestSummary` from a completed run's trade
    history. Reports counts and timing only - see module docstring
    for why P&L/win-rate are deliberately absent.
    """
    counts: dict[ExitReason, int] = {}
    for trade in trades:
        counts[trade.exit_reason] = counts.get(trade.exit_reason, 0) + 1

    average_duration = None
    if trades:
        total_seconds = sum(trade.duration.total_seconds() for trade in trades)
        average_duration = timedelta(seconds=total_seconds / len(trades))

    return BacktestSummary(
        total_trades=len(trades),
        exit_reason_counts=counts,
        average_duration=average_duration,
        candles_processed=candles_processed,
    )

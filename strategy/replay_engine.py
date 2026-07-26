"""Module 7: Replay Engine (Backtest Runner).

Single responsibility: replay historical 5-minute candles through
Modules 3-6 EXACTLY as they would run live - one candle at a time, in
chronological order, with no access to any candle beyond the one
currently being processed. This module computes NO entry, exit, or
position logic of its own; it only feeds candles, in order, to:

    - ``entry_signal.EntrySignalDetector``  (Module 3, unmodified)
    - ``position_manager.PositionManager``  (Module 5, unmodified)
    - ``paper_trading.PaperTradingEngine``  (Module 6, unmodified)

No-peek / no-repaint guarantee: the main loop only ever reads
``ce_series``/``pe_series`` at the CURRENT timestamp being iterated, in
ascending order. Once a timestamp has been processed, none of its
decisions (entry, exit) are revisited - there is no lookahead pass, no
second iteration, and no mutation of an already-recorded ``Trade``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Mapping, Optional

from strategy.entry_signal import Candle, EntrySignal, EntrySignalDetector, TradeSide
from strategy.exit_signal import ExitLevels
from strategy.paper_trading import PaperTradingEngine, Trade
from strategy.position_manager import Position, PositionManager
from strategy.premium_mapping import PremiumMapping

logger = logging.getLogger(__name__)

#: strike -> {timestamp -> candle}, one contract's full candle history.
CandleSeries = Mapping[int, Mapping[datetime, Candle]]


class ReplayEngineError(Exception):
    """Raised when the replay cannot proceed.

    Distinguished from generic exceptions so callers can catch replay
    failures specifically without swallowing unrelated bugs.
    """


@dataclass(frozen=True)
class BacktestResult:
    """The complete output of one replay run.

    Attributes:
        trades: Every completed trade, in the order they closed.
        win_count: Number of trades with pnl > 0.
        loss_count: Number of trades with pnl <= 0.
        win_rate_pct: win_count / total trades * 100. 0.0 if no trades.
        total_profit: Sum of all positive-pnl trades.
        total_loss: Sum of all negative-pnl trades (a negative number,
            or 0.0 if there were none).
        net_pnl: total_profit + total_loss.
        max_drawdown: The largest peak-to-trough decline in cumulative
            PnL across the trade sequence, as a positive number
            (0.0 if PnL never fell below a prior peak).
        open_position_at_end: The position still open when the replay
            ran out of candles, if any - NOT force-closed, since a
            time-based exit is explicitly out of scope for the Exit
            Engine (Module 4) unless separately requested.
    """

    trades: List[Trade]
    win_count: int
    loss_count: int
    win_rate_pct: float
    total_profit: float
    total_loss: float
    net_pnl: float
    max_drawdown: float
    open_position_at_end: Optional[Position]


def _select_signal(signals: List[EntrySignal]) -> Optional[EntrySignal]:
    """Deterministic tie-break when multiple signals fire in one candle.

    NOT a confirmed trading rule - no priority between simultaneous
    signals has been specified. This simply takes the first signal in
    the order ``EntrySignalDetector.process_candle`` itself produces
    them (TOP anchor before BOTTOM, ascending strike, CE before PE per
    its own iteration order), so the engine is deterministic rather
    than silently arbitrary. Flagged here explicitly so it can be
    replaced with a confirmed rule if one is specified.

    Args:
        signals: The signals returned by ``process_candle`` this candle.

    Returns:
        The first signal, or ``None`` if the list is empty.
    """
    return signals[0] if signals else None


def _candle_for(entry_or_position_side: TradeSide, strike: int, ts: datetime,
                 ce_series: CandleSeries, pe_series: CandleSeries) -> Optional[Candle]:
    """Look up the traded contract's own candle at one timestamp.

    Args:
        entry_or_position_side: TradeSide.CE or TradeSide.PE - which
            contract is being traded.
        strike: The strike being traded.
        ts: The timestamp to look up.
        ce_series: Full CE candle history, by strike.
        pe_series: Full PE candle history, by strike.

    Returns:
        The candle at ``(strike, ts)`` for the traded side, or
        ``None`` if that data point is missing.
    """
    series = ce_series if entry_or_position_side is TradeSide.CE else pe_series
    return series.get(strike, {}).get(ts)


def run_replay(
    mapping: PremiumMapping, ce_series: CandleSeries, pe_series: CandleSeries,
) -> BacktestResult:
    """Replay one session's candles through Modules 3-6, in order.

    Args:
        mapping: The frozen ``PremiumMapping`` (Module 2) for this session.
        ce_series: Every captured strike's full CE candle history for
            the session, strike -> {timestamp -> Candle}.
        pe_series: The PE counterpart of ``ce_series``.

    Returns:
        A ``BacktestResult`` summarizing every trade the replay produced.

    Raises:
        ReplayEngineError: if neither ``ce_series`` nor ``pe_series``
            contains any candles to replay.
    """
    all_timestamps = sorted({
        ts for strike_series in ce_series.values() for ts in strike_series
    } | {
        ts for strike_series in pe_series.values() for ts in strike_series
    })
    if not all_timestamps:
        raise ReplayEngineError("no candles supplied to replay")

    logger.info("Replay starting: %d timestamps, %d strikes",
                len(all_timestamps), len(mapping.top_ce_ladder))

    detector = EntrySignalDetector(mapping)
    manager = PositionManager()
    ledger = PaperTradingEngine()

    # Captured just before a position closes, since ClosedTrade (Module 5)
    # does not itself carry ExitLevels - see paper_trading.py's note.
    pending_exit_levels: Optional[ExitLevels] = None

    for ts in all_timestamps:
        ce_candles: Dict[int, Candle] = {
            strike: series[ts] for strike, series in ce_series.items() if ts in series
        }
        pe_candles: Dict[int, Candle] = {
            strike: series[ts] for strike, series in pe_series.items() if ts in series
        }

        # 1. Manage an already-open position FIRST, using only this
        #    candle's own data for the traded contract - never a future one.
        if manager.is_open:
            position = manager.current_position
            candle = _candle_for(position.entry.side, position.entry.strike, ts,
                                  ce_series, pe_series)
            if candle is not None:
                pending_exit_levels = position.exit_levels
                closed = manager.process_candle(ts, candle)
                if closed is not None:
                    ledger.record_trade(closed, pending_exit_levels)
                    pending_exit_levels = None

        # 2. Only look for a NEW entry if flat (either already flat, or
        #    just became flat from step 1 on this same candle).
        if manager.is_flat:
            signals = detector.process_candle(ts, ce_candles, pe_candles)
            chosen = _select_signal(signals)
            if chosen is not None:
                manager.open(chosen, mapping)
        else:
            # Still open - detector state must still advance every candle
            # so a later fresh-cross is correctly detected as fresh, not
            # stale, once this position eventually closes.
            detector.process_candle(ts, ce_candles, pe_candles)

    result = _summarize(ledger.trades, manager.current_position)
    logger.info("Replay complete: %d trades, win_rate=%.1f%%, net_pnl=%.2f",
                len(result.trades), result.win_rate_pct, result.net_pnl)
    return result


def _summarize(trades: List[Trade], open_position: Optional[Position]) -> BacktestResult:
    """Compute win/loss/drawdown statistics from a completed trade list.

    Args:
        trades: Every completed trade, in the order they closed.
        open_position: The position still open at the end of the
            replay, if any.

    Returns:
        A ``BacktestResult`` with all summary statistics filled in.
    """
    win_count = sum(1 for t in trades if t.pnl > 0)
    loss_count = sum(1 for t in trades if t.pnl <= 0)
    total_profit = sum(t.pnl for t in trades if t.pnl > 0)
    total_loss = sum(t.pnl for t in trades if t.pnl <= 0)
    win_rate_pct = (win_count / len(trades) * 100.0) if trades else 0.0

    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for t in trades:
        cumulative += t.pnl
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)

    return BacktestResult(
        trades=list(trades),
        win_count=win_count,
        loss_count=loss_count,
        win_rate_pct=win_rate_pct,
        total_profit=total_profit,
        total_loss=total_loss,
        net_pnl=total_profit + total_loss,
        max_drawdown=max_drawdown,
        open_position_at_end=open_position,
    )


def format_summary(result: BacktestResult) -> str:
    """Render a ``BacktestResult`` as a human-readable text report.

    Displays Entry, Exit, Reason, and PnL per trade, plus Profit,
    Loss, Drawdown, and Win % overall - per specification.

    Args:
        result: The result to render.

    Returns:
        A multi-line string report.
    """
    lines = ["Trade log:"]
    for i, t in enumerate(result.trades, start=1):
        lines.append(
            f"  {i:>3}. {t.trade_date} {t.trade_time} {t.side.value} "
            f"entry={t.entry:.2f} exit={t.exit:.2f} reason={t.reason} pnl={t.pnl:+.2f}"
        )
    if not result.trades:
        lines.append("  (no trades)")

    lines.append("")
    lines.append("Summary:")
    lines.append(f"  Trades:       {len(result.trades)}")
    lines.append(f"  Win %:        {result.win_rate_pct:.1f}%  "
                 f"({result.win_count}W / {result.loss_count}L)")
    lines.append(f"  Profit:       {result.total_profit:+.2f}")
    lines.append(f"  Loss:         {result.total_loss:+.2f}")
    lines.append(f"  Net PnL:      {result.net_pnl:+.2f}")
    lines.append(f"  Max Drawdown: {result.max_drawdown:.2f}")
    if result.open_position_at_end is not None:
        p = result.open_position_at_end
        lines.append(f"  Still open at end: {p.entry.side.value} at strike "
                     f"{p.entry.strike} (not force-closed - no time exit)")
    return "\n".join(lines)

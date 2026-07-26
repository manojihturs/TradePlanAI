"""Module 10: Multi-Day Backtest & Validation Framework.

Single responsibility: run the EXISTING strategy engine (Modules 1-9,
unmodified) independently across many captured trading days, and
produce comparable per-day and overall statistics. This module
contains NO new entry, exit, mapping, level-state, or confirmation
logic of its own - it only orchestrates calls to those modules, in
the same order and with the same semantics Module 7 (Replay Engine)
already uses, so results are identical to running Module 7 day by day.

It reimplements Module 7's per-candle loop internally (rather than
calling ``replay_engine.run_replay`` directly) ONLY so it can observe
two things Module 7's public return value does not expose: which
signals were rejected and why, and each mapped level's final state at
day end. Every call this module makes to Modules 3, 5, 6, 8, and 9 is
the same call, in the same order, that Module 7 makes - no strategy
behavior is changed, added, or removed.

This module has no direct network/database dependency of its own -
per-day market data and level-capture fetching are injected via the
``DayInput``/``fetch_first_candle`` callbacks, exactly like Module 1's
``FirstCandleFetcher`` pattern.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Tuple, Union

from openpyxl import Workbook

from strategy.entry_signal import Candle, EntrySignal, EntrySignalDetector, MappingAnchor, TradeSide
from strategy.exit_signal import ExitLevels
from strategy.ladder_expansion import ensure_exit_levels
from strategy.level_capture import FirstCandleFetcher, LevelCapture, capture_levels
from strategy.level_state_manager import LevelKey, LevelState, LevelStateManager, level_key_from_entry
from strategy.paper_trading import PaperTradingEngine, Trade
from strategy.position_manager import PositionManager
from strategy.premium_mapping import PremiumMapping, build_premium_mapping

logger = logging.getLogger(__name__)

CandleSeries = Mapping[int, Mapping[datetime, Candle]]


class MultiDayBacktestError(Exception):
    """Raised for setup errors in this module itself (not per-day failures,
    which are captured as ``DayFailure`` records instead - see the
    validation rules in the module docstring: a day failing must not stop
    the run, so per-day errors are data, not exceptions raised to the
    caller)."""


@dataclass(frozen=True)
class DayInput:
    """Everything Module 10 needs to run one day, fully pre-fetched/injected.

    Attributes:
        session_date: The trading date this input is for.
        spot_open: The underlying spot index's 09:20 open price.
        fetch_first_candle: Module 1's fetch callback for this day
            (also reused by Module 8 for ladder expansion).
        ce_series: strike -> {timestamp -> Candle}, the day's full CE history.
        pe_series: The PE counterpart of ``ce_series``.
    """

    session_date: date
    spot_open: float
    fetch_first_candle: FirstCandleFetcher
    ce_series: CandleSeries
    pe_series: CandleSeries


@dataclass(frozen=True)
class RejectedSignal:
    """A signal Module 3 confirmed that did NOT result in a trade.

    Attributes:
        timestamp: When the signal fired.
        strike, side, anchor: The signal's identity (see ``EntrySignal``).
        reason: Why it was rejected - "already in position" or
            "level already completed" (the only two rejection reasons
            possible under the current, unmodified strategy: Module 5
            only allows one open position at a time, and Module 9 only
            allows an ACTIVE level to open a trade).
    """

    timestamp: datetime
    strike: int
    side: TradeSide
    anchor: MappingAnchor
    reason: str


@dataclass(frozen=True)
class LevelRecord:
    """One mapped level's final state at the end of a trading day.

    Attributes:
        strike, anchor, side: The level's identity.
        final_state: ACTIVE, USED, or DISABLED at day close.
    """

    strike: int
    anchor: MappingAnchor
    side: TradeSide
    final_state: LevelState


@dataclass(frozen=True)
class DailyReport:
    """Per-day statistics, per specification."""

    session_date: date
    trades: int
    wins: int
    losses: int
    win_rate_pct: float
    gross_profit: float
    gross_loss: float
    net_pnl: float
    max_drawdown: float
    open_positions_at_close: int
    rejected_signals: int
    completed_mapped_levels: int
    unused_mapped_levels: int


@dataclass(frozen=True)
class DayFailure:
    """A day that could not be processed - recorded, never silently skipped.

    Attributes:
        session_date: The date that failed.
        reason: A short human-readable description of what failed.
        exception_text: The full exception traceback, for diagnosis.
    """

    session_date: date
    reason: str
    exception_text: str


@dataclass(frozen=True)
class OverallSummary:
    """Aggregate statistics across every successfully processed day."""

    trading_days: int
    total_trades: int
    overall_win_rate_pct: float
    total_gross_profit: float
    total_gross_loss: float
    net_pnl: float
    average_trades_per_day: float
    average_daily_pnl: float
    max_daily_drawdown: float
    best_day: Optional[date]
    best_day_pnl: Optional[float]
    worst_day: Optional[date]
    worst_day_pnl: Optional[float]


@dataclass(frozen=True)
class MultiDayResult:
    """The complete output of a multi-day backtest run."""

    daily_reports: List[DailyReport]
    all_trades: List[Trade]
    rejected_signals: List[Tuple[date, RejectedSignal]]
    level_records: List[Tuple[date, LevelRecord]]
    failures: List[DayFailure]
    overall: OverallSummary


def _run_single_day(
    day: DayInput, strike_gap: int, num_strikes: int,
) -> Tuple[DailyReport, List[Trade], List[RejectedSignal], List[LevelRecord]]:
    """Run one trading day through Modules 1-9, fresh state throughout.

    Mirrors ``replay_engine.run_replay``'s per-candle loop exactly (same
    calls, same order, same semantics) so results match Module 7
    precisely - the only difference is this function also records
    rejected signals and each level's final state, which Module 7's
    return value does not expose.

    Args:
        day: The pre-fetched ``DayInput`` for this session.
        strike_gap: The distance between adjacent tradable strikes.
        num_strikes: How many strikes to include on each side of ATM
            for the initial capture (Module 1).

    Returns:
        (DailyReport, trades, rejected_signals, level_records) for this day.
    """
    # Fresh state for everything, per specification rule 3 - new objects
    # every call, nothing carried over from a prior day.
    capture = capture_levels(
        session_date=day.session_date, spot_open=day.spot_open, strike_gap=strike_gap,
        num_strikes=num_strikes, fetch_first_candle=day.fetch_first_candle,
    )
    mapping = build_premium_mapping(capture, strike_gap=strike_gap)
    # Kept separate from `mapping` below, which Module 8 may reassign to an
    # EXPANDED mapping mid-day for SL/Target purposes only - the detector
    # (constructed once, here, from the original mapping) never trades from
    # an expansion strike, so level-state enumeration at day end must use
    # this original mapping, not whatever `mapping` ends up pointing to.
    original_mapping = mapping
    detector = EntrySignalDetector(mapping)
    manager = PositionManager()
    ledger = PaperTradingEngine()
    level_states = LevelStateManager()
    level_states.initialize_day(mapping)

    rejected: List[RejectedSignal] = []
    pending_exit_levels: Optional[ExitLevels] = None

    all_timestamps = sorted({
        ts for series in day.ce_series.values() for ts in series
    } | {
        ts for series in day.pe_series.values() for ts in series
    })

    for ts in all_timestamps:
        ce_candles: Dict[int, Candle] = {
            strike: series[ts] for strike, series in day.ce_series.items() if ts in series
        }
        pe_candles: Dict[int, Candle] = {
            strike: series[ts] for strike, series in day.pe_series.items() if ts in series
        }

        if manager.is_open:
            position = manager.current_position
            side_series = day.ce_series if position.entry.side is TradeSide.CE else day.pe_series
            candle = side_series.get(position.entry.strike, {}).get(ts)
            if candle is not None:
                pending_exit_levels = position.exit_levels
                closed = manager.process_candle(ts, candle)
                if closed is not None:
                    ledger.record_trade(closed, pending_exit_levels)
                    pending_exit_levels = None
                    level_states.mark_used(level_key_from_entry(closed.entry))

        if manager.is_flat:
            signals = detector.process_candle(ts, ce_candles, pe_candles)
            chosen: Optional[EntrySignal] = None
            for signal in signals:
                key = level_key_from_entry(signal)
                if not level_states.can_open(key):
                    rejected.append(RejectedSignal(
                        timestamp=ts, strike=signal.strike, side=signal.side,
                        anchor=signal.anchor, reason="level already completed",
                    ))
                    continue
                if chosen is None:
                    chosen = signal
                else:
                    # An ACTIVE, otherwise-qualifying signal that lost the
                    # same-candle tie-break to another ACTIVE signal - the
                    # only other rejection reason possible under the
                    # unmodified strategy (Module 5 allows one position).
                    rejected.append(RejectedSignal(
                        timestamp=ts, strike=signal.strike, side=signal.side,
                        anchor=signal.anchor, reason="already in position",
                    ))
            if chosen is not None:
                _levels, capture, mapping = ensure_exit_levels(
                    chosen, capture, mapping, strike_gap, day.fetch_first_candle,
                )
                manager.open(chosen, mapping)
        else:
            detector.process_candle(ts, ce_candles, pe_candles)

    trades = ledger.trades
    win_count = sum(1 for t in trades if t.pnl > 0)
    loss_count = sum(1 for t in trades if t.pnl <= 0)
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = sum(t.pnl for t in trades if t.pnl <= 0)
    win_rate_pct = (win_count / len(trades) * 100.0) if trades else 0.0

    cumulative = peak = max_drawdown = 0.0
    for t in trades:
        cumulative += t.pnl
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)

    # Enumerate every level from the ORIGINAL mapping's public ladders (not
    # a private attribute of LevelStateManager, and not the possibly-
    # expanded `mapping` - see the note where original_mapping is captured
    # above). This mirrors exactly what LevelStateManager.initialize_day()
    # itself enumerated at the start of this day.
    all_keys = set()
    for strike in original_mapping.top_ce_ladder:
        all_keys.add(LevelKey(strike, MappingAnchor.TOP, TradeSide.CE))
    for strike in original_mapping.top_pe_ladder:
        all_keys.add(LevelKey(strike, MappingAnchor.TOP, TradeSide.PE))
    for strike in original_mapping.bottom_ce_ladder:
        all_keys.add(LevelKey(strike, MappingAnchor.BOTTOM, TradeSide.CE))
    for strike in original_mapping.bottom_pe_ladder:
        all_keys.add(LevelKey(strike, MappingAnchor.BOTTOM, TradeSide.PE))

    level_records = [
        LevelRecord(strike=key.strike, anchor=key.anchor, side=key.side,
                    final_state=level_states.get_state(key))
        for key in sorted(all_keys, key=lambda k: (k.strike, k.anchor.value, k.side.value))
    ]
    completed = sum(1 for r in level_records if r.final_state is LevelState.USED)
    unused = sum(1 for r in level_records if r.final_state is LevelState.ACTIVE)

    report = DailyReport(
        session_date=day.session_date,
        trades=len(trades), wins=win_count, losses=loss_count, win_rate_pct=win_rate_pct,
        gross_profit=gross_profit, gross_loss=gross_loss, net_pnl=gross_profit + gross_loss,
        max_drawdown=max_drawdown,
        open_positions_at_close=1 if manager.is_open else 0,
        rejected_signals=len(rejected),
        completed_mapped_levels=completed, unused_mapped_levels=unused,
    )
    return report, trades, rejected, level_records


def run_multi_day_backtest(
    session_dates: List[date], fetch_day: Callable[[date], DayInput],
    strike_gap: int, num_strikes: int,
) -> MultiDayResult:
    """Run the backtest across every supplied day, per specification.

    A day that raises ANY exception is recorded as a ``DayFailure`` and
    processing continues with the next day - per validation rule 8,
    days are never silently skipped, and a single bad day never aborts
    the run.

    Args:
        session_dates: Every trading date to process (already
            discovered by the caller - see module docstring on why
            this module has no direct database dependency of its own).
        fetch_day: Callback that returns a fully pre-fetched
            ``DayInput`` for one date. Raising from this callback (or
            from anything during that day's processing) is caught and
            recorded as a ``DayFailure``, not propagated.
        strike_gap: The distance between adjacent tradable strikes.
        num_strikes: How many strikes to include on each side of ATM.

    Returns:
        A ``MultiDayResult`` with every successfully processed day's
        report, every trade, every rejected signal, every level's
        final state, every failure, and the overall summary.
    """
    daily_reports: List[DailyReport] = []
    all_trades: List[Trade] = []
    all_rejected: List[Tuple[date, RejectedSignal]] = []
    all_levels: List[Tuple[date, LevelRecord]] = []
    failures: List[DayFailure] = []

    for session_date in session_dates:
        try:
            day = fetch_day(session_date)
            report, trades, rejected, levels = _run_single_day(day, strike_gap, num_strikes)
            daily_reports.append(report)
            all_trades.extend(trades)
            all_rejected.extend((session_date, r) for r in rejected)
            all_levels.extend((session_date, l) for l in levels)
            logger.info("Day %s complete: %d trades, net_pnl=%.2f",
                        session_date, report.trades, report.net_pnl)
        except Exception as exc:
            failures.append(DayFailure(
                session_date=session_date, reason=str(exc),
                exception_text=traceback.format_exc(),
            ))
            logger.error("Day %s FAILED: %s", session_date, exc)

    overall = _summarize_overall(daily_reports)
    return MultiDayResult(
        daily_reports=daily_reports, all_trades=all_trades,
        rejected_signals=all_rejected, level_records=all_levels,
        failures=failures, overall=overall,
    )


def _summarize_overall(reports: List[DailyReport]) -> OverallSummary:
    """Compute the Overall Summary from every successfully processed day."""
    if not reports:
        return OverallSummary(
            trading_days=0, total_trades=0, overall_win_rate_pct=0.0,
            total_gross_profit=0.0, total_gross_loss=0.0, net_pnl=0.0,
            average_trades_per_day=0.0, average_daily_pnl=0.0, max_daily_drawdown=0.0,
            best_day=None, best_day_pnl=None, worst_day=None, worst_day_pnl=None,
        )

    total_trades = sum(r.trades for r in reports)
    total_wins = sum(r.wins for r in reports)
    total_gross_profit = sum(r.gross_profit for r in reports)
    total_gross_loss = sum(r.gross_loss for r in reports)
    best = max(reports, key=lambda r: r.net_pnl)
    worst = min(reports, key=lambda r: r.net_pnl)

    return OverallSummary(
        trading_days=len(reports),
        total_trades=total_trades,
        overall_win_rate_pct=(total_wins / total_trades * 100.0) if total_trades else 0.0,
        total_gross_profit=total_gross_profit,
        total_gross_loss=total_gross_loss,
        net_pnl=total_gross_profit + total_gross_loss,
        average_trades_per_day=total_trades / len(reports),
        average_daily_pnl=sum(r.net_pnl for r in reports) / len(reports),
        max_daily_drawdown=max(r.max_drawdown for r in reports),
        best_day=best.session_date, best_day_pnl=best.net_pnl,
        worst_day=worst.session_date, worst_day_pnl=worst.net_pnl,
    )


def export_to_excel(result: MultiDayResult, path: Union[str, Path]) -> Path:
    """Export a ``MultiDayResult`` to the 5-sheet workbook, per specification.

    Args:
        result: The result to export.
        path: Destination ``.xlsx`` path. Overwritten if it exists.

    Returns:
        The ``Path`` written to.
    """
    path = Path(path)
    wb = Workbook()

    daily = wb.active
    daily.title = "Daily Summary"
    daily.append(["Date", "Trades", "Wins", "Losses", "Win Rate %", "Gross Profit",
                  "Gross Loss", "Net PnL", "Max Drawdown", "Open At Close",
                  "Rejected Signals", "Completed Levels", "Unused Levels"])
    for r in result.daily_reports:
        daily.append([r.session_date.isoformat(), r.trades, r.wins, r.losses,
                      round(r.win_rate_pct, 2), r.gross_profit, r.gross_loss, r.net_pnl,
                      r.max_drawdown, r.open_positions_at_close, r.rejected_signals,
                      r.completed_mapped_levels, r.unused_mapped_levels])

    trades_sheet = wb.create_sheet("All Trades")
    trades_sheet.append(["Date", "Time", "Side", "Entry", "Exit", "Reason",
                          "Target", "Stop Loss", "PnL"])
    for t in result.all_trades:
        trades_sheet.append([t.trade_date.isoformat(), t.trade_time.isoformat(), t.side.value,
                              t.entry, t.exit, t.reason, t.target, t.stop_loss, t.pnl])

    levels_sheet = wb.create_sheet("Mapped Level Statistics")
    levels_sheet.append(["Date", "Strike", "Anchor", "Side", "Final State"])
    for session_date, rec in result.level_records:
        levels_sheet.append([session_date.isoformat(), rec.strike, rec.anchor.value,
                              rec.side.value, rec.final_state.value])

    rejected_sheet = wb.create_sheet("Rejected Signals")
    rejected_sheet.append(["Date", "Time", "Strike", "Side", "Anchor", "Reason"])
    for session_date, rej in result.rejected_signals:
        rejected_sheet.append([session_date.isoformat(), rej.timestamp.isoformat(),
                                rej.strike, rej.side.value, rej.anchor.value, rej.reason])

    validation_sheet = wb.create_sheet("Validation Summary")
    validation_sheet.append(["Metric", "Value"])
    o = result.overall
    validation_sheet.append(["Trading days processed", o.trading_days])
    validation_sheet.append(["Days failed", len(result.failures)])
    validation_sheet.append(["Total trades", o.total_trades])
    validation_sheet.append(["Overall win rate %", round(o.overall_win_rate_pct, 2)])
    validation_sheet.append(["Total gross profit", o.total_gross_profit])
    validation_sheet.append(["Total gross loss", o.total_gross_loss])
    validation_sheet.append(["Net PnL", o.net_pnl])
    validation_sheet.append(["Average trades per day", round(o.average_trades_per_day, 2)])
    validation_sheet.append(["Average daily PnL", round(o.average_daily_pnl, 2)])
    validation_sheet.append(["Max daily drawdown", o.max_daily_drawdown])
    validation_sheet.append(["Best day", o.best_day.isoformat() if o.best_day else ""])
    validation_sheet.append(["Best day PnL", o.best_day_pnl])
    validation_sheet.append(["Worst day", o.worst_day.isoformat() if o.worst_day else ""])
    validation_sheet.append(["Worst day PnL", o.worst_day_pnl])
    validation_sheet.append([])
    validation_sheet.append(["Failed Date", "Reason"])
    for f in result.failures:
        validation_sheet.append([f.session_date.isoformat(), f.reason])

    wb.save(path)
    logger.info("Exported multi-day backtest to %s", path)
    return path

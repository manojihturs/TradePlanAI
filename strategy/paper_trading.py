"""Module 6: Paper Trading Engine.

Single responsibility: record completed trades and export them to
Excel. This module NEVER places a real order and contains NO broker
or network code of any kind - it only turns a Module 5 ``ClosedTrade``
(plus the ``ExitLevels`` that produced it) into a stored ``Trade``
record, and writes accumulated records to an Excel workbook.

This module does not detect entries (Module 3), does not decide exits
(Module 4), and does not track open/flat state (Module 5) - it only
records what already happened.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import List, Union

from openpyxl import Workbook

from strategy.entry_signal import TradeSide
from strategy.exit_signal import ExitLevels
from strategy.position_manager import ClosedTrade

logger = logging.getLogger(__name__)

#: Column order for the exported Excel sheet - fixed, so downstream
#: readers can rely on column position, not just header text.
_COLUMNS = ("Date", "Time", "Side", "Entry", "Exit", "Reason", "Target", "Stop Loss", "PnL")


class PaperTradingError(Exception):
    """Raised when a trade cannot be recorded or exported.

    Distinguished from generic exceptions so callers can catch paper-
    trading failures specifically without swallowing unrelated bugs.
    """


@dataclass(frozen=True)
class Trade:
    """One completed paper trade - a plain record, per specification.

    Attributes:
        trade_date: The calendar date the trade was entered on.
        trade_time: The time of day the trade was entered.
        side: TradeSide.CE or TradeSide.PE.
        entry: The entry price.
        exit: The exit price.
        reason: The exit reason, as text ("TARGET" or "STOP_LOSS").
        target: The Target level this trade was managed against.
        stop_loss: The Mapped Stop Loss this trade was managed against.
        pnl: exit - entry, in premium points.
    """

    trade_date: date
    trade_time: time
    side: TradeSide
    entry: float
    exit: float
    reason: str
    target: float
    stop_loss: float
    pnl: float


def build_trade(closed: ClosedTrade, exit_levels: ExitLevels) -> Trade:
    """Build a ``Trade`` record from a Module 5 ``ClosedTrade``.

    Args:
        closed: The completed round trip (entry + exit) from
            ``PositionManager.process_candle``.
        exit_levels: The ``ExitLevels`` (Module 4) that were in effect
            for this position - not stored on ``ClosedTrade`` itself,
            so it must be supplied by the caller, which has it from
            ``PositionManager.current_position`` before the position
            closed.

    Returns:
        A frozen ``Trade`` record ready to store/export.
    """
    entry_price = (closed.entry.ce_level if closed.entry.side is TradeSide.CE
                   else closed.entry.pe_level)
    pnl = closed.exit.exit_price - entry_price

    return Trade(
        trade_date=closed.entry.timestamp.date(),
        trade_time=closed.entry.timestamp.time(),
        side=closed.entry.side,
        entry=entry_price,
        exit=closed.exit.exit_price,
        reason=closed.exit.reason.value,
        target=exit_levels.target,
        stop_loss=exit_levels.stop_loss,
        pnl=pnl,
    )


class PaperTradingEngine:
    """Records completed trades in memory and exports them to Excel.

    Never places a real order and never talks to a broker or the
    network - see module docstring. Purely an in-memory ledger plus a
    file writer.
    """

    def __init__(self) -> None:
        """Initialize the engine with an empty trade ledger."""
        self._trades: List[Trade] = []
        logger.info("PaperTradingEngine initialized: 0 trades recorded")

    @property
    def trades(self) -> List[Trade]:
        """A copy of every trade recorded so far, in recording order."""
        return list(self._trades)

    def record_trade(self, closed: ClosedTrade, exit_levels: ExitLevels) -> Trade:
        """Build and store a ``Trade`` record for a completed round trip.

        Args:
            closed: The completed round trip from
                ``PositionManager.process_candle``.
            exit_levels: The ``ExitLevels`` that were in effect for
                this position (see ``build_trade``).

        Returns:
            The stored ``Trade`` record.
        """
        trade = build_trade(closed, exit_levels)
        self._trades.append(trade)
        logger.info(
            "Trade recorded: %s %s entry=%.2f exit=%.2f reason=%s pnl=%.2f",
            trade.trade_date, trade.side.value, trade.entry, trade.exit,
            trade.reason, trade.pnl,
        )
        return trade

    def export_to_excel(self, path: Union[str, Path]) -> Path:
        """Export every recorded trade to a new Excel workbook.

        Args:
            path: Destination file path (``.xlsx``). Overwritten if it
                already exists.

        Returns:
            The ``Path`` the workbook was written to.

        Raises:
            PaperTradingError: if the file cannot be written (e.g. the
                destination directory does not exist, or the path is
                not writable).
        """
        path = Path(path)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Paper Trades"
        sheet.append(list(_COLUMNS))

        for trade in self._trades:
            sheet.append([
                trade.trade_date.isoformat(),
                trade.trade_time.isoformat(),
                trade.side.value,
                trade.entry,
                trade.exit,
                trade.reason,
                trade.target,
                trade.stop_loss,
                trade.pnl,
            ])

        try:
            workbook.save(path)
        except OSError as exc:
            raise PaperTradingError(f"failed to write Excel file to {path}: {exc}") from exc

        logger.info("Exported %d trade(s) to %s", len(self._trades), path)
        return path

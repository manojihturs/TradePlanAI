"""TradeRecord / TradeHistory: the completed-trade archive.

Traceability
------------
Field list is this sprint's own instruction. ``exit_strike`` and
``duration`` are mechanical derivations from an already-closed
:class:`~models.trade_position.TradePosition`, not new business
rules:

- ``exit_strike`` = ``target_level`` if ``exit_reason`` is
  ``TARGET_HIT`` (the trade exited at the target strike's own
  reference level, Specification Rule 2); ``competitor_monitor_strike``
  if ``COMPETITOR_HIT`` (exited at the competitor strike's own
  reference level, same rule); otherwise ``entry_strike`` (Stop
  Loss/Trailing Stop exits happen on the entry contract itself - no
  strike migration is described anywhere in the Specification for
  those two conditions).
- ``duration`` = ``closed_at - opened_at``, arithmetic only.

``winner`` duplicates ``direction`` (both = the entry side that
triggered the originating Winner event) - the sprint's own field list
names both separately; since no distinct "Winner" concept exists
beyond entry side anywhere in the Specification, this module does not
invent a different value for it, and documents the duplication
plainly rather than silently resolving it one way.

PnL: **NOT calculated**. ``TradeRecord.pnl`` is always ``None`` -
Specification Section 20 gives no P&L/scoring formula anywhere (see
``research/architecture/IMPLEMENTATION_ROADMAP.md`` Phase 12's own
note on this same gap). ``None`` is used rather than ``Decimal(0)``
so "not computed" is never confused with "computed as break-even."
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from core.enums import ExitReason, TradeDirection
from core.exceptions import ValidationError
from models.trade_position import TradePosition


@dataclass(frozen=True, slots=True)
class TradeRecord:
    """An immutable record of one completed trade.

    Attributes:
        trade_id: The trade's own identifier.
        direction: The entry side (CE or PE).
        winner: The winning side that triggered entry - duplicates
            ``direction``; see module docstring.
        entry_strike: The strike entered.
        exit_strike: The strike at which the trade exited (see module
            docstring for the derivation rule per exit reason).
        entry_time: When the trade was opened.
        exit_time: When the trade was closed.
        exit_reason: Why the trade closed.
        duration: ``exit_time - entry_time``.
        target_strike: The trade's Target strike (Specification Rule
            2).
        support_strike: The trade's Support strike (Specification
            Rule 2).
        competitor_exit_strike: The trade's Competitor Exit strike
            (Specification Rule 2).
        pnl: Always ``None`` - PnL calculation is not implemented.
    """

    trade_id: uuid.UUID
    direction: TradeDirection
    winner: TradeDirection
    entry_strike: Decimal
    exit_strike: Decimal
    entry_time: datetime
    exit_time: datetime
    exit_reason: ExitReason
    duration: timedelta
    target_strike: Decimal
    support_strike: Decimal
    competitor_exit_strike: Decimal
    pnl: Decimal | None = None

    def __post_init__(self) -> None:
        if self.trade_id is None:
            raise ValidationError("TradeRecord.trade_id must not be None.")
        if self.duration < timedelta(0):
            raise ValidationError("TradeRecord.duration must not be negative.")

    @classmethod
    def from_position(cls, position: TradePosition) -> TradeRecord:
        """Build a :class:`TradeRecord` from a closed
        :class:`~models.trade_position.TradePosition`.

        Raises:
            ValidationError: if ``position`` is still active.
        """
        if position.is_active():
            raise ValidationError("Cannot build a TradeRecord from an active TradePosition.")
        assert position.exit_reason is not None
        assert position.closed_at is not None

        if position.exit_reason is ExitReason.TARGET_HIT:
            exit_strike = position.target_level
        elif position.exit_reason is ExitReason.COMPETITOR_HIT:
            exit_strike = position.competitor_monitor_strike
        else:
            exit_strike = position.entry_strike

        return cls(
            trade_id=position.trade_id,
            direction=position.entry_side,
            winner=position.entry_side,
            entry_strike=position.entry_strike,
            exit_strike=exit_strike,
            entry_time=position.opened_at,
            exit_time=position.closed_at,
            exit_reason=position.exit_reason,
            duration=position.closed_at - position.opened_at,
            target_strike=position.target_level,
            support_strike=position.support_level,
            competitor_exit_strike=position.competitor_monitor_strike,
            pnl=None,
        )


class TradeHistory:
    """Maintains the archive of completed trades.

    No global state - each instance owns its own private list.
    """

    def __init__(self) -> None:
        self._trades: list[TradeRecord] = []

    def add_trade(self, position: TradePosition) -> TradeRecord:
        """Build a :class:`TradeRecord` from ``position`` and add it
        to the archive.

        Raises:
            ValidationError: if ``position`` is still active.
        """
        record = TradeRecord.from_position(position)
        self._trades.append(record)
        return record

    def get_trade(self, trade_id: uuid.UUID) -> TradeRecord | None:
        """The record for ``trade_id``, or ``None`` if not found."""
        for record in self._trades:
            if record.trade_id == trade_id:
                return record
        return None

    def get_all(self) -> tuple[TradeRecord, ...]:
        """Every recorded trade, in the order added."""
        return tuple(self._trades)

    def filter_by_direction(self, direction: TradeDirection) -> tuple[TradeRecord, ...]:
        """Every recorded trade with the given ``direction``."""
        return tuple(record for record in self._trades if record.direction is direction)

    def filter_by_date(self, trade_date: date) -> tuple[TradeRecord, ...]:
        """Every recorded trade whose ``entry_time`` falls on
        ``trade_date``."""
        return tuple(record for record in self._trades if record.entry_time.date() == trade_date)

    def clear(self) -> None:
        """Discard every recorded trade."""
        self._trades = []

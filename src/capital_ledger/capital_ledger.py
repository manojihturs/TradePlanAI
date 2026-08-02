"""CapitalLedger: tracks realized P&L against a starting capital
balance, for the live paper-trading harness.

Traceability
------------
Product Owner-confirmed sizing (2026-08-02, chat): "Fixed 1 lot per
trade, Top+Bottom independent" - capital is tracked/reported, not a
gating constraint (the alternative, capital-gated sizing, was
explicitly declined). This ledger therefore never blocks a trade; it
only records realized P&L after the fact.

Lot size: 65 - not invented. Matches the already-working legacy
``orb_common.py``'s own ``LOT_SIZE`` default (`ORB_LOT_SIZE` env var,
default "65") and independently corroborated by the Product Owner's
own manually-traded log, where every row's own "Total" column equals
"Captured points x 65" exactly (self-verifying arithmetic found and
recorded in ``research/evidence_log.md``, 2026-07-31 entry).

P&L formula: (exit_price - entry_level) * lot_size - matches this
project's own already-confirmed reading that both CE and PE positions
are long the premium bought at entry (never short), so Target/Stop
Loss/Competitor Exit are always numerically above/below entry
respectively regardless of side - no side-based sign flip needed (see
``research/scratch_backtest_last_week.py``'s own comment for the
worked-through reasoning).

A ``SESSION_END``-closed :class:`~models.qualified_position.QualifiedPosition`
has ``exit_price is None`` (no real fill occurred) - :meth:`record_position`
is a no-op for those, matching that field's own documented meaning.
"""

from __future__ import annotations

from decimal import Decimal

from core.exceptions import ValidationError
from models.qualified_position import QualifiedPosition

DEFAULT_LOT_SIZE = 65


class CapitalLedger:
    """Tracks realized P&L in rupees against a starting capital
    balance.

    Constructor-injected starting capital/lot size only - no globals,
    no singletons. Stateful across calls by design (accumulates
    realized P&L) - construct a fresh instance per trading session.
    """

    def __init__(self, starting_capital: Decimal, lot_size: int = DEFAULT_LOT_SIZE) -> None:
        if starting_capital <= 0:
            raise ValidationError("CapitalLedger.starting_capital must be greater than 0.")
        if lot_size <= 0:
            raise ValidationError("CapitalLedger.lot_size must be greater than 0.")
        self._starting_capital = starting_capital
        self._lot_size = lot_size
        self._realized_pnl = Decimal(0)
        self._trade_count = 0

    @property
    def starting_capital(self) -> Decimal:
        return self._starting_capital

    @property
    def lot_size(self) -> int:
        return self._lot_size

    @property
    def realized_pnl(self) -> Decimal:
        """Cumulative realized P&L in rupees across every recorded
        trade so far this session."""
        return self._realized_pnl

    @property
    def balance(self) -> Decimal:
        """Current capital: starting capital plus realized P&L so
        far. Never gates new trades - see module docstring."""
        return self._starting_capital + self._realized_pnl

    @property
    def trade_count(self) -> int:
        """How many trades have been recorded so far (SESSION_END
        closes with no fill are not counted)."""
        return self._trade_count

    def record_close(self, entry_level: Decimal, exit_price: Decimal) -> Decimal:
        """Record one closed trade's realized P&L and update the
        running balance.

        Returns:
            This trade's own P&L in rupees (captured premium points
            times lot size).
        """
        captured_points = exit_price - entry_level
        pnl_rupees = captured_points * self._lot_size
        self._realized_pnl += pnl_rupees
        self._trade_count += 1
        return pnl_rupees

    def record_position(self, position: QualifiedPosition) -> Decimal | None:
        """Record a closed :class:`~models.qualified_position.QualifiedPosition`'s
        P&L directly.

        Returns:
            This trade's P&L in rupees, or ``None`` if ``position``
            closed via SESSION_END (no real fill, nothing to record -
            see module docstring).

        Raises:
            core.exceptions.ValidationError: if ``position`` is still
                active (not yet closed).
        """
        if position.is_active():
            raise ValidationError(
                "CapitalLedger.record_position requires a closed QualifiedPosition."
            )
        if position.exit_price is None:
            return None
        return self.record_close(position.entry_level, position.exit_price)

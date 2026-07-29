"""ExitEngine: evaluates the four confirmed exit conditions.

Traceability
------------
Specification Section 11: "Exit when: Target Hit OR Competitor Strike
Reference Level Hit OR Stop Loss OR Trailing Stop." Rule 2 (v1.1,
CONFIRMED) already gives the Target/Competitor-Exit strike mapping;
that computation lives in
``position_manager.position_manager.PositionManager`` (Sprint 2) and
is read directly off the active :class:`~models.trade_position.TradePosition`
here - this module deliberately does not duplicate it, per this
sprint's own "Do NOT create another Competitor Engine" instruction.

Stop Loss and Trailing Stop are **not implemented** here (Specification
Section 20 items 4, 9-10, still MISSING INFORMATION). This engine
only calls the injected
:class:`~interfaces.stop_loss_engine.StopLossEngine`/
:class:`~interfaces.trailing_stop_engine.TrailingStopEngine`
``check()`` methods and uses whatever boolean they return - it
contains no SL/trailing-stop logic of its own. Until those interfaces
have real implementations, injecting the Sprint 1 stub
implementations (which always raise
:class:`~core.exceptions.UnresolvedBusinessRuleError`) will propagate
that exception on every evaluation; a caller that wants to run
without them must inject a test double that returns ``False``.

No :class:`~core.events.TradeClosedEvent` is published directly by
this module - closing a position already does that, transitively,
via :meth:`trade_manager.trade_manager.TradeManager.close` (reused
unmodified through
:meth:`position_manager.position_manager.PositionManager.close_position`).
Publishing it again here would duplicate the event.

Exit-condition precedence when multiple conditions are met on the
same evaluation is Specification Section 20 item 11, still MISSING
INFORMATION. This engine checks them in the literal order this
sprint's own instructions list them - Target, then Competitor, then
Stop Loss, then Trailing Stop - and returns on the first one that is
true. This is an engineering default for a genuinely simultaneous
case, not a resolution of that gap.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from core.enums import ExitReason, TradeDirection
from core.exceptions import ValidationError
from interfaces.stop_loss_engine import StopLossEngine
from interfaces.trailing_stop_engine import TrailingStopEngine
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from models.trade_position import TradePosition
from position_manager.position_manager import PositionManager
from trade_history.trade_history import TradeHistory


class ExitEngine:
    """Monitors the active position and closes it on Target,
    Competitor, Stop Loss, or Trailing Stop.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(
        self,
        position_manager: PositionManager,
        reference_levels: tuple[ReferenceLevel, ...],
        stop_loss_engine: StopLossEngine,
        trailing_stop_engine: TrailingStopEngine,
        trade_history: TradeHistory | None = None,
    ) -> None:
        self._position_manager = position_manager
        self._reference_levels = reference_levels
        self._stop_loss_engine = stop_loss_engine
        self._trailing_stop_engine = trailing_stop_engine
        self._trade_history = trade_history

    def evaluate(
        self,
        candle_timestamp: datetime,
        target_snapshot: MarketSnapshot,
        competitor_snapshot: MarketSnapshot,
    ) -> TradePosition | None:
        """Evaluate the four exit conditions against the currently
        active position, closing it on the first one that is met.

        Args:
            candle_timestamp: The candle being evaluated (currently
                unused in the exit test itself - accepted for
                symmetry with :class:`~winner_engine.winner_engine.WinnerEngine`
                and for future use once Stop Loss/Trailing Stop are
                resolved).
            target_snapshot: The entry side's contract at the Target
                strike, for this candle.
            competitor_snapshot: The competitor side's contract at
                the Competitor Exit strike, for this candle.

        Returns:
            The now-closed position if any condition was met;
            ``None`` if no trade is active or none of the conditions
            were met.
        """
        position = self._position_manager.current_position()
        if position is None:
            return None

        _ = candle_timestamp  # accepted for interface symmetry only - see docstring

        competitor_side = (
            TradeDirection.PE if position.entry_side is TradeDirection.CE else TradeDirection.CE
        )

        if self._touches(target_snapshot, position.target_level, position.entry_side):
            return self._close(ExitReason.TARGET_HIT)

        if self._touches(competitor_snapshot, position.competitor_monitor_strike, competitor_side):
            return self._close(ExitReason.COMPETITOR_HIT)

        if self._stop_loss_engine.check(position, target_snapshot):
            return self._close(ExitReason.STOP_LOSS)

        if self._trailing_stop_engine.check(position, target_snapshot):
            return self._close(ExitReason.TRAILING_STOP)

        return None

    def _close(self, reason: ExitReason) -> TradePosition:
        closed = self._position_manager.close_position(reason)
        if self._trade_history is not None:
            self._trade_history.add_trade(closed)
        return closed

    def _touches(self, snapshot: MarketSnapshot, strike: Decimal, side: TradeDirection) -> bool:
        level = self._level_for(strike)
        if not snapshot.is_candle():
            raise ValidationError(
                "ExitEngine requires candle-mode snapshots (OHLC) to evaluate touches."
            )
        assert snapshot.low is not None and snapshot.high is not None
        high, low = (
            (level.ce_high, level.ce_low)
            if side is TradeDirection.CE
            else (level.pe_high, level.pe_low)
        )
        return snapshot.low <= high <= snapshot.high or snapshot.low <= low <= snapshot.high

    def _level_for(self, strike: Decimal) -> ReferenceLevel:
        for level in self._reference_levels:
            if level.strike == strike:
                return level
        raise ValidationError(
            f"No ReferenceLevel found for strike {strike} in the injected ladder."
        )

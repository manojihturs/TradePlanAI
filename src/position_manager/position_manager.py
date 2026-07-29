"""PositionManager: computes Target/Support/Competitor-Exit strikes
and delegates single-active-trade enforcement to TradeManager.

Traceability
------------
Specification Rule 2 (v1.1, CONFIRMED) - the only business rule this
module encodes:

    Winner CE: Entry = S, Target = CE(S+1), Support = CE(S-1),
               Competitor Exit = PE(S-1)
    Winner PE: Entry = S, Target = PE(S-1), Support = PE(S+1),
               Competitor Exit = CE(S+1)

Where S+1/S-1 mean "the next strike up/down in the reference-level
ladder" - a purely mechanical adjacency lookup over an already-built
``tuple[ReferenceLevel, ...]``, not a step-size computation (ladder
step size itself remains MISSING INFORMATION, Specification Section
20 item 14, and is not needed here).

Tracks: Entry, Direction, Entry Strike, Target Strike, Support
Strike, Competitor Exit Strike, Current Status, Entry Time, Exit
Time - all of which are exactly ``models.trade_position.TradePosition``'s
own fields; this module builds that model and hands the
single-active-trade decision to the injected
``trade_manager.trade_manager.TradeManager`` (Sprint 1, unmodified).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.enums import ExitReason, TradeDirection
from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel
from models.trade_position import TradePosition
from trade_manager.trade_manager import TradeManager


class PositionManager:
    """Builds a :class:`~models.trade_position.TradePosition` from an
    entry strike/side and a reference-level ladder, then hands it to
    an injected :class:`~trade_manager.trade_manager.TradeManager`
    for the single-active-trade gate.

    Constructor-injected dependency, no globals/singletons.
    """

    def __init__(self, trade_manager: TradeManager) -> None:
        self._trade_manager = trade_manager

    def current_position(self) -> TradePosition | None:
        """The currently active position, or ``None`` if none is
        open. Delegates to the injected ``TradeManager``."""
        return self._trade_manager.active_position()

    def is_active(self) -> bool:
        """Whether a trade is currently active."""
        return self._trade_manager.is_trade_active()

    def open_position(
        self,
        trade_id: uuid.UUID,
        entry_strike: Decimal,
        entry_side: TradeDirection,
        opened_at: datetime,
        reference_levels: tuple[ReferenceLevel, ...],
    ) -> TradePosition | None:
        """Build a :class:`TradePosition` for ``entry_strike``/``entry_side``
        (Target/Support/Competitor-Exit computed per Specification
        Rule 2) and attempt to open it.

        Returns the opened position, or ``None`` if a trade was
        already active (Specification Rule 4 - the attempt is
        discarded, not queued; see
        :meth:`trade_manager.trade_manager.TradeManager.open`).

        Raises:
            ValidationError: if ``entry_strike`` is not present in
                ``reference_levels``, or has no adjacent strike on
                the required side of the ladder.
        """
        target, support, competitor_exit = self._compute_levels(
            entry_strike, entry_side, reference_levels
        )
        position = TradePosition(
            trade_id=trade_id,
            entry_strike=entry_strike,
            entry_side=entry_side,
            target_level=target,
            support_level=support,
            competitor_monitor_strike=competitor_exit,
            opened_at=opened_at,
        )
        return self._trade_manager.open(position)

    def close_position(self, reason: ExitReason) -> TradePosition:
        """Close the active trade. Delegates to the injected
        ``TradeManager``.

        Raises:
            core.exceptions.TradeManagerError: if no trade is
                currently active.
        """
        return self._trade_manager.close(reason)

    @staticmethod
    def _compute_levels(
        entry_strike: Decimal,
        entry_side: TradeDirection,
        reference_levels: tuple[ReferenceLevel, ...],
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Return ``(target, support, competitor_exit)`` per
        Specification Rule 2."""
        sorted_strikes = sorted({level.strike for level in reference_levels})
        try:
            index = sorted_strikes.index(entry_strike)
        except ValueError as exc:
            raise ValidationError(
                f"entry_strike {entry_strike} is not present in the supplied reference_levels."
            ) from exc
        if index + 1 >= len(sorted_strikes) or index - 1 < 0:
            raise ValidationError(
                f"entry_strike {entry_strike} has no adjacent strike(s) in the ladder "
                "required for Target/Support/Competitor-Exit mapping."
            )

        strike_plus_1 = sorted_strikes[index + 1]
        strike_minus_1 = sorted_strikes[index - 1]

        if entry_side is TradeDirection.CE:
            # Target = CE(S+1), Support = CE(S-1), Competitor Exit = PE(S-1)
            return strike_plus_1, strike_minus_1, strike_minus_1
        # Winner PE: Target = PE(S-1), Support = PE(S+1), Competitor Exit = CE(S+1)
        return strike_minus_1, strike_plus_1, strike_plus_1

"""QualificationExitEngine: ongoing exit monitoring for a
Qualification-Engine-derived position.

Traceability
------------
Sprint 11. Checks the active
:class:`~models.qualified_position.QualifiedPosition` against a
candle for its own side (Target/Stop Loss) and the opposite side
(Competitor Exit) - all three are already-confirmed concrete premium
values on the position itself
(``qualification_engine.qualification_engine.QualificationEngine``'s
own docstring has the full evidence trail), so unlike
``exit_engine.exit_engine.ExitEngine`` no reference-level re-lookup
by strike is needed here.

Checked in this order: Target, Competitor Exit, Stop Loss, Trailing
Stop. Precedence when multiple conditions are met on the same candle
is not confirmed by any evidence (mirrors
``exit_engine.exit_engine.ExitEngine``'s own documented gap for this
exact question, Specification Section 20 item 11) - this is an
engineering default for a genuinely simultaneous case, not a
resolution of that gap.

Trailing Stop is checked via an injected
:class:`~qualification_engine.qualification_trailing_stop.QualificationTrailingStop`
- see that module's own docstring for why it remains a null object
pending further evidence.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from core.enums import ExitReason
from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.qualified_position import QualifiedPosition
from qualification_engine.qualification_position_manager import QualificationPositionManager
from qualification_engine.qualification_trailing_stop import QualificationTrailingStop


class QualificationExitEngine:
    """Evaluates the active :class:`~models.qualified_position.QualifiedPosition`
    against one candle, closing it if any confirmed exit condition is
    met.

    Constructor-injected collaborators only - no globals, no
    singletons, matching every other engine in this codebase.
    """

    def __init__(
        self,
        position_manager: QualificationPositionManager,
        trailing_stop: QualificationTrailingStop,
    ) -> None:
        self._position_manager = position_manager
        self._trailing_stop = trailing_stop

    def evaluate(
        self,
        candle_timestamp: datetime,
        own_snapshot: MarketSnapshot,
        competitor_snapshot: MarketSnapshot,
    ) -> QualifiedPosition | None:
        """Evaluate the active position (if any) against this
        candle, closing it and returning the closed position if any
        exit condition is met, else returning ``None``.

        Args:
            candle_timestamp: This candle's timestamp (unused
                directly - :class:`QualificationPositionManager`'s own
                clock stamps ``closed_at`` - kept for symmetry with
                ``exit_engine.exit_engine.ExitEngine``'s own
                signature and for future use, e.g. session-boundary
                orchestration).
            own_snapshot: The position's own side's candle for this
                timestamp.
            competitor_snapshot: The opposite side's candle for this
                timestamp.

        Raises:
            core.exceptions.ValidationError: if either snapshot is
                not candle-mode (OHLC), or no trade is currently
                active.
        """
        position = self._position_manager.active_position()
        if position is None:
            raise ValidationError("QualificationExitEngine.evaluate() requires an active trade.")
        if not own_snapshot.is_candle() or not competitor_snapshot.is_candle():
            raise ValidationError(
                "QualificationExitEngine requires candle-mode snapshots (OHLC) to evaluate exits."
            )

        if self._touches(own_snapshot, position.target_level):
            return self._position_manager.close(ExitReason.TARGET_HIT)
        if self._touches(competitor_snapshot, position.competitor_exit_level):
            return self._position_manager.close(ExitReason.COMPETITOR_HIT)
        if self._touches(own_snapshot, position.stop_loss_level):
            return self._position_manager.close(ExitReason.STOP_LOSS)
        if self._trailing_stop.check(position, own_snapshot):
            return self._position_manager.close(ExitReason.TRAILING_STOP)
        _ = candle_timestamp  # unused directly - see docstring
        return None

    @staticmethod
    def _touches(snapshot: MarketSnapshot, level: Decimal) -> bool:
        assert snapshot.low is not None and snapshot.high is not None
        return snapshot.low <= level <= snapshot.high

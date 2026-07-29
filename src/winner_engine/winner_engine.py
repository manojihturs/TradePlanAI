"""WinnerEngine: detects same-candle CE/PE reference-level touches.

Traceability
------------
Specification Section 9: "Winner is evaluated candle by candle. If CE
touches any one of its reference levels AND PE touches any one of its
reference levels during the SAME candle, then one side wins, the
opposite side loses. Winner immediately generates Entry Signal."

Rule 3 (v1.1, CONFIRMED): "Multiple winner scenarios do not occur. Do
not invent tie-break logic." This engine therefore does not attempt to
choose a winner when both sides genuinely touch in the same
evaluation - it raises :class:`~core.exceptions.AmbiguousWinnerError`
instead, treating the documented-impossible case as a defensive
assertion failure rather than a silently-guessed outcome.

"Touches" is defined mechanically: a reference level is touched if it
falls within the evaluated candle's ``[low, high]`` range - the
conventional definition of a price level being reached within a bar,
not a business threshold invented for this strategy.

Which strike(s)' CE/PE are in scope for evaluation is Specification
Section 9's own open question (not resolved by Rule 3) - this engine
is therefore deliberately strike-agnostic: :meth:`WinnerEngine.evaluate`
takes one strike's :class:`~models.reference_level.ReferenceLevel`
and its CE/PE snapshots per call; the caller decides which strike(s)
to evaluate.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.enums import TradeDirection
from core.events import WinnerDetectedEvent
from core.exceptions import AmbiguousWinnerError, ValidationError
from core.protocols import Clock, EventBusProtocol, IdFactory
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel


class WinnerEngine:
    """Evaluates, for one strike on one candle, whether its CE and/or
    PE contract touched their own reference levels, and publishes
    :class:`~core.events.WinnerDetectedEvent` if exactly one side did.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(
        self,
        bus: EventBusProtocol,
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._bus = bus
        self._clock: Clock = clock if clock is not None else datetime.now
        self._id_factory: IdFactory = id_factory if id_factory is not None else uuid.uuid4

    def evaluate(
        self,
        session_id: uuid.UUID,
        candle_timestamp: datetime,
        strike: Decimal,
        level: ReferenceLevel,
        ce_snapshot: MarketSnapshot,
        pe_snapshot: MarketSnapshot,
    ) -> WinnerDetectedEvent | None:
        """Evaluate one strike's CE/PE snapshots against its
        :class:`ReferenceLevel` for this candle.

        Returns the published :class:`~core.events.WinnerDetectedEvent`
        if exactly one side touched its reference level(s); ``None``
        if neither touched.

        Raises:
            ValidationError: if ``ce_snapshot``/``pe_snapshot`` are
                not candle-mode (no OHLC), since a "touch" cannot be
                evaluated from a single tick price alone.
            AmbiguousWinnerError: if both CE and PE genuinely touched
                their reference levels on this candle - a scenario
                Specification Rule 3 states does not occur; see
                module docstring.
        """
        ce_touched = self._touches_any(ce_snapshot, level.ce_high, level.ce_low)
        pe_touched = self._touches_any(pe_snapshot, level.pe_high, level.pe_low)

        if ce_touched and pe_touched:
            raise AmbiguousWinnerError(
                f"Both CE and PE touched their reference levels for strike {strike} "
                f"on candle {candle_timestamp} - Specification Rule 3 states this "
                "does not occur; no tie-break logic exists to resolve it."
            )
        if ce_touched:
            winning_side = TradeDirection.CE
        elif pe_touched:
            winning_side = TradeDirection.PE
        else:
            return None

        event = WinnerDetectedEvent(
            event_id=self._id_factory(),
            occurred_at=self._clock(),
            session_id=session_id,
            candle_timestamp=candle_timestamp,
            winning_side=winning_side,
            winning_strike=strike,
        )
        self._bus.publish(event)
        return event

    @staticmethod
    def _touches_any(snapshot: MarketSnapshot, *levels: Decimal) -> bool:
        if not snapshot.is_candle():
            raise ValidationError(
                "WinnerEngine requires candle-mode snapshots (OHLC) to evaluate touches."
            )
        assert snapshot.low is not None and snapshot.high is not None
        return any(snapshot.low <= level <= snapshot.high for level in levels)

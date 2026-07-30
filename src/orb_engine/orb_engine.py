"""ORBEngine: computes Opening Range Breakout classification.

Traceability
------------
Opening High/Low are read directly from ``level`` (the strike's
already-built, Rule-1-CONFIRMED first-5-minute CE/PE values) - this
engine performs no extraction of its own, matching
``weekly_future.weekly_future_calculator.WeeklyFutureCalculator``'s
precedent of reusing ``ReferenceLevel`` rather than duplicating
``reference_builder``'s job.

Breakout/breakdown is determined by scanning ``candles`` in
chronological order for the first one whose high/low crosses the
opening range boundary - a standard, industry-generic ORB definition
(see ``core.enums.ORBStatus``'s own docstring), not an interpretation
of proprietary strategy evidence. A tick-mode candle (no OHLC, only
``underlying_price``) is compared against both boundaries using that
single price. If one candle's OHLC crosses *both* boundaries (a wide
candle spanning the whole opening range), breakout takes precedence
over breakdown - an engineering default for this ambiguous case (no
evidence specifies an order), documented here rather than left
implicit, matching this codebase's convention for such defaults (see
``strike_selector.strike_selector.StrikeSelector``'s ``ROUND_HALF_UP``
default).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.enums import OptionType, ORBStatus
from core.protocols import IdFactory
from models.market_snapshot import MarketSnapshot
from models.orb_result import ORBResult
from models.reference_level import ReferenceLevel


class ORBEngine:
    """Computes one strike/side's Opening Range Breakout classification.

    Constructor-injected ID factory only - no globals, no singletons,
    matching every other engine in this codebase.
    """

    def __init__(self, id_factory: IdFactory = uuid.uuid4) -> None:
        self._id_factory = id_factory

    def calculate(
        self,
        session_id: uuid.UUID,
        level: ReferenceLevel,
        side: OptionType,
        candles: tuple[MarketSnapshot, ...],
        calculated_at: datetime,
    ) -> ORBResult:
        """Compute Opening High/Low/Range/Breakout Status for ``side``
        at ``level.strike``. See module docstring for the
        breakout/breakdown rule."""
        if side is OptionType.CALL:
            opening_high, opening_low = level.ce_high, level.ce_low
        else:
            opening_high, opening_low = level.pe_high, level.pe_low

        status = self._classify(candles, opening_high, opening_low)

        return ORBResult(
            orb_result_id=self._id_factory(),
            session_id=session_id,
            strike=level.strike,
            side=side,
            opening_high=opening_high,
            opening_low=opening_low,
            range=opening_high - opening_low,
            status=status,
            calculated_at=calculated_at,
        )

    @staticmethod
    def _classify(
        candles: tuple[MarketSnapshot, ...], opening_high: Decimal, opening_low: Decimal
    ) -> ORBStatus:
        for candle in candles:
            candle_high = candle.high if candle.high is not None else candle.underlying_price
            candle_low = candle.low if candle.low is not None else candle.underlying_price
            broke_out = candle_high >= opening_high
            broke_down = candle_low <= opening_low
            if broke_out:
                return ORBStatus.BREAKOUT
            if broke_down:
                return ORBStatus.BREAKDOWN
        return ORBStatus.NONE

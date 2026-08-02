"""OpenInterestTrendEngine: derives session trend from underlying
price movement plus Call/Put Open Interest change, both measured
against the session's own opening values.

Traceability
------------
Product Owner-confirmed, 2026-08-02 (chat), recorded here directly -
no separate ``research/incoming/`` intake file was used for this
round since the exchange was a short chat clarification, not a
worked-example session; the exact confirmed answers are quoted below
verbatim so the rule is traceable without one.

Rule (standard Price/OI buildup-unwinding table, Product Owner
explicitly chose the strict 4-way reading over the collapsed
price-only reading):

    | Price | OI (Put OI change vs Call OI change) | Trend    |
    |-------|---------------------------------------|----------|
    | Up    | Put OI change > Call OI change (up)    | BULLISH  | (Long Buildup)
    | Down  | Put OI change > Call OI change (up)    | BEARISH  | (Short Buildup)
    | Up    | Put OI change < Call OI change (down)  | None     | (Short Covering - no signal)
    | Down  | Put OI change < Call OI change (down)  | None     | (Long Unwinding - no signal)

Confirmed inputs, verbatim:
- OI source: "Underlying/Index option chain total OI (Call vs Put OI)"
  - i.e. summed across the full strike ladder, not a single strike or
    the futures contract.
- OI combination: "Put OI rising faster than Call OI -> OI 'up'
  (bullish-leaning), and vice versa" - i.e. compare
  (current Put OI - session-open Put OI) against
  (current Call OI - session-open Call OI); whichever grew more sets
  the OI direction.
- Reference interval: "Compared to session open (9:15/9:20 first
  candle)" - both price and OI are compared against this session's own
  opening values, not the previous candle.
- Weak-signal handling: "OI should matter - use the strict 4-way
  table" - Short Covering and Long Unwinding produce NO trend signal
  (``None``), not a full Bullish/Bearish classification. This was
  chosen specifically because the alternative (treating every
  Price-Up as Bullish regardless of OI) makes OI irrelevant to the
  outcome, contradicting the Product Owner's stated intent to derive
  trend "from OI change every time."

Engineering default, not confirmed by evidence: a tie (price
unchanged from session open, or Put OI change exactly equals Call OI
change) also yields no trend signal (``None``) - the table has no row
for an exact tie, and inventing a direction for one would be a guess.
"""

from __future__ import annotations

from decimal import Decimal

from core.enums import TrendDirection


class OpenInterestTrendEngine:
    """Computes this candle's trend signal, or ``None`` if the
    Price/OI combination gives no clear signal (see module docstring's
    table). No constructor-injected state - purely a function of the
    values passed to :meth:`evaluate` each call, since the caller
    (``business.stages.trend_stage.TrendStage``) owns capturing and
    threading the session's own opening baseline forward.
    """

    def evaluate(
        self,
        session_open_price: Decimal,
        current_price: Decimal,
        session_open_call_oi: int,
        session_open_put_oi: int,
        current_call_oi: int,
        current_put_oi: int,
    ) -> TrendDirection | None:
        """Return this candle's trend, or ``None`` if Price and OI
        direction don't agree per the confirmed strict 4-way table.
        """
        price_delta = current_price - session_open_price
        call_oi_delta = current_call_oi - session_open_call_oi
        put_oi_delta = current_put_oi - session_open_put_oi
        oi_delta = put_oi_delta - call_oi_delta

        if price_delta > 0 and oi_delta > 0:
            return TrendDirection.BULLISH
        if price_delta < 0 and oi_delta > 0:
            return TrendDirection.BEARISH
        return None

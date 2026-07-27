"""Strike: a tradable options strike price under analysis.

Traceability notes
-------------------
Per ``docs/DOMAIN_MODEL.md``: "No other attributes (e.g. strike price
value type, expiry, option side) are evidenced yet." This model
therefore carries only ``price`` (the strike is, definitionally, an
options strike price - not itself an invented attribute) and its
identity/session linkage. Expiry and option side are deliberately
omitted.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from trading_engine.domain import DomainValidationError


@dataclass(frozen=True)
class Strike:
    """A tradable options strike price that has become the subject of
    analysis for a :class:`~trading_engine.domain.market_session.MarketSession`.

    Rule References
        STRIKE-001
        TREND-001
        TREND-003
        OPPONENT-001

    Entity
        ENT-001

    Attributes:
        strike_id: Unique identifier for this Strike instance.
        session_id: The MarketSession this Strike was selected within.
        price: The strike price value. Must be positive.
    """

    strike_id: uuid.UUID
    session_id: uuid.UUID
    price: Decimal

    def __post_init__(self) -> None:
        if self.strike_id is None:
            raise DomainValidationError("Strike.strike_id must not be None.")

        if self.session_id is None:
            raise DomainValidationError("Strike.session_id must not be None.")

        if self.price <= 0:
            raise DomainValidationError("Strike.price must be greater than 0.")

    # TODO (STRIKE-001): The calculation connecting a session's First
    # Candle to the resulting selected Strike is not yet evidenced
    # (see docs/TRADINGVIEW_STRATEGY_BIBLE.md Open Questions: "selected
    # based on the first candle" - selected *how*?). No selection
    # function exists in this module; a future rules/engine-layer
    # strategy extension point will produce Strike instances once that
    # calculation is known.

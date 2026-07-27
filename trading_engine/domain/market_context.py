"""MarketContext: the read-only snapshot a rule evaluation runs against.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Market
Context"): "The read-only snapshot of market data a rule evaluation
runs against for one moment in time - analogous to a single
candle/tick being fed to the engine." Market Context does not itself
compute anything - it is data, assembled once per evaluation step.
Instrument-agnostic: nothing here references a specific instrument
(NIFTY or otherwise) by name.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from trading_engine.domain import DomainValidationError
from trading_engine.domain.premium import Premium
from trading_engine.domain.strike import Strike


@dataclass(frozen=True)
class MarketContext:
    """A single-step, read-only snapshot of market data.

    Rule References
        None directly - a structural container for evaluation input.
        See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``.

    Attributes:
        context_id: Unique identifier for this snapshot.
        session_id: The MarketSession this snapshot belongs to.
        timestamp: The moment in time this snapshot represents.
        strikes: The Strike(s) under analysis at this moment.
        premiums: The Premium observation(s) available at this moment.
    """

    context_id: uuid.UUID
    session_id: uuid.UUID
    timestamp: datetime
    strikes: tuple[Strike, ...] = field(default_factory=tuple)
    premiums: tuple[Premium, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.context_id is None:
            raise DomainValidationError("MarketContext.context_id must not be None.")

        if self.session_id is None:
            raise DomainValidationError("MarketContext.session_id must not be None.")

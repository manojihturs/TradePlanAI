"""ReplayConfiguration: what a replay run's shape/scope is.

Traceability
------------
Field set matches this sprint's own instruction (replay speed, start
date, end date, symbols, timeframe) - all structural/infrastructure
concepts, no trading rule. ``replay_speed`` is captured for the
caller's own record-keeping only; this package never sleeps/throttles
based on it (no pacing mechanism is implemented, matching
``TradePlanAI-Lab``'s identical treatment of its own
``parallel_execution`` flag - captured, documented, never acted on).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class ReplayConfiguration:
    """Everything configurable about the scope of one replay run.

    Attributes:
        start_date: The first date the replay covers.
        end_date: The last date the replay covers.
        symbols: Which instrument symbols this replay concerns.
        timeframe: The candle timeframe label (e.g. ``"5m"``) - a
            structural label only, not interpreted by this package.
        replay_speed: Captured for reproducibility/record-keeping
            only - see module docstring. Must be positive.
    """

    start_date: date
    end_date: date
    symbols: tuple[str, ...] = field(default_factory=tuple)
    timeframe: str = ""
    replay_speed: Decimal = Decimal(1)

    def __post_init__(self) -> None:
        if self.start_date is None:
            raise ValidationError("ReplayConfiguration.start_date must not be None.")
        if self.end_date is None:
            raise ValidationError("ReplayConfiguration.end_date must not be None.")
        if self.end_date < self.start_date:
            raise ValidationError("ReplayConfiguration.end_date must not be before start_date.")
        if self.replay_speed <= 0:
            raise ValidationError("ReplayConfiguration.replay_speed must be greater than 0.")

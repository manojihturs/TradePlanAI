"""StrikeChainSnapshot: one strike's CE/PE market data at a single candle timestamp.

Traceability
------------
Backtest harness plumbing only - not a business rule. WinnerEngine
(Specification Section 9) and ExitEngine (Section 11) each need a
given strike's CE and PE observation for the *same* candle
simultaneously; ``PipelineContext.candles`` (a single flat stream, used
by ``business.stages.orb_stage.ORBStage`` for one anchor strike's one
side) cannot carry that. This model is the option-chain-shaped
alternative: one entry per strike, each carrying both sides' snapshots
for one candle. No business rule is computed here - it is a data
container only.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot


@dataclass(frozen=True, slots=True)
class StrikeChainSnapshot:
    """One strike's CE and PE :class:`~models.market_snapshot.MarketSnapshot`
    for a single candle timestamp.

    Attributes:
        strike: The strike this snapshot pair belongs to. Must be
            positive.
        ce: The CE contract's snapshot at this candle.
        pe: The PE contract's snapshot at this candle.
    """

    strike: Decimal
    ce: MarketSnapshot
    pe: MarketSnapshot

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValidationError("StrikeChainSnapshot.strike must be greater than 0.")
        if self.ce is None:
            raise ValidationError("StrikeChainSnapshot.ce must not be None.")
        if self.pe is None:
            raise ValidationError("StrikeChainSnapshot.pe must not be None.")
        if self.ce.timestamp != self.pe.timestamp:
            raise ValidationError(
                "StrikeChainSnapshot.ce and .pe must share the same timestamp "
                f"(got {self.ce.timestamp} and {self.pe.timestamp})."
            )

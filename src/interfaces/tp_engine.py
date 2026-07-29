"""TPEngine: interface only.

Traceability
------------
Specification Section 7, Section 20 item 3 (Critical): the TP
Engine's competitor-strike identity for the TP High/TP Low
qualification test is undefined - only shown by example for the
*Exit* Engine's competitor mapping (Rule 2), not this one. Update
cadence and whether "TP" is a price, a flag, or both are also
MISSING INFORMATION (Section 20 items 12-13). This interface defines
only the method shape a future implementation must satisfy. Do NOT
implement.

Naming note: this sprint's own instructions name this interface
"TrendPointEngine" in prose but ``tp_engine.py`` in the file list. No
"Trend Point" concept is evidenced anywhere in the Specification (see
``research/architecture/DATA_DICTIONARY.md`` Section 13's own note on
this) - "TP" here follows the Specification's own usage ("TP Engine",
Section 7, meaning the Top/Bottom Strike qualification test), not a
Trend concept. Flagged rather than silently resolved.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel


@runtime_checkable
class TPEngine(Protocol):
    """Continuously computes TP High (Top Strike) / TP Low (Bottom
    Strike) qualification state (Specification Section 7)."""

    def update(self, snapshot: MarketSnapshot, levels: tuple[ReferenceLevel, ...]) -> object:
        """Produce an updated TP qualification state.

        Return type is deliberately ``object`` rather than a concrete
        ``TPState`` model - whether TP is a price, a boolean flag, or
        both is itself MISSING INFORMATION (Specification Section 20
        item 13), so no such model is defined in this sprint.

        Raises:
            core.exceptions.UnresolvedBusinessRuleError: always, until
                the competitor identity rule (Specification Section
                20 item 3) is resolved and a real implementation
                replaces the stub.
        """
        ...  # pragma: no cover

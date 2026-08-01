"""QualificationTrailingStop: injected collaborator Protocol +
null-object stand-in for ``QualificationExitEngine``.

Traceability
------------
Trailing Stop's step ratio (2 points of trail per 5 points of
favourable premium movement, on top of the already-known minimum +3
net premium points) is confirmed
(``research/incoming/trailing_stop_session4_intake_2026-07-31.md``),
but its exact activation trigger and the brokerage/exchange/tax
figures needed to compute "+3 net" precisely are still missing -
Evidence Partial, not Evidence Complete. Implementing a real trail
here would mean guessing at the unconfirmed activation trigger.

``NeverTriggersQualificationTrailingStop`` mirrors
``backtest.null_engines.NeverTriggersTrailingStop``'s own pattern
exactly: ``check()`` always returns ``False`` - a position can only
close via Target/Competitor/Stop Loss, all of which ARE confirmed -
until real Trailing Stop evidence arrives and this is replaced with a
real implementation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from models.market_snapshot import MarketSnapshot
from models.qualified_position import QualifiedPosition


@runtime_checkable
class QualificationTrailingStop(Protocol):
    """Checks whether the active :class:`~models.qualified_position.QualifiedPosition`'s
    Trailing Stop condition has been met on this candle."""

    def check(self, position: QualifiedPosition, snapshot: MarketSnapshot) -> bool:
        """Return whether ``position`` should close via Trailing
        Stop, given ``snapshot``."""
        ...  # pragma: no cover


class NeverTriggersQualificationTrailingStop:
    """A :class:`QualificationTrailingStop` stand-in that never
    reports the Trailing Stop condition as met.

    See module docstring - a null object, not a business rule.
    """

    def check(self, position: QualifiedPosition, snapshot: MarketSnapshot) -> bool:
        _ = (position, snapshot)  # unused - see module docstring
        return False

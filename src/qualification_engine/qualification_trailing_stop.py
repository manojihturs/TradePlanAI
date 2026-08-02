"""QualificationTrailingStop: injected collaborator Protocol, a real
breakeven-first implementation, and a null-object stand-in, for
``QualificationExitEngine``.

Traceability
------------
Confirmed rule (``research/incoming/trailing_stop_session4_intake_2026-07-31.md``,
Product Owner-supplied, RESOLVED 2026-08-02):

- Activation trigger: "Breakeven-first, that's how I do it." (2026-08-01)
  - the trail does not move at all until the position has moved
    favourably by the confirmed minimum.
- Minimum/"net" basis: "Just 3 raw premium points, no cost
  adjustment." (2026-08-02) - resolves the previously-missing
  brokerage/exchange/tax question outright: no cost figures are
  needed. Activation = 3 raw premium points of favourable movement
  from entry.
- Step ratio: "if premium moved 5 points move the TSL 2 points."
  (2026-08-01) - once activated, the trail level = entry +/- 2 points
  for every additional 5 points of favourable movement beyond the
  initial 3-point activation, favourable direction depending on side
  (CE: upward; PE: downward).

``BreakevenFirstQualificationTrailingStop`` tracks each active
position's own high-water mark (best favourable premium touched so
far, using this project's existing touch definition - a candle's own
[low, high] range) since evidence does not specify a finer
granularity. Two engineering defaults not covered by evidence,
applied here rather than guessed at silently:

- The trail only ever tightens (moves favourably), never loosens -
  the only sane reading of "trailing"; not explicitly confirmed.
- Within a single candle, the high-water mark is updated (using this
  candle's own favourable extreme) BEFORE this same candle's touch
  check against the resulting trail level - mirrors this project's
  own existing touch-definition precedent (a level within a candle's
  [low, high] range is "touched" regardless of intra-candle order).

Stateful by construction (per Protocol instance, keyed by
``position.position_id`` - reset whenever a new position_id is seen,
since ``QualificationPositionManager``'s single-active-trade rule
guarantees at most one position is ever tracked at a time by a given
instance). One instance must not be shared across anchors that may
have concurrently active positions - ``backtest.runner.BacktestRunner``
already gives Top and Bottom their own ``QualificationExitEngine``,
so this follows the same one-per-anchor convention.

``NeverTriggersQualificationTrailingStop`` is kept as a null-object
stand-in for tests/fixtures that want Trailing Stop deliberately
disabled - mirrors ``backtest.null_engines.NeverTriggersTrailingStop``'s
own pattern.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Protocol, runtime_checkable

from core.enums import TradeDirection
from models.market_snapshot import MarketSnapshot
from models.qualified_position import QualifiedPosition

#: Minimum favourable premium-point movement before the trail
#: activates at all (Product Owner-confirmed, "3 raw premium points,
#: no cost adjustment").
_ACTIVATION_POINTS = Decimal(3)

#: Step ratio: for every _STEP_SOURCE points of favourable movement
#: beyond activation, the trail moves _STEP_TRAIL points.
_STEP_SOURCE = Decimal(5)
_STEP_TRAIL = Decimal(2)


@runtime_checkable
class QualificationTrailingStop(Protocol):
    """Checks whether the active :class:`~models.qualified_position.QualifiedPosition`'s
    Trailing Stop condition has been met on this candle."""

    def check(self, position: QualifiedPosition, snapshot: MarketSnapshot) -> bool:
        """Return whether ``position`` should close via Trailing
        Stop, given ``snapshot``."""
        ...  # pragma: no cover


class BreakevenFirstQualificationTrailingStop:
    """Confirmed, real Trailing Stop: breakeven-first activation at
    +3 raw premium points, then 2-points-of-trail-per-5-points-of-
    favourable-movement stepping. See module docstring for the full
    evidence trail and engineering defaults.
    """

    def __init__(self) -> None:
        self._tracked_position_id: uuid.UUID | None = None
        self._high_water: Decimal | None = None

    def check(self, position: QualifiedPosition, snapshot: MarketSnapshot) -> bool:
        assert snapshot.low is not None and snapshot.high is not None

        if position.position_id != self._tracked_position_id:
            self._tracked_position_id = position.position_id
            self._high_water = position.entry_level

        assert self._high_water is not None
        favourable_extreme = snapshot.high if position.side is TradeDirection.CE else snapshot.low
        if position.side is TradeDirection.CE:
            self._high_water = max(self._high_water, favourable_extreme)
            profit_points = self._high_water - position.entry_level
        else:
            self._high_water = min(self._high_water, favourable_extreme)
            profit_points = position.entry_level - self._high_water

        if profit_points < _ACTIVATION_POINTS:
            return False

        steps = (profit_points - _ACTIVATION_POINTS) // _STEP_SOURCE
        trail_offset = steps * _STEP_TRAIL
        trail_level = (
            position.entry_level + trail_offset
            if position.side is TradeDirection.CE
            else position.entry_level - trail_offset
        )
        return snapshot.low <= trail_level <= snapshot.high


class NeverTriggersQualificationTrailingStop:
    """A :class:`QualificationTrailingStop` stand-in that never
    reports the Trailing Stop condition as met.

    See module docstring - a null object for tests/fixtures that want
    Trailing Stop deliberately disabled, not the production default.
    """

    def check(self, position: QualifiedPosition, snapshot: MarketSnapshot) -> bool:
        _ = (position, snapshot)  # unused - see module docstring
        return False

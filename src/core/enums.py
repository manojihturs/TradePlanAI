"""Core enumerations shared across the strategy engine.

Traceability
------------
Every value here is either a structural/infrastructure concept (e.g.
``EventPriority``) or a direct restatement of terminology already
used verbatim in ``research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md``
v1.1 ("the Specification") - e.g. "Winner CE" / "Winner PE" (Section
9), the four named exit conditions (Section 11). No trading threshold
or formula is encoded in any enum below.
"""

from __future__ import annotations

from enum import Enum, IntEnum, unique


@unique
class OptionType(Enum):
    """The two option contract types a :class:`~models.reference_level.ReferenceLevel`
    carries CE/PE reference values for (Specification Section 6)."""

    CALL = "CALL"
    PUT = "PUT"


@unique
class TradeDirection(Enum):
    """Which side a trade/winner runs on - CE or PE, using the
    Specification's own wording ("Winner CE", "Winner PE", Section 9,
    Rule 2)."""

    CE = "CE"
    PE = "PE"


@unique
class TradeState(Enum):
    """The Sprint 1 trade/session lifecycle state, per the simplified
    state machine explicitly scoped for this sprint:
    Idle -> Ready -> TradeActive -> TradeClosed -> Ready.

    This is a deliberately narrower subset of the full lifecycle in
    ``research/architecture/STATE_MACHINE.md`` (18 states) - Sprint 1
    implements only the states named in this sprint's own
    instructions, not a redesign of the fuller architecture.
    """

    IDLE = "IDLE"
    READY = "READY"
    TRADE_ACTIVE = "TRADE_ACTIVE"
    TRADE_CLOSED = "TRADE_CLOSED"


@unique
class ExitReason(Enum):
    """The four exit conditions named in the Specification (Section
    11): Target Hit, Competitor Strike Reference Level Hit, Stop
    Loss, Trailing Stop. Stop Loss's own rule and Trailing Stop's own
    mechanics remain MISSING INFORMATION (Specification Section 20
    items 4, 9-10) - only the four names, not their trigger logic,
    are encoded here.
    """

    TARGET_HIT = "TARGET_HIT"
    COMPETITOR_HIT = "COMPETITOR_HIT"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"


@unique
class ORBStatus(Enum):
    """A strike/side's Opening Range Breakout classification.

    A standard, industry-generic definition (price crosses above the
    opening range's high -> ``BREAKOUT``; below its low ->
    ``BREAKDOWN``; neither observed -> ``NONE``) - not a proprietary
    interpretation requiring TradingView-strategy-specific evidence,
    unlike most other enums in this module. See
    ``orb_engine.orb_engine.ORBEngine`` for the calculation itself.
    """

    NONE = "NONE"
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"


@unique
class EventPriority(IntEnum):
    """Dispatch-priority tiers for :class:`events.event_bus.EventBus`.

    A pure infrastructure/engineering concept (ordering of handler
    dispatch), not a business rule - the Specification defines no
    priority scheme. Ordered so that a higher member compares greater
    (``CRITICAL > HIGH > NORMAL > LOW``), suitable for sorting.
    """

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

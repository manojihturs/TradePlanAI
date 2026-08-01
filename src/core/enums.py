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

    ``SESSION_END`` is a fifth member, added 2026-08-01 for QUAL-011
    (``research/specifications/qualification_rule_catalog.md``) - a
    real, confirmed event (Product Owner trade logs record it
    verbatim as "market closed, No level touched"), scoped as
    session-boundary orchestration rather than a per-candle
    ``ExitEngine``/``QualificationExitEngine`` condition.
    """

    TARGET_HIT = "TARGET_HIT"
    COMPETITOR_HIT = "COMPETITOR_HIT"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    SESSION_END = "SESSION_END"


@unique
class AnchorRole(Enum):
    """Which boundary strike a qualification ladder is anchored to -
    Top Strike or Bottom Strike (both already confirmed,
    ``strike_selector.strike_selector.StrikeSelector``). Determines
    which reference-level column plays the entry-column/confirm-
    column role for each trade side (Product Owner General Rule
    Statement, ``research/incoming/qualification_session1_intake_2026-07-31.md``)."""

    TOP = "TOP"
    BOTTOM = "BOTTOM"


@unique
class TrendDirection(Enum):
    """The underlying's directional bias, checked before any
    qualification crossover is evaluated (Product Owner Entry/
    Target/SL/TSL Clarification, 2026-08-01: "First we have get the
    current market trend bullish/bearish"). How trend itself is
    computed is UNRESOLVED - Awaiting Strategy Evidence; this enum is
    an injected input to ``qualification_engine.qualification_engine.QualificationEngine``,
    not something it computes."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


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
class TimelineEventType(Enum):
    """The six event kinds a :class:`~application.strategy_timeline.StrategyTimeline`
    records (Sprint: "Strategy Timeline") - a pure infrastructure/
    observability concept, not a business rule."""

    REFERENCE_LEVEL_CREATED = "REFERENCE_LEVEL_CREATED"
    WEEKLY_FUTURE_CALCULATED = "WEEKLY_FUTURE_CALCULATED"
    STRIKE_SELECTED = "STRIKE_SELECTED"
    ORB_CALCULATED = "ORB_CALCULATED"
    REPLAY_FINISHED = "REPLAY_FINISHED"
    PIPELINE_ERROR = "PIPELINE_ERROR"


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

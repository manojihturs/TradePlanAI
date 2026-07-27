"""SessionState: accumulating per-MarketSession state across evaluation steps.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Session
State") and ``docs/STATE_MACHINE.md`` (artifact IDs SM-001 through
SM-005). Per that document, this state set is explicitly incomplete:
most entry/exit conditions between these states are "UNKNOWN -
insufficient evidence," and OPPONENT_DEFEATED itself is flagged as a
hypothesis, not a confirmed state. This module only names the states
and lets a SessionState record which one currently applies - it
defines no transition logic.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from enum import Enum, auto

from trading_engine.domain import DomainValidationError
from trading_engine.domain.trend_point import TrendPoint


class SessionStateType(Enum):
    """The five states derived strictly from
    ``docs/TRADINGVIEW_STRATEGY_BIBLE.md`` and documented in
    ``docs/STATE_MACHINE.md`` (SM-001 through SM-005).
    """

    #: No state has been established yet for the session. Not one of
    #: the five evidenced states - a structural default only.
    NONE = auto()

    #: SM-001. Derived from STRIKE-001.
    STRIKE_SELECTED = auto()

    #: SM-002. Derived from TREND-001/TREND-002.
    TREND_TRACKING = auto()

    #: SM-003. Derived from OPPONENT-001.
    OPPONENT_ENGAGEMENT = auto()

    #: SM-004. Inferred only from OPPONENT-001's wording, not directly
    #: evidenced.
    OPPONENT_DEFEATED = auto()

    #: SM-005. Derived from REVERSAL-001.
    REVERSAL_IDENTIFIED = auto()


@dataclass(frozen=True)
class SessionState:
    """The accumulating state that persists across evaluation steps
    within one MarketSession.

    Does **not** encode any transition logic between the five
    :class:`SessionStateType` values - ``docs/STATE_MACHINE.md``
    itself states 4 of 5 states have unknown entry/exit conditions.
    This type is a place to *record* which state applies, not a state
    machine implementation that *decides* transitions.

    Rule References
        None directly - see ``docs/STATE_MACHINE.md`` for the
        per-state Rule ID citations (STRIKE-001, TREND-001,
        TREND-002, OPPONENT-001, REVERSAL-001).

    Attributes:
        session_id: The MarketSession this state belongs to.
        current_state: Which of the five evidenced states currently
            applies, or ``SessionStateType.NONE`` before any state is
            evidenced.
        trend_points: The TrendPoint(s) currently tracked for this
            session.
    """

    session_id: uuid.UUID
    current_state: SessionStateType = SessionStateType.NONE
    trend_points: tuple[TrendPoint, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.session_id is None:
            raise DomainValidationError("SessionState.session_id must not be None.")

    def with_state(self, new_state: SessionStateType) -> SessionState:
        """Return a new SessionState instance recording a different
        current state.

        Does not decide *whether* this transition is valid - see
        module docstring; transition logic between
        ``docs/STATE_MACHINE.md``'s states remains almost entirely
        Unknown. This method only expresses the immutable-update
        mechanic, given a caller-supplied target state.
        """
        return replace(self, current_state=new_state)

    # TODO (STATE_MACHINE): Entry/exit conditions and valid
    # transitions between the five SessionStateType values are
    # UNKNOWN - insufficient evidence, per docs/STATE_MACHINE.md, for
    # 4 of 5 states. No transition-validation logic exists here.

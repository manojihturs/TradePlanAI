"""Sprint 1 trade/session state machine.

Traceability
------------
Implements exactly the state sequence this sprint's own instructions
specify: Idle -> Ready -> TradeActive -> TradeClosed -> Ready. This is
a deliberately narrow subset of the full 18-state lifecycle in
``research/architecture/STATE_MACHINE.md`` - not a redesign of that
architecture, only the slice explicitly scoped to Sprint 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.enums import TradeState
from core.exceptions import StateMachineError

#: Allowed transitions for the Sprint 1 state machine. Keys are the
#: current state; values are the set of states that may be entered
#: next.
_ALLOWED_TRANSITIONS: dict[TradeState, frozenset[TradeState]] = {
    TradeState.IDLE: frozenset({TradeState.READY}),
    TradeState.READY: frozenset({TradeState.TRADE_ACTIVE}),
    TradeState.TRADE_ACTIVE: frozenset({TradeState.TRADE_CLOSED}),
    TradeState.TRADE_CLOSED: frozenset({TradeState.READY}),
}


@dataclass(slots=True)
class StateMachine:
    """A minimal, mutable state machine over :class:`core.enums.TradeState`.

    Starts in :attr:`TradeState.IDLE`. Only mutation is
    :meth:`transition` - illegal transitions raise
    :class:`~core.exceptions.StateMachineError` rather than silently
    applying.
    """

    current_state: TradeState = field(default=TradeState.IDLE)

    def can_transition(self, target: TradeState) -> bool:
        """Whether moving from the current state to ``target`` is
        allowed."""
        return target in _ALLOWED_TRANSITIONS[self.current_state]

    def transition(self, target: TradeState) -> None:
        """Move to ``target``.

        Raises:
            StateMachineError: if the transition is not allowed from
                the current state.
        """
        if not self.can_transition(target):
            raise StateMachineError(
                f"Illegal transition: {self.current_state.value} -> {target.value}."
            )
        self.current_state = target

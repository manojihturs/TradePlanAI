"""Tests for core.state_machine."""

from __future__ import annotations

import pytest

from core.enums import TradeState
from core.exceptions import StateMachineError
from core.state_machine import StateMachine


def test_starts_in_idle() -> None:
    machine = StateMachine()
    assert machine.current_state == TradeState.IDLE


def test_full_happy_path_cycle() -> None:
    machine = StateMachine()
    machine.transition(TradeState.READY)
    assert machine.current_state == TradeState.READY
    machine.transition(TradeState.TRADE_ACTIVE)
    assert machine.current_state == TradeState.TRADE_ACTIVE
    machine.transition(TradeState.TRADE_CLOSED)
    assert machine.current_state == TradeState.TRADE_CLOSED
    machine.transition(TradeState.READY)
    assert machine.current_state == TradeState.READY
    # Cycle repeats.
    machine.transition(TradeState.TRADE_ACTIVE)
    assert machine.current_state == TradeState.TRADE_ACTIVE


@pytest.mark.parametrize(
    ("start", "illegal_target"),
    [
        (TradeState.IDLE, TradeState.TRADE_ACTIVE),
        (TradeState.IDLE, TradeState.TRADE_CLOSED),
        (TradeState.READY, TradeState.IDLE),
        (TradeState.READY, TradeState.TRADE_CLOSED),
        (TradeState.TRADE_ACTIVE, TradeState.IDLE),
        (TradeState.TRADE_ACTIVE, TradeState.READY),
        (TradeState.TRADE_CLOSED, TradeState.IDLE),
        (TradeState.TRADE_CLOSED, TradeState.TRADE_ACTIVE),
    ],
)
def test_illegal_transition_raises(start: TradeState, illegal_target: TradeState) -> None:
    machine = StateMachine(current_state=start)
    with pytest.raises(StateMachineError, match="Illegal transition"):
        machine.transition(illegal_target)
    assert machine.current_state == start


def test_can_transition_reports_without_mutating() -> None:
    machine = StateMachine()
    assert machine.can_transition(TradeState.READY) is True
    assert machine.can_transition(TradeState.TRADE_ACTIVE) is False
    assert machine.current_state == TradeState.IDLE

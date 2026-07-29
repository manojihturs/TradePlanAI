"""Tests for core.enums."""

from __future__ import annotations

from core.enums import EventPriority, ExitReason, OptionType, TradeDirection, TradeState


class TestOptionType:
    def test_members(self) -> None:
        assert OptionType.CALL.value == "CALL"
        assert OptionType.PUT.value == "PUT"

    def test_exactly_two_members(self) -> None:
        assert len(OptionType) == 2


class TestTradeDirection:
    def test_members(self) -> None:
        assert TradeDirection.CE.value == "CE"
        assert TradeDirection.PE.value == "PE"

    def test_exactly_two_members(self) -> None:
        assert len(TradeDirection) == 2


class TestTradeState:
    def test_members(self) -> None:
        assert {member.value for member in TradeState} == {
            "IDLE",
            "READY",
            "TRADE_ACTIVE",
            "TRADE_CLOSED",
        }


class TestExitReason:
    def test_members(self) -> None:
        assert {member.value for member in ExitReason} == {
            "TARGET_HIT",
            "COMPETITOR_HIT",
            "STOP_LOSS",
            "TRAILING_STOP",
        }


class TestEventPriority:
    def test_ordering(self) -> None:
        assert (
            EventPriority.LOW < EventPriority.NORMAL < EventPriority.HIGH < EventPriority.CRITICAL
        )

    def test_int_values(self) -> None:
        assert EventPriority.LOW == 0
        assert EventPriority.CRITICAL == 3

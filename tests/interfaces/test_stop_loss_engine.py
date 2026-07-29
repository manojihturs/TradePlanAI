"""Conformance tests for interfaces.stop_loss_engine.

Verifies only the Protocol shape and stub convention - the Stop Loss
rule itself (Specification Section 20 item 4, Critical) remains
MISSING INFORMATION and is not implemented here.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import TradeDirection
from core.exceptions import UnresolvedBusinessRuleError
from interfaces.stop_loss_engine import StopLossEngine
from models.market_snapshot import MarketSnapshot
from models.trade_position import TradePosition


class _StubStopLossEngine:
    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        raise UnresolvedBusinessRuleError(
            "Stop Loss rule is MISSING INFORMATION (Specification Section 20 item 4)."
        )


def _position() -> TradePosition:
    return TradePosition(
        trade_id=uuid.uuid4(),
        entry_strike=Decimal(24100),
        entry_side=TradeDirection.CE,
        target_level=Decimal(24150),
        support_level=Decimal(24050),
        competitor_monitor_strike=Decimal(24050),
        opened_at=datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC),
    )


def _snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 35, 0, tzinfo=UTC), underlying_price=Decimal(24000)
    )


def test_stub_satisfies_protocol() -> None:
    assert isinstance(_StubStopLossEngine(), StopLossEngine)


def test_object_without_check_does_not_satisfy_protocol() -> None:
    class NotAStopLossEngine:
        pass

    assert not isinstance(NotAStopLossEngine(), StopLossEngine)


def test_stub_raises_unresolved_business_rule_error() -> None:
    engine: StopLossEngine = _StubStopLossEngine()
    with pytest.raises(UnresolvedBusinessRuleError, match="MISSING INFORMATION"):
        engine.check(_position(), _snapshot())

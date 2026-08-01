"""Tests for qualification_engine.qualification_trailing_stop."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from core.enums import AnchorRole, TradeDirection
from models.market_snapshot import MarketSnapshot
from models.qualified_position import QualifiedPosition
from qualification_engine.qualification_trailing_stop import (
    NeverTriggersQualificationTrailingStop,
    QualificationTrailingStop,
)

_TIMESTAMP = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)


def _position() -> QualifiedPosition:
    return QualifiedPosition(
        position_id=uuid.uuid4(),
        anchor_role=AnchorRole.TOP,
        side=TradeDirection.CE,
        entry_strike=Decimal(24250),
        entry_level=Decimal("120.1"),
        target_level=Decimal("145.2"),
        stop_loss_level=Decimal("98.3"),
        competitor_exit_level=Decimal("121.5"),
        opened_at=_TIMESTAMP,
    )


def _snapshot() -> MarketSnapshot:
    return MarketSnapshot(timestamp=_TIMESTAMP, underlying_price=Decimal(24140))


class TestNeverTriggersQualificationTrailingStop:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(NeverTriggersQualificationTrailingStop(), QualificationTrailingStop)

    def test_always_returns_false(self) -> None:
        assert NeverTriggersQualificationTrailingStop().check(_position(), _snapshot()) is False


def test_object_without_check_does_not_satisfy_protocol() -> None:
    class NotATrailingStop:
        pass

    assert not isinstance(NotATrailingStop(), QualificationTrailingStop)

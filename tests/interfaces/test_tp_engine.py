"""Conformance tests for interfaces.tp_engine.

Verifies only the Protocol shape and stub convention - the TP
Engine's competitor identity (Specification Section 20 item 3,
Critical) remains MISSING INFORMATION and is not implemented here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.exceptions import UnresolvedBusinessRuleError
from interfaces.tp_engine import TPEngine
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel


class _StubTPEngine:
    def update(self, snapshot: MarketSnapshot, levels: tuple[ReferenceLevel, ...]) -> object:
        raise UnresolvedBusinessRuleError(
            "TP Engine competitor identity is MISSING INFORMATION (Specification Section 20 item 3)."
        )


def _snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 25, 0, tzinfo=UTC), underlying_price=Decimal(24000)
    )


def test_stub_satisfies_protocol() -> None:
    assert isinstance(_StubTPEngine(), TPEngine)


def test_object_without_update_does_not_satisfy_protocol() -> None:
    class NotATPEngine:
        pass

    assert not isinstance(NotATPEngine(), TPEngine)


def test_stub_raises_unresolved_business_rule_error() -> None:
    engine: TPEngine = _StubTPEngine()
    with pytest.raises(UnresolvedBusinessRuleError, match="MISSING INFORMATION"):
        engine.update(_snapshot(), ())

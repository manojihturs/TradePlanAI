"""Conformance tests for interfaces.qualification_engine.

Verifies only the Protocol *shape* - the real implementation and its
own tests live in ``src/qualification_engine/`` (mechanism RESOLVED
2026-08-01, see
``research/specifications/qualification_engine_scoring_2026-08-01.md``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from core.enums import AnchorRole, TrendDirection
from interfaces.qualification_engine import QualificationEngine
from models.market_snapshot import MarketSnapshot
from models.qualification_signal import QualificationSignal
from models.reference_level import ReferenceLevel


class _StubQualificationEngine:
    """A stub satisfying the Protocol shape, for structural
    conformance testing only."""

    def evaluate(
        self,
        anchor_role: AnchorRole,
        trend: TrendDirection,
        reference_levels: tuple[ReferenceLevel, ...],
        own_ce_snapshot: MarketSnapshot,
        own_pe_snapshot: MarketSnapshot,
        candle_timestamp: datetime,
    ) -> QualificationSignal | None:
        return None


def _level() -> ReferenceLevel:
    return ReferenceLevel(
        strike=Decimal(24250),
        ce_high=Decimal("121.5"),
        ce_low=Decimal("87.0"),
        pe_high=Decimal("159.0"),
        pe_low=Decimal("120.1"),
    )


def _candle() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
        underlying_price=Decimal(24140),
        open=Decimal("120.05"),
        high=Decimal("120.15"),
        low=Decimal("120.05"),
        close=Decimal("120.1"),
    )


def test_stub_satisfies_protocol() -> None:
    assert isinstance(_StubQualificationEngine(), QualificationEngine)


def test_object_without_evaluate_does_not_satisfy_protocol() -> None:
    class NotAQualificationEngine:
        pass

    assert not isinstance(NotAQualificationEngine(), QualificationEngine)


def test_stub_returns_none() -> None:
    engine: QualificationEngine = _StubQualificationEngine()
    result = engine.evaluate(
        anchor_role=AnchorRole.TOP,
        trend=TrendDirection.BULLISH,
        reference_levels=(_level(),),
        own_ce_snapshot=_candle(),
        own_pe_snapshot=_candle(),
        candle_timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
    )
    assert result is None

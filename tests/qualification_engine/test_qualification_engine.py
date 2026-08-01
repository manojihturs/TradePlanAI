"""Tests for qualification_engine.qualification_engine.

Traceability
------------
The 13-strike ladder fixture and the Row 1/2/3/5 assertions below are
the REAL, confirmed 30-July-2026 reference ladder and trade-log values
from ``research/incoming/qualification_session1_intake_2026-07-31.md``
(fetched live via Upstox this session, and the Product-Owner-supplied
30-July trade log) - not synthetic numbers. Every Target/Stop
Loss/Competitor Exit assertion below matches a real, already-verified
row from that document exactly.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import AnchorRole, TradeDirection, TrendDirection
from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.reference_level import ReferenceLevel
from qualification_engine.qualification_engine import QualificationEngine

_TS = datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)

# The real, confirmed 30-July-2026 reference ladder (13 strikes,
# fetched live via Upstox this session - src/backtest/).
_LADDER: tuple[ReferenceLevel, ...] = (
    ReferenceLevel(
        Decimal(23950), Decimal("332.95"), Decimal("276.1"), Decimal("46.8"), Decimal("32.65")
    ),
    ReferenceLevel(
        Decimal(24000), Decimal("291.5"), Decimal("236.6"), Decimal("63.0"), Decimal("41.1")
    ),
    ReferenceLevel(
        Decimal(24050), Decimal("252.0"), Decimal("201.85"), Decimal("72.9"), Decimal("51.5")
    ),
    ReferenceLevel(
        Decimal(24100), Decimal("215.6"), Decimal("167.6"), Decimal("91.0"), Decimal("64.3")
    ),
    ReferenceLevel(
        Decimal(24150), Decimal("181.4"), Decimal("137.55"), Decimal("108.2"), Decimal("80.0")
    ),
    ReferenceLevel(
        Decimal(24200), Decimal("150.0"), Decimal("110.3"), Decimal("131.6"), Decimal("98.3")
    ),
    ReferenceLevel(
        Decimal(24250), Decimal("121.5"), Decimal("87.0"), Decimal("159.0"), Decimal("120.1")
    ),
    ReferenceLevel(
        Decimal(24300), Decimal("103.2"), Decimal("67.05"), Decimal("189.0"), Decimal("145.2")
    ),
    ReferenceLevel(
        Decimal(24350), Decimal("74.75"), Decimal("50.5"), Decimal("222.35"), Decimal("173.55")
    ),
    ReferenceLevel(
        Decimal(24400), Decimal("56.4"), Decimal("37.3"), Decimal("259.4"), Decimal("205.1")
    ),
    ReferenceLevel(
        Decimal(24450), Decimal("45.55"), Decimal("27.0"), Decimal("297.95"), Decimal("240.5")
    ),
    ReferenceLevel(
        Decimal(24500), Decimal("30.1"), Decimal("19.45"), Decimal("340.6"), Decimal("279.2")
    ),
    ReferenceLevel(
        Decimal(24550), Decimal("23.85"), Decimal("13.9"), Decimal("383.45"), Decimal("318.4")
    ),
)


def _tight_candle(value: Decimal) -> MarketSnapshot:
    """A candle whose [low, high] touches only ``value`` in its own
    column (no other ladder level) - isolates exactly what's under
    test without depending on unrecorded tick-level data."""
    return MarketSnapshot(
        timestamp=_TS,
        underlying_price=Decimal(24140),
        open=value - Decimal("0.05"),
        high=value + Decimal("0.05"),
        low=value - Decimal("0.05"),
        close=value,
    )


def _no_touch_candle() -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_TS,
        underlying_price=Decimal(24140),
        open=Decimal(9999),
        high=Decimal("9999.1"),
        low=Decimal("9998.9"),
        close=Decimal(9999),
    )


class TestConfirmedRegressionRows:
    """Each test reproduces one real, confirmed row from the 30-July
    trade log exactly - Target/Stop Loss/Competitor Exit all traced
    to actual evidence, not invented."""

    def test_row_1_top_ce_entry_at_anchor(self) -> None:
        # 30-July Row 1: CE @ 24250 (Top itself). Entry 120.1, Target
        # 145.2, SL 98.3, Competitor 121.5.
        signal = QualificationEngine(id_factory=lambda: uuid.UUID(int=1)).evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_tight_candle(Decimal("120.1")),
            own_pe_snapshot=_tight_candle(Decimal("121.5")),
            candle_timestamp=_TS,
        )
        assert signal is not None
        assert signal.side is TradeDirection.CE
        assert signal.entry_strike == Decimal(24250)
        assert signal.entry_level == Decimal("120.1")
        assert signal.target_level == Decimal("145.2")
        assert signal.stop_loss_level == Decimal("98.3")
        assert signal.competitor_exit_level == Decimal("121.5")

    def test_row_2_top_ce_entry_at_different_strike_than_anchor(self) -> None:
        # 30-July Row 2: CE @ 24250-TOP, but entry level belongs to
        # 24200. Entry 98.3, Target 120.1, SL 80, Competitor 121.5
        # (stays anchored to 24250's own CE High, confirmed fixed).
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_tight_candle(Decimal("98.3")),
            own_pe_snapshot=_tight_candle(Decimal("121.5")),
            candle_timestamp=_TS,
        )
        assert signal is not None
        assert signal.entry_strike == Decimal(24200)
        assert signal.entry_level == Decimal("98.3")
        assert signal.target_level == Decimal("120.1")
        assert signal.stop_loss_level == Decimal("80.0")
        assert signal.competitor_exit_level == Decimal("121.5")

    def test_row_3_top_pe_entry(self) -> None:
        # 30-July Row 3: PE @ 24250-TOP. Entry 103.2 (24300's own CE
        # High), Target 121.5, SL 74.75, Competitor 120.1.
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BEARISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_tight_candle(Decimal("120.1")),
            own_pe_snapshot=_tight_candle(Decimal("103.2")),
            candle_timestamp=_TS,
        )
        assert signal is not None
        assert signal.side is TradeDirection.PE
        assert signal.entry_strike == Decimal(24300)
        assert signal.entry_level == Decimal("103.2")
        assert signal.target_level == Decimal("121.5")
        assert signal.stop_loss_level == Decimal("74.75")
        assert signal.competitor_exit_level == Decimal("120.1")

    def test_row_5_bottom_ce_entry(self) -> None:
        # 30-July Row 5 (24150-BOTTOM section): CE trade, entry level
        # belongs to 24250 (not the 24150 anchor). Entry 159, Target
        # 189, SL 131.6, Competitor 87.
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.BOTTOM,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_tight_candle(Decimal(159)),
            own_pe_snapshot=_tight_candle(Decimal(87)),
            candle_timestamp=_TS,
        )
        assert signal is not None
        assert signal.anchor_role is AnchorRole.BOTTOM
        assert signal.entry_strike == Decimal(24250)
        assert signal.entry_level == Decimal(159)
        assert signal.target_level == Decimal("189.0")
        assert signal.stop_loss_level == Decimal("131.6")
        assert signal.competitor_exit_level == Decimal("87.0")


class TestNoQualification:
    def test_no_entry_touch_returns_none(self) -> None:
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_no_touch_candle(),
            own_pe_snapshot=_tight_candle(Decimal("121.5")),
            candle_timestamp=_TS,
        )
        assert signal is None

    def test_no_confirm_touch_returns_none(self) -> None:
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_tight_candle(Decimal("120.1")),
            own_pe_snapshot=_no_touch_candle(),
            candle_timestamp=_TS,
        )
        assert signal is None

    def test_entry_at_ladder_edge_has_no_target_returns_none(self) -> None:
        # 24550 is the top of the ladder - a CE entry there (pe_low
        # column) has no favourable rung above it.
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_tight_candle(Decimal("318.4")),
            own_pe_snapshot=_tight_candle(Decimal("121.5")),
            candle_timestamp=_TS,
        )
        assert signal is None

    def test_entry_at_ladder_edge_has_no_stop_loss_returns_none(self) -> None:
        # 23950 is the bottom of the ladder - a CE entry there
        # (pe_low column) has no unfavourable rung below it.
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_tight_candle(Decimal("32.65")),
            own_pe_snapshot=_tight_candle(Decimal("121.5")),
            candle_timestamp=_TS,
        )
        assert signal is None


class TestTieBreak:
    def test_lowest_strike_wins_when_multiple_levels_touched(self) -> None:
        # A wide CE candle spanning both 24200's pe_low (98.3) and
        # 24250's pe_low (120.1) - the engineering default (lowest
        # strike) picks 24200.
        wide_ce = MarketSnapshot(
            timestamp=_TS,
            underlying_price=Decimal(24140),
            open=Decimal("98.3"),
            high=Decimal("120.1"),
            low=Decimal("98.3"),
            close=Decimal("120.1"),
        )
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=wide_ce,
            own_pe_snapshot=_tight_candle(Decimal("121.5")),
            candle_timestamp=_TS,
        )
        assert signal is not None
        assert signal.entry_strike == Decimal(24200)
        assert signal.entry_level == Decimal("98.3")


class TestAdjacentColumnValuesDirect:
    """Direct tests for the private helper's own defensive branch -
    unreachable via evaluate() (entry_strike always comes from a
    level actually present in reference_levels), but tested directly
    since this codebase's own convention favours a real test over a
    pragma for every branch."""

    def test_strike_not_in_ladder_returns_none_none(self) -> None:
        target, stop_loss = QualificationEngine._adjacent_column_values(
            _LADDER, "pe_low", Decimal(99999), TradeDirection.CE
        )
        assert target is None
        assert stop_loss is None


class TestValidation:
    def test_empty_reference_levels_raises(self) -> None:
        with pytest.raises(ValidationError, match="non-empty reference ladder"):
            QualificationEngine().evaluate(
                anchor_role=AnchorRole.TOP,
                trend=TrendDirection.BULLISH,
                reference_levels=(),
                own_ce_snapshot=_tight_candle(Decimal("120.1")),
                own_pe_snapshot=_tight_candle(Decimal("121.5")),
                candle_timestamp=_TS,
            )

    def test_non_candle_ce_snapshot_raises(self) -> None:
        tick = MarketSnapshot(timestamp=_TS, underlying_price=Decimal(24140))
        with pytest.raises(ValidationError, match="candle-mode snapshots"):
            QualificationEngine().evaluate(
                anchor_role=AnchorRole.TOP,
                trend=TrendDirection.BULLISH,
                reference_levels=_LADDER,
                own_ce_snapshot=tick,
                own_pe_snapshot=_tight_candle(Decimal("121.5")),
                candle_timestamp=_TS,
            )

    def test_non_candle_pe_snapshot_raises(self) -> None:
        tick = MarketSnapshot(timestamp=_TS, underlying_price=Decimal(24140))
        with pytest.raises(ValidationError, match="candle-mode snapshots"):
            QualificationEngine().evaluate(
                anchor_role=AnchorRole.TOP,
                trend=TrendDirection.BULLISH,
                reference_levels=_LADDER,
                own_ce_snapshot=_tight_candle(Decimal("120.1")),
                own_pe_snapshot=tick,
                candle_timestamp=_TS,
            )

    def test_default_id_factory_produces_a_uuid(self) -> None:
        signal = QualificationEngine().evaluate(
            anchor_role=AnchorRole.TOP,
            trend=TrendDirection.BULLISH,
            reference_levels=_LADDER,
            own_ce_snapshot=_tight_candle(Decimal("120.1")),
            own_pe_snapshot=_tight_candle(Decimal("121.5")),
            candle_timestamp=_TS,
        )
        assert signal is not None
        assert isinstance(signal.signal_id, uuid.UUID)

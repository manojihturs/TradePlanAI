"""Tests for capital_ledger.capital_ledger."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from capital_ledger.capital_ledger import DEFAULT_LOT_SIZE, CapitalLedger
from core.enums import AnchorRole, ExitReason, TradeDirection
from core.exceptions import ValidationError
from models.qualified_position import QualifiedPosition

_TS = datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


def _position(**overrides: object) -> QualifiedPosition:
    fields: dict[str, object] = {
        "position_id": uuid.uuid4(),
        "anchor_role": AnchorRole.TOP,
        "side": TradeDirection.CE,
        "entry_strike": Decimal(24250),
        "entry_level": Decimal("120.1"),
        "target_level": Decimal("145.2"),
        "stop_loss_level": Decimal("98.3"),
        "competitor_exit_level": Decimal("121.5"),
        "opened_at": _TS,
    }
    fields.update(overrides)
    return QualifiedPosition(**fields)  # type: ignore[arg-type]


class TestConstruction:
    def test_default_lot_size_is_65(self) -> None:
        ledger = CapitalLedger(starting_capital=Decimal(50000))

        assert ledger.lot_size == DEFAULT_LOT_SIZE
        assert DEFAULT_LOT_SIZE == 65

    def test_starting_balance_equals_starting_capital(self) -> None:
        ledger = CapitalLedger(starting_capital=Decimal(50000))

        assert ledger.starting_capital == Decimal(50000)
        assert ledger.balance == Decimal(50000)
        assert ledger.realized_pnl == Decimal(0)
        assert ledger.trade_count == 0

    def test_non_positive_starting_capital_raises(self) -> None:
        with pytest.raises(ValidationError, match="starting_capital must be greater than 0"):
            CapitalLedger(starting_capital=Decimal(0))

    def test_non_positive_lot_size_raises(self) -> None:
        with pytest.raises(ValidationError, match="lot_size must be greater than 0"):
            CapitalLedger(starting_capital=Decimal(50000), lot_size=0)


class TestRecordClose:
    def test_winning_trade_increases_balance(self) -> None:
        ledger = CapitalLedger(starting_capital=Decimal(50000), lot_size=65)

        pnl = ledger.record_close(entry_level=Decimal("120.1"), exit_price=Decimal("145.2"))

        assert pnl == (Decimal("145.2") - Decimal("120.1")) * 65
        assert ledger.realized_pnl == pnl
        assert ledger.balance == Decimal(50000) + (Decimal("145.2") - Decimal("120.1")) * 65
        assert ledger.trade_count == 1

    def test_losing_trade_decreases_balance(self) -> None:
        ledger = CapitalLedger(starting_capital=Decimal(50000), lot_size=65)

        pnl = ledger.record_close(entry_level=Decimal("121.5"), exit_price=Decimal("103.2"))

        assert pnl == (Decimal("103.2") - Decimal("121.5")) * 65
        assert ledger.balance == Decimal(50000) + pnl
        assert pnl < 0

    def test_multiple_trades_accumulate(self) -> None:
        ledger = CapitalLedger(starting_capital=Decimal(50000), lot_size=65)

        ledger.record_close(Decimal("120.1"), Decimal("145.2"))
        ledger.record_close(Decimal("121.5"), Decimal("103.2"))

        expected = (Decimal("145.2") - Decimal("120.1")) * 65 + (
            Decimal("103.2") - Decimal("121.5")
        ) * 65
        assert ledger.realized_pnl == expected
        assert ledger.trade_count == 2


class TestRecordPosition:
    def test_records_pnl_from_closed_position(self) -> None:
        ledger = CapitalLedger(starting_capital=Decimal(50000), lot_size=65)
        position = _position().close(
            ExitReason.TARGET_HIT, datetime(2026, 7, 30, 9, 30, tzinfo=UTC), Decimal("145.2")
        )

        pnl = ledger.record_position(position)

        assert pnl == (Decimal("145.2") - Decimal("120.1")) * 65
        assert ledger.trade_count == 1

    def test_session_end_position_is_a_no_op(self) -> None:
        ledger = CapitalLedger(starting_capital=Decimal(50000), lot_size=65)
        position = _position().close(
            ExitReason.SESSION_END, datetime(2026, 7, 30, 15, 30, tzinfo=UTC)
        )

        pnl = ledger.record_position(position)

        assert pnl is None
        assert ledger.trade_count == 0
        assert ledger.balance == Decimal(50000)

    def test_active_position_raises(self) -> None:
        ledger = CapitalLedger(starting_capital=Decimal(50000))
        position = _position()

        with pytest.raises(ValidationError, match="requires a closed QualifiedPosition"):
            ledger.record_position(position)

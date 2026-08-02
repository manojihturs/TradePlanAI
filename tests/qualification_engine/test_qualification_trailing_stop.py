"""Tests for qualification_engine.qualification_trailing_stop."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from core.enums import AnchorRole, TradeDirection
from models.market_snapshot import MarketSnapshot
from models.qualified_position import QualifiedPosition
from qualification_engine.qualification_trailing_stop import (
    BreakevenFirstQualificationTrailingStop,
    NeverTriggersQualificationTrailingStop,
    QualificationTrailingStop,
)

_TIMESTAMP = datetime(2026, 7, 30, 9, 30, 0, tzinfo=UTC)


def _position(side: TradeDirection = TradeDirection.CE, **overrides: object) -> QualifiedPosition:
    fields: dict[str, object] = {
        "position_id": uuid.uuid4(),
        "anchor_role": AnchorRole.TOP,
        "side": side,
        "entry_strike": Decimal(24250),
        "entry_level": Decimal("120.1"),
        "target_level": Decimal("145.2"),
        "stop_loss_level": Decimal("98.3"),
        "competitor_exit_level": Decimal("121.5"),
        "opened_at": _TIMESTAMP,
    }
    fields.update(overrides)
    return QualifiedPosition(**fields)  # type: ignore[arg-type]


def _snapshot() -> MarketSnapshot:
    return MarketSnapshot(timestamp=_TIMESTAMP, underlying_price=Decimal(24140))


def _candle(low: str, high: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=_TIMESTAMP,
        underlying_price=Decimal(24140),
        open=Decimal(low),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(high),
    )


class TestNeverTriggersQualificationTrailingStop:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(NeverTriggersQualificationTrailingStop(), QualificationTrailingStop)

    def test_always_returns_false(self) -> None:
        assert NeverTriggersQualificationTrailingStop().check(_position(), _snapshot()) is False


def test_object_without_check_does_not_satisfy_protocol() -> None:
    class NotATrailingStop:
        pass

    assert not isinstance(NotATrailingStop(), QualificationTrailingStop)


class TestBreakevenFirstQualificationTrailingStop:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(BreakevenFirstQualificationTrailingStop(), QualificationTrailingStop)

    def test_below_activation_threshold_returns_false(self) -> None:
        tsl = BreakevenFirstQualificationTrailingStop()
        position = _position()

        # entry 120.1, high 123.05 -> profit 2.95, below the 3-point activation.
        result = tsl.check(position, _candle("122.90", "123.05"))

        assert result is False

    def test_at_activation_no_pullback_touch_returns_false(self) -> None:
        tsl = BreakevenFirstQualificationTrailingStop()
        position = _position()

        # profit 3.10 (>= 3) activates at breakeven (120.1) - this candle
        # never comes back down to it.
        result = tsl.check(position, _candle("123.05", "123.20"))

        assert result is False

    def test_activation_then_pullback_to_breakeven_triggers(self) -> None:
        tsl = BreakevenFirstQualificationTrailingStop()
        position = _position()

        first = tsl.check(position, _candle("123.05", "123.20"))
        second = tsl.check(position, _candle("120.00", "120.20"))

        assert first is False
        assert second is True

    def test_step_ratio_moves_trail_by_2_per_5_favourable_points(self) -> None:
        tsl = BreakevenFirstQualificationTrailingStop()
        position = _position()

        # profit 8.0 -> one full step of 5 beyond activation -> trail = 120.1 + 2 = 122.1.
        first = tsl.check(position, _candle("127.90", "128.10"))
        # pullback exactly to the stepped trail (122.1), not merely breakeven.
        second = tsl.check(position, _candle("122.00", "122.20"))

        assert first is False
        assert second is True

    def test_high_water_mark_persists_across_candles_not_just_local_extreme(self) -> None:
        tsl = BreakevenFirstQualificationTrailingStop()
        position = _position()

        # Peak profit 8.0 on the first candle -> trail should end up at 122.1
        # and stay there even though this later candle's OWN high (122.5) is
        # far below the earlier peak (128.1) - proves the engine remembers
        # the running high-water mark, not just this candle's own range.
        first = tsl.check(position, _candle("127.90", "128.10"))
        second = tsl.check(position, _candle("122.00", "122.50"))

        assert first is False
        assert second is True

    def test_pe_side_trails_downward(self) -> None:
        tsl = BreakevenFirstQualificationTrailingStop()
        position = _position(side=TradeDirection.PE)

        # PE favourable direction is downward: profit = entry - low.
        first = tsl.check(position, _candle("116.90", "117.10"))
        second = tsl.check(position, _candle("120.00", "120.20"))

        assert first is False
        assert second is True

    def test_new_position_id_resets_tracked_state(self) -> None:
        tsl = BreakevenFirstQualificationTrailingStop()
        first_position = _position()
        tsl.check(first_position, _candle("127.90", "128.10"))

        second_position = _position(entry_level=Decimal("50.0"))
        # If state were not reset, the stale high-water mark (128.10) would
        # make this candle appear to already be far in profit for the new
        # position. With a correct reset, profit is only 0.2 - below
        # activation - so this must return False.
        result = tsl.check(second_position, _candle("50.10", "50.30"))

        assert result is False

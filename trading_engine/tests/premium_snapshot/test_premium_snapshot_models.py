"""Tests for ContractSnapshot and PremiumSnapshot structural validation."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from trading_engine.market_data.instrument_resolver import OptionType
from trading_engine.premium_snapshot.exceptions import SnapshotValidationError
from trading_engine.premium_snapshot.premium_snapshot_models import (
    ContractSnapshot,
    PremiumSnapshot,
)


def _contract(instrument, timestamp: datetime, **overrides: object) -> ContractSnapshot:
    fields: dict[str, object] = {
        "instrument": instrument,
        "strike": Decimal(24000),
        "option_type": OptionType.CALL,
        "timestamp": timestamp,
        "open": Decimal(100),
        "high": Decimal(110),
        "low": Decimal(95),
        "close": Decimal(105),
        "last_traded_price": Decimal(105),
        "volume": 1000,
        "open_interest": 5000,
    }
    fields.update(overrides)
    return ContractSnapshot(**fields)  # type: ignore[arg-type]


class TestContractSnapshot:
    def test_valid_construction(self, top_ce_instrument, window_start: datetime) -> None:
        contract = _contract(top_ce_instrument, window_start)
        assert contract.close == Decimal(105)

    def test_high_below_low_raises(self, top_ce_instrument, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="high .* is less than low"):
            _contract(top_ce_instrument, window_start, high=Decimal(90), low=Decimal(95))

    def test_open_outside_range_raises(self, top_ce_instrument, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="open .* is outside"):
            _contract(top_ce_instrument, window_start, open=Decimal(200))

    def test_close_outside_range_raises(self, top_ce_instrument, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="close .* is outside"):
            _contract(top_ce_instrument, window_start, close=Decimal(1))

    def test_non_positive_strike_raises(self, top_ce_instrument, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="strike must be greater than 0"):
            _contract(top_ce_instrument, window_start, strike=Decimal(0))

    def test_non_positive_ltp_raises(self, top_ce_instrument, window_start: datetime) -> None:
        with pytest.raises(
            SnapshotValidationError, match="last_traded_price must be greater than 0"
        ):
            _contract(top_ce_instrument, window_start, last_traded_price=Decimal(0))

    def test_negative_volume_raises(self, top_ce_instrument, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="volume must not be negative"):
            _contract(top_ce_instrument, window_start, volume=-1)

    def test_negative_open_interest_raises(self, top_ce_instrument, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="open_interest must not be negative"):
            _contract(top_ce_instrument, window_start, open_interest=-1)

    def test_none_instrument_raises(self, window_start: datetime) -> None:
        with pytest.raises(SnapshotValidationError, match="instrument must not be None"):
            _contract(None, window_start)  # type: ignore[arg-type]

    def test_none_timestamp_raises(self, top_ce_instrument) -> None:
        with pytest.raises(SnapshotValidationError, match="timestamp must not be None"):
            _contract(top_ce_instrument, None)  # type: ignore[arg-type]


class TestPremiumSnapshot:
    def _snapshot(
        self,
        session_id: uuid.UUID,
        window_start: datetime,
        window_end: datetime,
        top_ce_instrument,
        **overrides: object,
    ) -> PremiumSnapshot:
        contract = _contract(top_ce_instrument, window_start)
        fields: dict[str, object] = {
            "snapshot_id": uuid.uuid4(),
            "session_id": session_id,
            "capture_window_start": window_start,
            "capture_window_end": window_end,
            "top_strike": Decimal(24000),
            "bottom_strike": Decimal(23900),
            "top_ce": contract,
            "top_pe": None,
            "bottom_ce": None,
            "bottom_pe": None,
        }
        fields.update(overrides)
        return PremiumSnapshot(**fields)  # type: ignore[arg-type]

    def test_valid_construction(
        self, session_id: uuid.UUID, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        snapshot = self._snapshot(session_id, window_start, window_end, top_ce_instrument)
        assert snapshot.top_strike == Decimal(24000)

    def test_window_end_not_after_start_raises(
        self, session_id: uuid.UUID, window_start: datetime, top_ce_instrument
    ) -> None:
        with pytest.raises(SnapshotValidationError, match="capture_window_end must be after"):
            self._snapshot(session_id, window_start, window_start, top_ce_instrument)

    def test_none_snapshot_id_raises(
        self, session_id: uuid.UUID, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        with pytest.raises(SnapshotValidationError, match="snapshot_id must not be None"):
            self._snapshot(
                session_id, window_start, window_end, top_ce_instrument, snapshot_id=None
            )

    def test_none_session_id_raises(
        self, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        with pytest.raises(SnapshotValidationError, match="session_id must not be None"):
            self._snapshot(None, window_start, window_end, top_ce_instrument)  # type: ignore[arg-type]

    def test_none_window_bounds_raise(
        self, session_id: uuid.UUID, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        with pytest.raises(SnapshotValidationError, match="capture window bounds must not be None"):
            self._snapshot(
                session_id, window_start, window_end, top_ce_instrument, capture_window_start=None
            )

    def test_non_positive_top_strike_raises(
        self, session_id: uuid.UUID, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        with pytest.raises(SnapshotValidationError, match="top_strike must be greater than 0"):
            self._snapshot(
                session_id, window_start, window_end, top_ce_instrument, top_strike=Decimal(0)
            )

    def test_non_positive_bottom_strike_raises(
        self, session_id: uuid.UUID, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        with pytest.raises(SnapshotValidationError, match="bottom_strike must be greater than 0"):
            self._snapshot(
                session_id, window_start, window_end, top_ce_instrument, bottom_strike=Decimal(0)
            )

    def test_core_contracts_returns_only_captured(
        self, session_id: uuid.UUID, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        snapshot = self._snapshot(session_id, window_start, window_end, top_ce_instrument)
        assert snapshot.core_contracts() == (snapshot.top_ce,)
        assert snapshot.missing_core_contract_count() == 3

    def test_all_contracts_missing(
        self, session_id: uuid.UUID, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        snapshot = self._snapshot(
            session_id, window_start, window_end, top_ce_instrument, top_ce=None
        )
        assert snapshot.core_contracts() == ()
        assert snapshot.missing_core_contract_count() == 4

    def test_range_contracts_default_empty(
        self, session_id: uuid.UUID, window_start: datetime, window_end: datetime, top_ce_instrument
    ) -> None:
        snapshot = self._snapshot(session_id, window_start, window_end, top_ce_instrument)
        assert snapshot.range_contracts == ()

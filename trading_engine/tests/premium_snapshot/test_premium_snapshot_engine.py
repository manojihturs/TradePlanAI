"""Tests for PremiumSnapshotEngine: capture timing, OHLC aggregation,
missing contracts, duplicate ticks, diagnostics."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from trading_engine.diagnostics.sink import InMemoryDiagnosticsSink
from trading_engine.market_data.instrument_resolver import OptionType
from trading_engine.premium_snapshot.exceptions import SnapshotCaptureError
from trading_engine.premium_snapshot.premium_snapshot_engine import (
    DEFAULT_CAPTURE_WINDOW,
    PremiumSnapshotEngine,
)
from trading_engine.premium_snapshot.premium_snapshot_events import (
    SnapshotCompleted,
    SnapshotStarted,
)
from trading_engine.tests.premium_snapshot.conftest import make_tick


@pytest.fixture
def engine() -> PremiumSnapshotEngine:
    return PremiumSnapshotEngine()


@pytest.fixture
def sink() -> InMemoryDiagnosticsSink:
    return InMemoryDiagnosticsSink()


@pytest.fixture
def engine_with_sink(sink: InMemoryDiagnosticsSink) -> PremiumSnapshotEngine:
    return PremiumSnapshotEngine(diagnostics_sink=sink)


class TestConstruction:
    def test_default_capture_window_is_5_minutes(self) -> None:
        assert DEFAULT_CAPTURE_WINDOW == timedelta(minutes=5)

    def test_capture_window_is_configurable(
        self,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine = PremiumSnapshotEngine(capture_window=timedelta(minutes=10))
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        tick_at_9 = make_tick(top_ce_instrument, window_start + timedelta(minutes=9), "100")
        assert engine.ingest_tick(tick_at_9) is True

    def test_non_positive_capture_window_raises(self) -> None:
        with pytest.raises(
            SnapshotCaptureError, match="capture_window must be a positive duration"
        ):
            PremiumSnapshotEngine(capture_window=timedelta(0))


class TestCaptureLifecycle:
    def test_complete_capture_without_start_raises(self, engine: PremiumSnapshotEngine) -> None:
        with pytest.raises(SnapshotCaptureError, match="No capture is in progress"):
            engine.complete_capture()

    def test_double_start_raises(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        with pytest.raises(SnapshotCaptureError, match="already in progress"):
            engine.start_capture(
                session_id,
                window_start,
                Decimal(24000),
                Decimal(23900),
                top_ce_instrument,
                top_pe_instrument,
                bottom_ce_instrument,
                bottom_pe_instrument,
            )

    def test_ingest_tick_without_start_returns_false(
        self, engine: PremiumSnapshotEngine, top_ce_instrument, window_start: datetime
    ) -> None:
        tick = make_tick(top_ce_instrument, window_start, "100")
        assert engine.ingest_tick(tick) is False

    def test_capture_can_restart_after_completion(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        engine.complete_capture()
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        snapshot = engine.complete_capture()
        assert snapshot.session_id == session_id


class TestOHLCCapture:
    def test_open_high_low_close_aggregation(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        window_end: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        engine.ingest_tick(
            make_tick(top_ce_instrument, window_start, "100", volume=10, open_interest=200)
        )
        engine.ingest_tick(
            make_tick(
                top_ce_instrument,
                window_start + timedelta(minutes=1),
                "120",
                volume=20,
                open_interest=210,
            )
        )
        engine.ingest_tick(
            make_tick(
                top_ce_instrument,
                window_start + timedelta(minutes=2),
                "90",
                volume=30,
                open_interest=220,
            )
        )
        engine.ingest_tick(
            make_tick(
                top_ce_instrument,
                window_start + timedelta(minutes=3),
                "110",
                volume=40,
                open_interest=230,
            )
        )
        snapshot = engine.complete_capture()

        assert snapshot.top_ce is not None
        assert snapshot.top_ce.open == Decimal(100)
        assert snapshot.top_ce.high == Decimal(120)
        assert snapshot.top_ce.low == Decimal(90)
        assert snapshot.top_ce.close == Decimal(110)
        assert snapshot.top_ce.last_traded_price == Decimal(110)
        assert snapshot.top_ce.volume == 40
        assert snapshot.top_ce.open_interest == 230
        assert snapshot.top_ce.option_type == OptionType.CALL
        assert snapshot.top_ce.strike == Decimal(24000)

    def test_tick_outside_window_ignored(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        window_end: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        before_window = make_tick(top_ce_instrument, window_start - timedelta(seconds=1), "50")
        after_window = make_tick(top_ce_instrument, window_end + timedelta(seconds=1), "999")
        assert engine.ingest_tick(before_window) is False
        assert engine.ingest_tick(after_window) is False
        snapshot = engine.complete_capture()
        assert snapshot.top_ce is None

    def test_unrecognised_instrument_ignored(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        from trading_engine.market_data.instrument_resolver import InstrumentKey

        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        other = InstrumentKey(token="NSE_FO|999", symbol="OTHER", exchange="NSE_FO")
        tick = make_tick(other, window_start, "100")
        assert engine.ingest_tick(tick) is False


class TestMissingContracts:
    def test_missing_contracts_do_not_fail(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        engine.ingest_tick(make_tick(top_ce_instrument, window_start, "100"))
        snapshot = engine.complete_capture()
        assert snapshot.top_ce is not None
        assert snapshot.top_pe is None
        assert snapshot.bottom_ce is None
        assert snapshot.bottom_pe is None
        assert snapshot.missing_core_contract_count() == 3

    def test_all_missing_produces_snapshot_with_no_core_contracts(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        snapshot = engine.complete_capture()
        assert snapshot.core_contracts() == ()


class TestRangeContracts:
    def test_best_effort_range_contracts_captured(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        from trading_engine.market_data.instrument_resolver import InstrumentKey

        range_instrument = InstrumentKey(
            token="NSE_FO|500", symbol="NIFTY24070124100CE", exchange="NSE_FO"
        )
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
            range_instruments=((range_instrument, Decimal(24100), OptionType.CALL),),
        )
        engine.ingest_tick(make_tick(range_instrument, window_start, "50"))
        snapshot = engine.complete_capture()
        assert len(snapshot.range_contracts) == 1
        assert snapshot.range_contracts[0].instrument == range_instrument

    def test_unavailable_range_contract_omitted_not_failed(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        from trading_engine.market_data.instrument_resolver import InstrumentKey

        range_instrument = InstrumentKey(
            token="NSE_FO|500", symbol="NIFTY24070124100CE", exchange="NSE_FO"
        )
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
            range_instruments=((range_instrument, Decimal(24100), OptionType.CALL),),
        )
        snapshot = engine.complete_capture()
        assert snapshot.range_contracts == ()


class TestDuplicateTicks:
    def test_duplicate_timestamp_tick_ignored(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        first = make_tick(top_ce_instrument, window_start, "100", volume=10)
        duplicate = make_tick(top_ce_instrument, window_start, "999", volume=999)
        assert engine.ingest_tick(first) is True
        assert engine.ingest_tick(duplicate) is False
        snapshot = engine.complete_capture()
        assert snapshot.top_ce is not None
        assert snapshot.top_ce.close == Decimal(100)
        assert snapshot.top_ce.volume == 10


class TestDiagnostics:
    def test_snapshot_started_and_completed_emitted(
        self,
        engine_with_sink: PremiumSnapshotEngine,
        sink: InMemoryDiagnosticsSink,
        session_id: uuid.UUID,
        window_start: datetime,
        window_end: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine_with_sink.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        engine_with_sink.ingest_tick(make_tick(top_ce_instrument, window_start, "100"))
        engine_with_sink.complete_capture()

        events = sink.events()
        assert len(events) == 2
        assert isinstance(events[0], SnapshotStarted)
        assert events[0].session_id == session_id
        assert events[0].window_start == window_start
        assert events[0].window_end == window_end
        assert isinstance(events[1], SnapshotCompleted)
        assert events[1].captured_contract_count == 1
        assert events[1].missing_contract_count == 3

    def test_no_sink_uses_null_sink_without_error(
        self,
        engine: PremiumSnapshotEngine,
        session_id: uuid.UUID,
        window_start: datetime,
        top_ce_instrument,
        top_pe_instrument,
        bottom_ce_instrument,
        bottom_pe_instrument,
    ) -> None:
        engine.start_capture(
            session_id,
            window_start,
            Decimal(24000),
            Decimal(23900),
            top_ce_instrument,
            top_pe_instrument,
            bottom_ce_instrument,
            bottom_pe_instrument,
        )
        engine.complete_capture()

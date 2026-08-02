"""Tests for live_session.live_session_runner."""

from __future__ import annotations

import gzip
import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from backtest.runner import BacktestResult
from capital_ledger.capital_ledger import CapitalLedger
from core.enums import AnchorRole, ExitReason, TradeDirection, TrendDirection
from core.exceptions import HistoricalDataError
from live_session.live_session_runner import LiveSessionRunner
from models.qualified_position import QualifiedPosition
from session_scheduler.session_scheduler import SessionScheduler

_IST = ZoneInfo("Asia/Kolkata")
_SESSION_DATE = date(2026, 7, 30)  # confirmed weekday
_EXPIRY = date(2026, 7, 31)
_ANCHOR = Decimal(24000)
_STRIKES = tuple(_ANCHOR + Decimal(i) * 50 for i in range(-6, 7))
_INDEX_KEY = "NSE_INDEX|Nifty 50"
_OPEN_MOMENT = datetime(2026, 7, 30, 10, 0, tzinfo=UTC)
_CLOSED_MOMENT = datetime(2026, 7, 30, 20, 0, tzinfo=UTC)


def _instrument_key(strike: Decimal, side: str) -> str:
    return f"NSE_FO|{strike}{side}"


def _instrument_master_bytes() -> bytes:
    rows = []
    expiry_ms = int(datetime(2026, 7, 31, 18, 30, tzinfo=_IST).timestamp() * 1000)
    for strike in _STRIKES:
        for side in ("CE", "PE"):
            rows.append(
                {
                    "segment": "NSE_FO",
                    "underlying_symbol": "NIFTY",
                    "instrument_type": side,
                    "expiry": expiry_ms,
                    "strike_price": float(strike),
                    "instrument_key": _instrument_key(strike, side),
                }
            )
    return gzip.compress(json.dumps(rows).encode())


def _candles_json(num_minutes: int = 20, start_price: float = 100.0) -> list[list[object]]:
    out = []
    t0 = datetime(2026, 7, 30, 9, 15, tzinfo=UTC)
    for m in range(num_minutes):
        ts = t0 + timedelta(minutes=m)
        price = start_price + m
        out.append([ts.isoformat(), price, price + 1, price - 1, price + 0.5, 10.0])
    return out


class _FakeRestClient:
    def __init__(self) -> None:
        self._master = _instrument_master_bytes()

    def get_bytes(self, url: str) -> bytes:
        return self._master

    def get_json(self, url: str, headers, params=None) -> object:
        return {"data": {"candles": _candles_json()}}


class _StubBacktestRunner:
    """Returns a pre-built sequence of results, one per call - the
    last one repeats for any extra calls."""

    def __init__(self, results: list[BacktestResult]) -> None:
        self._results = results
        self.call_count = 0

    def run(self, fixture, trend, underlying_index_candles=()):
        index = min(self.call_count, len(self._results) - 1)
        self.call_count += 1
        return self._results[index]


def _closed_position(**overrides: object) -> QualifiedPosition:
    fields: dict[str, object] = {
        "position_id": uuid.uuid4(),
        "anchor_role": AnchorRole.TOP,
        "side": TradeDirection.CE,
        "entry_strike": Decimal(24250),
        "entry_level": Decimal("120.1"),
        "target_level": Decimal("145.2"),
        "stop_loss_level": Decimal("98.3"),
        "competitor_exit_level": Decimal("121.5"),
        "opened_at": datetime(2026, 7, 30, 9, 20, tzinfo=UTC),
    }
    fields.update(overrides)
    position = QualifiedPosition(**fields)  # type: ignore[arg-type]
    return position.close(
        ExitReason.TARGET_HIT,
        datetime(2026, 7, 30, 9, 30, tzinfo=UTC),
        Decimal("145.2"),
    )


def _runner(
    backtest_runner: _StubBacktestRunner | None = None,
    capital_ledger: CapitalLedger | None = None,
    scheduler: SessionScheduler | None = None,
) -> LiveSessionRunner:
    return LiveSessionRunner(
        rest_client=_FakeRestClient(),
        access_token="fake-token",
        underlying_symbol="NIFTY",
        expiry=_EXPIRY,
        anchor_strike=_ANCHOR,
        session_date=_SESSION_DATE,
        trend=TrendDirection.BULLISH,
        capital_ledger=(
            capital_ledger if capital_ledger is not None else CapitalLedger(Decimal(50000))
        ),
        scheduler=scheduler,
        backtest_runner=backtest_runner,
    )


class TestSessionClosed:
    def test_poll_outside_session_hours_is_a_no_op(self) -> None:
        runner = _runner()

        result = runner.poll_once(_CLOSED_MOMENT)

        assert result.session_open is False
        assert result.newly_closed_positions == ()


class TestPolling:
    def test_first_poll_records_closed_positions(self) -> None:
        position = _closed_position()
        stub = _StubBacktestRunner(
            [BacktestResult(session_id=uuid.uuid4(), qualification_positions=(position,))]
        )
        ledger = CapitalLedger(Decimal(50000))
        runner = _runner(backtest_runner=stub, capital_ledger=ledger)

        result = runner.poll_once(_OPEN_MOMENT)

        assert result.session_open is True
        assert result.newly_closed_positions == (position,)
        assert ledger.trade_count == 1

    def test_second_poll_with_same_position_does_not_double_record(self) -> None:
        position = _closed_position()
        stub = _StubBacktestRunner(
            [BacktestResult(session_id=uuid.uuid4(), qualification_positions=(position,))]
        )
        ledger = CapitalLedger(Decimal(50000))
        runner = _runner(backtest_runner=stub, capital_ledger=ledger)

        runner.poll_once(_OPEN_MOMENT)
        second = runner.poll_once(_OPEN_MOMENT)

        assert second.newly_closed_positions == ()
        assert ledger.trade_count == 1

    def test_new_position_on_second_poll_is_recorded(self) -> None:
        first_position = _closed_position()
        second_position = _closed_position(
            entry_level=Decimal("98.3"), opened_at=datetime(2026, 7, 30, 10, 40, tzinfo=UTC)
        )
        stub = _StubBacktestRunner(
            [
                BacktestResult(session_id=uuid.uuid4(), qualification_positions=(first_position,)),
                BacktestResult(
                    session_id=uuid.uuid4(),
                    qualification_positions=(first_position, second_position),
                ),
            ]
        )
        ledger = CapitalLedger(Decimal(50000))
        runner = _runner(backtest_runner=stub, capital_ledger=ledger)

        runner.poll_once(_OPEN_MOMENT)
        second = runner.poll_once(_OPEN_MOMENT)

        assert second.newly_closed_positions == (second_position,)
        assert ledger.trade_count == 2

    def test_active_position_is_never_recorded(self) -> None:
        active_position = QualifiedPosition(
            position_id=uuid.uuid4(),
            anchor_role=AnchorRole.TOP,
            side=TradeDirection.CE,
            entry_strike=Decimal(24250),
            entry_level=Decimal("120.1"),
            target_level=Decimal("145.2"),
            stop_loss_level=Decimal("98.3"),
            competitor_exit_level=Decimal("121.5"),
            opened_at=datetime(2026, 7, 30, 9, 20, tzinfo=UTC),
        )
        stub = _StubBacktestRunner(
            [BacktestResult(session_id=uuid.uuid4(), qualification_positions=(active_position,))]
        )
        ledger = CapitalLedger(Decimal(50000))
        runner = _runner(backtest_runner=stub, capital_ledger=ledger)

        result = runner.poll_once(_OPEN_MOMENT)

        assert result.newly_closed_positions == ()
        assert ledger.trade_count == 0


class _NoCommonTimestampsRestClient(_FakeRestClient):
    def get_json(self, url: str, headers, params=None) -> object:
        if "NSE_INDEX" in url:
            return {"data": {"candles": _candles_json(start_price=9999.0)}}
        # Shift option candles onto a disjoint minute range so no
        # timestamp is ever shared with the index series below.
        out = []
        t0 = datetime(2026, 7, 30, 11, 15, tzinfo=UTC)
        for m in range(20):
            ts = t0 + timedelta(minutes=m)
            out.append([ts.isoformat(), 100.0 + m, 101.0 + m, 99.0 + m, 100.5 + m, 10.0])
        return {"data": {"candles": out}}


class TestNoCommonTimestamps:
    def test_raises_when_option_and_index_share_no_timestamp(self) -> None:
        runner = LiveSessionRunner(
            rest_client=_NoCommonTimestampsRestClient(),
            access_token="fake-token",
            underlying_symbol="NIFTY",
            expiry=_EXPIRY,
            anchor_strike=_ANCHOR,
            session_date=_SESSION_DATE,
            trend=TrendDirection.BULLISH,
            capital_ledger=CapitalLedger(Decimal(50000)),
        )

        with pytest.raises(HistoricalDataError, match="No candle timestamp is common"):
            runner.poll_once(_OPEN_MOMENT)


class TestRealFetchIntegration:
    def test_end_to_end_with_default_backtest_runner(self) -> None:
        # No stub - exercises the real fetch + BacktestRunner path
        # against the fake REST client, confirming the plumbing works
        # even if no trade qualifies on this synthetic data.
        runner = _runner()

        result = runner.poll_once(_OPEN_MOMENT)

        assert result.session_open is True
        assert isinstance(result.newly_closed_positions, tuple)

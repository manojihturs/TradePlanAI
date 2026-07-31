"""Tests for backtest.upstox_dataset_builder."""

from __future__ import annotations

import gzip
import json
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from backtest.upstox_dataset_builder import build_upstox_fixture
from core.exceptions import HistoricalDataError

_IST = ZoneInfo("Asia/Kolkata")
_SESSION_DATE = date(2026, 7, 30)
_EXPIRY = date(2026, 7, 31)
_ANCHOR = Decimal(24000)
_STRIKES = tuple(_ANCHOR + Decimal(i) * 50 for i in range(-6, 7))


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
    """Every instrument gets the same candle shape by default; a
    per-instrument override dict lets tests simulate gaps."""

    def __init__(self, overrides: dict[str, list[list[object]]] | None = None) -> None:
        self._master = _instrument_master_bytes()
        self._overrides = overrides or {}

    def get_bytes(self, url: str) -> bytes:
        return self._master

    def get_json(self, url: str, headers, params=None) -> object:
        instrument_key = url.split("/historical-candle/")[1].split("/minutes/")[0]
        candles = self._overrides.get(instrument_key, _candles_json())
        return {"data": {"candles": candles}}


class TestSuccessfulBuild:
    def test_builds_fixture_with_correct_shape(self) -> None:
        client = _FakeRestClient()

        fixture = build_upstox_fixture(
            rest_client=client,
            access_token="fake-token",
            underlying_symbol="NIFTY",
            expiry=_EXPIRY,
            anchor_strike=_ANCHOR,
            session_date=_SESSION_DATE,
        )

        assert fixture.session_date == _SESSION_DATE
        assert fixture.anchor_strike == _ANCHOR
        assert len(fixture.reference_inputs) == 13
        assert {row.strike for row in fixture.reference_inputs} == set(_STRIKES)
        # 20 one-minute candles resampled to 5-minute buckets = 4 buckets;
        # first bucket becomes the reference input, remaining 3 the dataset.
        assert len(fixture.dataset.candles) == 3

    def test_custom_candle_minutes_and_market_open(self) -> None:
        client = _FakeRestClient()

        fixture = build_upstox_fixture(
            rest_client=client,
            access_token="fake-token",
            underlying_symbol="NIFTY",
            expiry=_EXPIRY,
            anchor_strike=_ANCHOR,
            session_date=_SESSION_DATE,
            market_open=time(9, 15),
            candle_minutes=10,
        )

        # 20 one-minute candles resampled to 10-minute buckets = 2 buckets;
        # first bucket becomes the reference input, remaining 1 the dataset.
        assert len(fixture.dataset.candles) == 1

    def test_every_candle_carries_all_13_strikes(self) -> None:
        client = _FakeRestClient()

        fixture = build_upstox_fixture(
            rest_client=client,
            access_token="fake-token",
            underlying_symbol="NIFTY",
            expiry=_EXPIRY,
            anchor_strike=_ANCHOR,
            session_date=_SESSION_DATE,
        )

        for candle in fixture.dataset.candles:
            assert len(candle.strikes) == 13


class TestDataGaps:
    def test_strike_with_only_pre_market_candles_raises(self) -> None:
        # Candles that exist but are entirely before market_open (09:15)
        # are filtered out by resample_candles - a different gap than
        # HistoricalDataProvider's own "zero rows" check catches.
        missing_key = _instrument_key(_STRIKES[0], "CE")
        pre_market_only = [
            [f"2026-07-30T09:{minute:02d}:00", 100.0, 101.0, 99.0, 100.0, 10.0]
            for minute in range(10)
        ]
        client = _FakeRestClient(overrides={missing_key: pre_market_only})

        with pytest.raises(HistoricalDataError, match="No candles resampled"):
            build_upstox_fixture(
                rest_client=client,
                access_token="fake-token",
                underlying_symbol="NIFTY",
                expiry=_EXPIRY,
                anchor_strike=_ANCHOR,
                session_date=_SESSION_DATE,
            )

    def test_no_common_timestamps_raises(self) -> None:
        # Give the anchor strike's CE series a completely disjoint set
        # of timestamps from every other instrument.
        anchor_ce_key = _instrument_key(_ANCHOR, "CE")
        disjoint_candles = _candles_json(num_minutes=20)
        # Shift every timestamp by 3 hours so none overlap with the
        # default series used by every other instrument.
        shifted = []
        for row in disjoint_candles:
            ts = datetime.fromisoformat(str(row[0])) + timedelta(hours=3)
            shifted.append([ts.isoformat(), *row[1:]])
        client = _FakeRestClient(overrides={anchor_ce_key: shifted})

        with pytest.raises(HistoricalDataError, match="No candle timestamp is present"):
            build_upstox_fixture(
                rest_client=client,
                access_token="fake-token",
                underlying_symbol="NIFTY",
                expiry=_EXPIRY,
                anchor_strike=_ANCHOR,
                session_date=_SESSION_DATE,
            )

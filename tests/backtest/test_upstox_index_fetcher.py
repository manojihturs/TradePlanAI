"""Tests for backtest.upstox_index_fetcher."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from backtest.upstox_index_fetcher import (
    NIFTY_50_INSTRUMENT_KEY,
    fetch_underlying_index_candles,
)
from core.exceptions import HistoricalDataError


def _candles_json(num_minutes: int = 10, start_price: float = 24000.0) -> list[list[object]]:
    out = []
    t0 = datetime(2026, 7, 30, 9, 15, tzinfo=UTC)
    for m in range(num_minutes):
        ts = t0 + timedelta(minutes=m)
        price = start_price + m
        out.append([ts.isoformat(), price, price + 5, price - 5, price + 2, 0.0])
    return out


class _FakeRestClient:
    def __init__(self, candles: list[list[object]]) -> None:
        self._candles = candles
        self.last_url: str | None = None

    def get_json(self, url: str, headers, params=None) -> object:
        self.last_url = url
        return {"data": {"candles": self._candles}}

    def get_bytes(self, url: str) -> bytes:
        raise NotImplementedError


class TestFetchUnderlyingIndexCandles:
    def test_fetches_resamples_and_uses_the_index_instrument_key(self) -> None:
        client = _FakeRestClient(_candles_json())

        candles = fetch_underlying_index_candles(
            rest_client=client, access_token="fake-token", session_date=date(2026, 7, 30)
        )

        assert NIFTY_50_INSTRUMENT_KEY in (client.last_url or "")
        assert len(candles) == 2  # 10 one-minute candles resampled into 5-minute buckets
        assert candles[0].close == Decimal("24006.0")

    def test_custom_instrument_key_is_used(self) -> None:
        client = _FakeRestClient(_candles_json())

        fetch_underlying_index_candles(
            rest_client=client,
            access_token="fake-token",
            session_date=date(2026, 7, 30),
            instrument_key="NSE_INDEX|Custom",
        )

        assert "NSE_INDEX|Custom" in (client.last_url or "")

    def test_no_candles_raises(self) -> None:
        client = _FakeRestClient([])

        with pytest.raises(HistoricalDataError):
            fetch_underlying_index_candles(
                rest_client=client, access_token="fake-token", session_date=date(2026, 7, 30)
            )

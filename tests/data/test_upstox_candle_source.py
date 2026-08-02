"""Tests for data.upstox_candle_source."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import HistoricalDataError
from data.historical_data_provider import HistoricalDataProvider
from data.upstox_candle_source import UpstoxCandleSource


class _FakeRestClient:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.last_url: str | None = None
        self.last_headers: dict[str, str] | None = None

    def get_json(self, url: str, headers, params=None) -> object:
        self.last_url = url
        self.last_headers = dict(headers)
        return self.payload

    def get_bytes(self, url: str) -> bytes:
        raise NotImplementedError


def _source(payload: object) -> tuple[UpstoxCandleSource, _FakeRestClient]:
    client = _FakeRestClient(payload)
    source = UpstoxCandleSource(
        rest_client=client,
        access_token="fake-token",
        instrument_key="NSE_FO|12345",
        interval_minutes=1,
        day_from=date(2026, 7, 30),
        day_to=date(2026, 7, 30),
    )
    return source, client


class TestRequestShape:
    def test_url_and_headers(self) -> None:
        source, client = _source({"data": {"candles": []}})

        list(source.read_rows())

        assert client.last_url == (
            "https://api.upstox.com/v3/historical-candle/NSE_FO|12345/minutes/1/"
            "2026-07-30/2026-07-30"
        )
        assert client.last_headers == {
            "Authorization": "Bearer fake-token",
            "Accept": "application/json",
        }


class TestValidPayload:
    def test_single_row_converted_correctly(self) -> None:
        payload = {
            "data": {
                "candles": [
                    ["2026-07-30T09:15:00+05:30", 100.0, 105.0, 99.0, 102.5, 1000.0, 50.0],
                ]
            }
        }
        source, _ = _source(payload)

        rows = list(source.read_rows())

        assert rows == [
            {
                "Date": "2026-07-30",
                "Time": "09:15:00",
                "Open": "100.0",
                "High": "105.0",
                "Low": "99.0",
                "Close": "102.5",
                "Volume": "1000",
                "OpenInterest": "50",
            }
        ]

    def test_row_without_open_interest_omits_the_key(self) -> None:
        payload = {
            "data": {
                "candles": [
                    ["2026-07-30T09:15:00+05:30", 100.0, 105.0, 99.0, 102.5, 1000.0],
                ]
            }
        }
        source, _ = _source(payload)

        rows = list(source.read_rows())

        assert "OpenInterest" not in rows[0]

    def test_row_with_null_open_interest_omits_the_key(self) -> None:
        payload = {
            "data": {
                "candles": [
                    ["2026-07-30T09:15:00+05:30", 100.0, 105.0, 99.0, 102.5, 1000.0, None],
                ]
            }
        }
        source, _ = _source(payload)

        rows = list(source.read_rows())

        assert "OpenInterest" not in rows[0]

    def test_multiple_rows_preserve_order(self) -> None:
        payload = {
            "data": {
                "candles": [
                    ["2026-07-30T09:15:00+05:30", 100.0, 101.0, 99.0, 100.0, 10.0],
                    ["2026-07-30T09:16:00+05:30", 100.0, 102.0, 99.0, 101.0, 20.0],
                ]
            }
        }
        source, _ = _source(payload)

        rows = list(source.read_rows())

        assert [row["Time"] for row in rows] == ["09:15:00", "09:16:00"]

    def test_no_candles_yields_no_rows(self) -> None:
        source, _ = _source({"data": {"candles": []}})

        assert list(source.read_rows()) == []

    def test_integrates_with_historical_data_provider(self) -> None:
        payload = {
            "data": {
                "candles": [
                    ["2026-07-30T09:15:00+05:30", 100.0, 105.0, 99.0, 102.5, 1000.0],
                ]
            }
        }
        source, _ = _source(payload)

        dataset = HistoricalDataProvider().load(source, symbol="NSE_FO|12345", timeframe="1m")

        assert len(dataset.snapshots) == 1
        assert dataset.snapshots[0].close == Decimal("102.5")


class TestMalformedPayload:
    def test_payload_not_a_dict_raises(self) -> None:
        source, _ = _source(["not", "a", "dict"])

        with pytest.raises(HistoricalDataError, match="not a JSON object"):
            list(source.read_rows())

    def test_missing_data_key_raises(self) -> None:
        source, _ = _source({"foo": "bar"})

        with pytest.raises(HistoricalDataError, match="missing 'data' object"):
            list(source.read_rows())

    def test_missing_candles_key_raises(self) -> None:
        source, _ = _source({"data": {}})

        with pytest.raises(HistoricalDataError, match="missing 'data.candles' list"):
            list(source.read_rows())

    def test_row_not_a_list_raises(self) -> None:
        source, _ = _source({"data": {"candles": ["not-a-list"]}})

        with pytest.raises(HistoricalDataError, match="Malformed candle row"):
            list(source.read_rows())

    def test_row_too_short_raises(self) -> None:
        source, _ = _source({"data": {"candles": [["2026-07-30T09:15:00+05:30", 100.0]]}})

        with pytest.raises(HistoricalDataError, match="Malformed candle row"):
            list(source.read_rows())

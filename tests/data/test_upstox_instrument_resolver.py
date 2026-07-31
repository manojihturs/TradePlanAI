"""Tests for data.upstox_instrument_resolver."""

from __future__ import annotations

import gzip
import json
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from core.exceptions import HistoricalDataError
from data.upstox_instrument_resolver import UpstoxInstrumentResolver

_IST = ZoneInfo("Asia/Kolkata")
_EXPIRY = date(2026, 7, 31)


def _expiry_ms(expiry: date) -> int:
    return int(
        datetime(expiry.year, expiry.month, expiry.day, 18, 30, tzinfo=_IST).timestamp() * 1000
    )


def _row(
    strike: float,
    side: str,
    *,
    segment: str = "NSE_FO",
    underlying_symbol: str = "NIFTY",
    expiry: date = _EXPIRY,
    instrument_key: str | None = None,
) -> dict[str, object]:
    return {
        "segment": segment,
        "underlying_symbol": underlying_symbol,
        "instrument_type": side,
        "expiry": _expiry_ms(expiry),
        "strike_price": strike,
        "instrument_key": instrument_key or f"NSE_FO|{strike}{side}",
    }


class _FakeRestClient:
    def __init__(self, rows: object) -> None:
        self._rows = rows

    def get_json(self, url, headers, params=None):
        raise NotImplementedError

    def get_bytes(self, url: str) -> bytes:
        return gzip.compress(json.dumps(self._rows).encode())


def _resolver(rows: object) -> UpstoxInstrumentResolver:
    return UpstoxInstrumentResolver(rest_client=_FakeRestClient(rows))


_STRIKES = (Decimal(24000), Decimal(24050))


class TestSuccessfulResolution:
    def test_resolves_all_requested_strikes_and_sides(self) -> None:
        rows = [_row(24000, "CE"), _row(24000, "PE"), _row(24050, "CE"), _row(24050, "PE")]
        resolver = _resolver(rows)

        resolved = resolver.resolve_option_chain("NIFTY", _EXPIRY, _STRIKES)

        assert resolved == {
            (Decimal(24000), "CE"): "NSE_FO|24000CE",
            (Decimal(24000), "PE"): "NSE_FO|24000PE",
            (Decimal(24050), "CE"): "NSE_FO|24050CE",
            (Decimal(24050), "PE"): "NSE_FO|24050PE",
        }

    def test_ignores_strikes_not_requested(self) -> None:
        rows = [
            _row(24000, "CE"),
            _row(24000, "PE"),
            _row(24050, "CE"),
            _row(24050, "PE"),
            _row(24100, "CE"),
            _row(24100, "PE"),
        ]
        resolver = _resolver(rows)

        resolved = resolver.resolve_option_chain("NIFTY", _EXPIRY, _STRIKES)

        assert set(resolved) == {
            (Decimal(24000), "CE"),
            (Decimal(24000), "PE"),
            (Decimal(24050), "CE"),
            (Decimal(24050), "PE"),
        }


class TestFiltering:
    def test_wrong_segment_excluded(self) -> None:
        rows = [
            _row(24000, "CE", segment="NSE_EQ"),
            _row(24000, "PE"),
            _row(24050, "CE"),
            _row(24050, "PE"),
        ]
        with pytest.raises(HistoricalDataError, match="Missing"):
            _resolver(rows).resolve_option_chain("NIFTY", _EXPIRY, _STRIKES)

    def test_wrong_underlying_excluded(self) -> None:
        rows = [
            _row(24000, "CE", underlying_symbol="BANKNIFTY"),
            _row(24000, "PE"),
            _row(24050, "CE"),
            _row(24050, "PE"),
        ]
        with pytest.raises(HistoricalDataError, match="Missing"):
            _resolver(rows).resolve_option_chain("NIFTY", _EXPIRY, _STRIKES)

    def test_wrong_instrument_type_excluded(self) -> None:
        rows = [
            {**_row(24000, "CE"), "instrument_type": "FUT"},
            _row(24000, "PE"),
            _row(24050, "CE"),
            _row(24050, "PE"),
        ]
        with pytest.raises(HistoricalDataError, match="Missing"):
            _resolver(rows).resolve_option_chain("NIFTY", _EXPIRY, _STRIKES)

    def test_wrong_expiry_excluded(self) -> None:
        rows = [
            _row(24000, "CE", expiry=date(2026, 8, 7)),
            _row(24000, "PE"),
            _row(24050, "CE"),
            _row(24050, "PE"),
        ]
        with pytest.raises(HistoricalDataError, match="Missing"):
            _resolver(rows).resolve_option_chain("NIFTY", _EXPIRY, _STRIKES)

    def test_row_missing_expiry_field_skipped(self) -> None:
        rows = [{**_row(24000, "CE"), "expiry": None}, _row(24000, "PE")]
        with pytest.raises(HistoricalDataError, match="Missing"):
            _resolver(rows).resolve_option_chain("NIFTY", _EXPIRY, (Decimal(24000),))

    def test_non_dict_row_skipped(self) -> None:
        rows = ["not-a-dict", _row(24000, "CE"), _row(24000, "PE")]

        resolved = _resolver(rows).resolve_option_chain("NIFTY", _EXPIRY, (Decimal(24000),))

        assert (Decimal(24000), "CE") in resolved


class TestMissingContracts:
    def test_missing_contract_raises_with_details(self) -> None:
        rows = [_row(24000, "CE")]  # PE missing

        with pytest.raises(HistoricalDataError, match=r"\(Decimal\('24000'\), 'PE'\)"):
            _resolver(rows).resolve_option_chain("NIFTY", _EXPIRY, (Decimal(24000),))


class TestMalformedResponse:
    def test_not_valid_gzip_raises(self) -> None:
        class _BadRestClient:
            def get_json(self, url, headers, params=None):
                raise NotImplementedError

            def get_bytes(self, url: str) -> bytes:
                return b"not gzip data"

        with pytest.raises(HistoricalDataError, match="Could not parse"):
            UpstoxInstrumentResolver(rest_client=_BadRestClient()).resolve_option_chain(
                "NIFTY", _EXPIRY, (Decimal(24000),)
            )

    def test_non_list_json_raises(self) -> None:
        resolver = UpstoxInstrumentResolver(
            rest_client=_FakeRestClientRaw(gzip.compress(json.dumps({"not": "a list"}).encode()))
        )

        with pytest.raises(HistoricalDataError, match="not a JSON array"):
            resolver.resolve_option_chain("NIFTY", _EXPIRY, (Decimal(24000),))


class _FakeRestClientRaw:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    def get_json(self, url, headers, params=None):
        raise NotImplementedError

    def get_bytes(self, url: str) -> bytes:
        return self._raw

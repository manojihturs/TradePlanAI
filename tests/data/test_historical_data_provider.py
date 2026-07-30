"""Tests for data.historical_data_provider."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC
from pathlib import Path

import pytest

from core.exceptions import HistoricalDataError
from data.historical_data_provider import CsvHistoricalDataProvider, HistoricalDataProvider
from data.historical_data_source import CsvHistoricalDataSource
from data.historical_data_validation import HistoricalDataIssueKind

_HEADER = "Date,Time,Open,High,Low,Close,Volume"


class _FakeSource:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self._rows = rows

    def read_rows(self) -> Iterator[dict[str, str]]:
        yield from self._rows


def _row(
    date: str = "2026-07-30",
    time: str = "09:20:00",
    open_: str = "100",
    high: str = "110",
    low: str = "90",
    close: str = "105",
    volume: str = "1000",
    **extra: str,
) -> dict[str, str]:
    row = {
        "Date": date,
        "Time": time,
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
    }
    row.update(extra)
    return row


class TestSuccessfulLoad:
    def test_loads_and_sorts_valid_rows(self) -> None:
        provider = HistoricalDataProvider()
        source = _FakeSource([_row(time="09:21:00"), _row(time="09:20:00")])

        dataset = provider.load(source, symbol="NIFTY", timeframe="1m")

        assert dataset.symbol == "NIFTY"
        assert dataset.key == "NIFTY@1m"
        assert len(dataset.snapshots) == 2
        assert dataset.snapshots[0].timestamp < dataset.snapshots[1].timestamp
        assert dataset.metadata["row_count"] == "2"

    def test_underlying_price_defaults_to_close(self) -> None:
        provider = HistoricalDataProvider()
        source = _FakeSource([_row(close="105")])

        dataset = provider.load(source, symbol="NIFTY", timeframe="1m")

        assert dataset.snapshots[0].underlying_price == dataset.snapshots[0].close

    def test_underlying_price_column_is_used_when_present(self) -> None:
        provider = HistoricalDataProvider()
        source = _FakeSource([_row(UnderlyingPrice="24050")])

        dataset = provider.load(source, symbol="NIFTY", timeframe="1m")

        assert dataset.snapshots[0].underlying_price == 24050

    def test_tzinfo_is_applied(self) -> None:
        provider = HistoricalDataProvider()
        source = _FakeSource([_row()])

        dataset = provider.load(source, symbol="NIFTY", timeframe="1m", tzinfo=UTC)

        assert dataset.snapshots[0].timestamp.tzinfo is UTC


class TestValidateWithoutRaising:
    def test_validate_returns_report_without_raising(self) -> None:
        provider = HistoricalDataProvider()
        source = _FakeSource([_row(date="")])

        validation = provider.validate(source)

        assert validation.is_valid is False
        assert validation.issues_of(HistoricalDataIssueKind.MISSING_TIMESTAMP)


class TestEmptySource:
    def test_no_rows_raises_schema_error(self) -> None:
        provider = HistoricalDataProvider()

        with pytest.raises(HistoricalDataError, match="Source produced no rows"):
            provider.load(_FakeSource([]), symbol="NIFTY", timeframe="1m")


class TestMissingColumns:
    def test_missing_required_column_raises_schema_error(self) -> None:
        provider = HistoricalDataProvider()
        source = _FakeSource([{"Date": "2026-07-30", "Time": "09:20:00"}])

        with pytest.raises(HistoricalDataError, match="Missing required column"):
            provider.load(source, symbol="NIFTY", timeframe="1m")


class TestMissingTimestamp:
    def test_blank_date_is_missing_timestamp(self) -> None:
        provider = HistoricalDataProvider()
        validation = provider.validate(_FakeSource([_row(date="")]))

        assert validation.issues[0].kind is HistoricalDataIssueKind.MISSING_TIMESTAMP

    def test_blank_time_is_missing_timestamp(self) -> None:
        provider = HistoricalDataProvider()
        validation = provider.validate(_FakeSource([_row(time="")]))

        assert validation.issues[0].kind is HistoricalDataIssueKind.MISSING_TIMESTAMP


class TestUnparsableTimestamp:
    def test_unparsable_date_is_schema_error(self) -> None:
        provider = HistoricalDataProvider()
        validation = provider.validate(_FakeSource([_row(date="not-a-date")]))

        assert validation.issues[0].kind is HistoricalDataIssueKind.SCHEMA_ERROR


class TestDuplicateTimestamp:
    def test_duplicate_timestamp_detected(self) -> None:
        provider = HistoricalDataProvider()
        validation = provider.validate(_FakeSource([_row(), _row()]))

        assert len(validation.issues_of(HistoricalDataIssueKind.DUPLICATE_TIMESTAMP)) == 1
        assert validation.issues_of(HistoricalDataIssueKind.DUPLICATE_TIMESTAMP)[0].row_number == 2


class TestUnparsableNumericField:
    def test_non_numeric_open_is_schema_error(self) -> None:
        provider = HistoricalDataProvider()
        validation = provider.validate(_FakeSource([_row(open_="not-a-number")]))

        assert validation.issues[0].kind is HistoricalDataIssueKind.SCHEMA_ERROR

    def test_non_integer_volume_is_schema_error(self) -> None:
        provider = HistoricalDataProvider()
        validation = provider.validate(_FakeSource([_row(volume="1000.5")]))

        assert validation.issues[0].kind is HistoricalDataIssueKind.SCHEMA_ERROR


class TestInvalidOhlc:
    def test_high_less_than_low_is_invalid_ohlc(self) -> None:
        provider = HistoricalDataProvider()
        validation = provider.validate(_FakeSource([_row(high="50", low="90")]))

        assert validation.issues[0].kind is HistoricalDataIssueKind.INVALID_OHLC


class TestInvalidVolume:
    def test_negative_volume_is_invalid_volume(self) -> None:
        provider = HistoricalDataProvider()
        validation = provider.validate(_FakeSource([_row(volume="-1")]))

        assert validation.issues[0].kind is HistoricalDataIssueKind.INVALID_VOLUME


class TestErrorMessageSummary:
    def test_message_includes_row_and_kind(self) -> None:
        provider = HistoricalDataProvider()
        source = _FakeSource([_row(date="")])

        with pytest.raises(HistoricalDataError, match=r"row 1: MISSING_TIMESTAMP"):
            provider.load(source, symbol="NIFTY", timeframe="1m")

    def test_message_truncates_beyond_ten_issues(self) -> None:
        provider = HistoricalDataProvider()
        rows = [_row(date="") for _ in range(12)]

        with pytest.raises(HistoricalDataError, match=r"12 validation issue\(s\).*\.\.\.$"):
            provider.load(_FakeSource(rows), symbol="NIFTY", timeframe="1m")


class TestCsvHistoricalDataProvider:
    def test_load_csv_delegates_to_provider(self, tmp_path: Path) -> None:
        path = tmp_path / "nifty.csv"
        path.write_text(f"{_HEADER}\n2026-07-30,09:20:00,100,110,90,105,1000\n", encoding="utf-8")

        provider = CsvHistoricalDataProvider()
        dataset = provider.load_csv(path, symbol="NIFTY", timeframe="1m")

        assert dataset.key == "NIFTY@1m"
        assert len(dataset.snapshots) == 1

    def test_default_provider_is_constructed_when_none_injected(self, tmp_path: Path) -> None:
        path = tmp_path / "nifty.csv"
        path.write_text(f"{_HEADER}\n2026-07-30,09:20:00,100,110,90,105,1000\n", encoding="utf-8")

        provider = CsvHistoricalDataProvider(provider=HistoricalDataProvider())
        dataset = provider.load_csv(path, symbol="NIFTY", timeframe="1m")

        assert dataset.snapshots[0].underlying_price == dataset.snapshots[0].close

    def test_invalid_csv_raises_via_delegation(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.csv"
        path.write_text(f"{_HEADER}\n,09:20:00,100,110,90,105,1000\n", encoding="utf-8")

        provider = CsvHistoricalDataProvider()

        with pytest.raises(HistoricalDataError):
            provider.load_csv(path, symbol="NIFTY", timeframe="1m")


class TestSourceIntegration:
    def test_csv_source_end_to_end(self, tmp_path: Path) -> None:
        path = tmp_path / "nifty.csv"
        path.write_text(
            f"{_HEADER}\n"
            "2026-07-30,09:21:00,105,115,95,110,2000\n"
            "2026-07-30,09:20:00,100,110,90,105,1000\n",
            encoding="utf-8",
        )
        provider = HistoricalDataProvider()

        dataset = provider.load(CsvHistoricalDataSource(path), symbol="NIFTY", timeframe="1m")

        assert dataset.snapshots[0].timestamp < dataset.snapshots[1].timestamp

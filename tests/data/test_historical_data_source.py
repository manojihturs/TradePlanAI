"""Tests for data.historical_data_source."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.exceptions import HistoricalDataError
from data.historical_data_source import CsvHistoricalDataSource, HistoricalDataSource


def _write_csv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


class TestProtocolConformance:
    def test_csv_source_satisfies_protocol(self, tmp_path: Path) -> None:
        source = CsvHistoricalDataSource(tmp_path / "data.csv")

        assert isinstance(source, HistoricalDataSource)


class TestReadRows:
    def test_reads_rows_from_csv(self, tmp_path: Path) -> None:
        path = _write_csv(
            tmp_path / "data.csv",
            "Date,Time,Open,High,Low,Close,Volume\n"
            "2026-07-30,09:20:00,100,110,90,105,1000\n"
            "2026-07-30,09:21:00,105,115,95,110,2000\n",
        )
        source = CsvHistoricalDataSource(path)

        rows = list(source.read_rows())

        assert len(rows) == 2
        assert rows[0]["Open"] == "100"
        assert rows[1]["Close"] == "110"

    def test_empty_csv_yields_no_rows(self, tmp_path: Path) -> None:
        path = _write_csv(tmp_path / "data.csv", "Date,Time,Open,High,Low,Close,Volume\n")
        source = CsvHistoricalDataSource(path)

        assert list(source.read_rows()) == []

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        source = CsvHistoricalDataSource(tmp_path / "does-not-exist.csv")

        with pytest.raises(HistoricalDataError, match="Could not read CSV file"):
            list(source.read_rows())

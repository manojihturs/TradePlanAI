"""Tests for HistoryLoader, Candle, and MissingCandleGap."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from trading_engine.replay.exceptions import HistoryLoadError
from trading_engine.replay.history_loader import Candle, HistoryLoader, MissingCandleGap

from .conftest import make_candle, write_csv


class TestCandleConstructorValidation:
    def test_valid_construction(self, base_timestamp: datetime) -> None:
        candle = make_candle(base_timestamp)
        assert candle.open == Decimal(100)

    def test_none_timestamp_raises(self) -> None:
        with pytest.raises(HistoryLoadError, match="timestamp must not be None"):
            Candle(None, Decimal(1), Decimal(2), Decimal(1), Decimal(1), 1)  # type: ignore[arg-type]

    def test_high_less_than_low_raises(self, base_timestamp: datetime) -> None:
        with pytest.raises(HistoryLoadError, match="high .* is less than low"):
            Candle(base_timestamp, Decimal(100), Decimal(90), Decimal(95), Decimal(92), 1)

    def test_open_above_high_raises(self, base_timestamp: datetime) -> None:
        with pytest.raises(HistoryLoadError, match="open .* is outside"):
            Candle(base_timestamp, Decimal(200), Decimal(105), Decimal(95), Decimal(100), 1)

    def test_close_below_low_raises(self, base_timestamp: datetime) -> None:
        with pytest.raises(HistoryLoadError, match="close .* is outside"):
            Candle(base_timestamp, Decimal(100), Decimal(105), Decimal(95), Decimal(50), 1)

    def test_negative_volume_raises(self, base_timestamp: datetime) -> None:
        with pytest.raises(HistoryLoadError, match="volume .* must not be negative"):
            Candle(base_timestamp, Decimal(100), Decimal(105), Decimal(95), Decimal(100), -1)

    def test_open_equal_to_high_is_valid(self, base_timestamp: datetime) -> None:
        candle = Candle(base_timestamp, Decimal(105), Decimal(105), Decimal(95), Decimal(100), 1)
        assert candle.open == candle.high

    def test_zero_volume_is_valid(self, base_timestamp: datetime) -> None:
        candle = Candle(base_timestamp, Decimal(100), Decimal(105), Decimal(95), Decimal(100), 0)
        assert candle.volume == 0

    def test_immutability(self, base_timestamp: datetime) -> None:
        candle = make_candle(base_timestamp)
        with pytest.raises(dataclasses.FrozenInstanceError):
            candle.open = Decimal(999)  # type: ignore[misc]


class TestLoadCsvValidation:
    def test_loads_valid_csv(self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]) -> None:
        csv_path = write_csv(tmp_path / "candles.csv", valid_csv_rows)
        candles = HistoryLoader().load(csv_path)
        assert len(candles) == 3
        assert all(isinstance(candle, Candle) for candle in candles)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(HistoryLoadError, match="not found"):
            HistoryLoader().load(tmp_path / "does_not_exist.csv")

    def test_missing_required_column_raises(
        self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]
    ) -> None:
        csv_path = write_csv(
            tmp_path / "candles.csv",
            valid_csv_rows,
            header=["Date", "Time", "Open", "High", "Low", "Close"],  # Volume missing
        )
        with pytest.raises(HistoryLoadError, match="missing required column"):
            HistoryLoader().load(csv_path)

    def test_empty_file_with_only_header_raises(self, tmp_path: Path) -> None:
        csv_path = write_csv(tmp_path / "candles.csv", [])
        with pytest.raises(HistoryLoadError, match="no data rows"):
            HistoryLoader().load(csv_path)

    def test_completely_empty_file_raises(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("", encoding="utf-8")
        with pytest.raises(HistoryLoadError, match="no header row"):
            HistoryLoader().load(csv_path)

    def test_blank_date_raises(self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]) -> None:
        rows = [dict(valid_csv_rows[0], Date="")]
        csv_path = write_csv(tmp_path / "candles.csv", rows)
        with pytest.raises(HistoryLoadError, match="Date and Time must not be blank"):
            HistoryLoader().load(csv_path)

    def test_unparsable_date_raises(
        self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]
    ) -> None:
        rows = [dict(valid_csv_rows[0], Date="not-a-date")]
        csv_path = write_csv(tmp_path / "candles.csv", rows)
        with pytest.raises(HistoryLoadError, match="could not parse Date/Time"):
            HistoryLoader().load(csv_path)

    def test_unparsable_price_raises(
        self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]
    ) -> None:
        rows = [dict(valid_csv_rows[0], Open="not-a-number")]
        csv_path = write_csv(tmp_path / "candles.csv", rows)
        with pytest.raises(HistoryLoadError, match="could not parse Open/High/Low/Close"):
            HistoryLoader().load(csv_path)

    def test_unparsable_volume_raises(
        self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]
    ) -> None:
        rows = [dict(valid_csv_rows[0], Volume="not-a-number")]
        csv_path = write_csv(tmp_path / "candles.csv", rows)
        with pytest.raises(HistoryLoadError, match="could not parse Volume"):
            HistoryLoader().load(csv_path)

    def test_structurally_invalid_row_raises_with_line_number(
        self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]
    ) -> None:
        rows = [dict(valid_csv_rows[0], High="1")]  # High below Low/Open/Close
        csv_path = write_csv(tmp_path / "candles.csv", rows)
        with pytest.raises(HistoryLoadError, match="line 2"):
            HistoryLoader().load(csv_path)


class TestChronologicalOrdering:
    def test_out_of_order_rows_are_sorted(
        self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]
    ) -> None:
        reversed_rows = list(reversed(valid_csv_rows))
        csv_path = write_csv(tmp_path / "candles.csv", reversed_rows)
        candles = HistoryLoader().load(csv_path)
        timestamps = [candle.timestamp for candle in candles]
        assert timestamps == sorted(timestamps)


class TestDuplicateTimestampDetection:
    def test_duplicate_timestamp_raises(
        self, tmp_path: Path, valid_csv_rows: list[dict[str, str]]
    ) -> None:
        rows = valid_csv_rows + [valid_csv_rows[0]]
        csv_path = write_csv(tmp_path / "candles.csv", rows)
        with pytest.raises(HistoryLoadError, match="duplicate timestamp"):
            HistoryLoader().load(csv_path)


class TestMissingCandleDetection:
    def test_no_gap_when_interval_is_regular(self, base_timestamp: datetime) -> None:
        candles = tuple(make_candle(base_timestamp + timedelta(minutes=5 * i)) for i in range(5))
        gaps = HistoryLoader().detect_missing_candles(candles)
        assert gaps == ()

    def test_detects_a_gap_larger_than_the_modal_interval(self, base_timestamp: datetime) -> None:
        candles = (
            make_candle(base_timestamp),
            make_candle(base_timestamp + timedelta(minutes=5)),
            make_candle(base_timestamp + timedelta(minutes=10)),
            make_candle(base_timestamp + timedelta(minutes=30)),  # gap
            make_candle(base_timestamp + timedelta(minutes=35)),
        )
        gaps = HistoryLoader().detect_missing_candles(candles)
        assert len(gaps) == 1
        assert isinstance(gaps[0], MissingCandleGap)
        assert gaps[0].after == base_timestamp + timedelta(minutes=10)
        assert gaps[0].before == base_timestamp + timedelta(minutes=30)

    def test_fewer_than_three_candles_returns_no_gaps(self, base_timestamp: datetime) -> None:
        candles = (make_candle(base_timestamp), make_candle(base_timestamp + timedelta(minutes=5)))
        assert HistoryLoader().detect_missing_candles(candles) == ()

    def test_does_not_raise_or_block_loading(self) -> None:
        # detect_missing_candles is informational only - confirmed by
        # its own signature never raising for any well-formed input.
        gaps = HistoryLoader().detect_missing_candles(())
        assert gaps == ()

    def test_non_positive_modal_delta_returns_no_gaps(self, base_timestamp: datetime) -> None:
        # Constructed directly (not via HistoryLoader.load(), which
        # rejects duplicate timestamps) so the modal inter-candle
        # interval is 0 - detect_missing_candles must not divide by
        # zero or otherwise misbehave, and reports no gaps.
        candles = (
            make_candle(base_timestamp),
            make_candle(base_timestamp),
            make_candle(base_timestamp),
            make_candle(base_timestamp + timedelta(minutes=10)),
        )
        assert HistoryLoader().detect_missing_candles(candles) == ()

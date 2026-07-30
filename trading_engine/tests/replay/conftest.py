"""Shared fixtures for the replay engine test suite."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from trading_engine.replay.history_loader import Candle
from trading_engine.replay.replay_clock import ReplayClock


def make_candle(
    timestamp: datetime,
    open_: str = "100",
    high: str = "105",
    low: str = "95",
    close: str = "102",
    volume: int = 1000,
) -> Candle:
    return Candle(
        timestamp=timestamp,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=volume,
    )


@pytest.fixture
def base_timestamp() -> datetime:
    return datetime(2026, 7, 3, 9, 15, 0)  # noqa: DTZ001


@pytest.fixture
def sample_candles(base_timestamp: datetime) -> tuple[Candle, ...]:
    return tuple(
        make_candle(base_timestamp + timedelta(minutes=5 * i), volume=1000 + i) for i in range(5)
    )


@pytest.fixture
def single_candle(base_timestamp: datetime) -> tuple[Candle, ...]:
    return (make_candle(base_timestamp),)


@pytest.fixture
def sample_clock(sample_candles: tuple[Candle, ...]) -> ReplayClock:
    return ReplayClock(sample_candles)


def write_csv(path: Path, rows: list[dict[str, str]], header: list[str] | None = None) -> Path:
    header = header or ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(row.get(column, "") for column in header))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def valid_csv_rows() -> list[dict[str, str]]:
    return [
        {
            "Date": "2026-07-03",
            "Time": "09:15:00",
            "Open": "100",
            "High": "105",
            "Low": "95",
            "Close": "102",
            "Volume": "1000",
        },
        {
            "Date": "2026-07-03",
            "Time": "09:20:00",
            "Open": "102",
            "High": "108",
            "Low": "100",
            "Close": "106",
            "Volume": "1500",
        },
        {
            "Date": "2026-07-03",
            "Time": "09:25:00",
            "Open": "106",
            "High": "110",
            "Low": "104",
            "Close": "107",
            "Volume": "1200",
        },
    ]

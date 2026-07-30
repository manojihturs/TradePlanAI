"""Tests for tools.performance_benchmark.

Deterministic aggregation/reporting logic is tested with hand-built
BenchmarkResult fixtures - never asserting on exact wall-clock/memory
numbers, which would be flaky. One lightweight integration test
confirms `run_performance_benchmark` runs a real replay without
crashing and produces plausible (non-negative) measurements.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from performance_benchmark import (
    CSV_HEADER,
    BenchmarkResult,
    PerformanceBenchmarkSummary,
    StageTiming,
    build_summary,
    main,
    render_summary,
    run_performance_benchmark,
    write_performance_report_csv,
)

_ANCHOR_STRIKE = 24200
_SCHEMA = """
CREATE TABLE orb_summary (
    session_date TEXT PRIMARY KEY,
    atm INTEGER,
    fut_high REAL,
    fut_low REAL,
    sp_high INTEGER,
    sp_low INTEGER
);
CREATE TABLE orb_levels (
    session_date TEXT,
    strike INTEGER,
    side TEXT,
    first_open REAL,
    first_high REAL,
    first_low REAL,
    first_close REAL
);
"""


def _seed_db(db_path: Path, session_date: str) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT INTO orb_summary VALUES (?, ?, ?, ?, ?, ?)",
            (session_date, _ANCHOR_STRIKE, 24215.45, 24150.2, 24200, 24150),
        )
        strikes = [_ANCHOR_STRIKE - 300 + i * 50 for i in range(13)]
        for strike in strikes:
            if strike == _ANCHOR_STRIKE:
                ce = (120.0, 143.45, 116.0, 130.0)
                pe = (140.0, 165.8, 128.0, 150.0)
            else:
                ce = (130.0, 150.0, 100.0, 140.0)
                pe = (130.0, 150.0, 100.0, 140.0)
            conn.execute(
                "INSERT INTO orb_levels VALUES (?, ?, 'CE', ?, ?, ?, ?)",
                (session_date, strike, *ce),
            )
            conn.execute(
                "INSERT INTO orb_levels VALUES (?, ?, 'PE', ?, ?, ?, ?)",
                (session_date, strike, *pe),
            )
        conn.commit()
    finally:
        conn.close()


class TestRunPerformanceBenchmarkIntegration:
    def test_measures_a_real_replay_without_crashing(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29")

        results = run_performance_benchmark(db_path, tmp_path / "output")

        assert len(results) == 1
        result = results[0]
        assert result.session_date == "2026-07-29"
        assert result.candle_count == 1
        assert result.wall_time_seconds >= 0
        assert result.peak_memory_bytes >= 0
        assert len(result.stage_timings) == 1
        assert result.stage_timings[0].stage_name == "weekly_future"
        assert result.stage_timings[0].average_duration_seconds >= 0

    def test_skips_days_with_incomplete_ladder(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT INTO orb_summary VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-07-29", _ANCHOR_STRIKE, 24215.45, 24150.2, 24200, 24150),
        )
        conn.commit()
        conn.close()

        results = run_performance_benchmark(db_path, tmp_path / "output")

        assert results == ()

    def test_corrupted_database_raises_descriptive_runtime_error(self, tmp_path: Path) -> None:
        bad_db = tmp_path / "corrupted.db"
        bad_db.write_bytes(b"not a sqlite database")

        with pytest.raises(RuntimeError, match="Failed to read benchmark data"):
            run_performance_benchmark(bad_db, tmp_path / "output")

    def test_main_writes_report_and_returns_zero(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29")
        report_path = tmp_path / "performance_report.csv"

        exit_code = main(
            [
                "--db-path",
                str(db_path),
                "--report-path",
                str(report_path),
                "--output-dir",
                str(tmp_path / "output"),
            ]
        )

        assert exit_code == 0
        assert report_path.exists()

    def test_main_reports_corrupted_database_and_exits_one(self, tmp_path: Path) -> None:
        bad_db = tmp_path / "corrupted.db"
        bad_db.write_bytes(b"garbage")

        exit_code = main(
            [
                "--db-path",
                str(bad_db),
                "--report-path",
                str(tmp_path / "report.csv"),
                "--output-dir",
                str(tmp_path / "output"),
            ]
        )

        assert exit_code == 1


def _result(
    session_date: str, candle_count: int, wall_time: float, peak_memory: int
) -> BenchmarkResult:
    return BenchmarkResult(
        session_date=session_date,
        candle_count=candle_count,
        wall_time_seconds=wall_time,
        peak_memory_bytes=peak_memory,
        stage_timings=(StageTiming(stage_name="weekly_future", average_duration_seconds=0.01),),
    )


class TestBuildSummary:
    def test_aggregates_across_results(self) -> None:
        results = (
            _result("2026-07-21", 3, 0.10, 1000),
            _result("2026-07-22", 5, 0.20, 3000),
            _result("2026-07-23", 1, 0.05, 500),
        )

        summary = build_summary(results)

        assert summary.replays_measured == 3
        assert summary.average_wall_time_seconds == pytest.approx((0.10 + 0.20 + 0.05) / 3)
        assert summary.largest_replay_date == "2026-07-22"
        assert summary.largest_replay_candle_count == 5
        assert summary.peak_memory_bytes == 3000

    def test_empty_results(self) -> None:
        summary = build_summary(())

        assert summary.replays_measured == 0
        assert summary.average_wall_time_seconds is None
        assert summary.largest_replay_date is None
        assert summary.largest_replay_candle_count is None
        assert summary.peak_memory_bytes is None


class TestPerformanceBenchmarkSummaryValidation:
    def test_construction_is_a_plain_dataclass(self) -> None:
        summary = PerformanceBenchmarkSummary(
            replays_measured=1,
            average_wall_time_seconds=0.5,
            largest_replay_date="2026-07-29",
            largest_replay_candle_count=3,
            peak_memory_bytes=1000,
        )

        assert summary.replays_measured == 1


class TestWritePerformanceReportCsv:
    def test_writes_header_and_rows(self, tmp_path: Path) -> None:
        results = (_result("2026-07-29", 3, 0.123456, 1000),)
        csv_path = tmp_path / "report.csv"

        write_performance_report_csv(results, csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(CSV_HEADER)
        assert lines[1] == "2026-07-29,3,0.123456,1000,weekly_future=0.010000"

    def test_writes_empty_results_as_header_only(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "empty.csv"

        write_performance_report_csv((), csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines == [",".join(CSV_HEADER)]

    def test_multiple_stage_timings_are_semicolon_joined(self, tmp_path: Path) -> None:
        result = BenchmarkResult(
            session_date="2026-07-29",
            candle_count=1,
            wall_time_seconds=0.1,
            peak_memory_bytes=100,
            stage_timings=(
                StageTiming(stage_name="weekly_future", average_duration_seconds=0.01),
                StageTiming(stage_name="strike_selection", average_duration_seconds=0.02),
            ),
        )
        csv_path = tmp_path / "report.csv"

        write_performance_report_csv((result,), csv_path)

        line = csv_path.read_text(encoding="utf-8").splitlines()[1]
        assert "weekly_future=0.010000" in line
        assert "strike_selection=0.020000" in line


class TestRenderSummary:
    def test_renders_all_fields(self) -> None:
        summary = PerformanceBenchmarkSummary(
            replays_measured=2,
            average_wall_time_seconds=0.15,
            largest_replay_date="2026-07-22",
            largest_replay_candle_count=5,
            peak_memory_bytes=3000,
        )

        rendered = render_summary(summary)

        assert "Replays Measured: 2" in rendered
        assert "Largest Replay: 2026-07-22 (5 candles)" in rendered
        assert "Peak Memory: 3000 bytes" in rendered

    def test_renders_no_replays_measured(self) -> None:
        summary = build_summary(())

        rendered = render_summary(summary)

        assert rendered == "No replays measured."

"""Tests for tools.regression_validator."""

from __future__ import annotations

import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest
from regression_validator import (
    CSV_HEADER,
    RegressionCheckResult,
    compare_day,
    main,
    render_failure_details,
    render_summary,
    run_regression_suite,
    write_regression_report_csv,
)

# TC-1, verified in WEEKLY_FUTURE_CALCULATION_EXAMPLES.md - reused across
# this codebase's other test suites (test_weekly_future_stage.py, etc.)
_ANCHOR_STRIKE = 24200
_EXPECTED_HIGH = "24215.45"
_EXPECTED_LOW = "24150.2"
_EXPECTED_TOP = 24200
_EXPECTED_BOTTOM = 24150

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


def _seed_db(
    db_path: Path,
    session_date: str,
    *,
    fut_high: float = float(_EXPECTED_HIGH),
    fut_low: float = float(_EXPECTED_LOW),
    sp_high: int = _EXPECTED_TOP,
    sp_low: int = _EXPECTED_BOTTOM,
    include_full_ladder: bool = True,
) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT INTO orb_summary VALUES (?, ?, ?, ?, ?, ?)",
            (session_date, _ANCHOR_STRIKE, fut_high, fut_low, sp_high, sp_low),
        )
        strikes = [_ANCHOR_STRIKE - 300 + i * 50 for i in range(13)]
        rows_to_insert = strikes if include_full_ladder else strikes[:5]
        for strike in rows_to_insert:
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


class TestRunRegressionSuite:
    def test_matching_day_passes(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29")

        results = run_regression_suite(db_path, tmp_path / "output")

        assert len(results) == 1
        result = results[0]
        assert result.status == "PASS"
        assert result.actual_high == Decimal(_EXPECTED_HIGH)
        assert result.actual_low == Decimal(_EXPECTED_LOW)
        assert result.actual_top == Decimal(_EXPECTED_TOP)
        assert result.actual_bottom == Decimal(_EXPECTED_BOTTOM)

    def test_mismatched_day_fails_with_differences(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29", fut_high=99999.0)

        results = run_regression_suite(db_path, tmp_path / "output")

        result = results[0]
        assert result.status == "FAIL"
        assert any("Weekly Future High" in d for d in result.differences)

    def test_float_precision_noise_does_not_cause_false_failure(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        # Same value as float arithmetic would produce with representation noise.
        _seed_db(db_path, "2026-07-29", fut_low=24198.449999999997 - 48.25)

        results = run_regression_suite(db_path, tmp_path / "output")

        assert results[0].status == "PASS"

    def test_incomplete_ladder_fails(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29", include_full_ladder=False)

        results = run_regression_suite(db_path, tmp_path / "output")

        result = results[0]
        assert result.status == "FAIL"
        assert "Incomplete reference ladder" in result.differences[0]
        assert result.actual_high is None

    def test_multiple_days_processed_in_date_order(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(_SCHEMA)
        conn.commit()
        conn.close()
        _seed_db_append(db_path, "2026-07-30")
        _seed_db_append(db_path, "2026-07-29")

        results = run_regression_suite(db_path, tmp_path / "output")

        assert [r.session_date for r in results] == ["2026-07-29", "2026-07-30"]
        assert all(r.status == "PASS" for r in results)

    def test_empty_orb_summary_yields_no_results(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(_SCHEMA)
        conn.commit()
        conn.close()

        results = run_regression_suite(db_path, tmp_path / "output")

        assert results == ()


def _seed_db_append(db_path: Path, session_date: str) -> None:
    """Like _seed_db but does not recreate the schema (already exists)."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO orb_summary VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_date,
                _ANCHOR_STRIKE,
                float(_EXPECTED_HIGH),
                float(_EXPECTED_LOW),
                _EXPECTED_TOP,
                _EXPECTED_BOTTOM,
            ),
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


class TestEdgeCasesAndCorruptedData:
    """Sprint: Exception & Edge Case Testing. Every scenario here must
    degrade to a descriptive FAIL/RuntimeError - never an unhandled
    traceback with a cryptic message (e.g. decimal.InvalidOperation)."""

    def test_missing_reference_level_yields_descriptive_fail(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29", include_full_ladder=False)

        results = run_regression_suite(db_path, tmp_path / "output")

        result = results[0]
        assert result.status == "FAIL"
        assert "Incomplete reference ladder" in result.differences[0]

    def test_duplicate_strikes_in_ladder_yields_descriptive_fail(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT INTO orb_summary VALUES (?, ?, ?, ?, ?, ?)",
            (
                "2026-07-29",
                _ANCHOR_STRIKE,
                float(_EXPECTED_HIGH),
                float(_EXPECTED_LOW),
                _EXPECTED_TOP,
                _EXPECTED_BOTTOM,
            ),
        )
        # Insert the SAME strike (the anchor) 13 times instead of 13 distinct strikes.
        for _ in range(13):
            conn.execute(
                "INSERT INTO orb_levels VALUES (?, ?, 'CE', 120.0, 143.45, 116.0, 130.0)",
                ("2026-07-29", _ANCHOR_STRIKE),
            )
            conn.execute(
                "INSERT INTO orb_levels VALUES (?, ?, 'PE', 140.0, 165.8, 128.0, 150.0)",
                ("2026-07-29", _ANCHOR_STRIKE),
            )
        conn.commit()
        conn.close()

        # ReferenceValidator (via the real pipeline) rejects this - the
        # suite must report it descriptively, not crash.
        results = run_regression_suite(db_path, tmp_path / "output")

        result = results[0]
        assert result.status == "FAIL"
        assert result.differences  # some descriptive difference/error was recorded

    def test_incomplete_ladder_below_thirteen_strikes(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29", include_full_ladder=False)

        results = run_regression_suite(db_path, tmp_path / "output")

        assert results[0].status == "FAIL"
        assert results[0].actual_high is None

    def test_empty_orb_summary_is_an_empty_replay_not_a_crash(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(_SCHEMA)
        conn.commit()
        conn.close()

        results = run_regression_suite(db_path, tmp_path / "output")

        assert results == ()

    def test_corrupted_database_raises_descriptive_runtime_error(self, tmp_path: Path) -> None:
        bad_db = tmp_path / "corrupted.db"
        bad_db.write_bytes(b"this is not a sqlite database file, just garbage bytes")

        with pytest.raises(RuntimeError, match="Failed to read regression data"):
            run_regression_suite(bad_db, tmp_path / "output")

    def test_main_reports_corrupted_database_and_exits_nonzero(self, tmp_path: Path) -> None:
        bad_db = tmp_path / "corrupted.db"
        bad_db.write_bytes(b"garbage, not a database")

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

    def test_missing_database_file_raises_descriptive_error(self, tmp_path: Path) -> None:
        missing_db = tmp_path / "does_not_exist.db"

        with pytest.raises(RuntimeError, match="Failed to read regression data"):
            run_regression_suite(missing_db, tmp_path / "output")

    def test_null_legacy_value_yields_descriptive_fail_not_a_crash(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT INTO orb_summary VALUES (?, ?, NULL, ?, ?, ?)",
            ("2026-07-29", _ANCHOR_STRIKE, float(_EXPECTED_LOW), _EXPECTED_TOP, _EXPECTED_BOTTOM),
        )
        conn.commit()
        conn.close()

        results = run_regression_suite(db_path, tmp_path / "output")

        result = results[0]
        assert result.status == "FAIL"
        assert "NULL or invalid value" in result.differences[0]

    def test_null_reference_level_value_treated_as_incomplete_ladder(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT INTO orb_summary VALUES (?, ?, ?, ?, ?, ?)",
            (
                "2026-07-29",
                _ANCHOR_STRIKE,
                float(_EXPECTED_HIGH),
                float(_EXPECTED_LOW),
                _EXPECTED_TOP,
                _EXPECTED_BOTTOM,
            ),
        )
        strikes = [_ANCHOR_STRIKE - 300 + i * 50 for i in range(13)]
        for strike in strikes:
            ce_high = None if strike == _ANCHOR_STRIKE else 150.0
            conn.execute(
                "INSERT INTO orb_levels VALUES (?, ?, 'CE', 120.0, ?, 116.0, 130.0)",
                ("2026-07-29", strike, ce_high),
            )
            conn.execute(
                "INSERT INTO orb_levels VALUES (?, ?, 'PE', 140.0, 165.8, 128.0, 150.0)",
                ("2026-07-29", strike),
            )
        conn.commit()
        conn.close()

        results = run_regression_suite(db_path, tmp_path / "output")

        result = results[0]
        assert result.status == "FAIL"
        assert "Incomplete reference ladder" in result.differences[0]


class TestCompareDay:
    def test_exact_match_passes(self) -> None:
        result = compare_day(
            "2026-07-29",
            (Decimal("100.00"), Decimal("90.00"), Decimal(24200), Decimal(24150)),
            (Decimal("100.00"), Decimal("90.00"), Decimal(24200), Decimal(24150)),
        )

        assert result.status == "PASS"
        assert result.differences == ()

    def test_quantizes_high_low_before_comparing(self) -> None:
        result = compare_day(
            "2026-07-29",
            (Decimal("100.001"), Decimal("90.004"), Decimal(24200), Decimal(24150)),
            (Decimal("100.00"), Decimal("90.00"), Decimal(24200), Decimal(24150)),
        )

        assert result.status == "PASS"

    def test_missing_actual_value_fails(self) -> None:
        result = compare_day(
            "2026-07-29",
            (Decimal("100.00"), Decimal("90.00"), Decimal(24200), Decimal(24150)),
            (None, None, None, None),
        )

        assert result.status == "FAIL"
        assert len(result.differences) == 4

    def test_strike_mismatch_fails(self) -> None:
        result = compare_day(
            "2026-07-29",
            (Decimal("100.00"), Decimal("90.00"), Decimal(24200), Decimal(24150)),
            (Decimal("100.00"), Decimal("90.00"), Decimal(24250), Decimal(24150)),
        )

        assert result.status == "FAIL"
        assert any("Top Strike" in d for d in result.differences)


class TestWriteRegressionReportCsv:
    def test_writes_header_and_rows(self, tmp_path: Path) -> None:
        results = (
            RegressionCheckResult(
                session_date="2026-07-29",
                expected_high=Decimal("100.00"),
                actual_high=Decimal("100.00"),
                expected_low=Decimal("90.00"),
                actual_low=Decimal("90.00"),
                expected_top=Decimal(24200),
                actual_top=Decimal(24200),
                expected_bottom=Decimal(24150),
                actual_bottom=Decimal(24150),
                status="PASS",
            ),
        )
        csv_path = tmp_path / "report.csv"

        write_regression_report_csv(results, csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(CSV_HEADER)
        assert lines[1] == "2026-07-29,100.00,100.00,90.00,90.00,24200,24200,24150,24150,PASS"

    def test_writes_empty_results_as_header_only(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "empty.csv"

        write_regression_report_csv((), csv_path)

        lines = csv_path.read_text(encoding="utf-8").splitlines()
        assert lines == [",".join(CSV_HEADER)]


class TestRenderSummary:
    def test_summary_counts(self) -> None:
        results = (
            RegressionCheckResult(
                "2026-07-29", None, None, None, None, None, None, None, None, "PASS"
            ),
            RegressionCheckResult(
                "2026-07-30", None, None, None, None, None, None, None, None, "FAIL"
            ),
        )

        summary = render_summary(results)

        assert "PASS 2026-07-29" in summary
        assert "FAIL 2026-07-30" in summary
        assert "Days Tested: 2" in summary
        assert "Days Passed: 1" in summary
        assert "Days Failed: 1" in summary


class TestRenderFailureDetails:
    def test_renders_only_failed_days_with_differences(self) -> None:
        results = (
            RegressionCheckResult(
                "2026-07-29", None, None, None, None, None, None, None, None, "PASS"
            ),
            RegressionCheckResult(
                "2026-07-30",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                "FAIL",
                differences=("Weekly Future High: expected 100, got 200",),
            ),
        )

        details = render_failure_details(results)

        assert "2026-07-29" not in details
        assert "2026-07-30:" in details
        assert "Weekly Future High: expected 100, got 200" in details


class TestMain:
    def test_all_passing_returns_zero_and_writes_report(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29")
        report_path = tmp_path / "regression_report.csv"

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

    def test_any_failure_returns_one(self, tmp_path: Path) -> None:
        db_path = tmp_path / "orb_levels.db"
        _seed_db(db_path, "2026-07-29", fut_high=99999.0)
        report_path = tmp_path / "regression_report.csv"

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

        assert exit_code == 1
        assert report_path.exists()

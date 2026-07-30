"""Performance Benchmark: measures ReplayEngine/ReplayApplication timing
and memory usage against every real trading day in orb_levels.db.

Traceability
------------
Sprint: "Performance" (Delivery Mode) - measurement only, no
optimization and no business logic change. Reuses
``tools.regression_validator``'s own real-data loaders
(``_load_trading_days``/``_load_legacy_expected``/
``_load_reference_inputs``) rather than duplicating them, and reuses
``business.business_result.BusinessResult.stage_diagnostics`` (added
by the earlier "Pipeline Diagnostics" sprint) for real per-stage
timing - that field is already populated from the same
``business.execution_context.ExecutionContext.clock`` this project
always uses for real time (default ``core.protocols.utc_now``), so no
new instrumentation is introduced to get it.

"Time per replay" is real wall-clock (``time.perf_counter``), not the
domain ``Clock`` used for candle timestamps - a deliberate,
intentional use of the OS clock for measurement purposes only, never
fed into any business value.

"Memory usage" uses the stdlib ``tracemalloc`` (peak traced Python
allocation during one day's ``ReplayApplication.run()`` call) - no
new dependency (e.g. ``psutil``) was introduced for this.

Lives outside ``src/`` alongside ``tools/regression_validator.py``,
for the same reason: a maintenance/CI tool, not a business package.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import date as date_cls
from decimal import Decimal
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import regression_validator as rv  # the real-data loaders this benchmark reuses

from application.replay_application import ReplayApplication, ReplayApplicationConfiguration
from application.replay_configuration import ReplayConfiguration
from application.replay_result import ReplayResult
from business.stages.weekly_future_stage import WeeklyFutureStage
from reference_builder.reference_validator import StrikeCandleInput
from strike_selector.strike_selector import StrikeSelector
from weekly_future.weekly_future_calculator import WeeklyFutureCalculator

DEFAULT_DB_PATH = Path("orb_levels.db")
DEFAULT_REPORT_PATH = Path("performance_report.csv")
DEFAULT_OUTPUT_DIR = Path("performance_output")

CSV_HEADER = (
    "date",
    "candle_count",
    "wall_time_seconds",
    "peak_memory_bytes",
    "stage_timings",
)


@dataclass(frozen=True, slots=True)
class StageTiming:
    """One stage's average duration across a single replay's candles.

    Attributes:
        stage_name: The ``business.business_pipeline.PipelineStage.name``
            this timing concerns.
        average_duration_seconds: Mean of that stage's
            ``business.stage_diagnostics.StageDiagnostic.duration``
            across every candle in the replay.
    """

    stage_name: str
    average_duration_seconds: float


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """One trading day's replay performance measurement.

    Attributes:
        session_date: The trading day this measurement concerns.
        candle_count: How many candles that day's replay processed.
        wall_time_seconds: Real wall-clock duration of
            ``ReplayApplication.run()`` for that day
            (``time.perf_counter`` delta).
        peak_memory_bytes: Peak traced Python memory allocation
            (``tracemalloc``) during that run.
        stage_timings: One :class:`StageTiming` per distinct stage
            name observed, in first-seen order.
    """

    session_date: str
    candle_count: int
    wall_time_seconds: float
    peak_memory_bytes: int
    stage_timings: tuple[StageTiming, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class PerformanceBenchmarkSummary:
    """Aggregate figures across every :class:`BenchmarkResult`.

    Attributes:
        replays_measured: How many days were benchmarked.
        average_wall_time_seconds: Mean wall time across all replays,
            or ``None`` if none were measured.
        largest_replay_date: The ``session_date`` with the most
            candles processed, or ``None``.
        largest_replay_candle_count: That day's candle count, or ``None``.
        peak_memory_bytes: The maximum ``peak_memory_bytes`` observed
            across every replay, or ``None``.
    """

    replays_measured: int
    average_wall_time_seconds: float | None
    largest_replay_date: str | None
    largest_replay_candle_count: int | None
    peak_memory_bytes: int | None


def _stage_timings(result: ReplayResult) -> tuple[StageTiming, ...]:
    """Aggregate per-stage average duration across every candle in a
    ``ReplayResult``."""
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for business_result in result.business_results:
        for diagnostic in business_result.stage_diagnostics:
            totals[diagnostic.stage_name] = (
                totals.get(diagnostic.stage_name, 0.0) + diagnostic.duration.total_seconds()
            )
            counts[diagnostic.stage_name] = counts.get(diagnostic.stage_name, 0) + 1
    return tuple(
        StageTiming(stage_name=name, average_duration_seconds=totals[name] / counts[name])
        for name in totals
    )


def _benchmark_day(
    session_date: str,
    atm: int,
    reference_inputs: tuple[StrikeCandleInput, ...],
    output_dir: Path,
) -> BenchmarkResult:
    driver_csv = output_dir / f"driver_{session_date}.csv"
    driver_csv.write_text(
        "Date,Time,Open,High,Low,Close,Volume\n" f"{session_date},09:20:00,100,100,100,100,0\n",
        encoding="utf-8",
    )
    trading_day = date_cls.fromisoformat(session_date)
    configuration = ReplayApplicationConfiguration(
        dataset_path=driver_csv,
        symbol="NIFTY",
        timeframe="5m",
        output_directory=output_dir / f"reports_{session_date}",
        replay_configuration=ReplayConfiguration(start_date=trading_day, end_date=trading_day),
        reference_inputs=reference_inputs,
    )
    stage = WeeklyFutureStage(
        anchor_strike=Decimal(atm),
        weekly_future_calculator=WeeklyFutureCalculator(),
        strike_selector=StrikeSelector(),
    )
    app = ReplayApplication(configuration=configuration, stages=(stage,))

    tracemalloc.start()
    started = time.perf_counter()
    result = app.run()
    elapsed = time.perf_counter() - started
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return BenchmarkResult(
        session_date=session_date,
        candle_count=len(result.business_results),
        wall_time_seconds=elapsed,
        peak_memory_bytes=peak,
        stage_timings=_stage_timings(result),
    )


def run_performance_benchmark(db_path: Path, output_dir: Path) -> tuple[BenchmarkResult, ...]:
    """Benchmark every trading day in ``orb_summary`` at ``db_path``.
    One :class:`BenchmarkResult` per day, in date order.

    Raises:
        RuntimeError: if ``db_path`` cannot be read as a SQLite
            database - matches ``regression_validator.run_regression_suite``'s
            own error handling.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        try:
            trading_days = rv._load_trading_days(conn)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to read benchmark data from {db_path}: {exc}") from exc

        results: list[BenchmarkResult] = []
        for session_date in trading_days:
            try:
                legacy = rv._load_legacy_expected(conn, session_date)
            except ValueError:
                continue  # NULL/invalid legacy row - not this sprint's concern, skip
            if legacy is None:
                continue  # pragma: no cover - unreachable: date came from this same table
            atm = legacy[0]

            reference_inputs = rv._load_reference_inputs(conn, session_date, atm)
            if reference_inputs is None:
                continue  # incomplete ladder - nothing to benchmark for this day

            results.append(_benchmark_day(session_date, atm, reference_inputs, output_dir))
        return tuple(results)
    finally:
        conn.close()


def build_summary(results: tuple[BenchmarkResult, ...]) -> PerformanceBenchmarkSummary:
    """Aggregate ``results`` into a :class:`PerformanceBenchmarkSummary`."""
    if not results:
        return PerformanceBenchmarkSummary(
            replays_measured=0,
            average_wall_time_seconds=None,
            largest_replay_date=None,
            largest_replay_candle_count=None,
            peak_memory_bytes=None,
        )

    wall_times = [result.wall_time_seconds for result in results]
    largest = max(results, key=lambda result: result.candle_count)
    return PerformanceBenchmarkSummary(
        replays_measured=len(results),
        average_wall_time_seconds=sum(wall_times) / len(wall_times),
        largest_replay_date=largest.session_date,
        largest_replay_candle_count=largest.candle_count,
        peak_memory_bytes=max(result.peak_memory_bytes for result in results),
    )


def write_performance_report_csv(results: tuple[BenchmarkResult, ...], path: Path) -> None:
    """Write ``results`` to a CSV file at ``path``, one row per
    trading day, header first. ``stage_timings`` is written as a
    single ``"name=seconds; ..."`` column rather than dynamic
    per-stage columns, since the set of registered stages is not
    fixed."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADER)
        for result in results:
            stage_timings_text = "; ".join(
                f"{timing.stage_name}={timing.average_duration_seconds:.6f}"
                for timing in result.stage_timings
            )
            writer.writerow(
                (
                    result.session_date,
                    result.candle_count,
                    f"{result.wall_time_seconds:.6f}",
                    result.peak_memory_bytes,
                    stage_timings_text,
                )
            )


def render_summary(summary: PerformanceBenchmarkSummary) -> str:
    """Render the console Benchmark Summary."""
    if summary.replays_measured == 0:
        return "No replays measured."
    return "\n".join(
        [
            f"Replays Measured: {summary.replays_measured}",
            f"Average Processing Time: {summary.average_wall_time_seconds:.6f}s",
            (
                f"Largest Replay: {summary.largest_replay_date} "
                f"({summary.largest_replay_candle_count} candles)"
            ),
            f"Peak Memory: {summary.peak_memory_bytes} bytes",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Always returns ``0`` - this tool measures, it
    does not gate a build."""
    parser = argparse.ArgumentParser(
        description="Benchmark ReplayApplication timing/memory usage against orb_levels.db."
    )
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    try:
        results = run_performance_benchmark(args.db_path, args.output_dir)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    summary = build_summary(results)
    print(render_summary(summary))

    write_performance_report_csv(results, args.report_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

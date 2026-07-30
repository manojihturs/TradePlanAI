"""Regression Validation Suite: replays every real trading day in
``orb_levels.db`` through the pipeline and compares its Weekly
Future/Strike output against the legacy ``orb_summary`` values.

Traceability
------------
Sprint: "Regression Validation Suite" (Compact Development Mode) - no
new business logic, no architecture change. Automates the manual dry
run already performed by hand: for every trading day present in
``orb_summary``, build the real 13-strike reference ladder from
``orb_levels`` (first-5-minute CE/PE candle highs/lows, captured
live), run ``weekly_future.weekly_future_calculator.WeeklyFutureCalculator``/
``strike_selector.strike_selector.StrikeSelector`` through the real
``application.replay_application.ReplayApplication``/
``business.stages.weekly_future_stage.WeeklyFutureStage`` pipeline
with that day's real ATM as the anchor strike, and compare the
result's Weekly Future High/Low and Top/Bottom Strike against
``orb_summary``'s own ``fut_high``/``fut_low``/``sp_high``/``sp_low``
for that day - the legacy engine's independently computed values for
the same real captured data.

Lives outside ``src/`` (matches this repository's other root-level
scripts, e.g. ``run_real_backtest.py``) since it is a maintenance/CI
tool, not a business package - ``tools/`` is added to ``sys.path``
only by ``tests/conftest.py``, not by ``src/``.

``fut_high``/``fut_low`` are stored as SQLite ``REAL`` (float) and
carry tiny floating-point representation noise (observed:
``24198.449999999997`` for an exact ``24198.45``) - both sides of
every High/Low comparison are quantized to 2 decimal places before
comparing, to avoid a false failure from float representation, not
from an actual value mismatch. Top/Bottom Strike are integers and
compared exactly.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from datetime import date as date_cls
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from application.replay_application import ReplayApplication, ReplayApplicationConfiguration
from application.replay_configuration import ReplayConfiguration
from business.stages.weekly_future_stage import WeeklyFutureStage
from models.market_snapshot import MarketSnapshot
from reference_builder.reference_validator import EXPECTED_LADDER_SIZE, StrikeCandleInput
from strike_selector.strike_selector import StrikeSelector
from weekly_future.weekly_future_calculator import WeeklyFutureCalculator

STRIKE_SPACING = Decimal(50)
_QUANTIZE_TO = Decimal("0.01")
DEFAULT_DB_PATH = Path("orb_levels.db")
DEFAULT_REPORT_PATH = Path("regression_report.csv")
DEFAULT_OUTPUT_DIR = Path("regression_output")

CSV_HEADER = (
    "date",
    "expected_high",
    "actual_high",
    "expected_low",
    "actual_low",
    "expected_top",
    "actual_top",
    "expected_bottom",
    "actual_bottom",
    "status",
)

_STATUS_PASS = "PASS"
_STATUS_FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class RegressionCheckResult:
    """One trading day's regression comparison.

    Attributes:
        session_date: The trading day this result concerns, ``YYYY-MM-DD``.
        expected_high/expected_low: ``orb_summary.fut_high``/``fut_low``.
        actual_high/actual_low: The pipeline's own Weekly Future High/Low,
            or ``None`` if the pipeline never generated one.
        expected_top/expected_bottom: ``orb_summary.sp_high``/``sp_low``.
        actual_top/actual_bottom: The pipeline's own Top/Bottom Strike,
            or ``None`` if the pipeline never generated one.
        status: ``"PASS"`` or ``"FAIL"``.
        differences: One human-readable line per mismatched field,
            empty when ``status`` is ``"PASS"``.
    """

    session_date: str
    expected_high: Decimal | None
    actual_high: Decimal | None
    expected_low: Decimal | None
    actual_low: Decimal | None
    expected_top: Decimal | None
    actual_top: Decimal | None
    expected_bottom: Decimal | None
    actual_bottom: Decimal | None
    status: str
    differences: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.status == _STATUS_PASS


def _quantize(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(_QUANTIZE_TO, rounding=ROUND_HALF_UP)


def _load_trading_days(conn: sqlite3.Connection) -> list[str]:
    cur = conn.execute("SELECT session_date FROM orb_summary ORDER BY session_date")
    return [row[0] for row in cur.fetchall()]


def _load_legacy_expected(
    conn: sqlite3.Connection, session_date: str
) -> tuple[int, Decimal, Decimal, Decimal, Decimal] | None:
    """Load ``orb_summary``'s legacy values for ``session_date``.

    Raises:
        ValueError: if a row exists but a value is NULL or otherwise
            not convertible to ``Decimal`` - a descriptive error
            rather than letting ``decimal.InvalidOperation``/
            ``TypeError`` surface uncaught.
    """
    cur = conn.execute(
        "SELECT atm, fut_high, fut_low, sp_high, sp_low FROM orb_summary WHERE session_date = ?",
        (session_date,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    atm, fut_high, fut_low, sp_high, sp_low = row
    try:
        return (
            atm,
            Decimal(str(fut_high)),
            Decimal(str(fut_low)),
            Decimal(str(sp_high)),
            Decimal(str(sp_low)),
        )
    except (TypeError, InvalidOperation) as exc:
        raise ValueError(
            f"orb_summary row for {session_date} contains a NULL or invalid value "
            f"(atm={atm!r}, fut_high={fut_high!r}, fut_low={fut_low!r}, "
            f"sp_high={sp_high!r}, sp_low={sp_low!r}): {exc}"
        ) from exc


def _load_reference_inputs(
    conn: sqlite3.Connection, session_date: str, atm: int
) -> tuple[StrikeCandleInput, ...] | None:
    """Build the 13-strike reference ladder for ``session_date`` from
    ``orb_levels``. Returns ``None`` (an "incomplete ladder", the same
    outcome as a genuinely missing row) if any strike's CE/PE row is
    missing *or* contains a NULL/invalid OHLC value that cannot be
    converted to ``Decimal`` - a NULL value is data this tool cannot
    use, structurally no different from a missing row."""
    half_width = (EXPECTED_LADDER_SIZE // 2) * int(STRIKE_SPACING)
    strikes = [atm - half_width + i * int(STRIKE_SPACING) for i in range(EXPECTED_LADDER_SIZE)]
    timestamp = datetime.combine(date_cls.fromisoformat(session_date), datetime.min.time()).replace(
        hour=9, minute=20, tzinfo=UTC
    )

    inputs: list[StrikeCandleInput] = []
    for strike in strikes:
        candles: dict[str, MarketSnapshot] = {}
        cur = conn.execute(
            "SELECT side, first_open, first_high, first_low, first_close FROM orb_levels "
            "WHERE session_date = ? AND strike = ?",
            (session_date, strike),
        )
        for side, open_, high, low, close in cur.fetchall():
            try:
                candles[side] = MarketSnapshot(
                    timestamp=timestamp,
                    underlying_price=Decimal(str(close)),
                    open=Decimal(str(open_)),
                    high=Decimal(str(high)),
                    low=Decimal(str(low)),
                    close=Decimal(str(close)),
                )
            except (TypeError, InvalidOperation):
                continue  # NULL/invalid value - treat this candle as absent, see docstring
        if "CE" not in candles or "PE" not in candles:
            return None
        inputs.append(
            StrikeCandleInput(
                strike=Decimal(strike), ce_candle=candles["CE"], pe_candle=candles["PE"]
            )
        )
    return tuple(inputs)


def _run_replay_for_day(
    session_date: str,
    atm: int,
    reference_inputs: tuple[StrikeCandleInput, ...],
    output_dir: Path,
) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
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
    result = ReplayApplication(configuration=configuration, stages=(stage,)).run()

    context = result.business_results[0].context
    weekly_future = context.weekly_future
    selected_strike = context.selected_strike
    return (
        weekly_future.high if weekly_future else None,
        weekly_future.low if weekly_future else None,
        selected_strike.top_strike if selected_strike else None,
        selected_strike.bottom_strike if selected_strike else None,
    )


def compare_day(
    session_date: str,
    expected: tuple[Decimal, Decimal, Decimal, Decimal],
    actual: tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None],
) -> RegressionCheckResult:
    """Compare one day's expected (legacy) vs actual (pipeline) values,
    quantizing High/Low to 2 decimal places before comparing."""
    expected_high, expected_low, expected_top, expected_bottom = expected
    actual_high, actual_low, actual_top, actual_bottom = actual

    differences: list[str] = []
    for label, expected_value, actual_value in (
        ("Weekly Future High", _quantize(expected_high), _quantize(actual_high)),
        ("Weekly Future Low", _quantize(expected_low), _quantize(actual_low)),
        ("Top Strike", expected_top, actual_top),
        ("Bottom Strike", expected_bottom, actual_bottom),
    ):
        if expected_value != actual_value:
            differences.append(f"{label}: expected {expected_value}, got {actual_value}")

    return RegressionCheckResult(
        session_date=session_date,
        expected_high=expected_high,
        actual_high=actual_high,
        expected_low=expected_low,
        actual_low=actual_low,
        expected_top=expected_top,
        actual_top=actual_top,
        expected_bottom=expected_bottom,
        actual_bottom=actual_bottom,
        status=_STATUS_FAIL if differences else _STATUS_PASS,
        differences=tuple(differences),
    )


def run_regression_suite(db_path: Path, output_dir: Path) -> tuple[RegressionCheckResult, ...]:
    """Run the full regression suite: every trading day in
    ``orb_summary`` at ``db_path``, replayed and compared against its
    legacy values. One :class:`RegressionCheckResult` per day, in date
    order.

    Raises:
        RuntimeError: if ``db_path`` cannot be read as a SQLite
            database at all (missing, corrupted, or not a database
            file) - a clear, wrapped message rather than a raw
            ``sqlite3.Error`` traceback.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        try:
            trading_days = _load_trading_days(conn)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to read regression data from {db_path}: {exc}") from exc

        results: list[RegressionCheckResult] = []
        for session_date in trading_days:
            try:
                legacy = _load_legacy_expected(conn, session_date)
            except ValueError as exc:
                results.append(
                    RegressionCheckResult(
                        session_date=session_date,
                        expected_high=None,
                        actual_high=None,
                        expected_low=None,
                        actual_low=None,
                        expected_top=None,
                        actual_top=None,
                        expected_bottom=None,
                        actual_bottom=None,
                        status=_STATUS_FAIL,
                        differences=(str(exc),),
                    )
                )
                continue
            if legacy is None:
                continue  # pragma: no cover - unreachable: date came from this same table
            atm, fut_high, fut_low, sp_high, sp_low = legacy

            reference_inputs = _load_reference_inputs(conn, session_date, atm)
            if reference_inputs is None:
                results.append(
                    RegressionCheckResult(
                        session_date=session_date,
                        expected_high=fut_high,
                        actual_high=None,
                        expected_low=fut_low,
                        actual_low=None,
                        expected_top=sp_high,
                        actual_top=None,
                        expected_bottom=sp_low,
                        actual_bottom=None,
                        status=_STATUS_FAIL,
                        differences=("Incomplete reference ladder in orb_levels for this day.",),
                    )
                )
                continue

            actual = _run_replay_for_day(session_date, atm, reference_inputs, output_dir)
            results.append(compare_day(session_date, (fut_high, fut_low, sp_high, sp_low), actual))
        return tuple(results)
    finally:
        conn.close()


def write_regression_report_csv(results: tuple[RegressionCheckResult, ...], path: Path) -> None:
    """Write ``results`` to a CSV file at ``path``, one row per
    trading day, header first."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADER)
        for result in results:
            writer.writerow(
                (
                    result.session_date,
                    result.expected_high,
                    result.actual_high,
                    result.expected_low,
                    result.actual_low,
                    result.expected_top,
                    result.actual_top,
                    result.expected_bottom,
                    result.actual_bottom,
                    result.status,
                )
            )


def render_summary(results: tuple[RegressionCheckResult, ...]) -> str:
    """Render the console summary: one PASS/FAIL line per day, then
    Days Tested/Passed/Failed counts."""
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    lines = [f"{result.status} {result.session_date}" for result in results]
    lines.append("")
    lines.append(f"Days Tested: {len(results)}")
    lines.append(f"Days Passed: {passed}")
    lines.append(f"Days Failed: {failed}")
    return "\n".join(lines)


def render_failure_details(results: tuple[RegressionCheckResult, ...]) -> str:
    """Render one block per failed day, listing its differences."""
    lines: list[str] = []
    for result in results:
        if result.passed:
            continue
        lines.append(f"{result.session_date}:")
        lines.extend(f"  - {difference}" for difference in result.differences)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns ``0`` if every day passed, ``1`` if
    any day failed - suitable for a pre-commit gate."""
    parser = argparse.ArgumentParser(
        description=(
            "Replay every real trading day in orb_levels.db and compare Weekly "
            "Future High/Low and Top/Bottom Strike against legacy orb_summary values."
        )
    )
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        results = run_regression_suite(args.db_path, args.output_dir)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(render_summary(results))
    if any(not result.passed for result in results):
        print()
        print("Differences:")
        print(render_failure_details(results))

    write_regression_report_csv(results, args.report_path)

    return 1 if any(not result.passed for result in results) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

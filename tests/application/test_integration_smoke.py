"""Integration smoke test: CSV -> ReplayApplication -> ReferenceBuilder ->
BusinessOrchestrator -> WeeklyFutureStage -> ReplayResult.

Traceability
------------
Exercises the full, real wiring - no mocks, no fakes - end to end:
a historical CSV loaded via ``application.replay_application.ReplayApplication``'s
default ``data.historical_data_provider.CsvHistoricalDataProvider``,
a real ``reference_builder.reference_builder.ReferenceBuilder``, a real
``business.orchestrator.BusinessOrchestrator`` running a real
``business.stages.weekly_future_stage.WeeklyFutureStage`` (itself
wrapping the real ``weekly_future.weekly_future_calculator.WeeklyFutureCalculator``
and ``strike_selector.strike_selector.StrikeSelector``), producing a
real ``application.replay_result.ReplayResult``.

Reference-ladder inputs use TC-1 (2026-07-29, verified in
``WEEKLY_FUTURE_CALCULATION_EXAMPLES.md`` and already relied on by
``tests/business/stages/test_weekly_future_stage.py`` and
``tests/application/test_replay_runner.py``), so this test's expected
Weekly Future High/Low and Top/Bottom Strike are the same
independently-verified worked example, not new/invented numbers.

Also feeds the resulting ``ReplayResult`` through every downstream
reporting module built in this delivery sequence
(``application.replay_report``, ``application.replay_view``,
``application.replay_validation``), confirming they all consume a
real, application-produced result - not just the hand-built fixtures
their own unit test files use.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from application.replay_application import ReplayApplication, ReplayApplicationConfiguration
from application.replay_configuration import ReplayConfiguration
from application.replay_report import build_report_rows, write_report_csv
from application.replay_validation import build_validation_summary, render_validation_log
from application.replay_view import build_view_rows, render_view_table
from business.stages.weekly_future_stage import WeeklyFutureStage
from models.market_snapshot import MarketSnapshot
from reference_builder.reference_validator import StrikeCandleInput
from strike_selector.strike_selector import StrikeSelector
from weekly_future.weekly_future_calculator import WeeklyFutureCalculator

_HEADER = "Date,Time,Open,High,Low,Close,Volume"

# TC-1, 2026-07-29, verified in WEEKLY_FUTURE_CALCULATION_EXAMPLES.md
_ANCHOR_STRIKE = Decimal(24200)
_EXPECTED_HIGH = Decimal("24215.45")
_EXPECTED_LOW = Decimal("24150.2")
_EXPECTED_TOP = Decimal(24200)
_EXPECTED_BOTTOM = Decimal(24150)


def _write_dataset_csv(path: Path) -> Path:
    path.write_text(
        f"{_HEADER}\n"
        "2026-07-29,09:20:00,24200,24210,24190,24205,10000\n"
        "2026-07-29,09:25:00,24205,24220,24195,24215,12000\n"
        "2026-07-29,09:30:00,24215,24225,24200,24218,9000\n",
        encoding="utf-8",
    )
    return path


def _candle(*, open_: str, high: str, low: str, close: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 29, 9, 20, 0, tzinfo=UTC),
        underlying_price=Decimal(close),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
    )


def _anchor_strike_input() -> StrikeCandleInput:
    return StrikeCandleInput(
        strike=_ANCHOR_STRIKE,
        ce_candle=_candle(open_="120", high="143.45", low="116", close="130"),
        pe_candle=_candle(open_="140", high="165.8", low="128", close="150"),
    )


def _other_strike_input(strike: int) -> StrikeCandleInput:
    return StrikeCandleInput(
        strike=Decimal(strike),
        ce_candle=_candle(open_="130", high="150", low="100", close="140"),
        pe_candle=_candle(open_="130", high="150", low="100", close="140"),
    )


def _reference_inputs() -> tuple[StrikeCandleInput, ...]:
    others = tuple(
        _other_strike_input(24000 + i * 50) for i in range(13) if 24000 + i * 50 != _ANCHOR_STRIKE
    )
    return (_anchor_strike_input(), *others[:12])


def _configuration(tmp_path: Path) -> ReplayApplicationConfiguration:
    return ReplayApplicationConfiguration(
        dataset_path=_write_dataset_csv(tmp_path / "nifty.csv"),
        symbol="NIFTY",
        timeframe="5m",
        output_directory=tmp_path / "reports",
        replay_configuration=ReplayConfiguration(
            start_date=date(2026, 7, 29), end_date=date(2026, 7, 29)
        ),
        reference_inputs=_reference_inputs(),
    )


class TestFullReplayIntegrationSmoke:
    def test_csv_to_replay_result_through_weekly_future_stage(self, tmp_path: Path) -> None:
        stage = WeeklyFutureStage(
            anchor_strike=_ANCHOR_STRIKE,
            weekly_future_calculator=WeeklyFutureCalculator(),
            strike_selector=StrikeSelector(),
        )
        app = ReplayApplication(configuration=_configuration(tmp_path), stages=(stage,))

        result = app.run()

        assert len(result.business_results) == 3
        assert result.succeeded_count == 3
        assert result.failed_count == 0
        for business_result in result.business_results:
            context = business_result.context
            assert context.reference_strike == _ANCHOR_STRIKE
            assert context.weekly_future is not None
            assert context.weekly_future.high == _EXPECTED_HIGH
            assert context.weekly_future.low == _EXPECTED_LOW
            assert context.selected_strike is not None
            assert context.selected_strike.top_strike == _EXPECTED_TOP
            assert context.selected_strike.bottom_strike == _EXPECTED_BOTTOM

    def test_replay_result_reaches_report_view_and_validation_layers(self, tmp_path: Path) -> None:
        stage = WeeklyFutureStage(
            anchor_strike=_ANCHOR_STRIKE,
            weekly_future_calculator=WeeklyFutureCalculator(),
            strike_selector=StrikeSelector(),
        )
        app = ReplayApplication(configuration=_configuration(tmp_path), stages=(stage,))

        result = app.run()

        report_rows = build_report_rows(result)
        assert len(report_rows) == 3
        assert all(row.weekly_future_high == _EXPECTED_HIGH for row in report_rows)
        write_report_csv(report_rows, tmp_path / "report.csv")
        assert (tmp_path / "report.csv").exists()

        view_rows = build_view_rows(result)
        table = render_view_table(view_rows)
        assert "24200" in table
        assert "--" not in table

        summary = build_validation_summary(result)
        assert summary.reference_strike == _ANCHOR_STRIKE
        assert summary.weekly_future_high == _EXPECTED_HIGH
        assert summary.top_strike == _EXPECTED_TOP
        assert summary.failed_count == 0
        log = render_validation_log(summary)
        assert "FAILURE" not in log

    def test_replay_result_is_written_to_disk(self, tmp_path: Path) -> None:
        stage = WeeklyFutureStage(
            anchor_strike=_ANCHOR_STRIKE,
            weekly_future_calculator=WeeklyFutureCalculator(),
            strike_selector=StrikeSelector(),
        )
        config = _configuration(tmp_path)
        app = ReplayApplication(configuration=config, stages=(stage,))

        app.run()

        assert (config.output_directory / "replay_result.json").exists()
        assert (config.output_directory / "event_log.json").exists()

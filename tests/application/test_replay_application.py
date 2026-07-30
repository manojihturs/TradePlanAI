"""Tests for application.replay_application."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from application.replay_application import ReplayApplication, ReplayApplicationConfiguration
from application.replay_configuration import ReplayConfiguration
from business.business_errors import StageExecutionError
from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from business.stages.weekly_future_stage import WeeklyFutureStage
from core.exceptions import ApplicationError, EventBusError, ValidationError
from events.event_bus import EventBus
from models.market_snapshot import MarketSnapshot
from reference_builder.reference_validator import StrikeCandleInput
from strike_selector.strike_selector import StrikeSelector
from weekly_future.weekly_future_calculator import WeeklyFutureCalculator

_HEADER = "Date,Time,Open,High,Low,Close,Volume"


class _AlwaysReadyStage:
    @property
    def name(self) -> str:
        return "stage"

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        return StageOutcome(context=context)


class _DictStateStage:
    """Sets a dict-valued tp_state, exercising _to_serializable's dict branch."""

    @property
    def name(self) -> str:
        return "dict_state_stage"

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        return StageOutcome(context=context.with_tp_state({"qualified": "true"}))


class _FaultingStage:
    """Raises an unexpected error, exercising BusinessResult.error serialization."""

    @property
    def name(self) -> str:
        return "faulting_stage"

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        raise EventBusError("simulated fault")


class _BrokenEventBus:
    """Missing subscribe_all - breaks EventRecorder construction."""

    def publish(self, event: object) -> None:  # pragma: no cover - never reached
        raise AssertionError("should not be called")


def _write_valid_csv(path: Path) -> Path:
    path.write_text(
        f"{_HEADER}\n"
        "2026-07-30,09:20:00,100,110,90,105,1000\n"
        "2026-07-30,09:21:00,105,115,95,110,2000\n",
        encoding="utf-8",
    )
    return path


def _config(tmp_path: Path, **overrides: object) -> ReplayApplicationConfiguration:
    defaults: dict[str, object] = {
        "dataset_path": _write_valid_csv(tmp_path / "nifty.csv"),
        "symbol": "NIFTY",
        "timeframe": "1m",
        "output_directory": tmp_path / "reports",
        "replay_configuration": ReplayConfiguration(
            start_date=date(2026, 7, 1), end_date=date(2026, 7, 31)
        ),
    }
    defaults.update(overrides)
    return ReplayApplicationConfiguration(**defaults)  # type: ignore[arg-type]


class TestConfigurationValidation:
    def test_valid_construction(self, tmp_path: Path) -> None:
        config = _config(tmp_path)

        assert config.symbol == "NIFTY"

    def test_none_dataset_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="dataset_path must not be None"):
            _config(tmp_path, dataset_path=None)

    def test_blank_symbol_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="symbol must not be blank"):
            _config(tmp_path, symbol="  ")

    def test_blank_timeframe_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="timeframe must not be blank"):
            _config(tmp_path, timeframe="  ")

    def test_none_output_directory_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="output_directory must not be None"):
            _config(tmp_path, output_directory=None)

    def test_none_replay_configuration_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="replay_configuration must not be None"):
            _config(tmp_path, replay_configuration=None)


class TestApplicationConstruction:
    def test_none_configuration_raises(self) -> None:
        with pytest.raises(ValidationError, match="configuration must not be None"):
            ReplayApplication(configuration=None)  # type: ignore[arg-type]


class TestZeroStages:
    def test_runs_end_to_end_with_no_business_stages(self, tmp_path: Path) -> None:
        app = ReplayApplication(configuration=_config(tmp_path))

        result = app.run()

        assert result.session.statistics is not None
        assert result.session.statistics.candles_processed == 2
        assert result.succeeded_count == 2
        assert result.failed_count == 0
        assert result.session.dataset_id == "NIFTY@1m"


class TestWithStages:
    def test_runs_end_to_end_with_registered_stage(self, tmp_path: Path) -> None:
        app = ReplayApplication(configuration=_config(tmp_path), stages=(_AlwaysReadyStage(),))

        result = app.run()

        assert result.succeeded_count == 2
        assert result.business_results[0].completed_stages == ("stage",)


class TestReportsWritten:
    def test_writes_replay_result_and_event_log(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        app = ReplayApplication(configuration=config)

        app.run()

        result_path = config.output_directory / "replay_result.json"
        event_log_path = config.output_directory / "event_log.json"
        assert result_path.is_file()
        assert event_log_path.is_file()

        parsed_result = json.loads(result_path.read_text(encoding="utf-8"))
        assert parsed_result["session"]["dataset_id"] == "NIFTY@1m"

        parsed_events = json.loads(event_log_path.read_text(encoding="utf-8"))
        assert isinstance(parsed_events, list)
        assert len(parsed_events) == 2  # MarketOpenEvent + MarketCloseEvent


class TestInjectedEventBus:
    def test_uses_the_injected_bus(self, tmp_path: Path) -> None:
        bus = EventBus()
        received: list[object] = []
        bus.subscribe_all(received.append)

        app = ReplayApplication(configuration=_config(tmp_path), event_bus=bus)
        app.run()

        assert len(received) == 2


class TestDatasetLoadFailure:
    def test_missing_file_raises_application_error(self, tmp_path: Path) -> None:
        config = _config(tmp_path, dataset_path=tmp_path / "does-not-exist.csv")
        app = ReplayApplication(configuration=config)

        with pytest.raises(ApplicationError, match="Failed to load historical dataset"):
            app.run()

    def test_invalid_csv_raises_application_error(self, tmp_path: Path) -> None:
        bad_path = tmp_path / "bad.csv"
        bad_path.write_text(f"{_HEADER}\n,09:20:00,100,110,90,105,1000\n", encoding="utf-8")
        config = _config(tmp_path, dataset_path=bad_path)
        app = ReplayApplication(configuration=config)

        with pytest.raises(ApplicationError, match="Failed to load historical dataset"):
            app.run()


class TestDictStateSerialization:
    def test_dict_valued_context_field_serializes(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        app = ReplayApplication(configuration=config, stages=(_DictStateStage(),))

        app.run()

        parsed = json.loads(
            (config.output_directory / "replay_result.json").read_text(encoding="utf-8")
        )
        assert parsed["business_results"][0]["context"]["tp_state"] == {"qualified": "true"}


class TestErrorSerialization:
    def test_business_result_error_serializes_as_string(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        app = ReplayApplication(configuration=config, stages=(_FaultingStage(),))

        app.run()

        parsed = json.loads(
            (config.output_directory / "replay_result.json").read_text(encoding="utf-8")
        )
        error = parsed["business_results"][0]["error"]
        assert isinstance(error, str)
        assert "simulated fault" in error


class TestReplayExecutionFailure:
    def test_broken_event_bus_raises_application_error(self, tmp_path: Path) -> None:
        app = ReplayApplication(
            configuration=_config(tmp_path), event_bus=_BrokenEventBus()  # type: ignore[arg-type]
        )

        with pytest.raises(ApplicationError, match="Replay execution failed"):
            app.run()


class TestReportWriteFailure:
    def test_mkdir_failure_raises_application_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        app = ReplayApplication(configuration=_config(tmp_path))

        def raise_oserror(*args: object, **kwargs: object) -> None:
            raise OSError("boom")

        monkeypatch.setattr(Path, "mkdir", raise_oserror)

        with pytest.raises(ApplicationError, match="Failed to write replay reports"):
            app.run()

    def test_write_text_failure_raises_application_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        app = ReplayApplication(configuration=_config(tmp_path))

        def raise_oserror(*args: object, **kwargs: object) -> None:
            raise OSError("boom")

        monkeypatch.setattr(Path, "write_text", raise_oserror)

        with pytest.raises(ApplicationError, match="Failed to write replay reports"):
            app.run()


def _candle_ohlc(price: str) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC),
        underlying_price=Decimal(24000),
        open=Decimal(price),
        high=Decimal(price),
        low=Decimal(price),
        close=Decimal(price),
    )


def _reference_inputs(count: int = 13) -> tuple[StrikeCandleInput, ...]:
    return tuple(
        StrikeCandleInput(
            strike=Decimal(24000 + i * 50),
            ce_candle=_candle_ohlc("150"),
            pe_candle=_candle_ohlc("120"),
        )
        for i in range(count)
    )


class _ReferenceCapturingStage:
    def __init__(self) -> None:
        self.observed: list[tuple[object, ...]] = []

    @property
    def name(self) -> str:
        return "reference_capturing_stage"

    def is_ready(self, context: PipelineContext) -> bool:
        return True

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        self.observed.append(context.reference_data)
        return StageOutcome(context=context)


class TestReferenceBuilderIntegration:
    def test_reference_level_reaches_business_stages(self, tmp_path: Path) -> None:
        stage = _ReferenceCapturingStage()
        config = _config(tmp_path, reference_inputs=_reference_inputs())
        app = ReplayApplication(configuration=config, stages=(stage,))

        app.run()

        assert len(stage.observed) == 2
        assert all(len(observed) == 13 for observed in stage.observed)

    def test_default_reference_builder_is_constructed_when_none_injected(
        self, tmp_path: Path
    ) -> None:
        stage = _ReferenceCapturingStage()
        config = _config(tmp_path, reference_inputs=_reference_inputs())
        app = ReplayApplication(configuration=config, stages=(stage,))

        app.run()

        assert len(stage.observed[0]) == 13

    def test_no_reference_inputs_leaves_reference_data_empty(self, tmp_path: Path) -> None:
        stage = _ReferenceCapturingStage()
        app = ReplayApplication(configuration=_config(tmp_path), stages=(stage,))

        app.run()

        assert stage.observed == [(), ()]

    def test_reference_builder_failure_raises_application_error(self, tmp_path: Path) -> None:
        config = _config(tmp_path, reference_inputs=_reference_inputs(count=5))
        app = ReplayApplication(configuration=config)

        with pytest.raises(ApplicationError, match="Replay execution failed"):
            app.run()


class TestEdgeCaseStress:
    """Sprint: Exception & Edge Case Testing. Every scenario here must
    either return a valid ReplayResult or raise a descriptive
    ApplicationError - never an unhandled crash."""

    def test_empty_dataset_raises_descriptive_application_error(self, tmp_path: Path) -> None:
        empty_path = tmp_path / "empty.csv"
        empty_path.write_text(f"{_HEADER}\n", encoding="utf-8")
        config = _config(tmp_path, dataset_path=empty_path)
        app = ReplayApplication(configuration=config)

        with pytest.raises(ApplicationError, match="Failed to load historical dataset"):
            app.run()

    def test_missing_reference_level_for_anchor_is_absorbed_not_raised(
        self, tmp_path: Path
    ) -> None:
        """A full 13-strike ladder is built successfully, but none of
        its strikes match WeeklyFutureStage's configured anchor - the
        stage's ValidationError must be absorbed into BusinessResult,
        not raised out of ReplayApplication.run()."""
        stage = WeeklyFutureStage(
            anchor_strike=Decimal(99999),  # deliberately not in the ladder
            weekly_future_calculator=WeeklyFutureCalculator(),
            strike_selector=StrikeSelector(),
        )
        config = _config(tmp_path, reference_inputs=_reference_inputs())
        app = ReplayApplication(configuration=config, stages=(stage,))

        result = app.run()

        assert result.failed_count == len(result.business_results)
        for business_result in result.business_results:
            assert business_result.success is False
            assert isinstance(business_result.error, StageExecutionError)
            assert "No ReferenceLevel found for anchor strike" in str(business_result.error)

    def test_duplicate_strikes_in_reference_inputs_raises_application_error(
        self, tmp_path: Path
    ) -> None:
        duplicated = _reference_inputs()[:12] + (_reference_inputs()[0],)
        config = _config(tmp_path, reference_inputs=duplicated)
        app = ReplayApplication(configuration=config)

        with pytest.raises(ApplicationError, match="Replay execution failed"):
            app.run()

    def test_incomplete_ladder_raises_application_error_not_a_crash(self, tmp_path: Path) -> None:
        config = _config(tmp_path, reference_inputs=_reference_inputs(count=1))
        app = ReplayApplication(configuration=config)

        with pytest.raises(ApplicationError, match="Replay execution failed"):
            app.run()


class TestLogging:
    """Sprint: Logging. Every replay must log started/finished with
    execution time, ReferenceBuilder/WeeklyFuture/StrikeSelector
    completion, and failures - via the standard library logging
    module."""

    def test_logs_replay_started_and_finished(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        app = ReplayApplication(configuration=_config(tmp_path))

        with caplog.at_level("INFO"):
            result = app.run()

        assert "Replay started" in caplog.text
        assert "Replay finished" in caplog.text
        assert f"succeeded={result.succeeded_count}" in caplog.text
        assert f"failed={result.failed_count}" in caplog.text

    def test_logs_reference_builder_weekly_future_and_strike_selector_completed(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        stage = WeeklyFutureStage(
            anchor_strike=Decimal(24200),
            weekly_future_calculator=WeeklyFutureCalculator(),
            strike_selector=StrikeSelector(),
        )
        config = _config(tmp_path, reference_inputs=_reference_inputs())
        app = ReplayApplication(configuration=config, stages=(stage,))

        with caplog.at_level("INFO"):
            app.run()

        assert "ReferenceBuilder completed" in caplog.text
        assert "WeeklyFuture completed" in caplog.text
        assert "StrikeSelector completed" in caplog.text

    def test_logs_dataset_load_failure(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        config = _config(tmp_path, dataset_path=tmp_path / "does-not-exist.csv")
        app = ReplayApplication(configuration=config)

        with caplog.at_level("ERROR"), pytest.raises(ApplicationError):
            app.run()

        assert "Replay failed to load dataset" in caplog.text

    def test_logs_replay_execution_failure(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        config = _config(tmp_path, reference_inputs=_reference_inputs(count=1))
        app = ReplayApplication(configuration=config)

        with caplog.at_level("ERROR"), pytest.raises(ApplicationError):
            app.run()

        assert "Replay execution failed" in caplog.text

    def test_logs_report_write_failure(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        app = ReplayApplication(configuration=_config(tmp_path))

        def raise_oserror(self: Path, *args: object, **kwargs: object) -> None:
            raise OSError("boom")

        monkeypatch.setattr(Path, "write_text", raise_oserror)

        with caplog.at_level("ERROR"), pytest.raises(ApplicationError):
            app.run()

        assert "Replay failed to write reports" in caplog.text

    def test_logs_stage_failure(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        stage = WeeklyFutureStage(
            anchor_strike=Decimal(99999),  # not in the built ladder
            weekly_future_calculator=WeeklyFutureCalculator(),
            strike_selector=StrikeSelector(),
        )
        config = _config(tmp_path, reference_inputs=_reference_inputs())
        app = ReplayApplication(configuration=config, stages=(stage,))

        with caplog.at_level("ERROR"):
            app.run()

        assert "Stage weekly_future failed" in caplog.text

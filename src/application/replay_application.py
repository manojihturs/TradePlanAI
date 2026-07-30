"""ReplayApplication: the composition root for a historical replay run.

Traceability
------------
Wires together every component built in the prior three sprints -
:class:`~data.historical_data_provider.CsvHistoricalDataProvider`,
:class:`~business.orchestrator.BusinessOrchestrator`,
:class:`~application.replay_runner.ReplayRunner` - and nothing else.
This module contains no trading logic and instantiates no business
engine itself: every
:class:`~business.business_pipeline.PipelineStage` registered comes
from the caller (constructor-injected), so this class works
identically whether zero or six business engines are wired in.

"Load configuration" (this sprint's own instruction) is interpreted
as accepting an already-constructed, already-validated
:class:`ReplayApplicationConfiguration` via constructor injection -
no config-file format (YAML/JSON/TOML) has any evidence or prior
convention in this repository, and inventing one would be
speculative. See this sprint's Architecture Review for this decision
recorded explicitly.

Error handling: every step (dataset load, replay execution, report
writing) is wrapped in :class:`~core.exceptions.ApplicationError`
with a stage-labeled message and ``from exc`` - "gracefully report"
is read as *clearly labeled*, never as *silently recovered*, per this
sprint's own "never invent recovery behaviour" instruction.

Logging (Sprint: "Logging", Delivery Mode): uses the standard library
:mod:`logging` module via ``logging.getLogger(__name__)``, matching
this repository's own existing convention (e.g.
``strategy/replay_engine.py``) rather than introducing a new logging
abstraction - no handler/level is configured here, that remains the
caller's responsibility. Logs "Replay started"/"Replay finished" (with
succeeded/failed counts and execution time) at ``INFO``, and every
caught failure at ``ERROR`` before it is re-raised as
``ApplicationError`` - observability only, no behaviour change.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, date, datetime, timedelta
from datetime import tzinfo as TzInfo
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from application.replay_configuration import ReplayConfiguration
from application.replay_result import ReplayResult
from application.replay_runner import ReplayRunner
from business.business_pipeline import PipelineStage
from business.execution_context import ExecutionContext, ExecutionMode
from business.orchestrator import BusinessOrchestrator
from core.exceptions import ApplicationError, ValidationError
from core.protocols import Clock, EventBusProtocol, IdFactory, utc_now
from data.historical_data_provider import CsvHistoricalDataProvider
from data.historical_dataset import HistoricalDataset
from event_recorder.event_recorder import EventRecorder
from events.event_bus import EventBus
from reference_builder.reference_builder import ReferenceBuilder
from reference_builder.reference_validator import StrikeCandleInput
from replay.replay_engine import ReplayEngine

_REPLAY_RESULT_FILENAME = "replay_result.json"
_EVENT_LOG_FILENAME = "event_log.json"

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReplayApplicationConfiguration:
    """Everything a :class:`ReplayApplication` run needs to know.

    Attributes:
        dataset_path: Path to the historical CSV data source.
        symbol: The instrument symbol to load.
        timeframe: The candle timeframe label (structural only).
        output_directory: Where replay reports are written.
        replay_configuration: The
            :class:`~application.replay_configuration.ReplayConfiguration`
            the replay itself executes under.
        tzinfo: Timezone applied to parsed CSV timestamps.
    """

    dataset_path: Path
    symbol: str
    timeframe: str
    output_directory: Path
    replay_configuration: ReplayConfiguration
    tzinfo: TzInfo = UTC
    reference_inputs: tuple[StrikeCandleInput, ...] = ()

    def __post_init__(self) -> None:
        if self.dataset_path is None:
            raise ValidationError("ReplayApplicationConfiguration.dataset_path must not be None.")
        if not self.symbol or not self.symbol.strip():
            raise ValidationError("ReplayApplicationConfiguration.symbol must not be blank.")
        if not self.timeframe or not self.timeframe.strip():
            raise ValidationError("ReplayApplicationConfiguration.timeframe must not be blank.")
        if self.output_directory is None:
            raise ValidationError(
                "ReplayApplicationConfiguration.output_directory must not be None."
            )
        if self.replay_configuration is None:
            raise ValidationError(
                "ReplayApplicationConfiguration.replay_configuration must not be None."
            )


class ReplayApplication:
    """Composes a full historical replay run: load data, run the
    business pipeline candle by candle, write reports.

    The only place in this codebase responsible for wiring these
    components together. Constructor-injected dependencies only - no
    globals, no singletons. Registers only the
    :class:`~business.business_pipeline.PipelineStage` instances the
    caller supplies; instantiates none itself.
    """

    def __init__(
        self,
        configuration: ReplayApplicationConfiguration,
        stages: tuple[PipelineStage, ...] = (),
        event_bus: EventBusProtocol | None = None,
        clock: Clock = utc_now,
        id_factory: IdFactory = uuid.uuid4,
        data_provider: CsvHistoricalDataProvider | None = None,
        reference_builder: ReferenceBuilder | None = None,
    ) -> None:
        if configuration is None:
            raise ValidationError("ReplayApplication.configuration must not be None.")
        self._configuration = configuration
        self._stages = stages
        self._event_bus = event_bus
        self._clock = clock
        self._id_factory = id_factory
        self._data_provider = (
            data_provider if data_provider is not None else CsvHistoricalDataProvider()
        )
        self._reference_builder = (
            reference_builder if reference_builder is not None else ReferenceBuilder()
        )

    def run(self) -> ReplayResult:
        """Execute one full replay: load data, run the business
        pipeline over every candle, write reports, return the result.

        Raises:
            core.exceptions.ApplicationError: wrapping the original
                exception, if the dataset cannot be loaded, the
                replay itself fails, or reports cannot be written.
        """
        logger.info(
            "Replay started: dataset=%s symbol=%s timeframe=%s",
            self._configuration.dataset_path,
            self._configuration.symbol,
            self._configuration.timeframe,
        )
        dataset = self._load_dataset()
        result = self._execute_replay(dataset)
        self._write_reports(result)
        logger.info(
            "Replay finished: succeeded=%d failed=%d execution_time=%ss",
            result.succeeded_count,
            result.failed_count,
            result.session.duration_seconds,
        )
        return result

    def _load_dataset(self) -> HistoricalDataset:
        try:
            return self._data_provider.load_csv(
                path=self._configuration.dataset_path,
                symbol=self._configuration.symbol,
                timeframe=self._configuration.timeframe,
                tzinfo=self._configuration.tzinfo,
            )
        except Exception as exc:
            logger.error("Replay failed to load dataset: %s", exc)
            raise ApplicationError(
                f"Failed to load historical dataset for "
                f"{self._configuration.symbol}@{self._configuration.timeframe} "
                f"from {self._configuration.dataset_path}: {exc}"
            ) from exc

    def _execute_replay(self, dataset: HistoricalDataset) -> ReplayResult:
        try:
            bus = self._event_bus if self._event_bus is not None else EventBus()
            execution = ExecutionContext(
                mode=ExecutionMode.REPLAY, clock=self._clock, event_bus=bus
            )
            orchestrator = BusinessOrchestrator(execution)
            for stage in self._stages:
                orchestrator.register(stage)

            replay_engine = ReplayEngine(bus=bus, clock=self._clock, id_factory=self._id_factory)
            recorder = EventRecorder(bus)
            runner = ReplayRunner(
                replay_engine=replay_engine,
                orchestrator=orchestrator,
                event_recorder=recorder,
                clock=self._clock,
                id_factory=self._id_factory,
                reference_builder=self._reference_builder,
            )
            return runner.run(
                dataset,
                self._configuration.replay_configuration,
                reference_inputs=self._configuration.reference_inputs,
            )
        except Exception as exc:
            logger.error("Replay execution failed: %s", exc)
            raise ApplicationError(f"Replay execution failed: {exc}") from exc

    def _write_reports(self, result: ReplayResult) -> None:
        try:
            self._configuration.output_directory.mkdir(parents=True, exist_ok=True)
            (self._configuration.output_directory / _REPLAY_RESULT_FILENAME).write_text(
                json.dumps(_to_serializable(result), indent=2), encoding="utf-8"
            )
            (self._configuration.output_directory / _EVENT_LOG_FILENAME).write_text(
                json.dumps(_to_serializable(list(result.events)), indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Replay failed to write reports: %s", exc)
            raise ApplicationError(
                f"Failed to write replay reports to {self._configuration.output_directory}: {exc}"
            ) from exc


def _to_serializable(value: Any) -> Any:
    """Recursively convert ``value`` into JSON-safe primitives.

    A minimal, module-private helper - not a new public abstraction -
    scoped to exactly what :meth:`ReplayApplication._write_reports`
    needs (dataclasses, enums, ``Decimal``/``date``/``datetime``,
    collections).
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _to_serializable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_serializable(item) for key, item in value.items()}
    if isinstance(value, BaseException):
        return str(value)
    return value

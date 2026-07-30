"""ReplayRunner: drives historical candles through the Business Orchestration Layer.

Traceability
------------
Deliberately does not reimplement stage execution or failure handling
- ``business.business_pipeline.BusinessPipeline`` (v0.6.0) already
provides exactly that ("execute registered stages in order, stop on
unready/UnresolvedBusinessRuleError/fault, never raise, return an
immutable result"). This sprint's Architecture Review rejected a
requested "PipelineExecutor" for duplicating it - ``ReplayRunner``
calls ``business.orchestrator.BusinessOrchestrator.run()`` directly,
once per candle, instead.

Because ``BusinessOrchestrator.run()`` (via ``BusinessPipeline``)
never raises - even when a stage raises
``core.exceptions.UnresolvedBusinessRuleError`` - this loop already
"continues gracefully" through every business engine returning
UNRESOLVED, by construction, with no special-casing needed here.

Consumes a ``data.historical_dataset.HistoricalDataset`` (Sprint 6)
rather than a raw candle collection, so the dataset's own identity
(``symbol``/``timeframe``, via :attr:`~data.historical_dataset.HistoricalDataset.key`)
becomes the replay session's ``dataset_id`` automatically - no
separate identifier needs to be supplied by the caller.

Reference ladder integration: if a ``reference_builder.reference_builder.ReferenceBuilder``
and non-empty ``reference_inputs`` are supplied, the ladder is built
exactly once per run (matching Specification Rule 1's "first
5-minute candle" - a session-level, not per-candle, fact) and
threaded into every candle's ``PipelineContext.reference_data`` via
:meth:`~business.pipeline_context.PipelineContext.with_reference_data`.
``ReplayRunner`` does not call ``WeeklyFutureCalculator`` (or any
other business engine) directly - it only makes the reference ladder
available in context for whatever ``business.business_pipeline.PipelineStage``
adapters are registered on the injected ``BusinessOrchestrator`` to
consume. Calling the engine directly from here would duplicate
``BusinessPipeline``'s own responsibility, the same duplication this
project already rejected once for a proposed "PipelineExecutor".

Deriving ``reference_inputs`` (13 strikes' worth of per-strike CE/PE
option-chain data) automatically from a ``HistoricalDataset`` (a
single underlying instrument's plain OHLC series, with no strike or
option-chain dimension at all) is not implemented here and is not
possible from the data shapes that exist today - see this sprint's
report for why that remains a caller responsibility, not invented.
"""

from __future__ import annotations

import uuid

from application.replay_configuration import ReplayConfiguration
from application.replay_result import ReplayResult
from application.replay_session import ReplaySession, ReplayStatistics, ReplayStatus
from business.business_result import BusinessResult
from business.orchestrator import BusinessOrchestrator
from business.pipeline_context import PipelineContext
from core.protocols import Clock, IdFactory, utc_now
from data.historical_dataset import HistoricalDataset
from event_recorder.event_recorder import EventRecorder
from models.reference_level import ReferenceLevel
from reference_builder.reference_builder import ReferenceBuilder
from reference_builder.reference_validator import StrikeCandleInput
from replay.replay_engine import ReplayEngine


class ReplayRunner:
    """Feeds historical candles into a
    :class:`~business.orchestrator.BusinessOrchestrator`, one per
    candle, and reports the outcome.

    Constructor-injected dependencies only - no globals, no
    singletons.
    """

    def __init__(
        self,
        replay_engine: ReplayEngine,
        orchestrator: BusinessOrchestrator,
        event_recorder: EventRecorder | None = None,
        clock: Clock = utc_now,
        id_factory: IdFactory = uuid.uuid4,
        reference_builder: ReferenceBuilder | None = None,
    ) -> None:
        self._replay_engine = replay_engine
        self._orchestrator = orchestrator
        self._event_recorder = event_recorder
        self._clock = clock
        self._id_factory = id_factory
        self._reference_builder = reference_builder

    def run(
        self,
        dataset: HistoricalDataset,
        configuration: ReplayConfiguration,
        reference_inputs: tuple[StrikeCandleInput, ...] = (),
    ) -> ReplayResult:
        """Replay every candle in ``dataset`` end to end and return
        the full :class:`~application.replay_result.ReplayResult`.

        ``dataset.key`` (``"<symbol>@<timeframe>"``) becomes the
        resulting :attr:`~application.replay_session.ReplaySession.dataset_id`.

        If a ``reference_builder`` was injected and ``reference_inputs``
        is non-empty, the reference ladder is built once and made
        available to every candle via ``PipelineContext.reference_data``
        - see module docstring.

        Raises:
            core.exceptions.ReplayError: propagated unchanged from
                :meth:`~replay.replay_engine.ReplayEngine.run` - not
                expected in practice, since
                :class:`~data.historical_dataset.HistoricalDataset`
                already guarantees at least one snapshot.
            core.exceptions.ValidationError: propagated unchanged from
                :meth:`~reference_builder.reference_builder.ReferenceBuilder.build`
                if ``reference_inputs`` fails validation.
        """
        session_id = self._id_factory()
        started_at = self._clock()

        reference_data: tuple[ReferenceLevel, ...] = ()
        if self._reference_builder is not None and reference_inputs:
            reference_data = self._reference_builder.build(session_id, reference_inputs)

        business_results: list[BusinessResult] = []
        candles_processed = 0
        succeeded = 0
        failed = 0

        for candle in self._replay_engine.run(session_id, dataset.snapshots):
            candles_processed += 1
            context = PipelineContext(
                session_id=session_id,
                candle_timestamp=candle.timestamp,
                reference_data=reference_data,
            )
            result = self._orchestrator.run(context)
            business_results.append(result)
            if result.success:
                succeeded += 1
            else:
                failed += 1

        ended_at = self._clock()
        events = () if self._event_recorder is None else self._event_recorder.get_events()

        statistics = ReplayStatistics(
            candles_processed=candles_processed,
            events_recorded=len(events),
            business_runs_succeeded=succeeded,
            business_runs_failed=failed,
        )
        session = ReplaySession(
            session_id=session_id,
            dataset_id=dataset.key,
            started_at=started_at,
            status=ReplayStatus.COMPLETED,
            ended_at=ended_at,
            statistics=statistics,
        )

        return ReplayResult(
            session=session,
            configuration=configuration,
            generated_at=self._clock(),
            business_results=tuple(business_results),
            events=events,
        )

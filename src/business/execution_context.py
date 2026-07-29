"""ExecutionContext: run-mode and injected infrastructure for a pipeline run.

Traceability
------------
"Support replay mode / support live mode" is an infrastructure
requirement, not a business rule - both modes run the identical
pipeline/stage sequence; ``mode`` exists so a stage adapter *may*
branch on it if its own concrete implementation needs to (e.g. a
replay-sourced clock vs. a live feed's clock), matching
``replay.replay_engine.ReplayEngine``'s existing injected-clock
pattern (Sprint 1) rather than inventing a new mechanism.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum, unique

from core.exceptions import ValidationError
from core.protocols import Clock, EventBusProtocol, IdFactory, utc_now


@unique
class ExecutionMode(Enum):
    """Which data source this pipeline run is operating against.

    A pure infrastructure concept - no business rule differs between
    the two modes anywhere in this package.
    """

    LIVE = "LIVE"
    REPLAY = "REPLAY"


def default_id_factory() -> uuid.UUID:
    """The default :data:`~core.protocols.IdFactory` for
    :class:`ExecutionContext`, matching ``core.protocols.utc_now``'s
    role as the shared default :data:`~core.protocols.Clock`."""
    return uuid.uuid4()


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Constructor-injected infrastructure for a single pipeline run.

    Attributes:
        mode: :class:`ExecutionMode.LIVE` or :class:`ExecutionMode.REPLAY`.
        clock: Injectable time source, defaulting to
            :func:`core.protocols.utc_now` per
            ``CODING_STANDARDS.md`` - never call ``datetime.now()``
            directly.
        id_factory: Injectable UUID source, for deterministic testing,
            defaulting to :func:`default_id_factory`.
        event_bus: Optional bus a :class:`~business.business_pipeline.PipelineStage`'s
            events are published to, via
            :class:`~business.business_pipeline.BusinessPipeline`. ``None``
            is valid - a caller that doesn't need events published
            (e.g. a dry-run) simply omits it.
    """

    mode: ExecutionMode
    clock: Clock = utc_now
    id_factory: IdFactory = default_id_factory
    event_bus: EventBusProtocol | None = None

    def __post_init__(self) -> None:
        if self.mode is None:
            raise ValidationError("ExecutionContext.mode must not be None.")
        if self.clock is None:
            raise ValidationError("ExecutionContext.clock must not be None.")
        if self.id_factory is None:
            raise ValidationError("ExecutionContext.id_factory must not be None.")

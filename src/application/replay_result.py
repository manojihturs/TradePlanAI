"""ReplayResult: the full output of one ReplayRunner run.

Traceability
------------
Deliberately wraps ``business.business_result.BusinessResult`` (one
per candle) rather than defining a parallel "ExecutionSummary" type -
see ``ReplayRunner``'s own docstring and this sprint's Architecture
Review for why a second summary type was rejected as duplicating
existing v0.6.0 code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from application.replay_configuration import ReplayConfiguration
from application.replay_session import ReplaySession
from business.business_result import BusinessResult
from core.events import Event
from core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """The full output of one :meth:`~application.replay_runner.ReplayRunner.run`
    call.

    Attributes:
        session: The completed :class:`~application.replay_session.ReplaySession`.
        configuration: The :class:`~application.replay_configuration.ReplayConfiguration`
            this run executed under.
        business_results: One :class:`~business.business_result.BusinessResult`
            per candle processed, in candle order.
        events: Every domain event recorded during the run, if an
            :class:`~event_recorder.event_recorder.EventRecorder` was
            injected into the
            :class:`~application.replay_runner.ReplayRunner`. Empty
            otherwise.
        generated_at: When this result was produced.
    """

    session: ReplaySession
    configuration: ReplayConfiguration
    generated_at: datetime
    business_results: tuple[BusinessResult, ...] = field(default_factory=tuple)
    events: tuple[Event, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.session is None:
            raise ValidationError("ReplayResult.session must not be None.")
        if self.configuration is None:
            raise ValidationError("ReplayResult.configuration must not be None.")
        if self.generated_at is None:
            raise ValidationError("ReplayResult.generated_at must not be None.")

    @property
    def succeeded_count(self) -> int:
        """How many per-candle business results were successful."""
        return sum(1 for result in self.business_results if result.success)

    @property
    def failed_count(self) -> int:
        """How many per-candle business results were not successful."""
        return sum(1 for result in self.business_results if not result.success)

"""DiagnosticsSink: where diagnostic events go.

Traceability notes
-------------------
Three implementations are provided, covering the three consumption
modes this milestone anticipates:

- :class:`NullDiagnosticsSink` - discards every event. This is the
  sink effectively used whenever
  :attr:`trading_engine.engine.engine_configuration.EngineConfiguration.logging_enabled`
  is ``False``, guaranteeing the "no-op when disabled" requirement
  holds regardless of what sink a caller may have configured.
- :class:`InMemoryDiagnosticsSink` - collects events into an ordered,
  readable list. Intended for tests (see
  ``trading_engine/tests/diagnostics/``) and for a future
  replay/backtest consumer that needs to inspect the exact event
  sequence a run produced (see ``research/analysis/DIAGNOSTICS_GUIDE.md``).
- :class:`StandardLoggingDiagnosticsSink` - forwards every event to
  Python's standard library :mod:`logging` module, so a developer
  running the engine locally sees diagnostic output without wiring
  anything extra.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from trading_engine.diagnostics.events import DiagnosticEvent

#: The logger name every :class:`StandardLoggingDiagnosticsSink`
#: instance uses by default - callers can configure handlers/levels
#: for this logger the same way as any other standard library logger.
DEFAULT_LOGGER_NAME = "trading_engine.diagnostics"


@runtime_checkable
class DiagnosticsSink(Protocol):
    """The structural contract every diagnostics sink satisfies.

    A ``typing.Protocol``, matching the rest of this codebase's
    contract style (:class:`trading_engine.rules.protocols.Rule`,
    :class:`trading_engine.calculators.protocols.Calculator`) - any
    object with an ``emit`` method of the right shape qualifies,
    without a forced inheritance relationship.
    """

    def emit(self, event: DiagnosticEvent) -> None:
        """Record or forward one diagnostic event."""
        ...


class NullDiagnosticsSink:
    """A sink that discards every event.

    The effective sink whenever logging is disabled - see module
    docstring.
    """

    def emit(self, event: DiagnosticEvent) -> None:
        return None


class InMemoryDiagnosticsSink:
    """A sink that collects every event, in emission order.

    Not thread-safe - matches this codebase's synchronous, single
    execution-pipeline design (see
    :class:`trading_engine.engine.execution_pipeline.ExecutionPipeline`);
    no concurrent execution exists anywhere in this repository yet.
    """

    def __init__(self) -> None:
        self._events: list[DiagnosticEvent] = []

    def emit(self, event: DiagnosticEvent) -> None:
        self._events.append(event)

    def events(self) -> tuple[DiagnosticEvent, ...]:
        """Return every event recorded so far, in emission order."""
        return tuple(self._events)

    def __len__(self) -> int:
        return len(self._events)


class StandardLoggingDiagnosticsSink:
    """A sink that forwards every event to :mod:`logging`.

    Each event is logged at ``INFO`` level via ``%r``-style
    formatting (the event's own ``repr()``) - no custom formatting
    logic exists here, since every event is already a small, readable
    frozen dataclass.
    """

    def __init__(self, logger_name: str = DEFAULT_LOGGER_NAME) -> None:
        self._logger = logging.getLogger(logger_name)

    def emit(self, event: DiagnosticEvent) -> None:
        self._logger.info("%r", event)

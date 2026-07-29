"""Diagnostic events for the premium snapshot infrastructure.

Traceability notes
-------------------
Following the precedent established in Milestones B1 and I1, new
diagnostic event types are added *additively* to the existing, shared
``trading_engine/diagnostics/events.py`` - never as a parallel logging
mechanism - because :class:`~trading_engine.diagnostics.sink.DiagnosticsSink.emit`
is typed against a single closed ``DiagnosticEvent`` union, and
``trading_engine.diagnostics`` is deliberately foundational (nothing
in it depends on any other subsystem). Defining these six events here
instead would either break that dependency direction (this package
sits above diagnostics) or require widening ``DiagnosticsSink.emit``'s
parameter type away from the closed union, losing the compile-time
visibility that union gives every event kind.

This module is the package-local import surface Milestone I2 asks
for: the six event classes are defined in
``trading_engine.diagnostics.events`` and simply re-exported here, so
the rest of :mod:`trading_engine.premium_snapshot` imports them from
their own package rather than reaching into ``diagnostics`` directly.
"""

from __future__ import annotations

from trading_engine.diagnostics.events import (
    RecorderFlushed,
    RecorderStarted,
    RecorderStopped,
    SnapshotCompleted,
    SnapshotStarted,
    SnapshotStored,
)

__all__ = [
    "RecorderFlushed",
    "RecorderStarted",
    "RecorderStopped",
    "SnapshotCompleted",
    "SnapshotStarted",
    "SnapshotStored",
]

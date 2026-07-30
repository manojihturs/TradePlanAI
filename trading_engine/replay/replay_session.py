"""ReplaySession: identity and statistics wrapper around a ReplayClock.

Traceability notes
-------------------
Pure infrastructure - a thin bookkeeping layer over
:class:`~trading_engine.replay.replay_clock.ReplayClock`. All position
and state data is read directly from the wrapped clock (never
duplicated/cached here) so the two can never silently disagree; this
class adds only a stable session identity and derived statistics.

"Elapsed Replay Time" (Milestone B1's Task 5) is deliberately defined
as **simulated/data time** - the span between the first candle's
timestamp and the current candle's timestamp - rather than wall-clock
processing time. This matches "historical market replay" (the
sequence's own timeline), and avoids introducing a second, real-time
clock dependency into infrastructure that is explicitly not paced in
real time (see
``trading_engine/replay/replay_clock.py``'s "No GUI" note). A future
wall-clock "how long has this replay actually taken to process"
metric is a distinct, not-yet-built concept - see
``research/analysis/REPLAY_ENGINE_ARCHITECTURE.md``'s extension
points.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from trading_engine.replay.replay_clock import ReplayClock, ReplayState


@dataclass(frozen=True)
class ReplayStatistics:
    """A snapshot of one :class:`ReplaySession`'s progress.

    Attributes:
        processed_candles: How many candles have been visited so far
            (including the current one), or ``0`` if the session has
            not started.
        remaining_candles: How many candles remain after the current
            position.
        elapsed_replay_time: The simulated/data time span between the
            first candle and the current candle - see module
            docstring.
    """

    processed_candles: int
    remaining_candles: int
    elapsed_replay_time: timedelta


class ReplaySession:
    """Identity and statistics for one replay run over a
    :class:`~trading_engine.replay.replay_clock.ReplayClock`.

    Rule References
        None - infrastructure only.

    Attributes:
        session_id: This session's unique identifier.
        clock: The wrapped :class:`ReplayClock` this session reports on.
    """

    def __init__(self, clock: ReplayClock, session_id: uuid.UUID | None = None) -> None:
        self.session_id = session_id if session_id is not None else uuid.uuid4()
        self.clock = clock

    @property
    def current_index(self) -> int:
        """The wrapped clock's current candle index."""
        return self.clock.current_index

    @property
    def current_timestamp(self) -> datetime:
        """The wrapped clock's current candle's timestamp."""
        return self.clock.current_candle().timestamp

    @property
    def state(self) -> ReplayState:
        """The wrapped clock's current :class:`ReplayState`."""
        return self.clock.state

    def statistics(self) -> ReplayStatistics:
        """Compute this session's current :class:`ReplayStatistics`."""
        total = self.clock.total_candles
        processed = (
            0 if self.clock.state == ReplayState.NOT_STARTED else self.clock.current_index + 1
        )
        remaining = total - processed

        return ReplayStatistics(
            processed_candles=processed,
            remaining_candles=remaining,
            elapsed_replay_time=self._elapsed_replay_time(),
        )

    def _elapsed_replay_time(self) -> timedelta:
        if self.clock.state == ReplayState.NOT_STARTED:
            return timedelta(0)

        return self.clock.current_candle().timestamp - self.clock.first_candle().timestamp

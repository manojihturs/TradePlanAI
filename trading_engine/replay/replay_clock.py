"""ReplayClock: positional/state cursor over a loaded candle sequence.

Traceability notes
-------------------
Pure infrastructure - tracks *where* replay currently is (an index
into an immutable candle sequence) and *what state* it is in (not
started / running / paused / stopped / completed). No trading
mathematics: nothing here reads a candle's OHLC values or decides
anything based on them, only its position in the sequence.

"No GUI" (Milestone B1's Task 3): this class exposes state and
transitions only - it renders nothing, and ``playback_speed`` is
stored/exposed but not itself used to pace real-time execution (there
is no timer/sleep loop anywhere in this class) - see
``research/analysis/REPLAY_ENGINE_ARCHITECTURE.md``'s "Known
limitations" for why real-time pacing is an explicit, undone extension
point rather than something guessed at here.
"""

from __future__ import annotations

from enum import Enum, auto

from trading_engine.replay.exceptions import ReplayStateError
from trading_engine.replay.history_loader import Candle


class ReplayState(Enum):
    """The lifecycle states a :class:`ReplayClock` (and, by
    extension, a :class:`~trading_engine.replay.replay_session.ReplaySession`)
    can be in.
    """

    #: Constructed, but :meth:`ReplayClock` has not been asked to run yet.
    NOT_STARTED = auto()

    #: Actively positioned somewhere in the sequence, not paused.
    RUNNING = auto()

    #: Temporarily halted; can :meth:`ReplayClock.resume`.
    PAUSED = auto()

    #: Deliberately halted by the caller; not resumable (distinct from
    #: ``COMPLETED``, which means the sequence was exhausted, and from
    #: ``PAUSED``, which is resumable).
    STOPPED = auto()

    #: The last candle in the sequence has been reached via
    #: :meth:`ReplayClock.step_forward` - nothing left to step to.
    COMPLETED = auto()


class ReplayClock:
    """A positional cursor over an immutable sequence of
    :class:`~trading_engine.replay.history_loader.Candle` objects.

    Rule References
        None - infrastructure only.

    Attributes:
        playback_speed: A stored multiplier (default ``1.0``) with no
            effect on this class's own behaviour - see module
            docstring.
    """

    def __init__(self, candles: tuple[Candle, ...], playback_speed: float = 1.0) -> None:
        if not candles:
            raise ReplayStateError("ReplayClock requires at least one candle.")

        if playback_speed <= 0:
            raise ReplayStateError("ReplayClock.playback_speed must be positive.")

        self._candles = candles
        self._index = 0
        self._state = ReplayState.NOT_STARTED
        self.playback_speed = playback_speed

    @property
    def state(self) -> ReplayState:
        """The clock's current :class:`ReplayState`."""
        return self._state

    @property
    def current_index(self) -> int:
        """The index of :meth:`current_candle` within the loaded sequence."""
        return self._index

    @property
    def total_candles(self) -> int:
        """How many candles this clock was constructed with."""
        return len(self._candles)

    def current_candle(self) -> Candle:
        """Return the candle at the current position."""
        return self._candles[self._index]

    def first_candle(self) -> Candle:
        """Return the first candle in the sequence, regardless of the
        current position."""
        return self._candles[0]

    def last_candle(self) -> Candle:
        """Return the last candle in the sequence, regardless of the
        current position."""
        return self._candles[-1]

    def next_candle(self) -> Candle | None:
        """Return the candle after the current position, or ``None``
        if the current position is the last candle."""
        if self._index + 1 >= len(self._candles):
            return None
        return self._candles[self._index + 1]

    def previous_candle(self) -> Candle | None:
        """Return the candle before the current position, or ``None``
        if the current position is the first candle."""
        if self._index == 0:
            return None
        return self._candles[self._index - 1]

    def seek(self, index: int) -> Candle:
        """Move directly to ``index`` and return the candle there.

        Raises:
            ReplayStateError: if ``index`` is out of bounds.
        """
        if not 0 <= index < len(self._candles):
            raise ReplayStateError(
                f"ReplayClock.seek({index}) is out of bounds for a sequence of "
                f"{len(self._candles)} candles."
            )

        self._index = index
        self._state = (
            ReplayState.COMPLETED if self._index == len(self._candles) - 1 else ReplayState.RUNNING
        )
        return self.current_candle()

    def reset(self) -> None:
        """Return to the first candle and ``NOT_STARTED`` state."""
        self._index = 0
        self._state = ReplayState.NOT_STARTED

    def start(self) -> Candle:
        """Transition from ``NOT_STARTED`` to ``RUNNING`` at the first candle.

        Raises:
            ReplayStateError: if the clock is not in ``NOT_STARTED``.
        """
        if self._state != ReplayState.NOT_STARTED:
            raise ReplayStateError(
                f"ReplayClock.start() requires state NOT_STARTED, not {self._state.name}."
            )

        self._state = ReplayState.RUNNING
        return self.current_candle()

    def step_forward(self) -> Candle:
        """Advance to the next candle and return it.

        Transitions to ``COMPLETED`` (rather than raising) exactly
        when the step lands on the final candle - see
        :class:`ReplayState`.

        Raises:
            ReplayStateError: if already at or past the last candle
                (state is already ``COMPLETED``), or if the clock is
                ``PAUSED``/``STOPPED``.
        """
        if self._state in (ReplayState.PAUSED, ReplayState.STOPPED):
            raise ReplayStateError(
                f"ReplayClock.step_forward() cannot run while state is {self._state.name}."
            )

        if self._index + 1 >= len(self._candles):
            raise ReplayStateError("ReplayClock.step_forward() is already at the last candle.")

        self._index += 1
        if self._state == ReplayState.NOT_STARTED:
            self._state = ReplayState.RUNNING
        if self._index == len(self._candles) - 1:
            self._state = ReplayState.COMPLETED

        return self.current_candle()

    def step_backward(self) -> Candle:
        """Retreat to the previous candle and return it.

        Raises:
            ReplayStateError: if already at the first candle, or if
                the clock is ``PAUSED``/``STOPPED``.
        """
        if self._state in (ReplayState.PAUSED, ReplayState.STOPPED):
            raise ReplayStateError(
                f"ReplayClock.step_backward() cannot run while state is {self._state.name}."
            )

        if self._index == 0:
            raise ReplayStateError("ReplayClock.step_backward() is already at the first candle.")

        self._index -= 1
        if self._state == ReplayState.COMPLETED:
            self._state = ReplayState.RUNNING

        return self.current_candle()

    def pause(self) -> None:
        """Pause a running clock.

        Raises:
            ReplayStateError: if the clock is not ``RUNNING``.
        """
        if self._state != ReplayState.RUNNING:
            raise ReplayStateError(
                f"ReplayClock.pause() requires state RUNNING, not {self._state.name}."
            )
        self._state = ReplayState.PAUSED

    def resume(self) -> None:
        """Resume a paused clock.

        Raises:
            ReplayStateError: if the clock is not ``PAUSED``.
        """
        if self._state != ReplayState.PAUSED:
            raise ReplayStateError(
                f"ReplayClock.resume() requires state PAUSED, not {self._state.name}."
            )
        self._state = ReplayState.RUNNING

    def stop(self) -> None:
        """Deliberately, non-resumably halt the clock.

        Raises:
            ReplayStateError: if the clock is already ``STOPPED`` or
                ``COMPLETED``.
        """
        if self._state in (ReplayState.STOPPED, ReplayState.COMPLETED):
            raise ReplayStateError(
                f"ReplayClock.stop() cannot run while state is already {self._state.name}."
            )
        self._state = ReplayState.STOPPED

    def is_complete(self) -> bool:
        """Whether the clock has reached the end of the sequence."""
        return self._state == ReplayState.COMPLETED

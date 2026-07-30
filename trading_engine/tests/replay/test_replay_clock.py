"""Tests for ReplayClock and ReplayState."""

from __future__ import annotations

import pytest

from trading_engine.replay.exceptions import ReplayStateError
from trading_engine.replay.history_loader import Candle
from trading_engine.replay.replay_clock import ReplayClock, ReplayState


class TestConstructorValidation:
    def test_valid_construction(self, sample_candles: tuple[Candle, ...]) -> None:
        clock = ReplayClock(sample_candles)
        assert clock.state == ReplayState.NOT_STARTED
        assert clock.current_index == 0
        assert clock.total_candles == 5

    def test_empty_candles_raises(self) -> None:
        with pytest.raises(ReplayStateError, match="at least one candle"):
            ReplayClock(())

    def test_zero_playback_speed_raises(self, sample_candles: tuple[Candle, ...]) -> None:
        with pytest.raises(ReplayStateError, match="playback_speed must be positive"):
            ReplayClock(sample_candles, playback_speed=0)

    def test_negative_playback_speed_raises(self, sample_candles: tuple[Candle, ...]) -> None:
        with pytest.raises(ReplayStateError, match="playback_speed must be positive"):
            ReplayClock(sample_candles, playback_speed=-1)

    def test_default_playback_speed_is_one(self, sample_candles: tuple[Candle, ...]) -> None:
        assert ReplayClock(sample_candles).playback_speed == 1.0

    def test_custom_playback_speed_stored(self, sample_candles: tuple[Candle, ...]) -> None:
        clock = ReplayClock(sample_candles, playback_speed=2.5)
        assert clock.playback_speed == 2.5


class TestCurrentNextPrevious:
    def test_current_candle_at_start(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        assert sample_clock.current_candle() == sample_candles[0]

    def test_next_candle(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        assert sample_clock.next_candle() == sample_candles[1]

    def test_previous_candle_is_none_at_start(self, sample_clock: ReplayClock) -> None:
        assert sample_clock.previous_candle() is None

    def test_previous_candle_after_advancing(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        sample_clock.seek(2)
        assert sample_clock.previous_candle() == sample_candles[1]

    def test_next_candle_is_none_at_last_position(self, sample_clock: ReplayClock) -> None:
        sample_clock.seek(sample_clock.total_candles - 1)
        assert sample_clock.next_candle() is None

    def test_first_and_last_candle(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        assert sample_clock.first_candle() == sample_candles[0]
        assert sample_clock.last_candle() == sample_candles[-1]


class TestSeek:
    def test_seek_moves_to_index(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        candle = sample_clock.seek(2)
        assert candle == sample_candles[2]
        assert sample_clock.current_index == 2

    def test_seek_sets_running_state(self, sample_clock: ReplayClock) -> None:
        sample_clock.seek(1)
        assert sample_clock.state == ReplayState.RUNNING

    def test_seek_to_last_index_sets_completed(self, sample_clock: ReplayClock) -> None:
        sample_clock.seek(sample_clock.total_candles - 1)
        assert sample_clock.state == ReplayState.COMPLETED

    def test_seek_negative_raises(self, sample_clock: ReplayClock) -> None:
        with pytest.raises(ReplayStateError, match="out of bounds"):
            sample_clock.seek(-1)

    def test_seek_beyond_end_raises(self, sample_clock: ReplayClock) -> None:
        with pytest.raises(ReplayStateError, match="out of bounds"):
            sample_clock.seek(sample_clock.total_candles)


class TestReset:
    def test_reset_returns_to_start(self, sample_clock: ReplayClock) -> None:
        sample_clock.seek(3)
        sample_clock.reset()
        assert sample_clock.current_index == 0
        assert sample_clock.state == ReplayState.NOT_STARTED


class TestStartStopPauseResume:
    def test_start_transitions_to_running(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        candle = sample_clock.start()
        assert candle == sample_candles[0]
        assert sample_clock.state == ReplayState.RUNNING

    def test_start_twice_raises(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        with pytest.raises(ReplayStateError, match="requires state NOT_STARTED"):
            sample_clock.start()

    def test_pause_requires_running(self, sample_clock: ReplayClock) -> None:
        with pytest.raises(ReplayStateError, match="requires state RUNNING"):
            sample_clock.pause()

    def test_pause_then_resume(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        sample_clock.pause()
        assert sample_clock.state == ReplayState.PAUSED
        sample_clock.resume()
        assert sample_clock.state == ReplayState.RUNNING

    def test_resume_requires_paused(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        with pytest.raises(ReplayStateError, match="requires state PAUSED"):
            sample_clock.resume()

    def test_stop_sets_stopped_state(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        sample_clock.stop()
        assert sample_clock.state == ReplayState.STOPPED

    def test_stop_when_already_stopped_raises(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        sample_clock.stop()
        with pytest.raises(ReplayStateError, match="already STOPPED"):
            sample_clock.stop()

    def test_stop_when_completed_raises(self, sample_clock: ReplayClock) -> None:
        sample_clock.seek(sample_clock.total_candles - 1)
        with pytest.raises(ReplayStateError, match="already COMPLETED"):
            sample_clock.stop()


class TestStepForward:
    def test_step_forward_advances_index(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        candle = sample_clock.step_forward()
        assert candle == sample_candles[1]
        assert sample_clock.current_index == 1

    def test_step_forward_from_not_started_transitions_to_running(
        self, sample_clock: ReplayClock
    ) -> None:
        sample_clock.step_forward()
        assert sample_clock.state == ReplayState.RUNNING

    def test_step_forward_to_last_candle_completes(self, sample_clock: ReplayClock) -> None:
        for _ in range(sample_clock.total_candles - 1):
            sample_clock.step_forward()
        assert sample_clock.is_complete()
        assert sample_clock.state == ReplayState.COMPLETED

    def test_step_forward_past_end_raises(self, sample_clock: ReplayClock) -> None:
        for _ in range(sample_clock.total_candles - 1):
            sample_clock.step_forward()
        with pytest.raises(ReplayStateError, match="already at the last candle"):
            sample_clock.step_forward()

    def test_step_forward_while_paused_raises(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        sample_clock.pause()
        with pytest.raises(ReplayStateError, match="cannot run while state is PAUSED"):
            sample_clock.step_forward()

    def test_step_forward_while_stopped_raises(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        sample_clock.stop()
        with pytest.raises(ReplayStateError, match="cannot run while state is STOPPED"):
            sample_clock.step_forward()


class TestStepBackward:
    def test_step_backward_retreats_index(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        sample_clock.seek(2)
        candle = sample_clock.step_backward()
        assert candle == sample_candles[1]
        assert sample_clock.current_index == 1

    def test_step_backward_at_start_raises(self, sample_clock: ReplayClock) -> None:
        with pytest.raises(ReplayStateError, match="already at the first candle"):
            sample_clock.step_backward()

    def test_step_backward_from_completed_returns_to_running(
        self, sample_clock: ReplayClock
    ) -> None:
        sample_clock.seek(sample_clock.total_candles - 1)
        sample_clock.step_backward()
        assert sample_clock.state == ReplayState.RUNNING

    def test_step_backward_while_paused_raises(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        sample_clock.pause()
        with pytest.raises(ReplayStateError, match="cannot run while state is PAUSED"):
            sample_clock.step_backward()


class TestEdgeCases:
    def test_single_candle_clock_is_immediately_at_last_index(
        self, single_candle: tuple[Candle, ...]
    ) -> None:
        clock = ReplayClock(single_candle)
        assert clock.current_index == 0
        assert clock.next_candle() is None
        assert clock.previous_candle() is None

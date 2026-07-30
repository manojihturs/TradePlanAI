"""Tests for ReplaySession and ReplayStatistics."""

from __future__ import annotations

import uuid
from datetime import timedelta

from trading_engine.replay.history_loader import Candle
from trading_engine.replay.replay_clock import ReplayClock, ReplayState
from trading_engine.replay.replay_session import ReplaySession


class TestConstruction:
    def test_generates_a_session_id_by_default(self, sample_clock: ReplayClock) -> None:
        session = ReplaySession(sample_clock)
        assert isinstance(session.session_id, uuid.UUID)

    def test_accepts_an_explicit_session_id(self, sample_clock: ReplayClock) -> None:
        explicit_id = uuid.uuid4()
        session = ReplaySession(sample_clock, session_id=explicit_id)
        assert session.session_id == explicit_id

    def test_two_sessions_get_different_ids(self, sample_clock: ReplayClock) -> None:
        session_a = ReplaySession(sample_clock)
        session_b = ReplaySession(ReplayClock((sample_clock.current_candle(),)))
        assert session_a.session_id != session_b.session_id


class TestDelegatedProperties:
    def test_current_index_matches_clock(self, sample_clock: ReplayClock) -> None:
        sample_clock.seek(2)
        session = ReplaySession(sample_clock)
        assert session.current_index == 2

    def test_current_timestamp_matches_current_candle(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        session = ReplaySession(sample_clock)
        assert session.current_timestamp == sample_candles[0].timestamp

    def test_state_matches_clock(self, sample_clock: ReplayClock) -> None:
        session = ReplaySession(sample_clock)
        assert session.state == ReplayState.NOT_STARTED
        sample_clock.start()
        assert session.state == ReplayState.RUNNING


class TestStatistics:
    def test_not_started_has_zero_processed_and_zero_elapsed(
        self, sample_clock: ReplayClock
    ) -> None:
        session = ReplaySession(sample_clock)
        stats = session.statistics()
        assert stats.processed_candles == 0
        assert stats.remaining_candles == sample_clock.total_candles
        assert stats.elapsed_replay_time == timedelta(0)

    def test_after_start_processed_is_one(self, sample_clock: ReplayClock) -> None:
        sample_clock.start()
        session = ReplaySession(sample_clock)
        stats = session.statistics()
        assert stats.processed_candles == 1
        assert stats.remaining_candles == sample_clock.total_candles - 1

    def test_after_stepping_statistics_update(self, sample_clock: ReplayClock) -> None:
        session = ReplaySession(sample_clock)
        sample_clock.start()
        sample_clock.step_forward()
        sample_clock.step_forward()
        stats = session.statistics()
        assert stats.processed_candles == 3
        assert stats.remaining_candles == sample_clock.total_candles - 3

    def test_elapsed_replay_time_is_data_time_not_wallclock(
        self, sample_clock: ReplayClock, sample_candles: tuple[Candle, ...]
    ) -> None:
        session = ReplaySession(sample_clock)
        sample_clock.seek(2)
        stats = session.statistics()
        expected = sample_candles[2].timestamp - sample_candles[0].timestamp
        assert stats.elapsed_replay_time == expected

    def test_fully_processed_has_zero_remaining(self, sample_clock: ReplayClock) -> None:
        session = ReplaySession(sample_clock)
        sample_clock.seek(sample_clock.total_candles - 1)
        stats = session.statistics()
        assert stats.remaining_candles == 0
        assert stats.processed_candles == sample_clock.total_candles

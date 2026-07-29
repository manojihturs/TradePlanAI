"""Tests for the 5 market data diagnostic event dataclasses (Milestone I1).

A dedicated file, separate from ``test_events.py`` (Milestone 6.4) and
``test_replay_events.py`` (Milestone B1). No existing test file is
modified to add this.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from trading_engine.diagnostics.events import (
    MarketDataAuthenticationFailed,
    MarketDataConnected,
    MarketDataDisconnected,
    MarketDataReconnected,
    MarketDataSubscribed,
)
from trading_engine.diagnostics.exceptions import DiagnosticsError


class TestMarketDataConnected:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = MarketDataConnected(valid_uuid, valid_datetime, "upstox")
        assert event.provider_name == "upstox"

    def test_blank_provider_name_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="provider_name must not be blank"):
            MarketDataConnected(valid_uuid, valid_datetime, "")


class TestMarketDataDisconnected:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = MarketDataDisconnected(valid_uuid, valid_datetime, "upstox", "requested")
        assert event.reason == "requested"

    def test_blank_reason_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="reason must not be blank"):
            MarketDataDisconnected(valid_uuid, valid_datetime, "upstox", "")


class TestMarketDataSubscribed:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = MarketDataSubscribed(valid_uuid, valid_datetime, "upstox", "NSE_FO|12345")
        assert event.instrument_token == "NSE_FO|12345"

    def test_blank_instrument_token_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="instrument_token must not be blank"):
            MarketDataSubscribed(valid_uuid, valid_datetime, "upstox", "")


class TestMarketDataReconnected:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = MarketDataReconnected(valid_uuid, valid_datetime, "upstox", 1, 3)
        assert event.attempt == 1
        assert event.resubscribed_count == 3

    def test_attempt_below_one_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="attempt must be at least 1"):
            MarketDataReconnected(valid_uuid, valid_datetime, "upstox", 0, 0)

    def test_negative_resubscribed_count_raises(
        self, valid_uuid: uuid.UUID, valid_datetime: datetime
    ) -> None:
        with pytest.raises(DiagnosticsError, match="resubscribed_count must not be negative"):
            MarketDataReconnected(valid_uuid, valid_datetime, "upstox", 1, -1)


class TestMarketDataAuthenticationFailed:
    def test_valid_construction(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        event = MarketDataAuthenticationFailed(
            valid_uuid, valid_datetime, "upstox", "malformed response"
        )
        assert event.reason == "malformed response"

    def test_blank_reason_raises(self, valid_uuid: uuid.UUID, valid_datetime: datetime) -> None:
        with pytest.raises(DiagnosticsError, match="reason must not be blank"):
            MarketDataAuthenticationFailed(valid_uuid, valid_datetime, "upstox", "")

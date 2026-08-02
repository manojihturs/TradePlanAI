"""Tests for telegram_notifier.telegram_notifier."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from capital_ledger.capital_ledger import CapitalLedger
from core.enums import AnchorRole, ExitReason, TradeDirection
from core.exceptions import ValidationError
from models.qualified_position import QualifiedPosition
from telegram_notifier.telegram_notifier import TelegramNotifier

_TS = datetime(2026, 7, 30, 9, 20, 0, tzinfo=UTC)


class _FakeRestClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict, dict]] = []

    def get_json(self, url: str, headers, params=None) -> object:
        self.calls.append((url, dict(headers), dict(params or {})))
        return {"ok": True}

    def get_bytes(self, url: str) -> bytes:
        raise NotImplementedError


def _position(**overrides: object) -> QualifiedPosition:
    fields: dict[str, object] = {
        "position_id": uuid.uuid4(),
        "anchor_role": AnchorRole.TOP,
        "side": TradeDirection.CE,
        "entry_strike": Decimal(24250),
        "entry_level": Decimal("120.1"),
        "target_level": Decimal("145.2"),
        "stop_loss_level": Decimal("98.3"),
        "competitor_exit_level": Decimal("121.5"),
        "opened_at": _TS,
    }
    fields.update(overrides)
    return QualifiedPosition(**fields)  # type: ignore[arg-type]


class TestSend:
    def test_sends_via_get_json_with_bot_token_and_chat_id(self) -> None:
        client = _FakeRestClient()
        notifier = TelegramNotifier(bot_token="fake-token", chat_id="12345", rest_client=client)

        notifier.send("hello")

        assert len(client.calls) == 1
        url, _headers, params = client.calls[0]
        assert url == "https://api.telegram.org/botfake-token/sendMessage"
        assert params == {"chat_id": "12345", "text": "hello"}

    def test_custom_base_url_is_used(self) -> None:
        client = _FakeRestClient()
        notifier = TelegramNotifier(
            bot_token="fake-token",
            chat_id="12345",
            rest_client=client,
            base_url="https://custom.example",
        )

        notifier.send("hello")

        assert client.calls[0][0] == "https://custom.example/botfake-token/sendMessage"


class TestNotifyTradeClosed:
    def test_sends_formatted_message_for_closed_trade(self) -> None:
        client = _FakeRestClient()
        notifier = TelegramNotifier(bot_token="fake-token", chat_id="12345", rest_client=client)
        position = _position().close(
            ExitReason.TARGET_HIT, datetime(2026, 7, 30, 9, 30, tzinfo=UTC), Decimal("145.2")
        )

        notifier.notify_trade_closed(position)

        text = client.calls[0][2]["text"]
        assert "TOP CE @ 24250" in text
        assert "Entry: 120.1 at 09:20" in text
        assert "Exit: 145.2 at 09:30 (TARGET_HIT)" in text
        assert "Captured: 25.1 points" in text

    def test_session_end_trade_shows_dash_for_exit_and_captured(self) -> None:
        client = _FakeRestClient()
        notifier = TelegramNotifier(bot_token="fake-token", chat_id="12345", rest_client=client)
        position = _position().close(
            ExitReason.SESSION_END, datetime(2026, 7, 30, 15, 30, tzinfo=UTC)
        )

        notifier.notify_trade_closed(position)

        text = client.calls[0][2]["text"]
        assert "Exit: - at 15:30 (SESSION_END)" in text
        assert "Captured: - points" in text

    def test_active_position_raises(self) -> None:
        client = _FakeRestClient()
        notifier = TelegramNotifier(bot_token="fake-token", chat_id="12345", rest_client=client)

        with pytest.raises(ValidationError, match="requires a closed QualifiedPosition"):
            notifier.notify_trade_closed(_position())


class TestNotifySessionSummary:
    def test_sends_formatted_summary(self) -> None:
        client = _FakeRestClient()
        notifier = TelegramNotifier(bot_token="fake-token", chat_id="12345", rest_client=client)
        ledger = CapitalLedger(starting_capital=Decimal(50000), lot_size=65)
        ledger.record_close(Decimal("120.1"), Decimal("145.2"))

        notifier.notify_session_summary(date(2026, 7, 30), ledger)

        text = client.calls[0][2]["text"]
        assert "Session summary 2026-07-30" in text
        assert "Trades: 1" in text
        assert f"Realized P&L: ₹{ledger.realized_pnl}" in text
        assert f"Balance: ₹{ledger.balance}" in text
        assert "started ₹50000" in text


class TestNotifyError:
    def test_sends_error_prefixed_message(self) -> None:
        client = _FakeRestClient()
        notifier = TelegramNotifier(bot_token="fake-token", chat_id="12345", rest_client=client)

        notifier.notify_error("polling failed: connection timeout")

        text = client.calls[0][2]["text"]
        assert "ERROR: polling failed: connection timeout" in text

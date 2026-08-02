"""TelegramNotifier: sends trade/session alerts to Telegram, for the
live paper-trading harness.

Traceability
------------
Product Owner-confirmed notification scope (2026-08-02, chat,
multi-select): every trade entry+exit, end-of-day summary, and
errors/faults. Reuses ``data.upstox_rest_client.RestClient``'s
already-defined, already-tested ``get_json`` structural Protocol
unchanged - Telegram's Bot API ``sendMessage`` endpoint accepts plain
GET with query parameters, so no new HTTP transport/Protocol is
needed, matching this project's own precedent of reusing proven
pieces rather than duplicating them.

**Known gap, not silently missing**: real-time "entry" alerts the
moment a trade opens are not yet possible. ``backtest.runner.BacktestRunner``
(and therefore ``live_session.live_session_runner.LiveSessionRunner``)
only ever returns CLOSED positions - there is currently no way to
observe "a trade is open right now, still running" from its public
result shape. ``notify_trade_closed`` therefore reports entry AND
exit together, after the fact, once a trade closes - not two separate
alerts. Extending ``BacktestRunner`` to also expose currently-active
positions would close this gap; not done here.

Requires a real Telegram bot token and chat ID, both something the
Product Owner must create themselves (via @BotFather) - never
something this project can generate. UNTESTED AGAINST THE REAL
TELEGRAM API - unit-tested with a fake ``RestClient``, matching this
project's own established caveat for every third-party integration.
"""

from __future__ import annotations

from datetime import date

from capital_ledger.capital_ledger import CapitalLedger
from core.exceptions import ValidationError
from data.upstox_rest_client import RestClient
from models.qualified_position import QualifiedPosition

_BASE_URL = "https://api.telegram.org"


class TelegramNotifier:
    """Sends formatted trade/session alerts to one Telegram chat.

    Constructor-injected bot token/chat ID/REST client only - no
    globals, no singletons. Never logs or persists the bot token
    itself, matching this project's existing credential-handling
    convention (see ``data.upstox_rest_client.RestClient``'s own
    docstring on ``access_token``).
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        rest_client: RestClient,
        base_url: str = _BASE_URL,
    ) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._rest_client = rest_client
        self._base_url = base_url

    def send(self, text: str) -> None:
        """Send ``text`` as a plain message to the configured chat."""
        url = f"{self._base_url}/bot{self._bot_token}/sendMessage"
        self._rest_client.get_json(url, headers={}, params={"chat_id": self._chat_id, "text": text})

    def notify_trade_closed(self, position: QualifiedPosition) -> None:
        """Send a combined entry+exit alert for one closed trade -
        see module docstring for why this isn't split into two
        separate real-time alerts.

        Raises:
            core.exceptions.ValidationError: if ``position`` is still
                active (nothing to report yet).
        """
        if position.is_active():
            raise ValidationError(
                "TelegramNotifier.notify_trade_closed requires a closed QualifiedPosition."
            )
        self.send(self._format_trade_closed(position))

    def notify_session_summary(self, session_date: date, ledger: CapitalLedger) -> None:
        """Send an end-of-day summary from ``ledger``'s accumulated
        state."""
        self.send(self._format_session_summary(session_date, ledger))

    def notify_error(self, message: str) -> None:
        """Send an error/fault alert."""
        self.send(f"⚠️ ERROR: {message}")

    @staticmethod
    def _format_trade_closed(position: QualifiedPosition) -> str:
        exit_price = position.exit_price if position.exit_price is not None else "-"
        exit_reason = position.exit_reason.value if position.exit_reason else "-"
        captured = (
            position.exit_price - position.entry_level if position.exit_price is not None else "-"
        )
        return (
            f"{position.anchor_role.value} {position.side.value} @ {position.entry_strike}\n"
            f"Entry: {position.entry_level} at {position.opened_at.strftime('%H:%M')}\n"
            f"Exit: {exit_price} at "
            f"{position.closed_at.strftime('%H:%M') if position.closed_at else '-'} "
            f"({exit_reason})\n"
            f"Captured: {captured} points"
        )

    @staticmethod
    def _format_session_summary(session_date: date, ledger: CapitalLedger) -> str:
        return (
            f"Session summary {session_date.isoformat()}\n"
            f"Trades: {ledger.trade_count}\n"
            f"Realized P&L: ₹{ledger.realized_pnl}\n"
            f"Balance: ₹{ledger.balance} (started ₹{ledger.starting_capital})"
        )

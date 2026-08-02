"""Glue script: runs the live paper-trading harness against real
Upstox data during actual market hours.

Traceability
------------
NOT part of src/ - the composition root wiring together
live_session.live_session_runner.LiveSessionRunner,
capital_ledger.capital_ledger.CapitalLedger,
session_scheduler.session_scheduler.SessionScheduler, and
telegram_notifier.telegram_notifier.TelegramNotifier (optional - runs
without it if no bot token/chat ID is configured), matching the same
"glue script" category as run_upstox_backtest.py.

Replaces the prior 2026-07-29 version of this script (built on the
legacy strategy/ package's own LivePaperTradingEngine/CapitalTracker -
entry_signal.py/level_capture.py/premium_mapping.py - a separate,
older rule implementation). Product Owner confirmed 2026-08-02:
replace it entirely with the src/ package's confirmed pipeline, which
carries every fix made this session that the legacy path never had
(Top/Bottom independent trades, real breakeven-first Trailing Stop,
directional dual-crossover, UT Bot trend, exit-price tracking).

UNTESTED AGAINST A REAL LIVE UPSTOX SESSION. Every piece this wires
together is unit-tested with fake transports, but nobody has run this
exact script against a live account during real market hours yet.
Watch the first session closely.

Requires environment variables:
- UPSTOX_ACCESS_TOKEN (required) - see tools/upstox_rest_client.py's
  own docstring; never paste it into this file, a command-line
  argument, or a chat/AI session.
- TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (optional) - if both are set,
  trade-closed/session-summary/error alerts are sent to Telegram; if
  either is missing, the harness runs with console output only.

ANCHOR_STRIKE must be set fresh for the actual session being traded
(the confirmed Top Strike, via the Weekly Future formula) - it is NOT
computed automatically here, the same manual-edit requirement
run_upstox_backtest.py already documents.

Stop with Ctrl+C - sends a final session summary (if Telegram is
configured) before exiting.
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TOOLS = Path(__file__).resolve().parent / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from upstox_rest_client import RequestsRestClient, access_token_from_env

from capital_ledger.capital_ledger import CapitalLedger
from core.enums import TrendDirection
from core.exceptions import HistoricalDataError
from live_session.live_session_runner import LiveSessionRunner
from session_scheduler.session_scheduler import SessionScheduler
from telegram_notifier.telegram_notifier import TelegramNotifier

# Edit these for the session being traded.
UNDERLYING_SYMBOL = "NIFTY"
EXPIRY = date(2026, 8, 4)  # NIFTY weeklies expire on Tuesdays - verified against real Upstox data
ANCHOR_STRIKE = Decimal(24250)  # MUST be set fresh - the confirmed Top Strike for SESSION_DATE
SESSION_DATE = date(2026, 8, 3)
STARTING_CAPITAL = Decimal(50000)
POLL_INTERVAL_SECONDS = 300  # matches the 5-minute candle size used throughout the pipeline


def _build_notifier(rest_client: RequestsRestClient) -> TelegramNotifier | None:
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set - running with console output only.")
        return None
    return TelegramNotifier(bot_token=bot_token, chat_id=chat_id, rest_client=rest_client)


def main() -> None:
    access_token = access_token_from_env()
    rest_client = RequestsRestClient()

    ledger = CapitalLedger(starting_capital=STARTING_CAPITAL)
    scheduler = SessionScheduler()
    notifier = _build_notifier(rest_client)

    runner = LiveSessionRunner(
        rest_client=rest_client,
        access_token=access_token,
        underlying_symbol=UNDERLYING_SYMBOL,
        expiry=EXPIRY,
        anchor_strike=ANCHOR_STRIKE,
        session_date=SESSION_DATE,
        trend=TrendDirection.BULLISH,  # unused - UTBotTrendStage computes the real per-candle trend
        capital_ledger=ledger,
        scheduler=scheduler,
    )

    print(
        f"Live paper trading started: {SESSION_DATE}, anchor={ANCHOR_STRIKE}, "
        f"capital=Rs.{STARTING_CAPITAL}, poll every {POLL_INTERVAL_SECONDS}s."
    )

    summary_sent = False
    try:
        while True:
            now = datetime.now(UTC)

            if not scheduler.is_session_open(now):
                if (
                    not summary_sent
                    and scheduler.is_trading_day(now)
                    and now.time() >= scheduler.market_close
                ):
                    print(
                        f"Session closed. Trades={ledger.trade_count} "
                        f"P&L=Rs.{ledger.realized_pnl} Balance=Rs.{ledger.balance}"
                    )
                    if notifier is not None:
                        notifier.notify_session_summary(SESSION_DATE, ledger)
                    summary_sent = True
                    break
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            try:
                result = runner.poll_once(now)
                for position in result.newly_closed_positions:
                    reason = position.exit_reason.value if position.exit_reason else "-"
                    print(
                        f"CLOSED: {position.anchor_role.value} {position.side.value} "
                        f"@{position.entry_strike} entry={position.entry_level} "
                        f"exit={position.exit_price} reason={reason}"
                    )
                    if notifier is not None:
                        notifier.notify_trade_closed(position)
            except HistoricalDataError as exc:
                print(f"POLL ERROR: {exc}")
                if notifier is not None:
                    notifier.notify_error(str(exc))
            except Exception:  # noqa: BLE001 - a live trading loop must not die on one bad poll
                print("UNEXPECTED POLL ERROR:")
                traceback.print_exc()
                if notifier is not None:
                    notifier.notify_error("Unexpected error - see console/logs.")

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print(
            f"\nStopped by user. Trades={ledger.trade_count} "
            f"P&L=Rs.{ledger.realized_pnl} Balance=Rs.{ledger.balance}"
        )
        if notifier is not None:
            notifier.notify_session_summary(SESSION_DATE, ledger)


if __name__ == "__main__":
    main()

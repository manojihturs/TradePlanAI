"""Shared Telegram notification service.

Single responsibility: send a plain-text message to the configured
Telegram chat. Extracted from the Telegram-sending code that used to
live only inside ``orb_common.alert()`` so both the legacy system
(``orb_common.py``/``orb_auto.py``) and the strategy/ package's glue
scripts (``run_live_paper_trading.py``, ``run_post_market_workflow.py``)
send alerts through the same implementation instead of two copies.

Reuses the exact same environment variables the legacy system already
used (``ORB_TG_TOKEN`` / ``ORB_TG_CHAT``) - no new configuration is
introduced.
"""

from __future__ import annotations

import logging
import os

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

logger = logging.getLogger("notifications")

TELEGRAM_BOT_TOKEN = os.environ.get("ORB_TG_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("ORB_TG_CHAT", "")


def telegram_configured() -> bool:
    """Whether both required Telegram environment variables are set."""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def require_telegram_config() -> None:
    """Fail fast if Telegram is not configured.

    Raises:
        RuntimeError: if ``ORB_TG_TOKEN`` or ``ORB_TG_CHAT`` is unset.
    """
    if not telegram_configured():
        raise RuntimeError(
            "ORB_TG_TOKEN and ORB_TG_CHAT must both be set - Telegram "
            "notification is required for this workflow"
        )


def send_telegram_message(text: str) -> bool:
    """Send a plain-text message to the configured Telegram chat.

    Never raises - a notification failure should not interrupt the
    caller's own workflow (matches the legacy ``alert()``'s
    catch-and-log-only behavior).

    Args:
        text: The already-formatted message to send.

    Returns:
        True if the message was sent, False if Telegram is not
        configured or the send failed.
    """
    if not telegram_configured():
        logger.warning(
            "Telegram not configured (ORB_TG_TOKEN/ORB_TG_CHAT unset) - message not sent"
        )
        return False
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        return True
    except Exception as exc:  # noqa: BLE001 - notification failures must never propagate
        logger.error("Telegram send failed: %s", exc)
        return False

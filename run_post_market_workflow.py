"""Glue script: runs the post-market daily validation workflow.

Processes the latest completed trading session produced by Module 11
(``strategy/live_paper_trading.py`` via ``run_live_paper_trading.py``),
runs the Daily Validation Checklist, writes a full report, sends a
Telegram summary, and archives everything.

Does NOT touch the live trading loop, does NOT change any strategy
business rule, and does NOT modify any strategy/ package file - it
only reads the Excel export and log file that Module 11 already
produces. Intended to be run once after each market close (manually or
via a scheduler).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from notifications import send_telegram_message
from postmarket.archive import already_archived, archive_session
from postmarket.data_health import build_data_health_report
from postmarket.data_sources import find_latest_session_report, load_session_report
from postmarket.health_score import compute_health_score
from postmarket.report import build_report
from postmarket.signal_review import build_signal_review
from postmarket.strategy_validation import build_strategy_validation
from postmarket.trade_review import build_trade_review

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("post_market_workflow.log")],
)
logger = logging.getLogger("post_market_workflow")

REPO_ROOT = Path(__file__).resolve().parent
ARCHIVE_ROOT = REPO_ROOT / "postmarket_archive"


def main() -> None:
    xlsx_path = find_latest_session_report(REPO_ROOT)

    log_path = REPO_ROOT / "live_paper_trading.log"
    if not log_path.exists():
        log_path = None

    session = load_session_report(xlsx_path, log_path)
    session_date = session.session_date

    if already_archived(session_date, ARCHIVE_ROOT):
        logger.info("Session %s already processed - skipping (idempotent)", session_date)
        return

    logger.info("Processing session %s from %s", session_date, xlsx_path)

    trade_rows = build_trade_review(session)
    signal_summary = build_signal_review(session)
    data_health = build_data_health_report(session)
    strategy_findings = build_strategy_validation(session)
    health = compute_health_score(data_health, strategy_findings)

    report = build_report(session, trade_rows, signal_summary, data_health, strategy_findings, health)

    logger.info("Overall Status: %s", health.overall_status)
    print(report.full_text)

    sent = send_telegram_message(report.telegram_text)
    if not sent:
        logger.warning("Telegram summary was not sent (see notifications log above)")

    archive_dir = archive_session(session_date, ARCHIVE_ROOT, xlsx_path, log_path, report.full_text)
    logger.info("Post-market workflow complete for %s. Archived at %s", session_date, archive_dir)


if __name__ == "__main__":
    main()

"""Post-market workflow: Archiving.

Single responsibility: preserve the session's source files (Excel
export, run log, generated text report) under a dated archive
directory, untouched, so they remain available for later reference or
for the future real-time monitoring module without re-deriving
anything. Never deletes or modifies the originals.
"""

from __future__ import annotations

import logging
import shutil
from datetime import date
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("postmarket.archive")


def archive_session(
    session_date: date,
    archive_root: Path,
    xlsx_path: Path,
    log_path: Optional[Path],
    report_text: str,
) -> Path:
    """Copy the session's source files and write the report into a
    dated archive directory.

    Args:
        session_date: The session's trading date.
        archive_root: Root directory under which a ``<date>/``
            subdirectory is created.
        xlsx_path: The Module 11 Excel export to preserve.
        log_path: The matching run log to preserve, if it exists.
        report_text: The full post-market report text to write.

    Returns:
        The dated archive directory path.
    """
    day_dir = archive_root / session_date.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(xlsx_path, day_dir / xlsx_path.name)
    if log_path is not None and log_path.exists():
        shutil.copy2(log_path, day_dir / log_path.name)

    report_path = day_dir / f"post_market_report_{session_date.isoformat()}.txt"
    report_path.write_text(report_text, encoding="utf-8")

    logger.info("Archived session %s to %s", session_date, day_dir)
    return day_dir


def already_archived(session_date: date, archive_root: Path) -> bool:
    """Whether this session's report has already been archived.

    Used by the orchestrator to avoid re-processing (and re-notifying
    on Telegram for) the same session twice.
    """
    report_path = (
        archive_root / session_date.isoformat()
        / f"post_market_report_{session_date.isoformat()}.txt"
    )
    return report_path.exists()

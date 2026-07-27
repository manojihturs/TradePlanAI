"""Post-market workflow: API & Data Health Review.

Single responsibility: scan the session's run log for poll-iteration
failures (``run_live_paper_trading.py``'s broad except-and-continue
handler, the only "reconnect" signal that log currently carries) and
report each occurrence's timestamp, the gap to the next successful
poll, and whether any candle timestamps appear to be missing around
it. Performs no network I/O - reads only the already-loaded log lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from postmarket.data_sources import SessionData

_POLL_FAIL_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \[ERROR\] "
    r"Poll iteration failed \(continuing\): (?P<msg>.*)$"
)
_DASHBOARD_TS_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \[INFO\] DASHBOARD time=(?P<time>[\d:]+)"
)


@dataclass(frozen=True)
class ReconnectEvent:
    timestamp: Optional[datetime]
    message: str
    seconds_to_next_success: Optional[float]
    likely_missed_candles: bool


@dataclass(frozen=True)
class DataHealthReport:
    reconnect_events: List[ReconnectEvent]
    recovered_all: bool


def build_data_health_report(session: SessionData, poll_seconds: int = 20) -> DataHealthReport:
    """Scan the session log for API reconnect / poll-failure events.

    Args:
        session: The loaded session data (its ``log_lines`` are scanned).
        poll_seconds: The live loop's normal poll interval - used to
            judge whether a gap after a failure is longer than one
            missed poll (i.e. likely to have skipped a 5-minute candle
            boundary), matching ``run_live_paper_trading.py``'s
            ``POLL_SECONDS`` constant.

    Returns:
        A ``DataHealthReport`` listing every reconnect/failure event
        found, each annotated with the time to the next successful
        dashboard log line (a proxy for "recovered").
    """
    failures = []
    for line in session.log_lines:
        m = _POLL_FAIL_RE.match(line)
        if m:
            failures.append(m)

    dashboard_hits = []
    for line in session.log_lines:
        m = _DASHBOARD_TS_RE.match(line)
        if m:
            dashboard_hits.append(datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S"))

    events: List[ReconnectEvent] = []
    for m in failures:
        ts = datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S")
        next_success = next((d for d in dashboard_hits if d > ts), None)
        gap = (next_success - ts).total_seconds() if next_success else None
        events.append(ReconnectEvent(
            timestamp=ts, message=m.group("msg"),
            seconds_to_next_success=gap,
            likely_missed_candles=(gap is not None and gap > poll_seconds * 3),
        ))

    return DataHealthReport(
        reconnect_events=events,
        recovered_all=all(e.seconds_to_next_success is not None for e in events),
    )

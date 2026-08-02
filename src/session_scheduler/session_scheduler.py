"""SessionScheduler: whether NSE's equity/derivatives session is
currently open, for the live paper-trading harness.

Traceability
------------
Market hours (09:15-15:30 IST, Monday-Friday) are a standard,
publicly documented NSE exchange fact - not a trading business rule
requiring Product Owner evidence, the same distinction this project
already draws elsewhere for API-integration/exchange mechanics (see
``data.upstox_instrument_resolver.UpstoxInstrumentResolver``'s own
docstring). 09:15 already matches this project's own existing
``_DEFAULT_MARKET_OPEN`` convention in
``backtest.upstox_dataset_builder``/``backtest.upstox_index_fetcher``.

Explicitly NOT handled here: NSE's annual trading-holiday calendar.
That list changes every year and requires a real, current data source
this project does not have - inventing or hardcoding a holiday list
would be guessing at data, not a business rule. A caller running this
on an actual exchange holiday will see ``is_session_open`` return
``True`` for a day that isn't really trading - a known, documented gap,
not silently wrong. Wire in a real NSE holiday feed before relying on
this for real skip-the-holiday behaviour.
"""

from __future__ import annotations

from datetime import datetime, time

from core.exceptions import ValidationError

DEFAULT_MARKET_OPEN = time(9, 15)
DEFAULT_MARKET_CLOSE = time(15, 30)

_WEEKEND_WEEKDAYS = frozenset({5, 6})  # datetime.weekday(): Saturday=5, Sunday=6


class SessionScheduler:
    """Answers whether the market session is open at a given moment.

    Constructor-injected open/close times only - no globals, no
    singletons. Stateless - every call is a pure function of the
    ``now`` passed in, no wall-clock reads of its own (the caller
    supplies "now", matching this project's existing
    ``core.protocols.Clock`` convention of never reading wall-clock
    time directly inside business logic).
    """

    def __init__(
        self,
        market_open: time = DEFAULT_MARKET_OPEN,
        market_close: time = DEFAULT_MARKET_CLOSE,
    ) -> None:
        if market_close <= market_open:
            raise ValidationError("SessionScheduler.market_close must be after market_open.")
        self._market_open = market_open
        self._market_close = market_close

    @property
    def market_open(self) -> time:
        return self._market_open

    @property
    def market_close(self) -> time:
        return self._market_close

    def is_trading_day(self, now: datetime) -> bool:
        """Whether ``now``'s calendar date is a weekday (Monday-Friday).

        Does NOT check the NSE holiday calendar - see module
        docstring."""
        return now.weekday() not in _WEEKEND_WEEKDAYS

    def is_within_session_hours(self, now: datetime) -> bool:
        """Whether ``now``'s time-of-day falls within
        [market_open, market_close) - date-independent."""
        return self._market_open <= now.time() < self._market_close

    def is_session_open(self, now: datetime) -> bool:
        """Whether the market is open for trading at ``now`` - both a
        trading day AND within session hours. See module docstring
        for the holiday-calendar gap."""
        return self.is_trading_day(now) and self.is_within_session_hours(now)

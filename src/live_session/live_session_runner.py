"""LiveSessionRunner: polls Upstox for the trading day's data-so-far
and drives the confirmed pipeline, for the live paper-trading
harness.

Traceability
------------
Live-polling insight: Upstox's historical-candle endpoint (already
wired via ``backtest.upstox_dataset_builder``/
``backtest.upstox_index_fetcher``) serves TODAY's own candles when
queried with today's date as both ``day_from`` and ``day_to`` - up to
"now", not just prior days. This means "live" doesn't need a separate
streaming/websocket integration: each poll re-fetches the full trading
day's data-so-far and replays it deterministically through
``backtest.runner.BacktestRunner`` (the same, already-confirmed
pipeline used for backtesting) - no new business logic, no duplicated
rules.

Deduplication: replaying the full day-so-far on every poll means
already-closed positions reappear on every subsequent poll. Since
``backtest.runner.BacktestRunner``'s default ``id_factory`` mints a
fresh ``uuid.UUID`` every run, ``position_id`` cannot be used to
detect "already recorded" - two polls produce different
``position_id``s for the same real, logical trade. Instead, a
closed position's identity for dedup purposes is
``(anchor_role, side, entry_strike, entry_level, opened_at,
exit_reason, closed_at, exit_price)`` - every field that describes
the real-world event, excluding the synthetic ``position_id``.

UNTESTED AGAINST A REAL LIVE UPSTOX SESSION - same caveat as
``run_upstox_backtest.py``/``backtest.upstox_dataset_builder``. Every
piece here is unit-tested with a fake ``RestClient``, but nobody has
run this against a live account during real market hours yet.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal

from backtest.runner import BacktestRunner
from backtest.upstox_dataset_builder import build_upstox_fixture
from backtest.upstox_index_fetcher import fetch_underlying_index_candles
from capital_ledger.capital_ledger import CapitalLedger
from core.enums import AnchorRole, ExitReason, TradeDirection, TrendDirection
from core.exceptions import HistoricalDataError
from data.option_chain_dataset import OptionChainDataset
from data.upstox_rest_client import RestClient
from models.qualified_position import QualifiedPosition
from session_scheduler.session_scheduler import SessionScheduler

_PositionIdentity = tuple[
    AnchorRole,
    TradeDirection,
    Decimal,
    Decimal,
    datetime,
    ExitReason,
    datetime | None,
    Decimal | None,
]


def _position_identity(position: QualifiedPosition) -> _PositionIdentity:
    assert position.exit_reason is not None
    return (
        position.anchor_role,
        position.side,
        position.entry_strike,
        position.entry_level,
        position.opened_at,
        position.exit_reason,
        position.closed_at,
        position.exit_price,
    )


@dataclass(frozen=True, slots=True)
class LivePollResult:
    """One poll's outcome.

    Attributes:
        session_open: Whether the market was open at the polled
            moment - if ``False``, no data was fetched and
            ``newly_closed_positions`` is always empty.
        newly_closed_positions: Positions closed since the previous
            poll (deduplicated - see module docstring), in the order
            ``BacktestRunner`` produced them. Empty if none, or if the
            session was closed.
    """

    session_open: bool
    newly_closed_positions: tuple[QualifiedPosition, ...]


class LiveSessionRunner:
    """Polls Upstox for one session's data-so-far and drives the
    confirmed pipeline, recording newly-closed positions into an
    injected :class:`~capital_ledger.capital_ledger.CapitalLedger`.

    Constructor-injected collaborators only - no globals, no
    singletons. Stateful across calls (tracks which closed positions
    have already been recorded) - construct a fresh instance per
    trading session.
    """

    def __init__(
        self,
        rest_client: RestClient,
        access_token: str,
        underlying_symbol: str,
        expiry: date,
        anchor_strike: Decimal,
        session_date: date,
        trend: TrendDirection,
        capital_ledger: CapitalLedger,
        scheduler: SessionScheduler | None = None,
        backtest_runner: BacktestRunner | None = None,
    ) -> None:
        """``trend`` is required by ``BacktestRunner.run``'s own
        signature but is never actually consulted here - every poll
        always supplies ``underlying_index_candles``, which makes
        ``BacktestRunner`` compute a real per-candle trend via
        UTBotTrendStage instead (Product Owner's confirmed choice,
        2026-08-02). Pass any value; ``TrendDirection.BULLISH`` is a
        reasonable placeholder.

        ``backtest_runner`` is injectable (defaults to a fresh
        ``BacktestRunner()``) primarily so tests can substitute a
        stub returning canned results, isolating the dedup logic from
        needing to engineer real qualifying market data - matches
        this project's own constructor-injection convention."""
        self._rest_client = rest_client
        self._access_token = access_token
        self._underlying_symbol = underlying_symbol
        self._expiry = expiry
        self._anchor_strike = anchor_strike
        self._session_date = session_date
        self._trend = trend
        self._capital_ledger = capital_ledger
        self._scheduler = scheduler if scheduler is not None else SessionScheduler()
        self._backtest_runner = backtest_runner if backtest_runner is not None else BacktestRunner()
        self._recorded_identities: set[_PositionIdentity] = set()

    def poll_once(self, now: datetime) -> LivePollResult:
        """Fetch the trading day's data-so-far (if the session is
        open at ``now``) and replay it through ``BacktestRunner``,
        recording any newly-closed positions into the capital ledger.

        Raises:
            core.exceptions.HistoricalDataError: if the Upstox fetch
                fails (network, malformed response, etc.), or if
                option and index data share no common candle
                timestamp - propagated unchanged, the caller decides
                how to handle a failed poll (e.g. retry next interval).
        """
        if not self._scheduler.is_session_open(now):
            return LivePollResult(session_open=False, newly_closed_positions=())

        fixture = build_upstox_fixture(
            rest_client=self._rest_client,
            access_token=self._access_token,
            underlying_symbol=self._underlying_symbol,
            expiry=self._expiry,
            anchor_strike=self._anchor_strike,
            session_date=self._session_date,
        )
        index_candles = fetch_underlying_index_candles(
            self._rest_client, self._access_token, self._session_date
        )

        index_by_ts = {candle.timestamp: candle for candle in index_candles}
        common_candles = tuple(
            candle for candle in fixture.dataset.candles if candle.timestamp in index_by_ts
        )
        if not common_candles:
            raise HistoricalDataError(
                f"No candle timestamp is common between option and index data for "
                f"{self._session_date} - cannot poll."
            )
        aligned_index = tuple(index_by_ts[candle.timestamp] for candle in common_candles)
        fixture = replace(
            fixture,
            dataset=OptionChainDataset(
                session_date=fixture.dataset.session_date, candles=common_candles
            ),
        )

        result = self._backtest_runner.run(
            fixture, self._trend, underlying_index_candles=aligned_index
        )

        newly_closed: list[QualifiedPosition] = []
        for position in result.qualification_positions:
            if position.exit_reason is None:
                continue
            identity = _position_identity(position)
            if identity in self._recorded_identities:
                continue
            self._recorded_identities.add(identity)
            self._capital_ledger.record_position(position)
            newly_closed.append(position)

        return LivePollResult(session_open=True, newly_closed_positions=tuple(newly_closed))

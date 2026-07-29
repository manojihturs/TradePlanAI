"""PremiumSnapshotEngine: captures the first completed 5-minute
premium reference window.

Traceability notes
-------------------
Milestone I2 ("PREMIUM SNAPSHOT ENGINE") is explicit: this engine
captures and stores data only. No Weekly Future, Strike selection,
Trend, Winner, Entry, Exit, or Risk logic appears anywhere here, and
it never computes Top/Bottom Strike itself - both are supplied by the
caller.

A single live tick (:class:`~trading_engine.market_data.market_tick.MarketTick`)
carries only a last-traded-price point observation, not an
already-aggregated OHLC bar (see ``market_tick.py``'s own module
docstring distinguishing it from
:class:`trading_engine.replay.history_loader.Candle`). Capturing "the
first 5-minute candle" for a contract that has no such candle anywhere
upstream therefore requires aggregating the ticks observed during the
window - a purely mechanical operation (min/max/first/last over
observed prices), not a trading calculation. :class:`_ContractTickAggregator`
does exactly that and nothing else.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

from trading_engine.diagnostics.sink import DiagnosticsSink, NullDiagnosticsSink
from trading_engine.market_data.instrument_resolver import InstrumentKey, OptionType
from trading_engine.market_data.market_tick import MarketTick
from trading_engine.premium_snapshot.exceptions import SnapshotCaptureError
from trading_engine.premium_snapshot.premium_snapshot_events import (
    SnapshotCompleted,
    SnapshotStarted,
)
from trading_engine.premium_snapshot.premium_snapshot_models import (
    ContractSnapshot,
    PremiumSnapshot,
)

#: The default capture window length - the first completed 5-minute
#: candle after the trading window begins (Milestone I2). Kept as a
#: default argument, not a hardcoded constant used internally, so
#: every call site remains configurable per Milestone I2's own
#: instruction ("must be configurable, not hardcoded").
DEFAULT_CAPTURE_WINDOW = timedelta(minutes=5)


@dataclass
class _ContractTickAggregator:
    """Aggregates :class:`MarketTick` observations for one contract
    into a :class:`ContractSnapshot`, over a fixed time window.

    Mutable by design (ticks arrive incrementally) - not part of the
    public API, used internally by :class:`PremiumSnapshotEngine`.
    """

    instrument: InstrumentKey
    strike: Decimal
    option_type: OptionType
    window_start: datetime
    window_end: datetime
    _open: Decimal | None = field(default=None, init=False)
    _high: Decimal | None = field(default=None, init=False)
    _low: Decimal | None = field(default=None, init=False)
    _close: Decimal | None = field(default=None, init=False)
    _volume: int = field(default=0, init=False)
    _open_interest: int = field(default=0, init=False)
    _last_timestamp: datetime | None = field(default=None, init=False)
    _seen_timestamps: set[datetime] = field(default_factory=set, init=False)

    def ingest(self, tick: MarketTick) -> bool:
        """Ingest one tick, assumed by the caller to already belong to
        this contract (:class:`PremiumSnapshotEngine.ingest_tick`
        routes by instrument before calling this). Returns ``True`` if
        the tick contributed (in-window, not a duplicate), ``False``
        otherwise - a duplicate tick (same timestamp observed again)
        is silently ignored, not re-applied.
        """
        if not (self.window_start <= tick.timestamp <= self.window_end):
            return False
        if tick.timestamp in self._seen_timestamps:
            return False

        self._seen_timestamps.add(tick.timestamp)
        price = tick.last_traded_price
        if self._open is None:
            self._open = price
        self._high = price if self._high is None else max(self._high, price)
        self._low = price if self._low is None else min(self._low, price)
        self._close = price
        self._volume = tick.volume
        self._open_interest = tick.open_interest
        self._last_timestamp = tick.timestamp
        return True

    def snapshot(self) -> ContractSnapshot | None:
        """Build the final :class:`ContractSnapshot`, or ``None`` if
        no tick was ever ingested (the contract is unavailable)."""
        if self._open is None or self._high is None or self._low is None or self._close is None:
            return None
        assert self._last_timestamp is not None
        return ContractSnapshot(
            instrument=self.instrument,
            strike=self.strike,
            option_type=self.option_type,
            timestamp=self._last_timestamp,
            open=self._open,
            high=self._high,
            low=self._low,
            close=self._close,
            last_traded_price=self._close,
            volume=self._volume,
            open_interest=self._open_interest,
        )


@dataclass(frozen=True)
class _CaptureRequest:
    session_id: uuid.UUID
    top_strike: Decimal
    bottom_strike: Decimal


class PremiumSnapshotEngine:
    """Captures the first completed capture-window premium reference
    for the Top/Bottom CE/PE contracts, plus a best-effort ITM/ATM/OTM
    range.

    Caller-driven, synchronous: :meth:`start_capture` opens a capture
    window for a fixed set of contracts, :meth:`ingest_tick` routes
    incoming ticks to the matching contract's aggregator (called
    repeatedly by whatever supplies live ticks - a
    :class:`~trading_engine.market_data.market_data_provider.MarketDataProvider`,
    a replay driver, or a test), and :meth:`complete_capture` builds
    the final :class:`~trading_engine.premium_snapshot.premium_snapshot_models.PremiumSnapshot`
    once the window has elapsed. No thread, timer, or blocking wait
    exists here - matches this codebase's synchronous, no-concurrency
    design (see ``market_data``'s own implementation report).
    """

    def __init__(
        self,
        capture_window: timedelta = DEFAULT_CAPTURE_WINDOW,
        diagnostics_sink: DiagnosticsSink | None = None,
        clock: Callable[[], datetime] = datetime.now,
        id_factory: Callable[[], uuid.UUID] = uuid.uuid4,
    ) -> None:
        if capture_window <= timedelta(0):
            raise SnapshotCaptureError("capture_window must be a positive duration.")
        self._capture_window = capture_window
        self._sink: DiagnosticsSink = (
            diagnostics_sink if diagnostics_sink is not None else NullDiagnosticsSink()
        )
        self._clock = clock
        self._id_factory = id_factory
        self._request: _CaptureRequest | None = None
        self._window_start: datetime | None = None
        self._window_end: datetime | None = None
        self._aggregators: dict[InstrumentKey, _ContractTickAggregator] = {}
        self._core_keys: dict[str, InstrumentKey] = {}

    def start_capture(
        self,
        session_id: uuid.UUID,
        window_start: datetime,
        top_strike: Decimal,
        bottom_strike: Decimal,
        top_ce: InstrumentKey,
        top_pe: InstrumentKey,
        bottom_ce: InstrumentKey,
        bottom_pe: InstrumentKey,
        range_instruments: tuple[tuple[InstrumentKey, Decimal, OptionType], ...] = (),
    ) -> None:
        """Open a capture window for the four core contracts, plus an
        optional best-effort ITM/ATM/OTM range.

        ``range_instruments`` is a tuple of ``(instrument, strike,
        option_type)`` triples - kept explicit rather than inferred,
        since no repository evidence defines how ITM/ATM/OTM strikes
        are derived (see ``PremiumSnapshot.range_contracts`` docstring).

        Raises:
            SnapshotCaptureError: if a capture is already in progress.
        """
        if self._request is not None:
            raise SnapshotCaptureError(
                "A capture is already in progress; call complete_capture() first."
            )

        window_end = window_start + self._capture_window
        self._request = _CaptureRequest(
            session_id=session_id, top_strike=top_strike, bottom_strike=bottom_strike
        )
        self._window_start = window_start
        self._window_end = window_end
        self._aggregators = {}
        self._core_keys = {
            "top_ce": top_ce,
            "top_pe": top_pe,
            "bottom_ce": bottom_ce,
            "bottom_pe": bottom_pe,
        }

        self._aggregators[top_ce] = _ContractTickAggregator(
            top_ce, top_strike, OptionType.CALL, window_start, window_end
        )
        self._aggregators[top_pe] = _ContractTickAggregator(
            top_pe, top_strike, OptionType.PUT, window_start, window_end
        )
        self._aggregators[bottom_ce] = _ContractTickAggregator(
            bottom_ce, bottom_strike, OptionType.CALL, window_start, window_end
        )
        self._aggregators[bottom_pe] = _ContractTickAggregator(
            bottom_pe, bottom_strike, OptionType.PUT, window_start, window_end
        )
        for instrument, strike, option_type in range_instruments:
            self._aggregators[instrument] = _ContractTickAggregator(
                instrument, strike, option_type, window_start, window_end
            )

        self._sink.emit(
            SnapshotStarted(
                event_id=self._id_factory(),
                occurred_at=self._clock(),
                session_id=session_id,
                window_start=window_start,
                window_end=window_end,
            )
        )

    def ingest_tick(self, tick: MarketTick) -> bool:
        """Route one tick to its matching contract's aggregator, if a
        capture is in progress and the tick's instrument is one of the
        contracts being captured.

        Returns ``True`` if the tick contributed, ``False`` otherwise
        (no capture in progress, unrecognised instrument, out of
        window, or a duplicate).
        """
        if self._request is None:
            return False
        aggregator = self._aggregators.get(tick.instrument)
        if aggregator is None:
            return False
        return aggregator.ingest(tick)

    def complete_capture(self) -> PremiumSnapshot:
        """Close the current capture window and build the final
        :class:`~trading_engine.premium_snapshot.premium_snapshot_models.PremiumSnapshot`.

        Missing contracts (no tick ever observed) are stored as
        ``None``/omitted, never treated as a failure - per Milestone
        I2's explicit "do not fail" instruction.

        Raises:
            SnapshotCaptureError: if no capture is in progress.
        """
        if self._request is None or self._window_start is None or self._window_end is None:
            raise SnapshotCaptureError("No capture is in progress; call start_capture() first.")

        request = self._request
        core = {name: self._aggregators[key].snapshot() for name, key in self._core_keys.items()}
        range_snapshots = tuple(
            contract_snapshot
            for key, aggregator in self._aggregators.items()
            if key not in self._core_keys.values()
            and (contract_snapshot := aggregator.snapshot()) is not None
        )

        snapshot = PremiumSnapshot(
            snapshot_id=self._id_factory(),
            session_id=request.session_id,
            capture_window_start=self._window_start,
            capture_window_end=self._window_end,
            top_strike=request.top_strike,
            bottom_strike=request.bottom_strike,
            top_ce=core["top_ce"],
            top_pe=core["top_pe"],
            bottom_ce=core["bottom_ce"],
            bottom_pe=core["bottom_pe"],
            range_contracts=range_snapshots,
        )

        captured_count = len(snapshot.core_contracts()) + len(range_snapshots)
        missing_count = snapshot.missing_core_contract_count()
        self._sink.emit(
            SnapshotCompleted(
                event_id=self._id_factory(),
                occurred_at=self._clock(),
                session_id=request.session_id,
                captured_contract_count=captured_count,
                missing_contract_count=missing_count,
            )
        )

        self._request = None
        self._window_start = None
        self._window_end = None
        self._aggregators = {}
        self._core_keys = {}
        return snapshot

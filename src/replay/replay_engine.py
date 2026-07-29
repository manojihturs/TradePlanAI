"""ReplayEngine: accepts historical candles and publishes events.

Traceability
------------
This sprint's own instruction: "Accept historical candles. Publish
events. No strategy logic." No Weekly Future/Strike/TP/Winner/Exit
computation exists here or is triggered here - this engine only marks
session boundaries (``MarketOpenEvent``/``MarketCloseEvent``) and
hands each historical candle to its caller. Matches
``research/architecture/MODULE_ARCHITECTURE.md`` Section 3.15's
forbidden-dependency rule: replay must not contain its own copy of
strategy logic.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Iterator
from datetime import datetime

from core.events import MarketCloseEvent, MarketOpenEvent
from core.exceptions import ReplayError
from core.protocols import Clock, EventBusProtocol, IdFactory
from models.market_snapshot import MarketSnapshot


class ReplayEngine:
    """Drives a historical sequence of :class:`MarketSnapshot`
    candles through the event pipeline.

    Publishes :class:`~core.events.MarketOpenEvent` before the first
    candle and :class:`~core.events.MarketCloseEvent` after the last
    one, then yields each candle in order for the caller to route to
    whatever strategy modules are wired up. Contains no strategy
    logic of its own.
    """

    def __init__(
        self,
        bus: EventBusProtocol | None = None,
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._bus = bus
        self._clock: Clock = clock if clock is not None else datetime.now
        self._id_factory: IdFactory = id_factory if id_factory is not None else uuid.uuid4

    def run(
        self, session_id: uuid.UUID, candles: Iterable[MarketSnapshot]
    ) -> Iterator[MarketSnapshot]:
        """Replay ``candles`` for ``session_id``, in order.

        Raises:
            ReplayError: if ``candles`` is empty - a replay session
                with no data is not meaningful.
        """
        candle_list = list(candles)
        if not candle_list:
            raise ReplayError("ReplayEngine.run() received no candles to replay.")

        self._publish(MarketOpenEvent(self._id_factory(), self._clock(), session_id))
        yield from candle_list
        self._publish(MarketCloseEvent(self._id_factory(), self._clock(), session_id))

    def _publish(self, event: MarketOpenEvent | MarketCloseEvent) -> None:
        if self._bus is not None:
            self._bus.publish(event)

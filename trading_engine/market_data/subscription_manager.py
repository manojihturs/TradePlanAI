"""SubscriptionManager: tracks which instruments are actively subscribed.

Traceability notes
-------------------
Pure bookkeeping - never sends a network message itself (that is
:class:`~trading_engine.market_data.upstox_provider.UpstoxProvider`'s
job, via its injected ``WebSocketTransport``). Kept separate so
subscription *tracking* (idempotent add/remove, "what should we
resubscribe to after a reconnect") is independently testable from
transport/wire concerns.
"""

from __future__ import annotations

from trading_engine.market_data.instrument_resolver import InstrumentKey


class SubscriptionManager:
    """Tracks the set of currently-active instrument subscriptions.

    Responsibilities: subscribe, unsubscribe, and report every active
    subscription (so a caller can resubscribe them all after a
    reconnect). Idempotent: subscribing an already-active instrument,
    or unsubscribing an inactive one, is a no-op that reports "no
    change" via its boolean return value rather than raising.
    """

    def __init__(self) -> None:
        self._active: set[InstrumentKey] = set()

    def subscribe(self, instrument: InstrumentKey) -> bool:
        """Mark ``instrument`` as actively subscribed.

        Returns:
            ``True`` if this newly added the subscription, ``False``
            if it was already active.
        """
        if instrument in self._active:
            return False
        self._active.add(instrument)
        return True

    def unsubscribe(self, instrument: InstrumentKey) -> bool:
        """Mark ``instrument`` as no longer subscribed.

        Returns:
            ``True`` if this removed an active subscription, ``False``
            if it was not active.
        """
        if instrument not in self._active:
            return False
        self._active.discard(instrument)
        return True

    def is_subscribed(self, instrument: InstrumentKey) -> bool:
        """Whether ``instrument`` is currently marked as subscribed."""
        return instrument in self._active

    def active_subscriptions(self) -> tuple[InstrumentKey, ...]:
        """Every currently-active subscription.

        Order is not meaningful (backed by a set) - callers that need
        a deterministic resubscribe order should sort the result
        themselves.
        """
        return tuple(self._active)

    def __len__(self) -> int:
        return len(self._active)

    def clear(self) -> None:
        """Remove every tracked subscription without sending any
        network message - used when a caller wants to rebuild
        subscription state from scratch."""
        self._active.clear()

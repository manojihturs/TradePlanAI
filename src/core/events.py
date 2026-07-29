"""Domain event definitions.

Traceability
------------
Event names and payload fields are drawn from this sprint's own
instructions and, where applicable,
``research/architecture/EVENT_CATALOG.md``. Payloads use only
primitive types (``Decimal``, ``datetime``, ``UUID``, ``str``) and
``core.enums`` members - never a ``models`` import - so that
``core`` remains the most foundational package (nothing in ``core``
depends on ``models``; ``models``/``events``/``trade_manager``/``replay``
depend on ``core``, never the reverse). This mirrors the existing
``trading_engine.diagnostics`` foundational-package precedent already
established in this repository.

No business rule is encoded in any event below - every field is
either structural (IDs, timestamps) or a direct restatement of an
already-confirmed Specification value (e.g. a strike price, a side).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

from core.enums import EventPriority, ExitReason, TradeDirection
from core.exceptions import ValidationError


def _validate_common(event_id: uuid.UUID, occurred_at: datetime, class_name: str) -> None:
    if event_id is None:
        raise ValidationError(f"{class_name}.event_id must not be None.")
    if occurred_at is None:
        raise ValidationError(f"{class_name}.occurred_at must not be None.")


@runtime_checkable
class Event(Protocol):
    """The structural contract every domain event satisfies.

    A ``typing.Protocol`` rather than a base class, matching this
    project's stated preference for ``Protocol`` over inheritance.
    Declared via read-only ``@property`` (rather than plain
    attributes) so that frozen dataclasses - whose fields are
    immutable - structurally satisfy this protocol; a plain mutable
    attribute declaration would otherwise require the implementing
    type's attribute to be settable too.
    """

    @property
    def event_id(self) -> uuid.UUID: ...  # pragma: no cover

    @property
    def occurred_at(self) -> datetime: ...  # pragma: no cover

    @property
    def priority(self) -> EventPriority: ...  # pragma: no cover


@dataclass(frozen=True, slots=True)
class MarketOpenEvent:
    """The trading session's market data feed has started."""

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "MarketOpenEvent")
        if self.session_id is None:
            raise ValidationError("MarketOpenEvent.session_id must not be None.")


@dataclass(frozen=True, slots=True)
class MarketCloseEvent:
    """The trading session's market data feed has ended."""

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "MarketCloseEvent")
        if self.session_id is None:
            raise ValidationError("MarketCloseEvent.session_id must not be None.")


@dataclass(frozen=True, slots=True)
class WeeklyFutureCalculatedEvent:
    """Weekly Future High/Low have been computed for the session.

    Formula: MISSING INFORMATION (Specification Section 20 item 1).
    This event only carries whatever values an eventual
    ``interfaces.weekly_future_calculator.WeeklyFutureCalculator``
    implementation produces - it does not itself compute anything.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    weekly_future_high: Decimal
    weekly_future_low: Decimal
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "WeeklyFutureCalculatedEvent")
        if self.session_id is None:
            raise ValidationError("WeeklyFutureCalculatedEvent.session_id must not be None.")


@dataclass(frozen=True, slots=True)
class StrikeSelectedEvent:
    """Top Strike and Bottom Strike have been selected for the session.

    Selection rule: MISSING INFORMATION (Specification Section 20
    item 2).
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    top_strike: Decimal
    bottom_strike: Decimal
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "StrikeSelectedEvent")
        if self.session_id is None:
            raise ValidationError("StrikeSelectedEvent.session_id must not be None.")


@dataclass(frozen=True, slots=True)
class WinnerDetectedEvent:
    """A Winner has been determined (Specification Section 9).

    No tie-break field exists - Specification Rule 3 confirms the
    scenario requiring one does not occur.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    session_id: uuid.UUID
    candle_timestamp: datetime
    winning_side: TradeDirection
    winning_strike: Decimal
    priority: EventPriority = EventPriority.HIGH

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "WinnerDetectedEvent")
        if self.session_id is None:
            raise ValidationError("WinnerDetectedEvent.session_id must not be None.")


@dataclass(frozen=True, slots=True)
class TradeOpenedEvent:
    """A trade has been opened (Specification Section 10).

    Entry price: MISSING INFORMATION - not carried here.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    trade_id: uuid.UUID
    entry_strike: Decimal
    entry_side: TradeDirection
    target_level: Decimal
    support_level: Decimal
    competitor_monitor_strike: Decimal
    priority: EventPriority = EventPriority.HIGH

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "TradeOpenedEvent")
        if self.trade_id is None:
            raise ValidationError("TradeOpenedEvent.trade_id must not be None.")


@dataclass(frozen=True, slots=True)
class TradeClosedEvent:
    """A trade has been closed (Specification Section 11)."""

    event_id: uuid.UUID
    occurred_at: datetime
    trade_id: uuid.UUID
    exit_reason: ExitReason
    priority: EventPriority = EventPriority.HIGH

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "TradeClosedEvent")
        if self.trade_id is None:
            raise ValidationError("TradeClosedEvent.trade_id must not be None.")


@dataclass(frozen=True, slots=True)
class TargetHitEvent:
    """The active trade's Target reference level was reached
    (Specification Rule 2, CONFIRMED mapping)."""

    event_id: uuid.UUID
    occurred_at: datetime
    trade_id: uuid.UUID
    target_level: Decimal
    priority: EventPriority = EventPriority.CRITICAL

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "TargetHitEvent")
        if self.trade_id is None:
            raise ValidationError("TargetHitEvent.trade_id must not be None.")


@dataclass(frozen=True, slots=True)
class CompetitorHitEvent:
    """The competitor strike's option reached its own reference level
    (Specification Section 11). Which of the competitor's own
    High/Low triggered this is MISSING INFORMATION (Specification
    Section 20 item 8) - not carried here.
    """

    event_id: uuid.UUID
    occurred_at: datetime
    trade_id: uuid.UUID
    competitor_strike: Decimal
    priority: EventPriority = EventPriority.CRITICAL

    def __post_init__(self) -> None:
        _validate_common(self.event_id, self.occurred_at, "CompetitorHitEvent")
        if self.trade_id is None:
            raise ValidationError("CompetitorHitEvent.trade_id must not be None.")


#: The union of every event type defined in this sprint, used as
#: :class:`events.event_bus.EventBus`'s generic bound.
DomainEvent = (
    MarketOpenEvent
    | MarketCloseEvent
    | WeeklyFutureCalculatedEvent
    | StrikeSelectedEvent
    | WinnerDetectedEvent
    | TradeOpenedEvent
    | TradeClosedEvent
    | TargetHitEvent
    | CompetitorHitEvent
)

__all__ = [
    "CompetitorHitEvent",
    "DomainEvent",
    "Event",
    "MarketCloseEvent",
    "MarketOpenEvent",
    "StrikeSelectedEvent",
    "TargetHitEvent",
    "TradeClosedEvent",
    "TradeOpenedEvent",
    "WeeklyFutureCalculatedEvent",
    "WinnerDetectedEvent",
]

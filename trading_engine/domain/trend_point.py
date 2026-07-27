"""TrendPoint: a per-Strike reference value ("Trend Point Low" / "TP Low").

Traceability notes
-------------------
Per ``docs/RULE_INDEX.md``, TREND-001's Mathematical Definition is
"Partially Known" and TREND-002's is "Unknown." This model exposes
only that a TrendPoint has a value and belongs to exactly one Strike
(TREND-001: "Every analysed strike maintains a Trend Point Low"), and
that the value can change over time (TREND-002). It does not compute
what the value should be, and it does not decide when an update
should happen.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from trading_engine.domain import DomainValidationError


@dataclass(frozen=True)
class TrendPoint:
    """A per-Strike reference value that is marked and can later be
    updated.

    Because this type is immutable, a "change" to a TrendPoint's value
    is represented by constructing a new :class:`TrendPoint` instance
    (see :meth:`with_updated_value`), never by mutating an existing
    one.

    Rule References
        TREND-001
        TREND-002
        TREND-003
        OPPONENT-001

    Entity
        ENT-003

    Attributes:
        trend_point_id: Unique identifier for this TrendPoint instance.
        strike_id: The Strike this TrendPoint belongs to.
        value: The currently marked value. Cannot be negative.
        marked_at: When this value was marked/last updated.
    """

    trend_point_id: uuid.UUID
    strike_id: uuid.UUID
    value: Decimal
    marked_at: datetime

    def __post_init__(self) -> None:
        if self.trend_point_id is None:
            raise DomainValidationError("TrendPoint.trend_point_id must not be None.")

        if self.strike_id is None:
            raise DomainValidationError("TrendPoint.strike_id must not be None.")

        if self.value < 0:
            raise DomainValidationError("TrendPoint.value cannot be negative.")

    def with_updated_value(self, new_value: Decimal, updated_at: datetime) -> TrendPoint:
        """Return a new TrendPoint instance representing this
        TrendPoint after an update, preserving identity and Strike
        linkage.

        Does not decide *whether* or *to what value* an update should
        occur - both remain TODO (TREND-002); this method only
        expresses the immutable-update mechanic itself, given a
        caller-supplied new value.
        """
        return replace(self, value=new_value, marked_at=updated_at)

    # TODO (TREND-001): The formula that produces a TrendPoint's
    # initial value is "Partially Known" only - not implemented here.
    # TODO (TREND-002): What constitutes "market structure changes" as
    # the trigger for updating this value is Unknown (see
    # docs/DOMAIN_MODEL.md, "Market Structure" entity, ENT-004). No
    # trigger-detection type exists in this milestone's scope.

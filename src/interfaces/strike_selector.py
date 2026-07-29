"""StrikeSelector: interface only.

Traceability
------------
Specification Section 5, Section 20 item 2 (Critical): "Select Top
Strike (ATM). Bottom Strike (ATM)." No ATM basis or rounding rule
exists in the Specification - this interface defines only the method
shape a future implementation must satisfy. Do NOT implement.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol, runtime_checkable

from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture


@runtime_checkable
class StrikeSelector(Protocol):
    """Selects the session's Top Strike and Bottom Strike (both
    "ATM") from the session's :class:`~models.weekly_future.WeeklyFuture`."""

    def select(
        self, session_id: uuid.UUID, weekly_future: WeeklyFuture, selected_at: datetime
    ) -> StrikeSelection:
        """Select Top Strike and Bottom Strike.

        Raises:
            core.exceptions.UnresolvedBusinessRuleError: always, until
                the ATM selection rule (Specification Section 20 item
                2) is resolved and a real implementation replaces the
                stub.
        """
        ...  # pragma: no cover

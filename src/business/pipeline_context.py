"""PipelineContext: the immutable state threaded through every stage.

Traceability
------------
Field set matches the instruction's own list (Session, Reference
Data, Weekly Future, Selected Strike, TP State, Qualification State,
Winner, Diagnostics) plus ``session_id``/``candle_timestamp`` needed
to identify *which* session/candle a run concerns - no field encodes a
business rule's value, only whichever already-defined model
(``models.weekly_future.WeeklyFuture``, ``models.strike.StrikeSelection``,
``core.events.WinnerDetectedEvent``) an eventual business engine
produces. ``tp_state``/``qualification_state`` are typed ``object``,
mirroring ``interfaces.tp_engine.TPEngine.update``'s own deliberately
undecided return type (Specification Section 20 item 13) - this
package does not resolve that decision either.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal

from core.events import WinnerDetectedEvent
from core.exceptions import ValidationError
from models.reference_level import ReferenceLevel
from models.strike import StrikeSelection
from models.weekly_future import WeeklyFuture


@dataclass(frozen=True, slots=True)
class PipelineContext:
    """Immutable, evolving state passed from stage to stage.

    Every business-derived field is optional (``None`` until the
    corresponding stage produces it) except ``session_id`` and
    ``candle_timestamp``, which must exist before any stage can run at
    all.

    Attributes:
        session_id: The trading session this run concerns.
        candle_timestamp: The candle currently being processed.
        reference_data: The 13-level reference ladder, once built.
        reference_strike: The anchor strike
            (``business.stages.weekly_future_stage.WeeklyFutureStage``'s
            constructor-injected ``anchor_strike``) that
            ``weekly_future``/``selected_strike`` were computed
            against, once that stage has run.
        weekly_future: Weekly Future High/Low, once calculated.
        selected_strike: Top/Bottom Strike selection, once made.
        tp_state: TP Engine's output. Typed ``object`` - see module
            docstring.
        qualification_state: Qualification Engine's output.
        winner: The detected Winner, if any this cycle.
        diagnostics: Free-text notes accumulated by stages themselves
            (distinct from :class:`~business.business_result.BusinessResult`'s
            own pipeline-level diagnostics).
    """

    session_id: uuid.UUID
    candle_timestamp: datetime
    reference_data: tuple[ReferenceLevel, ...] = field(default_factory=tuple)
    reference_strike: Decimal | None = None
    weekly_future: WeeklyFuture | None = None
    selected_strike: StrikeSelection | None = None
    tp_state: object | None = None
    qualification_state: object | None = None
    winner: WinnerDetectedEvent | None = None
    diagnostics: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.session_id is None:
            raise ValidationError("PipelineContext.session_id must not be None.")
        if self.candle_timestamp is None:
            raise ValidationError("PipelineContext.candle_timestamp must not be None.")

    def with_diagnostic(self, note: str) -> PipelineContext:
        """Return a new context with ``note`` appended to
        ``diagnostics``. Does not mutate ``self`` - matches this
        codebase's frozen-dataclass, replace-not-mutate convention
        (see ``models.trade_position.TradePosition.close``)."""
        return replace(self, diagnostics=(*self.diagnostics, note))

    def with_reference_data(self, reference_data: tuple[ReferenceLevel, ...]) -> PipelineContext:
        return replace(self, reference_data=reference_data)

    def with_reference_strike(self, reference_strike: Decimal) -> PipelineContext:
        return replace(self, reference_strike=reference_strike)

    def with_weekly_future(self, weekly_future: WeeklyFuture) -> PipelineContext:
        return replace(self, weekly_future=weekly_future)

    def with_selected_strike(self, selected_strike: StrikeSelection) -> PipelineContext:
        return replace(self, selected_strike=selected_strike)

    def with_tp_state(self, tp_state: object) -> PipelineContext:
        return replace(self, tp_state=tp_state)

    def with_qualification_state(self, qualification_state: object) -> PipelineContext:
        return replace(self, qualification_state=qualification_state)

    def with_winner(self, winner: WinnerDetectedEvent) -> PipelineContext:
        return replace(self, winner=winner)

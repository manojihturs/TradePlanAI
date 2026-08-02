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

from core.enums import TrendDirection
from core.events import WinnerDetectedEvent
from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot
from models.orb_result import ORBResult
from models.qualified_position import QualifiedPosition
from models.reference_level import ReferenceLevel
from models.strike import StrikeSelection
from models.strike_chain_snapshot import StrikeChainSnapshot
from models.trade_position import TradePosition
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
        candles: Every candle from the replay's own driver dataset
            observed so far this session, in order (threaded in by
            ``application.replay_runner.ReplayRunner``, accumulating
            one candle per iteration - distinct from ``reference_data``,
            which comes from a separate source, see
            ``business.stages.orb_stage.ORBStage``'s own docstring).
        orb_result: This session's Opening Range Breakout
            classification, once ``business.stages.orb_stage.ORBStage``
            has run.
        tp_state: TP Engine's output. Typed ``object`` - see module
            docstring.
        qualification_state: Qualification Engine's output.
        winner: The detected Winner, if any this cycle.
        chain_snapshot: Every strike's CE/PE
            :class:`~models.market_snapshot.MarketSnapshot` pair for
            *this* candle timestamp only (not accumulated) - the
            option-chain-shaped data ``business.stages.winner_stage.WinnerStage``
            and ``business.stages.exit_stage.ExitStage`` read from,
            since both need a specific strike's CE+PE simultaneously,
            unlike ``candles`` (one anchor strike/side, accumulated).
        exited_position: The position closed this candle, if
            ``business.stages.exit_stage.ExitStage`` closed one.
        trend: The underlying's directional bias for this candle,
            added Sprint 11 for
            ``business.stages.qualification_stage.QualificationStage``.
            Externally supplied - how trend itself is computed
            remains UNRESOLVED (see
            ``core.enums.TrendDirection``'s own docstring); this
            field exists purely so a caller who *does* have a trend
            value can feed it into the qualification pipeline, not to
            imply this package computes it.
        qualified_position_top: The Top-anchor
            :class:`~models.qualified_position.QualifiedPosition`
            opened this candle, if a Top-scoped
            ``business.stages.qualification_stage.QualificationStage``
            opened one. Split from Bottom (2026-08-01) because Top and
            Bottom are confirmed to each hold their own independent
            active trade simultaneously (Product Owner-confirmed,
            evidenced by real overlapping trades in
            ``research/incoming/daily_data_2026-07-31.md``) - a single
            shared field/position-manager was a modelling error, not a
            business rule.
        qualified_position_bottom: The Bottom-anchor equivalent of
            ``qualified_position_top``.
        qualification_exited_position_top: The Top-anchor
            :class:`~models.qualified_position.QualifiedPosition`
            closed this candle, if a Top-scoped
            ``business.stages.qualification_exit_stage.QualificationExitStage``
            closed one.
        qualification_exited_position_bottom: The Bottom-anchor
            equivalent of ``qualification_exited_position_top``.
        underlying_index_candles: The underlying index's own OHLC
            candle series observed so far this session (distinct from
            ``candles``, which - depending on which stages are
            registered - may instead hold an anchor strike's own CE
            premium stream for ``business.stages.orb_stage.ORBStage``;
            the two must never be conflated). Added for
            ``business.stages.ut_bot_trend_stage.UTBotTrendStage`` and
            ``business.stages.multi_timeframe_confirmation_stage.MultiTimeframeConfirmationStage``,
            2026-08-02.
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
    candles: tuple[MarketSnapshot, ...] = field(default_factory=tuple)
    orb_result: ORBResult | None = None
    tp_state: object | None = None
    qualification_state: object | None = None
    winner: WinnerDetectedEvent | None = None
    chain_snapshot: tuple[StrikeChainSnapshot, ...] = field(default_factory=tuple)
    exited_position: TradePosition | None = None
    trend: TrendDirection | None = None
    qualified_position_top: QualifiedPosition | None = None
    qualified_position_bottom: QualifiedPosition | None = None
    qualification_exited_position_top: QualifiedPosition | None = None
    qualification_exited_position_bottom: QualifiedPosition | None = None
    underlying_index_candles: tuple[MarketSnapshot, ...] = field(default_factory=tuple)
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

    def with_candles(self, candles: tuple[MarketSnapshot, ...]) -> PipelineContext:
        return replace(self, candles=candles)

    def with_orb_result(self, orb_result: ORBResult) -> PipelineContext:
        return replace(self, orb_result=orb_result)

    def with_tp_state(self, tp_state: object) -> PipelineContext:
        return replace(self, tp_state=tp_state)

    def with_qualification_state(self, qualification_state: object) -> PipelineContext:
        return replace(self, qualification_state=qualification_state)

    def with_winner(self, winner: WinnerDetectedEvent) -> PipelineContext:
        return replace(self, winner=winner)

    def with_chain_snapshot(
        self, chain_snapshot: tuple[StrikeChainSnapshot, ...]
    ) -> PipelineContext:
        return replace(self, chain_snapshot=chain_snapshot)

    def with_exited_position(self, exited_position: TradePosition) -> PipelineContext:
        return replace(self, exited_position=exited_position)

    def with_trend(self, trend: TrendDirection | None) -> PipelineContext:
        """Set (or clear, passing ``None``) ``trend``. Clearing was
        added for
        ``business.stages.multi_timeframe_confirmation_stage.MultiTimeframeConfirmationStage``,
        which revokes a lower-timeframe trend signal that higher
        timeframes don't confirm - see that module's own docstring."""
        return replace(self, trend=trend)

    def with_qualified_position_top(
        self, qualified_position_top: QualifiedPosition
    ) -> PipelineContext:
        return replace(self, qualified_position_top=qualified_position_top)

    def with_qualified_position_bottom(
        self, qualified_position_bottom: QualifiedPosition
    ) -> PipelineContext:
        return replace(self, qualified_position_bottom=qualified_position_bottom)

    def with_qualification_exited_position_top(
        self, qualification_exited_position_top: QualifiedPosition
    ) -> PipelineContext:
        return replace(self, qualification_exited_position_top=qualification_exited_position_top)

    def with_qualification_exited_position_bottom(
        self, qualification_exited_position_bottom: QualifiedPosition
    ) -> PipelineContext:
        return replace(
            self, qualification_exited_position_bottom=qualification_exited_position_bottom
        )

    def with_underlying_index_candles(
        self, underlying_index_candles: tuple[MarketSnapshot, ...]
    ) -> PipelineContext:
        return replace(self, underlying_index_candles=underlying_index_candles)

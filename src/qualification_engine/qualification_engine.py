"""QualificationEngine: detects a confirmed simultaneous dual-
crossover qualification event, and computes its Target/Stop Loss/
Competitor Exit levels.

Traceability
------------
RESOLVED 2026-08-01 - see
``research/incoming/qualification_session1_intake_2026-07-31.md`` and
``research/specifications/qualification_engine_scoring_2026-08-01.md``
(Evidence Complete, 6/6 ``evidence_acceptance_checklist.md`` items).

Mechanism (General Rule Statement + Entry Trigger Rule + Entry/
Target/SL/TSL Clarification, all Product-Owner-supplied):

- Ladder: the anchor strike (Top or Bottom) +/- 6 strikes, each
  strike's own first-5-minute CE/PE High/Low - already built by
  ``reference_builder.reference_builder.ReferenceBuilder``, unchanged.
- Column mapping (which ``models.reference_level.ReferenceLevel``
  field plays "entry column" vs "confirm column" for each
  (anchor_role, side) pair):
    TOP,    CE: entry=pe_low,  confirm=ce_high
    TOP,    PE: entry=ce_high, confirm=pe_low
    BOTTOM, CE: entry=pe_high, confirm=ce_low
    BOTTOM, PE: entry=ce_low,  confirm=pe_high
  (Top: "CE - Mark PE Low", "PE - Mark CE High"; Bottom: "CE - Mark
  PE High", "PE - Mark CE Low" - General Rule Statement.)
- Trend gates which single side is checked: bullish -> CE, bearish
  -> PE (Entry/Target/SL/TSL Clarification). How trend itself is
  computed is UNRESOLVED - Awaiting Strategy Evidence; it is an
  injected input here, never computed by this engine.
- A "touch" (used for "crosses" here) reuses this project's own
  already-confirmed touch definition
  (``winner_engine.winner_engine.WinnerEngine``, Specification Rule
  3): a level is touched if it falls within the evaluated candle's
  [low, high] range. No evidence at a finer granularity (e.g. candle
  open/close-based crossing direction) exists, so this project's
  existing convention is reused rather than inventing a new one.
- If more than one level in a column is touched on the same candle,
  the lowest-strike match is used - an engineering default for a
  genuinely ambiguous case (mirrors ``exit_engine.exit_engine.ExitEngine``'s
  own precedent for handling an unspecified tie), not a confirmed
  business rule.
- Only the anchor's own CE and own PE premiums are watched (four
  streams total across Top+Bottom) - the wider ladder supplies the
  levels crossed, not additional streams watched (Entry/Target/SL/TSL
  Clarification: "watch both top and bottom strike").
- Target = the next value, in the SAME reference column as the entry
  crossing, one rung favourable from the entry level.
- Stop Loss = the next value, in the same column, one rung
  unfavourable from the entry level.
- Competitor Exit = the confirming leg's own crossed value (opposite
  column) - fixed for the life of the trade once qualified (Product
  Owner confirmed 2026-08-01: "Yes, it stays fixed").

Explicitly out of scope for this engine (belongs to a later sprint):
ongoing exit monitoring (whether Target/SL/Competitor Exit is
subsequently touched), Trailing Stop application, and end-of-session
forced close (QUAL-011,
``research/specifications/qualification_rule_catalog.md``) - this
engine only detects and computes a single qualification event.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.enums import AnchorRole, TradeDirection, TrendDirection
from core.exceptions import ValidationError
from core.protocols import IdFactory
from models.market_snapshot import MarketSnapshot
from models.qualification_signal import QualificationSignal
from models.reference_level import ReferenceLevel

#: (anchor_role, side) -> (entry_column, confirm_column), each naming
#: the ``models.reference_level.ReferenceLevel`` attribute to read.
_COLUMN_MAP: dict[tuple[AnchorRole, TradeDirection], tuple[str, str]] = {
    (AnchorRole.TOP, TradeDirection.CE): ("pe_low", "ce_high"),
    (AnchorRole.TOP, TradeDirection.PE): ("ce_high", "pe_low"),
    (AnchorRole.BOTTOM, TradeDirection.CE): ("pe_high", "ce_low"),
    (AnchorRole.BOTTOM, TradeDirection.PE): ("ce_low", "pe_high"),
}

#: Trend gates which single side is checked (Entry/Target/SL/TSL
#: Clarification, 2026-08-01).
_TREND_SIDE: dict[TrendDirection, TradeDirection] = {
    TrendDirection.BULLISH: TradeDirection.CE,
    TrendDirection.BEARISH: TradeDirection.PE,
}


class QualificationEngine:
    """Detects a confirmed dual-crossover qualification event for one
    candle, and computes its Target/Stop Loss/Competitor Exit levels.

    Constructor-injected ID factory only - no globals, no singletons,
    matching every other engine in this codebase.
    """

    def __init__(self, id_factory: IdFactory = uuid.uuid4) -> None:
        self._id_factory = id_factory

    def evaluate(
        self,
        anchor_role: AnchorRole,
        trend: TrendDirection,
        reference_levels: tuple[ReferenceLevel, ...],
        own_ce_snapshot: MarketSnapshot,
        own_pe_snapshot: MarketSnapshot,
        candle_timestamp: datetime,
    ) -> QualificationSignal | None:
        """Return a :class:`~models.qualification_signal.QualificationSignal`
        if a dual crossover is confirmed on this candle for the
        trend-implied side, else ``None``.

        Args:
            anchor_role: TOP or BOTTOM.
            trend: The already-determined underlying trend direction
                (injected - this engine does not compute it).
            reference_levels: The full marked-level ladder (anchor
                +/- 6 strikes), already built by
                ``reference_builder.reference_builder.ReferenceBuilder``.
            own_ce_snapshot: The anchor's own CE candle for this
                timestamp.
            own_pe_snapshot: The anchor's own PE candle for this
                timestamp.
            candle_timestamp: This candle's timestamp.

        Raises:
            core.exceptions.ValidationError: if ``reference_levels``
                is empty, or the snapshots are not candle-mode (OHLC).
        """
        if not reference_levels:
            raise ValidationError("QualificationEngine requires a non-empty reference ladder.")
        if not own_ce_snapshot.is_candle() or not own_pe_snapshot.is_candle():
            raise ValidationError(
                "QualificationEngine requires candle-mode snapshots (OHLC) to evaluate crossings."
            )

        side = _TREND_SIDE[trend]
        own_snapshot = own_ce_snapshot if side is TradeDirection.CE else own_pe_snapshot
        confirm_snapshot = own_pe_snapshot if side is TradeDirection.CE else own_ce_snapshot
        entry_column, confirm_column = _COLUMN_MAP[(anchor_role, side)]

        entry_hit = self._find_touch(own_snapshot, reference_levels, entry_column)
        confirm_hit = self._find_touch(confirm_snapshot, reference_levels, confirm_column)
        if entry_hit is None or confirm_hit is None:
            return None
        entry_strike, entry_level = entry_hit
        _, competitor_exit_level = confirm_hit

        target_level, stop_loss_level = self._adjacent_column_values(
            reference_levels, entry_column, entry_strike, side
        )
        if target_level is None or stop_loss_level is None:
            return None

        return QualificationSignal(
            signal_id=self._id_factory(),
            anchor_role=anchor_role,
            side=side,
            entry_strike=entry_strike,
            entry_level=entry_level,
            target_level=target_level,
            stop_loss_level=stop_loss_level,
            competitor_exit_level=competitor_exit_level,
            qualified_at=candle_timestamp,
        )

    @staticmethod
    def _find_touch(
        snapshot: MarketSnapshot,
        reference_levels: tuple[ReferenceLevel, ...],
        column: str,
    ) -> tuple[Decimal, Decimal] | None:
        """Return ``(strike, value)`` for the lowest-strike level in
        ``column`` that ``snapshot`` touches, or ``None`` if none is
        touched. See the module docstring's tie-break note."""
        assert snapshot.low is not None and snapshot.high is not None
        for level in sorted(reference_levels, key=lambda lvl: lvl.strike):
            value: Decimal = getattr(level, column)
            if snapshot.low <= value <= snapshot.high:
                return level.strike, value
        return None

    @staticmethod
    def _adjacent_column_values(
        reference_levels: tuple[ReferenceLevel, ...],
        column: str,
        entry_strike: Decimal,
        side: TradeDirection,
    ) -> tuple[Decimal | None, Decimal | None]:
        """Return ``(target_level, stop_loss_level)`` - the next
        value in ``column``, sorted by strike, one rung
        favourable/unfavourable from ``entry_strike``.

        A CE trade's entry column (``pe_low``/``pe_high``) increases
        with strike; a PE trade's entry column (``ce_high``/``ce_low``)
        decreases with strike (standard option pricing behaviour,
        independently verified against real Upstox data,
        ``research/incoming/qualification_session1_intake_2026-07-31.md``
        Worked Examples 2-4). Favourable therefore means "next higher
        strike" for a CE trade and "next lower strike" for a PE
        trade. Returns ``(None, None)`` if there is no adjacent strike
        on the required side of the ladder.
        """
        sorted_levels = sorted(reference_levels, key=lambda lvl: lvl.strike)
        strikes = [lvl.strike for lvl in sorted_levels]
        try:
            index = strikes.index(entry_strike)
        except ValueError:
            return None, None

        favorable_index = index + 1 if side is TradeDirection.CE else index - 1
        unfavorable_index = index - 1 if side is TradeDirection.CE else index + 1

        target = (
            getattr(sorted_levels[favorable_index], column)
            if 0 <= favorable_index < len(sorted_levels)
            else None
        )
        stop_loss = (
            getattr(sorted_levels[unfavorable_index], column)
            if 0 <= unfavorable_index < len(sorted_levels)
            else None
        )
        return target, stop_loss

"""TrendStage: PipelineStage adapter for OpenInterestTrendEngine.

Traceability
------------
Wires ``trend_engine.open_interest_trend_engine.OpenInterestTrendEngine``
(Product Owner-confirmed, 2026-08-02 - see that module's own docstring
for the full evidence trail) into the pipeline, writing
``PipelineContext.trend`` via the already-existing ``with_trend``
method - the same field ``business.stages.qualification_stage.QualificationStage``
already reads as an externally-supplied input.

Scope: not yet wired into ``backtest.runner.BacktestRunner``. Historical
candle data fetched via ``backtest.upstox_dataset_builder`` carries no
Open Interest (Upstox's historical-candle endpoint does not return
it) - only a live market-quote/option-chain feed does. This stage
exists for the live paper-trading harness (which polls a live feed
that does carry OI), not the backtest replay path, which still takes
an explicit, manually-supplied ``TrendDirection`` per
``BacktestRunner.run``'s own signature - unchanged, zero regression
risk to the 30+ already-passing backtest fixtures.

Session-open baseline (this session's own opening price/Call OI/Put
OI) is captured once, on the first candle this stage instance ever
sees, and held for the lifetime of the instance - construct a fresh
``TrendStage`` per trading session, mirroring
``qualification_engine.qualification_trailing_stop.BreakevenFirstQualificationTrailingStop``'s
own per-session statefulness convention.

If the Price/OI combination yields no signal this candle (see
``OpenInterestTrendEngine``'s own docstring table), ``context.trend``
is left unchanged from whatever it already was (its previous value,
or ``None`` if this is the first candle) - not reset to ``None`` -
so a trend established on an earlier candle remains available to
gate entries on a later no-signal candle, rather than needing to
re-agree every single candle. This is an engineering default, not
confirmed by evidence; it mirrors this project's own general
precedent of preserving prior state rather than discarding it absent
an explicit "flip back" rule.
"""

from __future__ import annotations

from decimal import Decimal

from business.business_pipeline import StageOutcome
from business.execution_context import ExecutionContext
from business.pipeline_context import PipelineContext
from core.exceptions import ValidationError
from models.strike_chain_snapshot import StrikeChainSnapshot
from trend_engine.open_interest_trend_engine import OpenInterestTrendEngine


class TrendStage:
    """Runs ``OpenInterestTrendEngine`` for this candle's full
    chain_snapshot, capturing the session's own opening baseline the
    first time it runs, and updates ``PipelineContext.trend`` if a
    signal results.

    Constructor-injected engine only - no globals, no singletons.
    Stateful across calls (session-open baseline) by design - see
    module docstring.
    """

    def __init__(self, engine: OpenInterestTrendEngine) -> None:
        self._engine = engine
        self._session_open_price: Decimal | None = None
        self._session_open_call_oi: int | None = None
        self._session_open_put_oi: int | None = None

    @property
    def name(self) -> str:
        return "trend"

    def is_ready(self, context: PipelineContext) -> bool:
        """Ready once this candle's chain_snapshot is present."""
        return len(context.chain_snapshot) > 0

    def run(self, context: PipelineContext, execution: ExecutionContext) -> StageOutcome:
        """Compute this candle's Open-Interest-derived trend and
        update context if a signal results.

        Raises:
            core.exceptions.ValidationError: if any strike's CE or PE
                snapshot in ``context.chain_snapshot`` is missing
                ``open_interest``.
        """
        _ = execution
        call_oi, put_oi = self._total_oi(context.chain_snapshot)
        price = context.chain_snapshot[0].ce.underlying_price

        if self._session_open_price is None:
            self._session_open_price = price
            self._session_open_call_oi = call_oi
            self._session_open_put_oi = put_oi

        assert self._session_open_call_oi is not None
        assert self._session_open_put_oi is not None
        trend = self._engine.evaluate(
            session_open_price=self._session_open_price,
            current_price=price,
            session_open_call_oi=self._session_open_call_oi,
            session_open_put_oi=self._session_open_put_oi,
            current_call_oi=call_oi,
            current_put_oi=put_oi,
        )
        if trend is None:
            return StageOutcome(context=context)
        return StageOutcome(context=context.with_trend(trend))

    @staticmethod
    def _total_oi(chain_snapshot: tuple[StrikeChainSnapshot, ...]) -> tuple[int, int]:
        call_oi = 0
        put_oi = 0
        for pair in chain_snapshot:
            if pair.ce.open_interest is None or pair.pe.open_interest is None:
                raise ValidationError(
                    f"TrendStage requires open_interest on every strike's CE and PE "
                    f"snapshot - missing for strike {pair.strike}."
                )
            call_oi += pair.ce.open_interest
            put_oi += pair.pe.open_interest
        return call_oi, put_oi

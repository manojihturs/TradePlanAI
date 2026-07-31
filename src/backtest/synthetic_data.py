"""Synthetic multi-strike option-chain data for backtest harness plumbing tests.

Traceability
------------
**NOT real market data.** No real historical option-chain data exists
anywhere in this repository (confirmed by repo-wide search) - this
generator exists solely to exercise the confirmed pipeline
(``docs/BUSINESS_LOGIC_FLOW.md``) end to end: Weekly Future through
Exit (Target leg). Any figures this produces (win rate, trade
timing, etc.) describe the ENGINEERING correctness of the wiring, not
real strategy performance - do not read them as a claim about how
this strategy would perform against real markets. Swapping in a real
data source later requires no pipeline changes, only a different
producer of :class:`~data.option_chain_dataset.OptionChainDataset` /
``tuple[StrikeCandleInput, ...]``.

Deterministic and parameterized, not hand-typed magic numbers - every
strike's reference levels and filler candles are derived from its
offset from the anchor strike, so the shape is easy to audit.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from backtest.fixture import BacktestFixture
from data.option_chain_dataset import OptionChainCandle, OptionChainDataset
from models.market_snapshot import MarketSnapshot
from models.strike_chain_snapshot import StrikeChainSnapshot
from reference_builder.reference_validator import StrikeCandleInput

_STRIKE_STEP = Decimal(50)
_LADDER_HALF_WIDTH = 6  # 6 ITM + ATM + 6 OTM = 13 strikes, matching ReferenceBuilder.


def _strikes(anchor_strike: Decimal) -> tuple[Decimal, ...]:
    return tuple(
        anchor_strike + (Decimal(i) * _STRIKE_STEP)
        for i in range(-_LADDER_HALF_WIDTH, _LADDER_HALF_WIDTH + 1)
    )


def _offset(strike: Decimal, anchor_strike: Decimal) -> int:
    return int((strike - anchor_strike) / _STRIKE_STEP)


def build_synthetic_fixture(
    session_date: date | None = None,
    anchor_strike: Decimal | None = None,
) -> BacktestFixture:
    """Build a deterministic synthetic fixture that exercises the
    confirmed pipeline end to end: a Winner is declared on the CE side
    of ``anchor_strike``, Entry opens a position, and the Target leg
    closes it two candles later.

    See module docstring - NOT real market data.
    """
    session_date = session_date if session_date is not None else date(2026, 7, 30)
    anchor_strike = anchor_strike if anchor_strike is not None else Decimal(24000)
    strikes = _strikes(anchor_strike)

    reference_candle_time = datetime(
        session_date.year, session_date.month, session_date.day, 9, 15, tzinfo=UTC
    )
    reference_inputs = tuple(
        _first_candle_input(strike, _offset(strike, anchor_strike), reference_candle_time)
        for strike in strikes
    )

    winner_time = datetime(
        session_date.year, session_date.month, session_date.day, 9, 25, tzinfo=UTC
    )
    exit_time = datetime(session_date.year, session_date.month, session_date.day, 9, 30, tzinfo=UTC)
    filler_time_1 = datetime(
        session_date.year, session_date.month, session_date.day, 9, 26, tzinfo=UTC
    )

    candles = (
        _filler_candle(strikes, anchor_strike, winner_time, winner_touch=True),
        _filler_candle(strikes, anchor_strike, filler_time_1, winner_touch=False),
        _filler_candle(strikes, anchor_strike, exit_time, winner_touch=False, target_touch=True),
    )

    return BacktestFixture(
        session_date=session_date,
        anchor_strike=anchor_strike,
        reference_inputs=reference_inputs,
        dataset=OptionChainDataset(session_date=session_date, candles=candles),
    )


def _first_candle_input(strike: Decimal, offset: int, timestamp: datetime) -> StrikeCandleInput:
    """The 09:15-09:20 first candle for one strike - IS the reference
    level (Specification Rule 1, CONFIRMED: direct field copy, no
    formula)."""
    ce_high = Decimal(100 + offset)
    ce_low = Decimal(90 + offset)
    pe_high = Decimal(100 - offset)
    pe_low = Decimal(90 - offset)
    return StrikeCandleInput(
        strike=strike,
        ce_candle=MarketSnapshot(
            timestamp=timestamp,
            underlying_price=strike,
            open=ce_low + Decimal(5),
            high=ce_high,
            low=ce_low,
            close=ce_low + Decimal(5),
            volume=1000,
        ),
        pe_candle=MarketSnapshot(
            timestamp=timestamp,
            underlying_price=strike,
            open=pe_low + Decimal(5),
            high=pe_high,
            low=pe_low,
            close=pe_low + Decimal(5),
            volume=1000,
        ),
    )


def _filler_candle(
    strikes: tuple[Decimal, ...],
    anchor_strike: Decimal,
    timestamp: datetime,
    winner_touch: bool,
    target_touch: bool = False,
) -> OptionChainCandle:
    """One post-reference candle across every strike.

    By default every strike's CE/PE sit well below their own
    reference band (no touch, see module docstring on why this is
    deliberate rather than trivially self-touching). ``winner_touch``
    pushes the anchor strike's CE into its own ce_high, for exactly
    one candle, to deterministically trigger Winner Detection without
    triggering PE (avoiding the "both sides touch" ambiguous case
    Specification Rule 3 says does not occur). ``target_touch`` pushes
    the Target strike (anchor + 1 rung, per Specification Rule 2's
    CE mapping) into its own ce_high, to deterministically close the
    resulting trade via the Target leg.
    """
    pairs = []
    target_strike = anchor_strike + _STRIKE_STEP
    for strike in strikes:
        offset = _offset(strike, anchor_strike)
        ce_high = Decimal(100 + offset)
        ce_low = Decimal(90 + offset)
        pe_low = Decimal(90 - offset)

        is_touch_candle = (winner_touch and strike == anchor_strike) or (
            target_touch and strike == target_strike
        )
        if is_touch_candle:
            ce = _candle(timestamp, strike, ce_high - Decimal(5), ce_high + Decimal(5))
            pe = _candle(timestamp, strike, pe_low - Decimal(20), pe_low - Decimal(10))
        else:
            ce = _candle(timestamp, strike, ce_low - Decimal(20), ce_low - Decimal(10))
            pe = _candle(timestamp, strike, pe_low - Decimal(20), pe_low - Decimal(10))

        pairs.append(StrikeChainSnapshot(strike=strike, ce=ce, pe=pe))

    return OptionChainCandle(timestamp=timestamp, strikes=tuple(pairs))


def _candle(timestamp: datetime, strike: Decimal, low: Decimal, high: Decimal) -> MarketSnapshot:
    mid = (low + high) / 2
    return MarketSnapshot(
        timestamp=timestamp,
        underlying_price=strike,
        open=mid,
        high=high,
        low=low,
        close=mid,
        volume=500,
    )

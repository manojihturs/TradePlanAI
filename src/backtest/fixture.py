"""BacktestFixture: the input contract BacktestRunner drives.

Traceability
------------
Deliberately data-source-agnostic - the same shape whether the data
comes from ``backtest.synthetic_data.build_synthetic_fixture`` (not
real market data - see that module's own docstring) or a real source
(e.g. ``backtest.upstox_dataset_builder``, Upstox historical candles).
Splitting this out of ``synthetic_data`` avoids a real-data producer
having to import a type literally named "synthetic".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from data.option_chain_dataset import OptionChainDataset
from reference_builder.reference_validator import StrikeCandleInput


@dataclass(frozen=True, slots=True)
class BacktestFixture:
    """Everything a backtest run needs: the first-candle reference
    inputs and the subsequent option-chain candle series.

    Attributes:
        session_date: The trading day this fixture covers.
        anchor_strike: The strike Winner/Entry/Exit are evaluated
            against in this fixture.
        reference_inputs: First-5-minute-candle CE/PE data for every
            ladder strike, for ``reference_builder.reference_builder.ReferenceBuilder``.
        dataset: Every subsequent candle (09:21 onward), for
            ``backtest.runner.BacktestRunner`` to drive
            Winner/Entry/Exit/ORB with.
    """

    session_date: date
    anchor_strike: Decimal
    reference_inputs: tuple[StrikeCandleInput, ...]
    dataset: OptionChainDataset

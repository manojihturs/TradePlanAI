"""Historical Market Data Provider.

Traceability
------------
Pure data-loading infrastructure - zero trading logic. Loads and
validates historical market data from an injected
:class:`~data.historical_data_source.HistoricalDataSource` into an
immutable :class:`~data.historical_dataset.HistoricalDataset`, which
:class:`~application.replay_runner.ReplayRunner` consumes.

Validation logic (schema, chronological ordering, duplicate
timestamps, invalid OHLC/volume) lives once, in
:class:`~data.historical_data_provider.HistoricalDataProvider`,
parameterized over the :class:`~data.historical_data_source.HistoricalDataSource`
Protocol - a future Parquet/SQL/API source only needs to implement
that Protocol's ``read_rows()``; neither this validation logic nor
``ReplayRunner`` needs to change.

One engineering default, not a trading rule, is applied here:
``models.market_snapshot.MarketSnapshot.underlying_price`` (required,
positive) has no dedicated column in a plain OHLCV CSV. Absent
evidence of the intended relationship, this package defaults
``underlying_price`` to the candle's own ``close``, unless an
optional ``UnderlyingPrice`` column is present - see
``historical_data_provider.py`` for where this is applied.
"""

from __future__ import annotations

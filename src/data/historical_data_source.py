"""HistoricalDataSource: the format-agnostic raw-row contract.

Traceability
------------
The extension point named in this sprint's own instruction ("design
so additional providers can be added later without modifying
ReplayRunner"). A future Parquet/SQL/API source only needs to
implement ``read_rows()`` returning the same generic
``dict[str, str]`` row shape - every validation/parsing rule in
:class:`~data.historical_data_provider.HistoricalDataProvider` stays
format-agnostic and unchanged.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, runtime_checkable

from core.exceptions import HistoricalDataError


@runtime_checkable
class HistoricalDataSource(Protocol):
    """The structural contract every historical-data source satisfies."""

    def read_rows(self) -> Iterator[dict[str, str]]:
        """Yield every raw row, in source order, as a string-keyed
        dict (matching ``csv.DictReader``'s row shape - the common
        denominator every future format's own reader is expected to
        produce)."""
        ...  # pragma: no cover


class CsvHistoricalDataSource:
    """Reads rows from a CSV file at ``path``.

    Constructor-injected path only - no globals.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def read_rows(self) -> Iterator[dict[str, str]]:
        """Yield every row of the CSV at ``path`` as a string-keyed
        dict, using the header row as keys.

        Raises:
            core.exceptions.HistoricalDataError: if ``path`` does not
                exist or cannot be read.
        """
        try:
            with self._path.open(newline="", encoding="utf-8") as handle:
                yield from csv.DictReader(handle)
        except OSError as exc:
            raise HistoricalDataError(f"Could not read CSV file {self._path}: {exc}") from exc

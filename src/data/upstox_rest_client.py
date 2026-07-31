"""RestClient: the structural contract every Upstox HTTP transport satisfies.

Traceability
------------
Mirrors ``trading_engine.market_data.upstox_provider.RestTransport``'s
own DI seam ("no real HTTP client is a dependency of this package").
The real ``requests``-based implementation lives in
``tools/upstox_rest_client.py``, outside this package's
``mypy --strict`` boundary (matching where ``tools/performance_benchmark.py``/
``tools/regression_validator.py`` already live) - so this package never
needs ``types-requests``, and every Upstox-facing class here is
unit-testable with a fake transport, no real network or credentials
required.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class RestClient(Protocol):
    """The structural contract every Upstox HTTP transport satisfies."""

    def get_json(
        self, url: str, headers: Mapping[str, str], params: Mapping[str, str] | None = None
    ) -> object:
        """GET ``url`` and return the parsed JSON response body."""
        ...  # pragma: no cover

    def get_bytes(self, url: str) -> bytes:
        """GET ``url`` and return the raw response body (e.g. the
        gzip-compressed instrument master file)."""
        ...  # pragma: no cover

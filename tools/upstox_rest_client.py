"""RequestsRestClient: the real, requests-based RestClient implementation.

Traceability
------------
Implements ``data.upstox_rest_client.RestClient`` (the injected seam
``src/`` depends on). Lives here, outside ``src/``'s ``mypy --strict``
scope, so ``src/`` never needs ``types-requests`` - mirrors where
``tools/performance_benchmark.py``/``tools/regression_validator.py``
already live for the same reason (maintenance/integration tooling, not
the strictly-typed business package).

Retry/backoff mirrors this repository's own already-working legacy
integration (``orb_common.py``'s ``_get()``) - reused as an
engineering fact, not a business rule.

Credentials: reads ``UPSTOX_ACCESS_TOKEN`` from the environment via
``access_token_from_env()`` - this file, and only this file, ever
references a real access token, and only via ``os.environ``, never a
literal value. Set the environment variable yourself before running
anything that uses this; never pass a token as a command-line
argument (visible in shell history/process listings) or hardcode one
here.

UNTESTED AGAINST THE REAL UPSTOX API - see
``backtest.upstox_dataset_builder``'s own docstring. Validate a single
small request manually (e.g. one instrument's historical candles)
before relying on a full backtest run.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import requests


class RequestsRestClient:
    """Real HTTP transport for Upstox, via the ``requests`` library.

    Retries on 429/5xx with exponential backoff, honoring a
    Retry-After header if present - mirrors this repository's proven
    legacy integration (``orb_common.py``'s ``_get()``).
    """

    def __init__(self, timeout_seconds: int = 20, max_retries: int = 10) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._session = requests.Session()
        self._session.mount(
            "https://", requests.adapters.HTTPAdapter(pool_maxsize=20, pool_connections=20)
        )

    def get_json(self, url, headers, params=None):
        """GET ``url`` and return the parsed JSON response body."""
        response = self._get(url, headers=headers, params=params)
        return response.json()

    def get_bytes(self, url):
        """GET ``url`` and return the raw response body."""
        response = self._get(url, headers={}, params=None)
        return response.content

    def _get(self, url, headers, params):
        last_exc = None
        for attempt in range(self._max_retries):
            try:
                response = self._session.get(
                    url, headers=headers, params=params, timeout=self._timeout_seconds
                )
                if response.status_code == 429 or response.status_code >= 500:
                    retry_after = response.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else (2**attempt)
                    time.sleep(min(wait, 30))
                    last_exc = requests.HTTPError(
                        f"HTTP {response.status_code} on attempt {attempt + 1}"
                    )
                    continue
                response.raise_for_status()
                return response
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                time.sleep(min(2**attempt, 30))
        raise (
            last_exc
            if last_exc is not None
            else RuntimeError("RequestsRestClient._get failed with no captured exception")
        )


def access_token_from_env(var_name: str = "UPSTOX_ACCESS_TOKEN") -> str:
    """Read the Upstox access token from the environment.

    Set the ``UPSTOX_ACCESS_TOKEN`` environment variable yourself
    before calling this - never pass a literal token value into this
    function or any other code.

    Raises:
        RuntimeError: if the environment variable is not set.
    """
    token = os.environ.get(var_name, "")
    if not token:
        raise RuntimeError(f"Set the {var_name} environment variable before running this.")
    return token

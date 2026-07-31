"""UpstoxCandleSource: one instrument's historical candles, via Upstox's REST API.

Traceability
------------
Implements the existing ``data.historical_data_source.HistoricalDataSource``
Protocol - the extension point that module's own docstring names
("a future Parquet/SQL/API source only needs to implement
``read_rows()``"). Produces rows in exactly the schema
``data.historical_data_provider.HistoricalDataProvider`` already
expects (``Date``, ``Time``, ``Open``, ``High``, ``Low``, ``Close``,
``Volume``), so that already-tested provider parses/validates Upstox
candles completely unchanged - no new parsing/validation logic here.

Endpoint shape (``/v3/historical-candle/{instrument_key}/minutes/{interval}/{to}/{from}``,
response ``{"data": {"candles": [[iso_ts, open, high, low, close,
volume, oi?], ...]}}``) matches the already-working legacy integration
in the repository's ``orb_common.py`` (``fetch_historical_candles``) -
reused here as an engineering/API-integration fact, not a trading
business rule (per this project's established distinction between the
two - see ``research/specifications/qualification_evidence.md``'s own
package-boundary note).

Retry/backoff is NOT this module's concern - it lives in the injected
``RestClient`` transport (the real implementation, ``tools/upstox_rest_client.py``,
mirrors the legacy retry convention). This module makes exactly one
request per :meth:`read_rows` call.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime

from core.exceptions import HistoricalDataError
from data.upstox_rest_client import RestClient

_BASE_URL = "https://api.upstox.com"


class UpstoxCandleSource:
    """Reads one instrument's historical candles from Upstox.

    Constructor-injected ``rest_client``/``access_token`` only - no
    globals. ``access_token`` is an opaque string this class never
    logs or persists; the caller is responsible for how it was
    obtained (see ``tools/upstox_rest_client.py``'s ``from_env``).
    """

    def __init__(
        self,
        rest_client: RestClient,
        access_token: str,
        instrument_key: str,
        interval_minutes: int,
        day_from: date,
        day_to: date,
        base_url: str = _BASE_URL,
    ) -> None:
        self._rest_client = rest_client
        self._access_token = access_token
        self._instrument_key = instrument_key
        self._interval_minutes = interval_minutes
        self._day_from = day_from
        self._day_to = day_to
        self._base_url = base_url

    def read_rows(self) -> Iterator[dict[str, str]]:
        """Yield every candle for this instrument/date-range as a
        string-keyed dict, matching
        ``data.historical_data_provider.HistoricalDataProvider``'s
        expected schema.

        Raises:
            core.exceptions.HistoricalDataError: if the response is
                not shaped as Upstox's documented candle payload.
        """
        url = (
            f"{self._base_url}/v3/historical-candle/{self._instrument_key}/minutes/"
            f"{self._interval_minutes}/{self._day_to.isoformat()}/{self._day_from.isoformat()}"
        )
        headers = {"Authorization": f"Bearer {self._access_token}", "Accept": "application/json"}
        payload = self._rest_client.get_json(url, headers)
        for row in self._extract_candle_rows(payload):
            yield self._row_to_dict(row)

    def _extract_candle_rows(self, payload: object) -> list[object]:
        if not isinstance(payload, dict):
            raise HistoricalDataError(
                f"Unexpected Upstox response shape (not a JSON object) "
                f"for {self._instrument_key}."
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise HistoricalDataError(
                f"Upstox response missing 'data' object for {self._instrument_key}."
            )
        candles = data.get("candles")
        if not isinstance(candles, list):
            raise HistoricalDataError(
                f"Upstox response missing 'data.candles' list for {self._instrument_key}."
            )
        return candles

    def _row_to_dict(self, row: object) -> dict[str, str]:
        if not isinstance(row, list) or len(row) < 6:
            raise HistoricalDataError(
                f"Malformed candle row from Upstox for {self._instrument_key}: {row!r}"
            )
        timestamp_str, open_, high, low, close, volume = (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
        )
        timestamp = datetime.fromisoformat(str(timestamp_str))
        return {
            "Date": timestamp.date().isoformat(),
            "Time": timestamp.strftime("%H:%M:%S"),
            "Open": str(open_),
            "High": str(high),
            "Low": str(low),
            "Close": str(close),
            "Volume": str(int(float(volume))),
        }

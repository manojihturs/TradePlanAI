"""UpstoxInstrumentResolver: resolves strike/side to Upstox instrument_key.

Traceability
------------
Reproduces the already-working legacy resolution logic in this
repository's ``orb_common.py`` (``resolve_option_chain``) against
Upstox's real instrument master file - reused here as an
engineering/API-integration fact (field names, segment/expiry
encoding), not a trading business rule, per this project's established
distinction between the two (see
``research/specifications/qualification_evidence.md``'s own
package-boundary note on why legacy ORB code is excluded as evidence
for business rules, but not for API-integration mechanics).

Expiry timestamps in the instrument master are Unix milliseconds,
interpreted in IST (``Asia/Kolkata``) to get the correct calendar
date - NSE expiry dates are defined in IST, and interpreting the same
instant in another timezone can shift the calendar date by one day
around midnight IST.
"""

from __future__ import annotations

import gzip
import json
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from core.exceptions import HistoricalDataError
from data.upstox_rest_client import RestClient

_INSTRUMENT_MASTER_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
_IST = ZoneInfo("Asia/Kolkata")


class UpstoxInstrumentResolver:
    """Resolves ``(strike, side)`` pairs to Upstox instrument keys for
    one underlying/expiry, from the Upstox instrument master.

    Constructor-injected ``rest_client`` only - no globals. The
    instrument master is fetched fresh on every call; callers that
    need caching should cache at their own layer (matching this
    class's single responsibility: resolve, not cache).
    """

    def __init__(
        self, rest_client: RestClient, instrument_master_url: str = _INSTRUMENT_MASTER_URL
    ) -> None:
        self._rest_client = rest_client
        self._instrument_master_url = instrument_master_url

    def resolve_option_chain(
        self, underlying_symbol: str, expiry: date, strikes: tuple[Decimal, ...]
    ) -> dict[tuple[Decimal, str], str]:
        """Return ``{(strike, "CE"|"PE"): instrument_key}`` for every
        strike in ``strikes``.

        Raises:
            core.exceptions.HistoricalDataError: if the instrument
                master cannot be parsed, or any requested
                ``(strike, side)`` contract is not found in it.
        """
        raw = self._rest_client.get_bytes(self._instrument_master_url)
        try:
            rows = json.loads(gzip.decompress(raw))
        except (OSError, gzip.BadGzipFile, json.JSONDecodeError) as exc:
            raise HistoricalDataError(f"Could not parse Upstox instrument master: {exc}") from exc
        if not isinstance(rows, list):
            raise HistoricalDataError("Upstox instrument master is not a JSON array.")

        wanted = set(strikes)
        resolved: dict[tuple[Decimal, str], str] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            if row.get("segment") != "NSE_FO":
                continue
            if row.get("underlying_symbol") != underlying_symbol:
                continue
            instrument_type = row.get("instrument_type")
            if instrument_type not in ("CE", "PE"):
                continue
            expiry_ms = row.get("expiry")
            if expiry_ms is None:
                continue
            expiry_date = datetime.fromtimestamp(expiry_ms / 1000, tz=_IST).date()
            if expiry_date != expiry:
                continue
            strike = Decimal(str(row.get("strike_price", 0)))
            if strike in wanted:
                resolved[(strike, instrument_type)] = row["instrument_key"]

        missing = [
            (strike, side)
            for strike in sorted(wanted)
            for side in ("CE", "PE")
            if (strike, side) not in resolved
        ]
        if missing:
            raise HistoricalDataError(
                f"Missing {underlying_symbol} {expiry} contracts in Upstox instrument master: "
                f"{missing}"
            )
        return resolved

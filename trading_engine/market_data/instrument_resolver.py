"""InstrumentResolver: resolves spot/option symbols to instrument identifiers.

Traceability notes
-------------------
A pure lookup table - it never fetches or invents instrument-master
data itself. No document in this repository evidences the real
structure of a broker's instrument master (Upstox's or any other's),
so this resolver is populated entirely by the caller (via
:meth:`InstrumentResolver.register`) - it defines the *shape* of a
resolvable instrument (:class:`InstrumentKey`) and the *lookup keys*
Milestone I1 asks for (spot, and option by underlying/expiry/strike/type),
never the data source.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum, auto

from trading_engine.market_data.exceptions import (
    InstrumentResolutionError,
    MarketDataValidationError,
)


class OptionType(Enum):
    """The two option sides Milestone I1 requires resolution for."""

    CALL = auto()
    PUT = auto()


@dataclass(frozen=True)
class InstrumentKey:
    """An immutable identifier for one tradable instrument.

    Attributes:
        token: The broker-assigned instrument token/identifier
            string. Opaque to this package - never parsed or
            interpreted, only looked up and compared.
        symbol: A human-readable symbol (e.g. ``"NIFTY"``,
            ``"NIFTY24070124000CE"``).
        exchange: The exchange segment (e.g. ``"NSE_FO"``,
            ``"NSE_INDEX"``) - a plain string, no fixed vocabulary is
            evidenced.
    """

    token: str
    symbol: str
    exchange: str

    def __post_init__(self) -> None:
        if not self.token or not self.token.strip():
            raise MarketDataValidationError("InstrumentKey.token must not be blank.")
        if not self.symbol or not self.symbol.strip():
            raise MarketDataValidationError("InstrumentKey.symbol must not be blank.")
        if not self.exchange or not self.exchange.strip():
            raise MarketDataValidationError("InstrumentKey.exchange must not be blank.")


def _option_lookup_key(
    underlying: str, expiry: date, strike: Decimal, option_type: OptionType
) -> str:
    return f"{underlying}|{expiry.isoformat()}|{strike}|{option_type.name}"


class InstrumentResolver:
    """Resolves spot and option lookup keys to :class:`InstrumentKey`.

    Responsibilities: resolve spot instrument, resolve option
    instrument (by underlying/expiry/strike/CE-or-PE), and list every
    registered option instrument for one underlying/expiry pair. Never
    fetches instrument-master data itself - see module docstring.
    """

    def __init__(self) -> None:
        self._spot_instruments: dict[str, InstrumentKey] = {}
        self._option_instruments: dict[str, InstrumentKey] = {}

    def register_spot(self, symbol: str, instrument: InstrumentKey) -> None:
        """Register the instrument resolved by :meth:`resolve_spot` for ``symbol``."""
        self._spot_instruments[symbol] = instrument

    def register_option(
        self,
        underlying: str,
        expiry: date,
        strike: Decimal,
        option_type: OptionType,
        instrument: InstrumentKey,
    ) -> None:
        """Register the instrument resolved by :meth:`resolve_option`
        for the given underlying/expiry/strike/type combination."""
        key = _option_lookup_key(underlying, expiry, strike, option_type)
        self._option_instruments[key] = instrument

    def resolve_spot(self, symbol: str) -> InstrumentKey:
        """Resolve the spot instrument for ``symbol``.

        Raises:
            InstrumentResolutionError: if no spot instrument was
                registered for ``symbol``.
        """
        try:
            return self._spot_instruments[symbol]
        except KeyError as exc:
            raise InstrumentResolutionError(
                f"No spot instrument registered for symbol {symbol!r}."
            ) from exc

    def resolve_option(
        self, underlying: str, expiry: date, strike: Decimal, option_type: OptionType
    ) -> InstrumentKey:
        """Resolve one option instrument.

        Raises:
            InstrumentResolutionError: if no option instrument was
                registered for this exact
                underlying/expiry/strike/option_type combination.
        """
        key = _option_lookup_key(underlying, expiry, strike, option_type)
        try:
            return self._option_instruments[key]
        except KeyError as exc:
            raise InstrumentResolutionError(
                f"No option instrument registered for {underlying!r} "
                f"expiry={expiry.isoformat()} strike={strike} type={option_type.name}."
            ) from exc

    def option_chain(self, underlying: str, expiry: date) -> tuple[InstrumentKey, ...]:
        """Return every registered option instrument for one
        underlying/expiry pair, in registration order."""
        prefix = f"{underlying}|{expiry.isoformat()}|"
        return tuple(
            instrument
            for key, instrument in self._option_instruments.items()
            if key.startswith(prefix)
        )

"""Data models for the first-5-minute premium reference capture.

Traceability notes
-------------------
Milestone I2 ("PREMIUM SNAPSHOT ENGINE") requires capturing, per
contract: Instrument Token, Strike, Option Type, Timestamp, Open,
High, Low, Close, LTP, Volume, OI - and storing four core contracts
(Top CE, Top PE, Bottom CE, Bottom PE) plus a best-effort ITM/ATM/OTM
range. ``docs/architecture/DOMAIN_ARCHITECTURE.md`` established the
existing :class:`trading_engine.domain.premium.Premium` model as
deliberately thin (id/value/timestamp only) - no CE/PE-specific
structure or "capture" formula is evidenced anywhere, so this module
does not extend or reinterpret that model. It defines the richer,
purely observational contract-snapshot shape Milestone I2's own field
list specifies, reusing :class:`trading_engine.market_data.instrument_resolver.InstrumentKey`
and :class:`trading_engine.market_data.instrument_resolver.OptionType`
rather than inventing a parallel instrument-identity concept.

No trading mathematics, threshold, or decision appears anywhere in
this module - it is a record of what was observed, nothing more.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from trading_engine.market_data.instrument_resolver import InstrumentKey, OptionType
from trading_engine.premium_snapshot.exceptions import SnapshotValidationError


@dataclass(frozen=True)
class ContractSnapshot:
    """One contract's captured OHLC/LTP/Volume/OI over a capture window.

    Attributes:
        instrument: The contract's instrument identity.
        strike: The contract's strike price.
        option_type: CALL or PUT.
        timestamp: The timestamp of the last tick that contributed to
            this snapshot (i.e. when it became final).
        open: The first observed traded price in the window.
        high: The highest observed traded price in the window.
        low: The lowest observed traded price in the window.
        close: The last observed traded price in the window.
        last_traded_price: The most recent traded price - equal to
            ``close`` for a completed window, kept as a distinct field
            because it is one of Milestone I2's explicitly required
            columns.
        volume: Traded volume as of the last observed tick.
        open_interest: Open interest as of the last observed tick.
    """

    instrument: InstrumentKey
    strike: Decimal
    option_type: OptionType
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    last_traded_price: Decimal
    volume: int
    open_interest: int

    def __post_init__(self) -> None:
        if self.instrument is None:
            raise SnapshotValidationError("ContractSnapshot.instrument must not be None.")
        if self.timestamp is None:
            raise SnapshotValidationError("ContractSnapshot.timestamp must not be None.")
        if self.strike <= 0:
            raise SnapshotValidationError("ContractSnapshot.strike must be greater than 0.")
        if self.high < self.low:
            raise SnapshotValidationError(
                f"ContractSnapshot high ({self.high}) is less than low ({self.low})."
            )
        if not (self.low <= self.open <= self.high):
            raise SnapshotValidationError(
                f"ContractSnapshot open ({self.open}) is outside [low, high] = "
                f"[{self.low}, {self.high}]."
            )
        if not (self.low <= self.close <= self.high):
            raise SnapshotValidationError(
                f"ContractSnapshot close ({self.close}) is outside [low, high] = "
                f"[{self.low}, {self.high}]."
            )
        if self.last_traded_price <= 0:
            raise SnapshotValidationError(
                "ContractSnapshot.last_traded_price must be greater than 0."
            )
        if self.volume < 0:
            raise SnapshotValidationError("ContractSnapshot.volume must not be negative.")
        if self.open_interest < 0:
            raise SnapshotValidationError("ContractSnapshot.open_interest must not be negative.")


@dataclass(frozen=True)
class PremiumSnapshot:
    """The complete first-capture-window premium reference for one
    session.

    Attributes:
        snapshot_id: This snapshot's own identifier.
        session_id: The trading session this snapshot belongs to.
        capture_window_start: When the capture window began.
        capture_window_end: When the capture window ended.
        top_strike: The Top Strike supplied by the caller (already
            calculated externally - this engine never computes a
            strike).
        bottom_strike: The Bottom Strike supplied by the caller.
        top_ce: The Top Strike's CE contract snapshot, or ``None`` if
            no tick was observed for it during the window.
        top_pe: The Top Strike's PE contract snapshot, or ``None``.
        bottom_ce: The Bottom Strike's CE contract snapshot, or
            ``None``.
        bottom_pe: The Bottom Strike's PE contract snapshot, or
            ``None``.
        range_contracts: Best-effort 6-ITM/ATM/6-OTM contract
            snapshots. Whatever subset was actually observed - never
            required to be complete (no repository evidence for this
            range exists; see ``REALTIME_TRADING_SPECIFICATION.md``
            Section 3).
    """

    snapshot_id: uuid.UUID
    session_id: uuid.UUID
    capture_window_start: datetime
    capture_window_end: datetime
    top_strike: Decimal
    bottom_strike: Decimal
    top_ce: ContractSnapshot | None
    top_pe: ContractSnapshot | None
    bottom_ce: ContractSnapshot | None
    bottom_pe: ContractSnapshot | None
    range_contracts: tuple[ContractSnapshot, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.snapshot_id is None:
            raise SnapshotValidationError("PremiumSnapshot.snapshot_id must not be None.")
        if self.session_id is None:
            raise SnapshotValidationError("PremiumSnapshot.session_id must not be None.")
        if self.capture_window_start is None or self.capture_window_end is None:
            raise SnapshotValidationError("PremiumSnapshot capture window bounds must not be None.")
        if self.capture_window_end <= self.capture_window_start:
            raise SnapshotValidationError(
                "PremiumSnapshot.capture_window_end must be after capture_window_start."
            )
        if self.top_strike <= 0:
            raise SnapshotValidationError("PremiumSnapshot.top_strike must be greater than 0.")
        if self.bottom_strike <= 0:
            raise SnapshotValidationError("PremiumSnapshot.bottom_strike must be greater than 0.")

    def core_contracts(self) -> tuple[ContractSnapshot, ...]:
        """The four core contracts that were actually captured (not
        ``None``), in a fixed order: top CE, top PE, bottom CE, bottom
        PE."""
        return tuple(
            contract
            for contract in (self.top_ce, self.top_pe, self.bottom_ce, self.bottom_pe)
            if contract is not None
        )

    def missing_core_contract_count(self) -> int:
        """How many of the four core contracts were not captured."""
        return 4 - len(self.core_contracts())

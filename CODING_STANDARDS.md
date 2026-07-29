# Coding Standards

Project-wide conventions for `src/`, beyond what `mypy --strict`/`ruff`/`black` already enforce mechanically.

## Time Handling

**Never call `datetime.now()` directly.** Always use `core.protocols.utc_now()`, or accept an injected `Clock` (`core.protocols.Clock = Callable[[], datetime]`) and default it to `utc_now`.

**Reason:** `datetime.now()` returns a naive (timezone-less) datetime, while every timestamp elsewhere in this codebase — every test fixture, and any real market-data feed — is timezone-aware. Mixing the two raises `TypeError: can't subtract offset-naive and offset-aware datetimes` the moment a naive default-clock timestamp is compared against or subtracted from an aware one. This already happened once, during Sprint 3 development (see `ARCHITECTURE_REVIEW.md` Finding 1), and was fixed by introducing `utc_now()` as the single canonical clock source across `TradeManager`, `EntryEngine`, `WinnerEngine`, and `ReplayEngine`.

This also keeps every clock:
- deterministic under test (inject a fixed `lambda: some_datetime` instead),
- consistent in timezone handling across every module, and
- swappable for a future clock source (e.g. an exchange-time clock) without touching call sites.

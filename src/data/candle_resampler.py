"""resample_candles: aggregate finer-grained candles into coarser ones.

Traceability
------------
Standard OHLCV bucket aggregation (open = first, high = max, low =
min, close = last, volume = sum), aligned to a session start time -
mirrors this repository's already-working legacy ``orb_common.py``
``resample()`` function, reused here as a mechanical
data-transformation fact, not a trading business rule. Needed because
Upstox's historical-candle endpoint is only known, from this
repository's own working integration, to serve 1-minute candles
reliably - requesting a coarser interval directly is unverified, so
``data.upstox_candle_source.UpstoxCandleSource`` always fetches
1-minute data and this function resamples it.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from core.exceptions import ValidationError
from models.market_snapshot import MarketSnapshot


def resample_candles(
    candles: tuple[MarketSnapshot, ...], bucket_minutes: int, session_start: time
) -> tuple[MarketSnapshot, ...]:
    """Aggregate ``candles`` (assumed 1-minute, chronologically
    ordered, all candle-mode) into ``bucket_minutes``-wide candles,
    aligned to ``session_start`` on each candle's own date.

    Raises:
        core.exceptions.ValidationError: if any input candle is not
            candle-mode (no OHLC), or ``bucket_minutes`` is not
            positive.
    """
    if bucket_minutes <= 0:
        raise ValidationError("resample_candles: bucket_minutes must be positive.")
    if not candles:
        return ()

    buckets: dict[datetime, list[MarketSnapshot]] = {}
    for candle in candles:
        if not candle.is_candle():
            raise ValidationError(
                "resample_candles requires candle-mode (OHLC) snapshots throughout."
            )
        anchor = datetime.combine(
            candle.timestamp.date(), session_start, tzinfo=candle.timestamp.tzinfo
        )
        offset_minutes = int((candle.timestamp - anchor).total_seconds() // 60)
        if offset_minutes < 0:
            continue
        bucket_start = anchor + timedelta(
            minutes=(offset_minutes // bucket_minutes) * bucket_minutes
        )
        buckets.setdefault(bucket_start, []).append(candle)

    resampled = []
    for bucket_start in sorted(buckets):
        members = buckets[bucket_start]
        resampled.append(_merge(bucket_start, members))
    return tuple(resampled)


def _merge(bucket_start: datetime, members: list[MarketSnapshot]) -> MarketSnapshot:
    opens = members[0].open
    closes = members[-1].close
    highs = max(member.high for member in members if member.high is not None)
    lows = min(member.low for member in members if member.low is not None)
    total_volume = sum(member.volume or 0 for member in members)
    underlying_price = members[-1].underlying_price
    assert opens is not None and closes is not None  # candle-mode already checked
    return MarketSnapshot(
        timestamp=bucket_start,
        underlying_price=underlying_price,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        volume=total_volume,
    )

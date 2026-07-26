"""Unit tests for strategy.replay_engine (Module 7).

No network access required. Modules 1-6 are used unmodified.
"""

import unittest
from datetime import date, datetime

from strategy.level_capture import LevelCapture, StrikeLevels
from strategy.premium_mapping import build_premium_mapping
from strategy.entry_signal import Candle
from strategy.replay_engine import ReplayEngineError, run_replay, format_summary


# Narrowed real data (23850-24300) reproducing the exact real-data gap
# found this session: an entry at the lowest strike (23850) has no lower
# rung for its Mapped Stop Loss within this range.
_NARROW_RAW = {
    23850: (342.80, 288.00, 86.50, 52.65),
    23900: (310.00, 253.80, 102.65, 63.65),
    23950: (269.95, 221.85, 120.85, 78.20),
    24000: (238.75, 192.00, 141.65, 94.40),
    24050: (206.35, 165.50, 164.65, 114.00),
    24100: (176.85, 140.75, 190.00, 135.05),
    24150: (154.00, 118.85, 218.00, 159.55),
}
_EXTRA_STRIKE = {23800: (383.40, 324.00, 72.30, 42.60)}


def _make_narrow_capture():
    levels = {
        strike: StrikeLevels(strike=strike, ce_high=ce_h, ce_low=ce_l,
                              pe_high=pe_h, pe_low=pe_l)
        for strike, (ce_h, ce_l, pe_h, pe_l) in _NARROW_RAW.items()
    }
    return LevelCapture(
        session_date=date(2026, 7, 22), spot_open=24150.0, atm=24150,
        top_strike=24144.45, bottom_strike=24050.85, levels=levels,
    )


def _narrow_fetcher(strike: int, side: str):
    table = {**_NARROW_RAW, **_EXTRA_STRIKE}
    if strike not in table:
        raise RuntimeError(f"strike {strike} not available (test stub)")
    ce_h, ce_l, pe_h, pe_l = table[strike]
    return (0.0, ce_h if side == "CE" else pe_h, ce_l if side == "CE" else pe_l, 0.0)


def _make_mapping():
    raw = {
        23700: (459.20, 402.40, 50.20, 28.15),
        23750: (408.50, 361.70, 60.40, 31.95),
        23800: (383.40, 324.00, 72.30, 42.60),
        23850: (342.80, 288.00, 86.50, 52.65),
        23900: (310.00, 253.80, 102.65, 63.65),
        23950: (269.95, 221.85, 120.85, 78.20),
        24000: (238.75, 192.00, 141.65, 94.40),
        24050: (206.35, 165.50, 164.65, 114.00),
        24100: (176.85, 140.75, 190.00, 135.05),
        24150: (154.00, 118.85, 218.00, 159.55),
        24200: (133.00, 99.10, 248.40, 186.05),
        24250: (106.45, 81.70, 280.65, 215.05),
        24300: (92.50, 66.80, 315.40, 245.05),
    }
    levels = {
        strike: StrikeLevels(strike=strike, ce_high=ce_h, ce_low=ce_l,
                              pe_high=pe_h, pe_low=pe_l)
        for strike, (ce_h, ce_l, pe_h, pe_l) in raw.items()
    }
    capture = LevelCapture(
        session_date=date(2026, 7, 22), spot_open=24150.0, atm=24150,
        top_strike=24144.45, bottom_strike=24050.85, levels=levels,
    )
    return build_premium_mapping(capture, strike_gap=50)


def _c(o, h, l, c):
    return Candle(o, h, l, c)


class RunReplayTests(unittest.TestCase):
    """Builds a minimal candle series around ONLY strike 24050 that
    reproduces the trader's real row 1 (PE @ 24050: entry 09:25 @
    206.35, exit 09:45 @ 238.75, target hit, pnl +32.40)."""

    def setUp(self) -> None:
        self.mapping = _make_mapping()

    def test_no_candles_raises(self) -> None:
        with self.assertRaises(ReplayEngineError):
            run_replay(self.mapping, {}, {})

    # CE stays flat and well below BOTH of strike 24050's CE thresholds
    # (TOP=114.00, BOTTOM=164.65) throughout every test below, so only
    # PE's own movement controls entry timing - avoids the same
    # trivial-threshold trap found earlier in this session, where a
    # "neutral" candle accidentally crossed a threshold it wasn't meant to.
    _CE_SAFE = _c(90.0, 95.0, 85.0, 90.0)
    # PE stays flat and below BOTH of strike 24050's PE thresholds
    # (BOTTOM=165.50, TOP=206.35) until the candle meant to trigger entry.
    _PE_SAFE = _c(150.0, 155.0, 145.0, 150.0)

    def test_reproduces_row1_end_to_end(self) -> None:
        strike = 24050
        ce_series = {strike: {
            datetime(2026, 7, 22, 9, 20): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 25): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 30): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 35): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 40): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 45): self._CE_SAFE,
        }}
        pe_series = {strike: {
            datetime(2026, 7, 22, 9, 20): self._PE_SAFE,
            # 09:25: PE crosses ABOVE CE-High(206.35) - fresh cross - entry.
            datetime(2026, 7, 22, 9, 25): _c(200.0, 220.0, 200.0, 217.2),
            datetime(2026, 7, 22, 9, 30): _c(217.0, 225.0, 215.0, 222.0),
            datetime(2026, 7, 22, 9, 35): _c(222.0, 230.0, 220.0, 228.0),
            datetime(2026, 7, 22, 9, 40): _c(228.0, 235.0, 225.0, 233.0),
            # 09:45: PE's high reaches target 238.75.
            datetime(2026, 7, 22, 9, 45): _c(233.0, 240.0, 230.0, 236.0),
        }}

        result = run_replay(self.mapping, ce_series, pe_series)

        self.assertEqual(len(result.trades), 1)
        trade = result.trades[0]
        self.assertEqual(trade.trade_time, datetime(2026, 7, 22, 9, 25).time())
        self.assertEqual(trade.entry, 206.35)
        self.assertEqual(trade.exit, 238.75)
        self.assertEqual(trade.reason, "TARGET")
        self.assertAlmostEqual(trade.pnl, 32.40, places=2)
        self.assertEqual(result.win_count, 1)
        self.assertEqual(result.loss_count, 0)
        self.assertEqual(result.win_rate_pct, 100.0)
        self.assertIsNone(result.open_position_at_end)

    def test_open_position_at_end_is_not_force_closed(self) -> None:
        strike = 24050
        ce_series = {strike: {
            datetime(2026, 7, 22, 9, 20): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 25): self._CE_SAFE,
        }}
        pe_series = {strike: {
            datetime(2026, 7, 22, 9, 20): self._PE_SAFE,
            datetime(2026, 7, 22, 9, 25): _c(200.0, 220.0, 200.0, 217.2),
        }}
        # Data ends immediately after entry - never reaches target or SL.
        result = run_replay(self.mapping, ce_series, pe_series)
        self.assertEqual(result.trades, [])
        self.assertIsNotNone(result.open_position_at_end)

    def test_never_peeks_at_future_candle_for_entry_timing(self) -> None:
        # A candle far in the future that WOULD confirm entry must not
        # affect an earlier candle's decision - entries can only fire on
        # the candle where the condition is actually first satisfied.
        strike = 24050
        ce_series = {strike: {
            datetime(2026, 7, 22, 9, 20): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 25): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 30): self._CE_SAFE,
        }}
        pe_series = {strike: {
            datetime(2026, 7, 22, 9, 20): self._PE_SAFE,
            datetime(2026, 7, 22, 9, 25): self._PE_SAFE,             # still below 206.35
            datetime(2026, 7, 22, 9, 30): _c(200.0, 220.0, 200.0, 217.2),  # crosses now
        }}
        result = run_replay(self.mapping, ce_series, pe_series)
        self.assertIsNotNone(result.open_position_at_end)
        self.assertEqual(result.open_position_at_end.entry.timestamp,
                          datetime(2026, 7, 22, 9, 30))


class RunReplayWithLadderExpansionTests(unittest.TestCase):
    """A CE entry at the LOWEST captured strike (23850) whose Mapped Stop
    Loss requires a strike (23800) beyond the initial capture - Module 8
    must extend on demand rather than the trade being skipped, reproducing
    the exact real-data gap found this session."""

    def setUp(self) -> None:
        self.capture = _make_narrow_capture()
        self.mapping = build_premium_mapping(self.capture, strike_gap=50)

    def test_expands_ladder_and_completes_trade(self) -> None:
        strike = 23850
        ce_series = {strike: {
            datetime(2026, 7, 22, 9, 20): _c(40.0, 45.0, 35.0, 40.0),   # safe: high < 52.65
            datetime(2026, 7, 22, 9, 25): _c(55.0, 60.0, 50.0, 55.0),   # crosses 52.65 - entry
            datetime(2026, 7, 22, 9, 30): _c(58.0, 65.0, 55.0, 58.0),   # reaches target 63.65
        }}
        pe_series = {strike: {
            datetime(2026, 7, 22, 9, 20): _c(200.0, 210.0, 195.0, 200.0),
            datetime(2026, 7, 22, 9, 25): _c(200.0, 210.0, 195.0, 200.0),
            datetime(2026, 7, 22, 9, 30): _c(200.0, 210.0, 195.0, 200.0),
        }}

        result = run_replay(
            self.mapping, ce_series, pe_series,
            capture=self.capture, strike_gap=50, fetch_first_candle=_narrow_fetcher,
        )

        self.assertEqual(len(result.trades), 1)
        trade = result.trades[0]
        self.assertEqual(trade.entry, 52.65)
        self.assertEqual(trade.exit, 63.65)
        self.assertEqual(trade.reason, "TARGET")
        # The Mapped Stop Loss (42.60, from the expanded strike 23800) was
        # computed successfully even though 23800 was never in the
        # original capture - proof the expansion actually happened.
        self.assertEqual(trade.stop_loss, 42.60)

    def test_without_expansion_params_raises_as_before(self) -> None:
        # Backward compatibility: omitting capture/strike_gap/fetch_first_candle
        # preserves the exact pre-Module-8 behavior (propagates the error).
        strike = 23850
        ce_series = {strike: {
            datetime(2026, 7, 22, 9, 20): _c(40.0, 45.0, 35.0, 40.0),
            datetime(2026, 7, 22, 9, 25): _c(55.0, 60.0, 50.0, 55.0),
        }}
        pe_series = {strike: {
            datetime(2026, 7, 22, 9, 20): _c(200.0, 210.0, 195.0, 200.0),
            datetime(2026, 7, 22, 9, 25): _c(200.0, 210.0, 195.0, 200.0),
        }}
        with self.assertRaises(Exception):
            run_replay(self.mapping, ce_series, pe_series)


class LevelReuseIsBlockedTests(unittest.TestCase):
    """Reproduces the exact real-data bug found this session (2026-07-22
    trades 3 and 4 both entering at level 206.35, ce_high@24050, TOP/PE) -
    with Module 9 wired in, the second attempt must now be blocked."""

    _CE_SAFE = _c(90.0, 95.0, 85.0, 90.0)   # stays below both CE thresholds at 24050

    def setUp(self) -> None:
        self.mapping = _make_mapping()

    def test_second_entry_from_used_level_is_blocked(self) -> None:
        strike = 24050
        ce_series = {strike: {
            datetime(2026, 7, 22, 9, 20): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 25): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 30): self._CE_SAFE,
            datetime(2026, 7, 22, 9, 35): self._CE_SAFE,
        }}
        pe_series = {strike: {
            datetime(2026, 7, 22, 9, 20): _c(150.0, 155.0, 145.0, 150.0),   # safe baseline
            # Entry 1: PE crosses above 206.35 (ce_high@24050).
            datetime(2026, 7, 22, 9, 25): _c(200.0, 220.0, 200.0, 210.0),
            # Exit 1: PE falls to/through the Mapped Stop Loss (176.85).
            datetime(2026, 7, 22, 9, 30): _c(200.0, 205.0, 170.0, 175.0),
            # PE crosses back ABOVE 206.35 again - same level, same day.
            # Without Module 9 this would be a second, legitimate-looking
            # fresh cross; with it, the level is USED and must be skipped.
            datetime(2026, 7, 22, 9, 35): _c(180.0, 215.0, 178.0, 210.0),
        }}

        result = run_replay(self.mapping, ce_series, pe_series)

        self.assertEqual(len(result.trades), 1)   # only the first trade, not a second
        first = result.trades[0]
        self.assertEqual(first.entry, 206.35)
        self.assertEqual(first.exit, 176.85)
        self.assertEqual(first.reason, "STOP_LOSS")
        # No position re-opened at 09:35 despite the level being crossed
        # again - flat for the rest of the (short) replay.
        self.assertIsNone(result.open_position_at_end)


class FormatSummaryTests(unittest.TestCase):
    def test_no_trades_summary_does_not_error(self) -> None:
        strike = 24050
        mapping = _make_mapping()
        ce_series = {strike: {datetime(2026, 7, 22, 9, 20): _c(90.0, 95.0, 85.0, 90.0)}}
        pe_series = {strike: {datetime(2026, 7, 22, 9, 20): _c(150.0, 155.0, 145.0, 150.0)}}
        result = run_replay(mapping, ce_series, pe_series)
        text = format_summary(result)
        self.assertIn("(no trades)", text)
        self.assertIn("Win %:", text)


if __name__ == "__main__":
    unittest.main()

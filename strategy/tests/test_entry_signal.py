"""Unit tests for strategy.entry_signal (Module 3).

No network access required - PremiumMapping and Candle objects are
built directly in-memory.
"""

import unittest
from datetime import date, datetime

from strategy.level_capture import LevelCapture, StrikeLevels
from strategy.premium_mapping import build_premium_mapping
from strategy.entry_signal import (
    Candle,
    EntrySignalDetector,
    EntrySignalError,
    MappingAnchor,
    TradeSide,
    _raw_condition,
)


def _make_mapping() -> "PremiumMapping":
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


class RawConditionTests(unittest.TestCase):
    """Direct tests of the two-condition BUY rule, isolated from any
    particular strike's mapped levels - this is the core "both must
    confirm in the same candle, otherwise NO TRADE" rule."""

    def test_buy_ce_requires_both_conditions(self) -> None:
        ce_level, pe_level = 100.0, 200.0
        # Both conditions met: ce.high > 100, pe.low < 200.
        ce = Candle(90.0, 105.0, 90.0, 102.0)
        pe = Candle(210.0, 215.0, 195.0, 205.0)
        self.assertTrue(_raw_condition(ce, pe, ce_level, pe_level, TradeSide.CE))

    def test_buy_ce_fails_if_only_ce_condition_met(self) -> None:
        ce_level, pe_level = 100.0, 200.0
        ce = Candle(90.0, 105.0, 90.0, 102.0)      # ce.high (105) > 100: met
        pe = Candle(210.0, 215.0, 205.0, 208.0)    # pe.low (205) NOT < 200: not met
        self.assertFalse(_raw_condition(ce, pe, ce_level, pe_level, TradeSide.CE))

    def test_buy_ce_fails_if_only_pe_condition_met(self) -> None:
        ce_level, pe_level = 100.0, 200.0
        ce = Candle(90.0, 95.0, 85.0, 92.0)        # ce.high (95) NOT > 100: not met
        pe = Candle(210.0, 215.0, 195.0, 205.0)    # pe.low (195) < 200: met
        self.assertFalse(_raw_condition(ce, pe, ce_level, pe_level, TradeSide.CE))

    def test_buy_ce_fails_if_neither_condition_met(self) -> None:
        ce_level, pe_level = 100.0, 200.0
        ce = Candle(90.0, 95.0, 85.0, 92.0)
        pe = Candle(210.0, 215.0, 205.0, 208.0)
        self.assertFalse(_raw_condition(ce, pe, ce_level, pe_level, TradeSide.CE))

    def test_buy_pe_is_the_mirror(self) -> None:
        ce_level, pe_level = 100.0, 200.0
        # BUY PE: pe.high > pe_level AND ce.low < ce_level.
        ce = Candle(90.0, 95.0, 85.0, 92.0)        # ce.low (85) < 100: met
        pe = Candle(190.0, 210.0, 190.0, 205.0)    # pe.high (210) > 200: met
        self.assertTrue(_raw_condition(ce, pe, ce_level, pe_level, TradeSide.PE))

    def test_buy_pe_fails_if_only_one_condition_met(self) -> None:
        ce_level, pe_level = 100.0, 200.0
        ce = Candle(105.0, 110.0, 102.0, 108.0)     # ce.low (102) NOT < 100: not met
        pe = Candle(190.0, 210.0, 190.0, 205.0)     # pe.high (210) > 200: met
        self.assertFalse(_raw_condition(ce, pe, ce_level, pe_level, TradeSide.PE))


class CandleValidationTests(unittest.TestCase):
    def test_valid_candle_constructs(self) -> None:
        Candle(open=100.0, high=110.0, low=95.0, close=105.0)

    def test_high_below_low_raises(self) -> None:
        with self.assertRaises(EntrySignalError):
            Candle(open=100.0, high=90.0, low=95.0, close=92.0)

    def test_open_outside_range_raises(self) -> None:
        with self.assertRaises(EntrySignalError):
            Candle(open=200.0, high=110.0, low=95.0, close=105.0)

    def test_close_outside_range_raises(self) -> None:
        with self.assertRaises(EntrySignalError):
            Candle(open=100.0, high=110.0, low=95.0, close=200.0)


class EntrySignalDetectorTests(unittest.TestCase):
    """Reproduces the trader's own logged 2026-07-22 entries exactly:
    row 1 (PE @ strike 24050, TOP anchor) and row 3 (CE @ strike 24000,
    TOP anchor) - see the trade log discussed in this session."""

    def setUp(self) -> None:
        self.mapping = _make_mapping()
        self.detector = EntrySignalDetector(self.mapping)

    def test_0915_never_produces_a_signal_even_if_condition_holds(self) -> None:
        # The 09:15 candle IS the same candle Module 1 used to capture
        # strike 24000's own CE-High/PE-Low - so the raw condition is
        # structurally guaranteed true here regardless of real movement.
        # This test confirms it is still suppressed even though the raw
        # inequality genuinely holds (using the strike's own captured
        # first-candle values as the "crossing" candle).
        ce_candles = {24000: Candle(90.0, 238.75, 90.0, 200.0)}   # its own captured high
        pe_candles = {24000: Candle(200.0, 200.0, 94.40, 150.0)}  # its own captured low
        signals = self.detector.process_candle(datetime(2026, 7, 22, 9, 15), ce_candles, pe_candles)
        self.assertEqual(signals, [])

    def test_0920_can_still_fire_after_0915_suppressed(self) -> None:
        # Confirms suppression at 09:15 does not corrupt fresh-cross state
        # for later candles - a genuine fresh cross at 09:20 must still work.
        ce_candles_0915 = {24000: Candle(90.0, 90.0, 85.0, 88.0)}   # below threshold - no cross
        pe_candles_0915 = {24000: Candle(250.0, 250.0, 245.0, 248.0)}  # above threshold - no cross
        first = self.detector.process_candle(datetime(2026, 7, 22, 9, 15), ce_candles_0915, pe_candles_0915)
        self.assertEqual(first, [])

        ce_candles_0920 = {24000: Candle(90.0, 96.0, 90.0, 94.55)}     # now crosses fresh
        pe_candles_0920 = {24000: Candle(220.0, 220.0, 200.0, 210.0)}
        second = self.detector.process_candle(datetime(2026, 7, 22, 9, 20), ce_candles_0920, pe_candles_0920)
        self.assertEqual(len(second), 1)
        self.assertEqual(second[0].side, TradeSide.CE)

    def test_row1_pe_entry_at_strike_24050_top_anchor(self) -> None:
        # PE_WINS: pe.high > ce_high(24050)=206.35 AND ce.low < pe_low(24050)=114.00
        # CE's candle must stay entirely BELOW 114.00 (not straddle it) -
        # otherwise ce.high > 114.00 would also trip BUY CE's own condition
        # on the same shared threshold, since ce_level does double duty
        # (BUY CE checks ce.high > level, BUY PE checks ce.low < level).
        ce_candles = {24050: Candle(105.0, 110.0, 100.0, 105.0)}   # fully below 114.00
        pe_candles = {24050: Candle(200.0, 220.0, 200.0, 217.2)}   # high 220 > 206.35
        signals = self.detector.process_candle(datetime(2026, 7, 22, 9, 25), ce_candles, pe_candles)
        matching = [s for s in signals if s.strike == 24050 and s.anchor is MappingAnchor.TOP]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].side, TradeSide.PE)
        self.assertEqual(matching[0].ce_level, 114.00)   # top_ce_ladder = PE Low
        self.assertEqual(matching[0].pe_level, 206.35)   # top_pe_ladder = CE High

    def test_row3_ce_entry_at_strike_24000_top_anchor(self) -> None:
        # CE_WINS: ce.high > pe_low(24000)=94.40 AND pe.low < ce_high(24000)=238.75
        ce_candles = {24000: Candle(90.0, 96.0, 90.0, 94.55)}       # high 96 > 94.40 (TOP PE-Low)
        pe_candles = {24000: Candle(220.0, 220.0, 200.0, 210.0)}    # low 200 < 238.75 (TOP CE-High)
        signals = self.detector.process_candle(datetime(2026, 7, 22, 10, 50), ce_candles, pe_candles)
        matching = [s for s in signals if s.strike == 24000 and s.anchor is MappingAnchor.TOP]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].side, TradeSide.CE)
        self.assertEqual(matching[0].ce_level, 94.40)
        self.assertEqual(matching[0].pe_level, 238.75)


    def test_stale_condition_does_not_refire(self) -> None:
        # A condition already true on the PREVIOUS candle must not fire
        # again on this candle just because it's still true - fresh-cross
        # only.
        ce_candles = {24000: Candle(90.0, 96.0, 90.0, 94.55)}
        pe_candles = {24000: Candle(220.0, 220.0, 200.0, 210.0)}
        first = self.detector.process_candle(datetime(2026, 7, 22, 10, 50), ce_candles, pe_candles)
        self.assertTrue(any(s.strike == 24000 and s.side is TradeSide.CE for s in first))

        # Same condition holds again next candle - should NOT re-fire.
        second = self.detector.process_candle(datetime(2026, 7, 22, 10, 55), ce_candles, pe_candles)
        self.assertFalse(any(s.strike == 24000 and s.side is TradeSide.CE for s in second))

    def test_missing_candle_data_is_skipped_not_erroring(self) -> None:
        # Strike 24000 has no candle data at all this call - the detector
        # must skip it silently, not raise.
        ce_candles: dict = {}
        pe_candles: dict = {}
        signals = self.detector.process_candle(datetime(2026, 7, 22, 9, 25), ce_candles, pe_candles)
        self.assertEqual([s for s in signals if s.strike == 24000], [])


if __name__ == "__main__":
    unittest.main()

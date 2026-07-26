"""Unit tests for strategy.ladder_expansion (Module 8) and the additive
extend_capture()/extend_mapping() functions in Modules 1 and 2.

No network access required - fetches are stubbed via an in-memory table.
"""

import unittest
from datetime import date, datetime

from strategy.level_capture import (
    LevelCapture,
    LevelCaptureError,
    StrikeLevels,
    extend_capture,
)
from strategy.premium_mapping import PremiumMappingError, build_premium_mapping, extend_mapping
from strategy.entry_signal import EntrySignal, MappingAnchor, TradeSide
from strategy.ladder_expansion import LadderExpansionError, ensure_exit_levels


# Real 2026-07-22 data, but deliberately narrowed to a small range
# (23850-24300) so an entry at the edge strike (23850) has no lower rung -
# reproducing the exact real-data gap found in this session.
_NARROW_RAW = {
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
# The next strike beyond the edge (23800), needed to extend the TOP CE
# ladder's SL for an entry at 23850. Not part of the initial capture.
_EXTRA_STRIKE = {
    23800: (383.40, 324.00, 72.30, 42.60),
}


def _make_narrow_capture() -> LevelCapture:
    levels = {
        strike: StrikeLevels(strike=strike, ce_high=ce_h, ce_low=ce_l,
                              pe_high=pe_h, pe_low=pe_l)
        for strike, (ce_h, ce_l, pe_h, pe_l) in _NARROW_RAW.items()
    }
    return LevelCapture(
        session_date=date(2026, 7, 22), spot_open=24150.0, atm=24150,
        top_strike=24144.45, bottom_strike=24050.85, levels=levels,
    )


def _fetcher(strike: int, side: str):
    table = {**_NARROW_RAW, **_EXTRA_STRIKE}
    if strike not in table:
        raise RuntimeError(f"strike {strike} not available from broker (test stub)")
    ce_h, ce_l, pe_h, pe_l = table[strike]
    return (0.0, ce_h if side == "CE" else pe_h, ce_l if side == "CE" else pe_l, 0.0)


def _failing_fetcher(strike: int, side: str):
    raise RuntimeError("simulated broker outage")


class ExtendCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capture = _make_narrow_capture()

    def test_extends_with_new_strike(self) -> None:
        extended = extend_capture(self.capture, 23800, _fetcher)
        self.assertIn(23800, extended.levels)
        self.assertEqual(extended.levels[23800].ce_high, 383.40)

    def test_original_capture_is_untouched(self) -> None:
        extend_capture(self.capture, 23800, _fetcher)
        self.assertNotIn(23800, self.capture.levels)   # immutability preserved

    def test_already_present_strike_is_a_noop(self) -> None:
        result = extend_capture(self.capture, 23850, _fetcher)
        self.assertIs(result, self.capture)

    def test_fetch_failure_raises(self) -> None:
        with self.assertRaises(LevelCaptureError):
            extend_capture(self.capture, 23800, _failing_fetcher)


class ExtendMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capture = _make_narrow_capture()
        self.mapping = build_premium_mapping(self.capture, strike_gap=50)

    def test_extends_all_four_ladders(self) -> None:
        extended_capture = extend_capture(self.capture, 23800, _fetcher)
        extended_mapping = extend_mapping(self.mapping, extended_capture, 23800)
        self.assertEqual(extended_mapping.top_ce_ladder[23800], 42.60)     # PE Low
        self.assertEqual(extended_mapping.top_pe_ladder[23800], 383.40)   # CE High
        self.assertEqual(extended_mapping.bottom_ce_ladder[23800], 72.30) # PE High
        self.assertEqual(extended_mapping.bottom_pe_ladder[23800], 324.00) # CE Low

    def test_original_mapping_is_untouched(self) -> None:
        extended_capture = extend_capture(self.capture, 23800, _fetcher)
        extend_mapping(self.mapping, extended_capture, 23800)
        self.assertNotIn(23800, self.mapping.top_ce_ladder)

    def test_strike_not_in_capture_raises(self) -> None:
        with self.assertRaises(PremiumMappingError):
            extend_mapping(self.mapping, self.capture, 23800)   # capture NOT extended first


class EnsureExitLevelsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capture = _make_narrow_capture()
        self.mapping = build_premium_mapping(self.capture, strike_gap=50)

    def test_no_expansion_needed_for_interior_strike(self) -> None:
        # Real row 1: entry at 24050, well inside the narrow range.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=24050,
            side=TradeSide.PE, anchor=MappingAnchor.TOP,
            ce_level=114.00, pe_level=206.35,
        )
        levels, capture, mapping = ensure_exit_levels(entry, self.capture, self.mapping, 50, _fetcher)
        self.assertEqual(levels.target, 238.75)
        self.assertEqual(levels.stop_loss, 176.85)
        self.assertIs(capture, self.capture)     # untouched - no expansion happened
        self.assertIs(mapping, self.mapping)

    def test_expands_ladder_for_edge_strike_entry(self) -> None:
        # A PE entry at the LOWEST captured strike (23850) - its own TOP CE
        # ladder value (PE Low = 52.65) has no lower rung within the
        # narrow range, exactly reproducing the real-data gap found this
        # session.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=23850,
            side=TradeSide.CE, anchor=MappingAnchor.TOP,
            ce_level=52.65, pe_level=342.80,
        )
        levels, capture, mapping = ensure_exit_levels(entry, self.capture, self.mapping, 50, _fetcher)
        # Target = next value up from 52.65 in the TOP CE ladder (PE Low),
        # which is 63.65 at strike 23900 - already present, no expansion
        # needed on that side.
        self.assertEqual(levels.target, 63.65)
        # Stop Loss required extending to strike 23800 (PE Low = 42.60).
        self.assertEqual(levels.stop_loss, 42.60)
        self.assertIn(23800, capture.levels)
        self.assertIn(23800, mapping.top_ce_ladder)

    def test_never_skips_the_trade_just_raises_when_data_unavailable(self) -> None:
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=23850,
            side=TradeSide.CE, anchor=MappingAnchor.TOP,
            ce_level=52.65, pe_level=342.80,
        )
        with self.assertRaises(LadderExpansionError):
            ensure_exit_levels(entry, self.capture, self.mapping, 50, _failing_fetcher)


if __name__ == "__main__":
    unittest.main()

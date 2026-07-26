"""Unit tests for strategy.premium_mapping (Module 2).

No network access required - builds a Module 1 LevelCapture directly
from in-memory StrikeLevels rather than fetching anything.
"""

import unittest
from datetime import date

from strategy.level_capture import LevelCapture, StrikeLevels
from strategy.premium_mapping import (
    PremiumMappingError,
    build_premium_mapping,
)


def _make_capture() -> LevelCapture:
    """A LevelCapture matching the real 2026-07-22 data used elsewhere
    in this session, spanning strikes 23700-24600 (spot open ~24150)."""
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
    return LevelCapture(
        session_date=date(2026, 7, 22),
        spot_open=24150.0,
        atm=24150,
        top_strike=24150.0 + (154.00 - 159.55),   # 24144.45
        bottom_strike=24150.0 - (218.00 - 118.85),  # 24050.85
        levels=levels,
    )


class BuildPremiumMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capture = _make_capture()
        self.mapping = build_premium_mapping(self.capture, strike_gap=50)

    def test_top_and_bottom_anchors_rounded_correctly(self) -> None:
        # top_strike 24144.45 -> nearest 50 -> 24150
        # bottom_strike 24050.85 -> nearest 50 -> 24050
        self.assertEqual(self.mapping.top_strike_rounded, 24150)
        self.assertEqual(self.mapping.bottom_strike_rounded, 24050)

    def test_top_ce_ladder_is_pe_low(self) -> None:
        # TOP: CE chart <- PE Low
        self.assertEqual(self.mapping.top_ce_level(24050), 114.00)
        self.assertEqual(self.mapping.top_ce_level(24000), 94.40)

    def test_top_pe_ladder_is_ce_high(self) -> None:
        # TOP: PE chart <- CE High
        self.assertEqual(self.mapping.top_pe_level(24050), 206.35)
        self.assertEqual(self.mapping.top_pe_level(24000), 238.75)

    def test_bottom_ce_ladder_is_pe_high(self) -> None:
        # BOTTOM: CE chart <- PE High
        self.assertEqual(self.mapping.bottom_ce_level(24150), 218.00)

    def test_bottom_pe_ladder_is_ce_low(self) -> None:
        # BOTTOM: PE chart <- CE Low
        self.assertEqual(self.mapping.bottom_pe_level(24150), 118.85)

    def test_ladders_cover_every_captured_strike(self) -> None:
        self.assertEqual(set(self.mapping.top_ce_ladder), set(self.capture.levels))
        self.assertEqual(set(self.mapping.top_pe_ladder), set(self.capture.levels))
        self.assertEqual(set(self.mapping.bottom_ce_ladder), set(self.capture.levels))
        self.assertEqual(set(self.mapping.bottom_pe_ladder), set(self.capture.levels))

    def test_lookup_of_uncaptured_strike_raises(self) -> None:
        with self.assertRaises(PremiumMappingError):
            self.mapping.top_ce_level(99999)


class RealTradeReplayTests(unittest.TestCase):
    """Reproduces the trader's own logged 2026-07-22 trade rows exactly,
    using ONLY values read off the built PremiumMapping - see the row
    log discussed in this session (K=24050 entry 206.35/target 238.75/
    SL 176.85; K=24000 entry 94.40/target 114.00/SL 78.20)."""

    def setUp(self) -> None:
        self.mapping = build_premium_mapping(_make_capture(), strike_gap=50)

    def test_row1_pe_trade_levels(self) -> None:
        # PE_WINS at K=24050: entry = CE-High(24050) = 206.35 (TOP PE ladder)
        self.assertEqual(self.mapping.top_pe_level(24050), 206.35)

    def test_row3_ce_trade_levels(self) -> None:
        # CE_WINS at K=24000: entry = PE-Low(24000) = 94.40 (TOP CE ladder)
        self.assertEqual(self.mapping.top_ce_level(24000), 94.40)


if __name__ == "__main__":
    unittest.main()

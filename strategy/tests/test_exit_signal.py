"""Unit tests for strategy.exit_signal (Module 4).

No network access required - PremiumMapping and EntrySignal objects
are built directly in-memory. entry_signal.py is not modified by, or
required to change for, this module.
"""

import unittest
from datetime import date, datetime

from strategy.level_capture import LevelCapture, StrikeLevels
from strategy.premium_mapping import build_premium_mapping
from strategy.entry_signal import Candle, EntrySignal, MappingAnchor, TradeSide
from strategy.exit_signal import (
    CompetitorLevel,
    ExitLevels,
    ExitReason,
    ExitSignalError,
    check_exit,
    check_exit_with_competitor,
    compute_competitor_exit_level,
    compute_exit_levels,
)


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


class ComputeExitLevelsTests(unittest.TestCase):
    """Reproduces the trader's own logged 2026-07-22 target/SL exactly."""

    def setUp(self) -> None:
        self.mapping = _make_mapping()

    def test_row1_pe_entry_at_24050_top_anchor(self) -> None:
        # Real row: entry 206.35, target 238.75, SL 176.85.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=24050,
            side=TradeSide.PE, anchor=MappingAnchor.TOP,
            ce_level=114.00, pe_level=206.35,
        )
        levels = compute_exit_levels(entry, self.mapping)
        self.assertEqual(levels.target, 238.75)
        self.assertEqual(levels.stop_loss, 176.85)

    def test_row2_pe_entry_at_24000_top_anchor(self) -> None:
        # Real row: entry 238.75, target 269.95, SL 206.35.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 10, 20), strike=24000,
            side=TradeSide.PE, anchor=MappingAnchor.TOP,
            ce_level=94.40, pe_level=238.75,
        )
        levels = compute_exit_levels(entry, self.mapping)
        self.assertEqual(levels.target, 269.95)
        self.assertEqual(levels.stop_loss, 206.35)

    def test_row3_ce_entry_at_24000_top_anchor(self) -> None:
        # Real row: entry 94.40, target 114.00, SL 78.20.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 10, 50), strike=24000,
            side=TradeSide.CE, anchor=MappingAnchor.TOP,
            ce_level=94.40, pe_level=238.75,
        )
        levels = compute_exit_levels(entry, self.mapping)
        self.assertEqual(levels.target, 114.00)
        self.assertEqual(levels.stop_loss, 78.20)

    def test_lowest_rung_has_no_stop_loss_raises(self) -> None:
        # 23700 is the lowest PE-Low value in the TOP CE ladder - no
        # lower rung exists to serve as a Mapped Stop Loss.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=23700,
            side=TradeSide.CE, anchor=MappingAnchor.TOP,
            ce_level=28.15, pe_level=459.20,
        )
        with self.assertRaises(ExitSignalError):
            compute_exit_levels(entry, self.mapping)

    def test_highest_rung_has_no_target_raises(self) -> None:
        # 24300 is the highest CE-High value in the TOP PE ladder - no
        # higher rung exists to serve as a Target.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=24300,
            side=TradeSide.PE, anchor=MappingAnchor.TOP,
            ce_level=245.05, pe_level=92.50,
        )
        with self.assertRaises(ExitSignalError):
            compute_exit_levels(entry, self.mapping)


class ExitLevelsValidationTests(unittest.TestCase):
    def test_target_below_stop_loss_raises(self) -> None:
        with self.assertRaises(ExitSignalError):
            ExitLevels(target=100.0, stop_loss=150.0)

    def test_target_equal_stop_loss_raises(self) -> None:
        with self.assertRaises(ExitSignalError):
            ExitLevels(target=100.0, stop_loss=100.0)


class CheckExitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.levels = ExitLevels(target=238.75, stop_loss=176.85)
        self.ts = datetime(2026, 7, 22, 9, 45)

    def test_no_exit_when_neither_level_reached(self) -> None:
        candle = Candle(200.0, 210.0, 195.0, 205.0)
        self.assertIsNone(check_exit(self.ts, candle, self.levels))

    def test_target_hit(self) -> None:
        candle = Candle(230.0, 240.0, 225.0, 238.75)
        result = check_exit(self.ts, candle, self.levels)
        self.assertIsNotNone(result)
        self.assertEqual(result.reason, ExitReason.TARGET)
        self.assertEqual(result.exit_price, 238.75)

    def test_stop_loss_hit(self) -> None:
        candle = Candle(180.0, 182.0, 170.0, 178.0)
        result = check_exit(self.ts, candle, self.levels)
        self.assertIsNotNone(result)
        self.assertEqual(result.reason, ExitReason.STOP_LOSS)
        self.assertEqual(result.exit_price, 176.85)

    def test_target_priority_when_both_reached_same_candle(self) -> None:
        # A wide-range candle that spans both levels - Target must win,
        # per specification priority (checked first).
        candle = Candle(200.0, 240.0, 170.0, 230.0)
        result = check_exit(self.ts, candle, self.levels)
        self.assertEqual(result.reason, ExitReason.TARGET)


class ComputeCompetitorExitLevelTests(unittest.TestCase):
    """Version 1.1 - Competitor Exit threshold computation."""

    def setUp(self) -> None:
        self.mapping = _make_mapping()

    def test_ce_entry_uses_same_anchor_opposite_side_ladder(self) -> None:
        # CE entry at 24000 (TOP anchor): competitor ladder is TOP_PE
        # (ce_high). entry.pe_level=238.75 sits at strike 24000 in that
        # ladder; one rung below by value is 206.35 at strike 24050.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 10, 50), strike=24000,
            side=TradeSide.CE, anchor=MappingAnchor.TOP,
            ce_level=94.40, pe_level=238.75,
        )
        result = compute_competitor_exit_level(entry, self.mapping)
        self.assertEqual(result, CompetitorLevel(ladder_name="TOP_PE", source_strike=24050, trigger_level=206.35))

    def test_pe_entry_uses_same_anchor_opposite_side_ladder(self) -> None:
        # PE entry at 24050 (TOP anchor): competitor ladder is TOP_CE
        # (pe_low). entry.ce_level=114.00 sits at strike 24050 in that
        # ladder; one rung below by value is 94.40 at strike 24000.
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=24050,
            side=TradeSide.PE, anchor=MappingAnchor.TOP,
            ce_level=114.00, pe_level=206.35,
        )
        result = compute_competitor_exit_level(entry, self.mapping)
        self.assertEqual(result, CompetitorLevel(ladder_name="TOP_CE", source_strike=24000, trigger_level=94.40))

    def test_no_lower_rung_returns_none(self) -> None:
        # 24300's ce_high (92.50) is the lowest value in the TOP_PE
        # ladder - no lower rung exists, so Competitor Exit does not
        # apply to this trade (not an error).
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=24300,
            side=TradeSide.CE, anchor=MappingAnchor.TOP,
            ce_level=245.05, pe_level=92.50,
        )
        self.assertIsNone(compute_competitor_exit_level(entry, self.mapping))


class CheckExitWithCompetitorTests(unittest.TestCase):
    """Version 1.1 - Competitor Exit priority validation.

    Uses the CE@24000 TOP-anchor entry from ComputeExitLevelsTests
    (target=114.00, stop_loss=78.20) with its computed Competitor Exit
    threshold (trigger_level=206.35, from TOP_PE ladder, source_strike=24050).
    """

    def setUp(self) -> None:
        self.levels = ExitLevels(target=114.00, stop_loss=78.20)
        self.competitor = CompetitorLevel(ladder_name="TOP_PE", source_strike=24050, trigger_level=206.35)
        self.ts = datetime(2026, 7, 22, 9, 45)

    def test_competitor_exit_before_target(self) -> None:
        # Own candle would hit Target; competitor candle also touches
        # its trigger level - Competitor Exit must win.
        own_candle = Candle(100.0, 120.0, 95.0, 115.0)   # high 120 >= target 114.00
        competitor_candle = Candle(210.0, 212.0, 200.0, 205.0)  # low 200 <= 206.35
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertEqual(result.reason, ExitReason.COMPETITOR_EXIT)

    def test_competitor_exit_before_stop_loss(self) -> None:
        # Own candle would hit Stop Loss; competitor candle also
        # touches its trigger level - Competitor Exit must win.
        own_candle = Candle(90.0, 92.0, 75.0, 80.0)   # low 75 <= stop 78.20
        competitor_candle = Candle(210.0, 212.0, 200.0, 205.0)  # low 200 <= 206.35
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertEqual(result.reason, ExitReason.COMPETITOR_EXIT)

    def test_target_without_competitor_trigger(self) -> None:
        own_candle = Candle(100.0, 120.0, 95.0, 115.0)   # high 120 >= target 114.00
        competitor_candle = Candle(230.0, 235.0, 220.0, 225.0)  # low 220 > 206.35 - no trigger
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertEqual(result.reason, ExitReason.TARGET)
        self.assertEqual(result.exit_price, 114.00)

    def test_stop_loss_without_competitor_trigger(self) -> None:
        own_candle = Candle(90.0, 92.0, 75.0, 80.0)   # low 75 <= stop 78.20
        competitor_candle = Candle(230.0, 235.0, 220.0, 225.0)  # low 220 > 206.35 - no trigger
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertEqual(result.reason, ExitReason.STOP_LOSS)
        self.assertEqual(result.exit_price, 78.20)

    def test_simultaneous_competitor_and_target_prefers_competitor(self) -> None:
        # A wide-range own candle spans both Target and Stop Loss, and
        # the competitor also triggers - Competitor Exit still wins
        # over Target even when Target would itself have won the
        # own-side-only tie-break.
        own_candle = Candle(100.0, 130.0, 70.0, 100.0)  # covers both target and stop
        competitor_candle = Candle(210.0, 212.0, 200.0, 205.0)
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertEqual(result.reason, ExitReason.COMPETITOR_EXIT)

    def test_simultaneous_competitor_and_stop_prefers_competitor(self) -> None:
        own_candle = Candle(90.0, 92.0, 75.0, 80.0)  # only stop reachable
        competitor_candle = Candle(210.0, 212.0, 200.0, 205.0)
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertEqual(result.reason, ExitReason.COMPETITOR_EXIT)

    def test_no_competitor_candle_falls_back_to_target_stop_only(self) -> None:
        own_candle = Candle(100.0, 120.0, 95.0, 115.0)
        result = check_exit_with_competitor(self.ts, own_candle, None, self.levels, self.competitor)
        self.assertEqual(result.reason, ExitReason.TARGET)

    def test_no_competitor_level_falls_back_to_target_stop_only(self) -> None:
        own_candle = Candle(100.0, 120.0, 95.0, 115.0)
        competitor_candle = Candle(210.0, 212.0, 200.0, 205.0)
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, None)
        self.assertEqual(result.reason, ExitReason.TARGET)

    def test_competitor_exit_price_is_own_candle_open_not_close(self) -> None:
        own_candle = Candle(101.5, 120.0, 95.0, 115.0)  # open=101.5, close=115.0
        competitor_candle = Candle(210.0, 212.0, 200.0, 205.0)
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertEqual(result.exit_price, 101.5)
        self.assertEqual(result.pricing_method, "CANDLE_APPROXIMATION")

    def test_competitor_exit_records_all_required_fields(self) -> None:
        own_candle = Candle(101.5, 120.0, 95.0, 115.0)
        competitor_candle = Candle(210.0, 212.0, 200.0, 203.5)  # low=200.0 <= 206.35
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertEqual(result.competitor_ladder, "TOP_PE")
        self.assertEqual(result.competitor_strike, 24050)
        self.assertEqual(result.competitor_trigger_level, 206.35)
        self.assertEqual(result.competitor_trigger_price, 200.0)
        self.assertEqual(result.pricing_method, "CANDLE_APPROXIMATION")

    def test_no_exit_at_all_returns_none(self) -> None:
        own_candle = Candle(100.0, 105.0, 95.0, 100.0)
        competitor_candle = Candle(230.0, 235.0, 220.0, 225.0)
        result = check_exit_with_competitor(self.ts, own_candle, competitor_candle, self.levels, self.competitor)
        self.assertIsNone(result)

    def test_pre_1_1_check_exit_is_unchanged(self) -> None:
        # check_exit() itself (Target/Stop Loss only, no Competitor
        # Exit awareness) must still behave exactly as before Version
        # 1.1 - existing callers that never pass competitor data are
        # unaffected.
        own_candle = Candle(230.0, 240.0, 225.0, 238.75)
        levels = ExitLevels(target=238.75, stop_loss=176.85)
        result = check_exit(self.ts, own_candle, levels)
        self.assertEqual(result.reason, ExitReason.TARGET)
        self.assertIsNone(result.competitor_ladder)


if __name__ == "__main__":
    unittest.main()

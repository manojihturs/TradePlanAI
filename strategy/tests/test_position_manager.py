"""Unit tests for strategy.position_manager (Module 5).

No network access required. Neither entry_signal.py nor exit_signal.py
is modified by, or required to change for, this module.
"""

import unittest
from datetime import date, datetime

from strategy.level_capture import LevelCapture, StrikeLevels
from strategy.premium_mapping import build_premium_mapping
from strategy.entry_signal import Candle, EntrySignal, MappingAnchor, TradeSide
from strategy.exit_signal import ExitReason
from strategy.position_manager import (
    PositionManager,
    PositionManagerError,
    PositionState,
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


class PositionManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapping = _make_mapping()
        self.manager = PositionManager()
        # Real row 1: PE entry at strike 24050, TOP anchor - entry 206.35,
        # target 238.75, stop_loss 176.85.
        self.entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=24050,
            side=TradeSide.PE, anchor=MappingAnchor.TOP,
            ce_level=114.00, pe_level=206.35,
        )

    def test_starts_flat(self) -> None:
        self.assertEqual(self.manager.state, PositionState.FLAT)
        self.assertTrue(self.manager.is_flat)
        self.assertFalse(self.manager.is_open)
        self.assertIsNone(self.manager.current_position)

    def test_open_transitions_to_open(self) -> None:
        position = self.manager.open(self.entry, self.mapping)
        self.assertEqual(self.manager.state, PositionState.OPEN)
        self.assertTrue(self.manager.is_open)
        self.assertIs(self.manager.current_position, position)
        self.assertEqual(position.exit_levels.target, 238.75)
        self.assertEqual(position.exit_levels.stop_loss, 176.85)

    def test_cannot_open_while_already_open(self) -> None:
        self.manager.open(self.entry, self.mapping)
        with self.assertRaises(PositionManagerError):
            self.manager.open(self.entry, self.mapping)

    def test_process_candle_while_flat_is_a_noop(self) -> None:
        candle = Candle(200.0, 250.0, 190.0, 240.0)
        result = self.manager.process_candle(datetime(2026, 7, 22, 9, 45), candle)
        self.assertIsNone(result)
        self.assertTrue(self.manager.is_flat)

    def test_process_candle_no_exit_stays_open(self) -> None:
        self.manager.open(self.entry, self.mapping)
        candle = Candle(200.0, 210.0, 195.0, 205.0)   # neither target nor SL reached
        result = self.manager.process_candle(datetime(2026, 7, 22, 9, 30), candle)
        self.assertIsNone(result)
        self.assertTrue(self.manager.is_open)

    def test_target_hit_closes_position(self) -> None:
        self.manager.open(self.entry, self.mapping)
        candle = Candle(230.0, 240.0, 225.0, 238.75)   # real row 1: exit @ 09:45, target 238.75
        closed = self.manager.process_candle(datetime(2026, 7, 22, 9, 45), candle)
        self.assertIsNotNone(closed)
        self.assertEqual(closed.entry, self.entry)
        self.assertEqual(closed.exit.reason, ExitReason.TARGET)
        self.assertEqual(closed.exit.exit_price, 238.75)
        self.assertTrue(self.manager.is_flat)

    def test_stop_loss_hit_closes_position(self) -> None:
        self.manager.open(self.entry, self.mapping)
        candle = Candle(180.0, 182.0, 170.0, 178.0)   # below stop_loss 176.85
        closed = self.manager.process_candle(datetime(2026, 7, 22, 9, 30), candle)
        self.assertIsNotNone(closed)
        self.assertEqual(closed.exit.reason, ExitReason.STOP_LOSS)
        self.assertEqual(closed.exit.exit_price, 176.85)
        self.assertTrue(self.manager.is_flat)

    def test_can_reopen_after_close(self) -> None:
        self.manager.open(self.entry, self.mapping)
        candle = Candle(230.0, 240.0, 225.0, 238.75)
        self.manager.process_candle(datetime(2026, 7, 22, 9, 45), candle)
        self.assertTrue(self.manager.is_flat)

        second_entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 10, 20), strike=24000,
            side=TradeSide.PE, anchor=MappingAnchor.TOP,
            ce_level=94.40, pe_level=238.75,
        )
        position = self.manager.open(second_entry, self.mapping)
        self.assertTrue(self.manager.is_open)
        self.assertEqual(position.exit_levels.target, 269.95)
        self.assertEqual(position.exit_levels.stop_loss, 206.35)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for strategy.level_state_manager (Module 9).

No network access required, no dependency on the strategy engine
(Modules 3-8) beyond the types needed to build test fixtures.
"""

import unittest
from datetime import date, datetime

from strategy.level_capture import LevelCapture, StrikeLevels
from strategy.premium_mapping import build_premium_mapping
from strategy.entry_signal import EntrySignal, MappingAnchor, TradeSide
from strategy.level_state_manager import (
    LevelKey,
    LevelState,
    LevelStateError,
    LevelStateManager,
    level_key_from_entry,
)


def _make_mapping():
    raw = {
        24000: (238.75, 192.00, 141.65, 94.40),
        24050: (206.35, 165.50, 164.65, 114.00),
        24100: (176.85, 140.75, 190.00, 135.05),
        24150: (154.00, 118.85, 218.00, 159.55),
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


class LevelKeyIdentityTests(unittest.TestCase):
    """The state belongs to the LEVEL, not the strike or the value -
    four different keys can exist at one strike, and are independent."""

    def test_same_strike_different_anchor_are_different_keys(self) -> None:
        k1 = LevelKey(24050, MappingAnchor.TOP, TradeSide.PE)
        k2 = LevelKey(24050, MappingAnchor.BOTTOM, TradeSide.PE)
        self.assertNotEqual(k1, k2)

    def test_same_strike_different_side_are_different_keys(self) -> None:
        k1 = LevelKey(24050, MappingAnchor.TOP, TradeSide.CE)
        k2 = LevelKey(24050, MappingAnchor.TOP, TradeSide.PE)
        self.assertNotEqual(k1, k2)

    def test_level_key_from_entry(self) -> None:
        entry = EntrySignal(
            timestamp=datetime(2026, 7, 22, 9, 25), strike=24050,
            side=TradeSide.PE, anchor=MappingAnchor.TOP,
            ce_level=114.00, pe_level=206.35,
        )
        key = level_key_from_entry(entry)
        self.assertEqual(key, LevelKey(24050, MappingAnchor.TOP, TradeSide.PE))


class LevelStateManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapping = _make_mapping()
        self.manager = LevelStateManager()
        self.key = LevelKey(24050, MappingAnchor.TOP, TradeSide.PE)

    def test_lookup_before_initialize_raises(self) -> None:
        with self.assertRaises(LevelStateError):
            self.manager.get_state(self.key)

    def test_initialize_day_sets_every_level_active(self) -> None:
        self.manager.initialize_day(self.mapping)
        self.assertEqual(self.manager.get_state(self.key), LevelState.ACTIVE)
        self.assertTrue(self.manager.can_open(self.key))

    def test_initialize_day_covers_all_four_ladders_per_strike(self) -> None:
        self.manager.initialize_day(self.mapping)
        for anchor in (MappingAnchor.TOP, MappingAnchor.BOTTOM):
            for side in (TradeSide.CE, TradeSide.PE):
                self.assertEqual(
                    self.manager.get_state(LevelKey(24050, anchor, side)), LevelState.ACTIVE
                )

    def test_mark_used_transitions_from_active(self) -> None:
        self.manager.initialize_day(self.mapping)
        self.manager.mark_used(self.key)
        self.assertEqual(self.manager.get_state(self.key), LevelState.USED)
        self.assertFalse(self.manager.can_open(self.key))

    def test_mark_used_on_non_active_level_raises(self) -> None:
        self.manager.initialize_day(self.mapping)
        self.manager.mark_used(self.key)
        with self.assertRaises(LevelStateError):
            self.manager.mark_used(self.key)   # already USED, not ACTIVE

    def test_used_level_cannot_reactivate_intraday(self) -> None:
        self.manager.initialize_day(self.mapping)
        self.manager.mark_used(self.key)
        # No method exists to move USED -> ACTIVE except a new day's
        # initialize_day - confirm the state simply stays USED over time.
        self.assertEqual(self.manager.get_state(self.key), LevelState.USED)
        self.assertEqual(self.manager.get_state(self.key), LevelState.USED)

    def test_new_trading_day_discards_previous_state(self) -> None:
        self.manager.initialize_day(self.mapping)
        self.manager.mark_used(self.key)
        self.assertEqual(self.manager.get_state(self.key), LevelState.USED)

        # Next day's map - even if it happens to produce the SAME LevelKey
        # (same strike/anchor/side), it must start ACTIVE again.
        self.manager.initialize_day(self.mapping)
        self.assertEqual(self.manager.get_state(self.key), LevelState.ACTIVE)

    def test_register_level_adds_new_level_as_active(self) -> None:
        self.manager.initialize_day(self.mapping)
        expansion_key = LevelKey(23950, MappingAnchor.TOP, TradeSide.CE)
        with self.assertRaises(LevelStateError):
            self.manager.get_state(expansion_key)   # not part of the original map
        self.manager.register_level(expansion_key)
        self.assertEqual(self.manager.get_state(expansion_key), LevelState.ACTIVE)

    def test_register_level_does_not_reset_existing_level(self) -> None:
        self.manager.initialize_day(self.mapping)
        self.manager.mark_used(self.key)
        self.manager.register_level(self.key)   # already tracked - must be a no-op
        self.assertEqual(self.manager.get_state(self.key), LevelState.USED)

    def test_disable_sets_disabled_state(self) -> None:
        self.manager.initialize_day(self.mapping)
        self.manager.disable(self.key)
        self.assertEqual(self.manager.get_state(self.key), LevelState.DISABLED)
        self.assertFalse(self.manager.can_open(self.key))


if __name__ == "__main__":
    unittest.main()

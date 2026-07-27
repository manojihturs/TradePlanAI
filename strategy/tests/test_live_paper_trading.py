"""Unit tests for strategy.live_paper_trading (Module 11).

No network access required. Modules 1-9 used unmodified.
"""

import unittest
from datetime import date, datetime

from strategy.level_capture import LevelCapture, StrikeLevels
from strategy.premium_mapping import build_premium_mapping
from strategy.entry_signal import Candle
from strategy.live_paper_trading import CapitalTracker, LivePaperTradingEngine, LivePaperTradingError

STRIKE_GAP = 50
_RAW = {
    23850: (342.80, 288.00, 86.50, 52.65), 23900: (310.00, 253.80, 102.65, 63.65),
    23950: (269.95, 221.85, 120.85, 78.20), 24000: (238.75, 192.00, 141.65, 94.40),
    24050: (206.35, 165.50, 164.65, 114.00), 24100: (176.85, 140.75, 190.00, 135.05),
    24150: (154.00, 118.85, 218.00, 159.55), 24200: (133.00, 99.10, 248.40, 186.05),
    24250: (106.45, 81.70, 280.65, 215.05), 24300: (92.50, 66.80, 315.40, 245.05),
    24350: (76.00, 53.65, 352.35, 280.00), 24400: (59.75, 43.05, 391.65, 320.35),
    24450: (49.60, 34.20, 433.20, 357.55),
}
_CE_SAFE = Candle(90.0, 95.0, 85.0, 90.0)
_PE_SAFE = Candle(150.0, 155.0, 145.0, 150.0)


def _fetcher(strike, side):
    ce_h, ce_l, pe_h, pe_l = _RAW[strike]
    return (0.0, ce_h if side == "CE" else pe_h, ce_l if side == "CE" else pe_l, 0.0)


def _make_capture_and_mapping():
    levels = {s: StrikeLevels(strike=s, ce_high=v[0], ce_low=v[1], pe_high=v[2], pe_low=v[3])
              for s, v in _RAW.items()}
    capture = LevelCapture(session_date=date(2026, 7, 27), spot_open=24150.0, atm=24150,
                            top_strike=24144.45, bottom_strike=24050.85, levels=levels)
    return capture, build_premium_mapping(capture, strike_gap=STRIKE_GAP)


class CapitalTrackerTests(unittest.TestCase):
    def test_starts_with_full_capital(self):
        c = CapitalTracker(initial_capital=50000.0)
        self.assertEqual(c.available_capital, 50000.0)
        self.assertEqual(c.used_capital, 0.0)

    def test_reserve_and_release_profit(self):
        c = CapitalTracker(initial_capital=50000.0, lot_size=65)
        c.reserve_for_entry(100.0)
        self.assertAlmostEqual(c.available_capital, 50000.0 - 100.0 * 65)
        self.assertAlmostEqual(c.used_capital, 100.0 * 65)
        pnl = c.release_on_exit(100.0, 120.0)
        self.assertAlmostEqual(pnl, 20.0 * 65)
        self.assertAlmostEqual(c.available_capital, 50000.0 + 20.0 * 65)
        self.assertAlmostEqual(c.running_pnl, 20.0 * 65)
        self.assertEqual(c.used_capital, 0.0)

    def test_insufficient_capital_raises(self):
        c = CapitalTracker(initial_capital=1000.0, lot_size=65)
        with self.assertRaises(LivePaperTradingError):
            c.reserve_for_entry(100.0)   # 100*65=6500 > 1000

    def test_drawdown_tracked_after_loss(self):
        c = CapitalTracker(initial_capital=50000.0, lot_size=65)
        c.reserve_for_entry(100.0); c.release_on_exit(100.0, 120.0)   # +profit, peak set
        c.reserve_for_entry(100.0); c.release_on_exit(100.0, 90.0)    # -loss
        self.assertGreater(c.max_drawdown, 0)


class LivePaperTradingEngineTests(unittest.TestCase):
    def setUp(self):
        self.capture, self.mapping = _make_capture_and_mapping()
        self.engine = LivePaperTradingEngine(
            session_date=date(2026, 7, 27), capture=self.capture, mapping=self.mapping,
            strike_gap=STRIKE_GAP, fetch_first_candle=_fetcher,
            capital=CapitalTracker(initial_capital=50000.0),
        )

    def test_full_trade_lifecycle_updates_capital_and_records(self):
        strike = 24050
        # 09:20 baseline, 09:25 fresh PE cross, 09:45 target hit (real row 1 numbers)
        self.engine.on_candle_close(datetime(2026, 7, 27, 9, 20),
                                     {strike: _CE_SAFE}, {strike: _PE_SAFE})
        self.engine.on_candle_close(datetime(2026, 7, 27, 9, 25),
                                     {strike: _CE_SAFE}, {strike: Candle(200.0, 220.0, 200.0, 217.2)})
        self.assertEqual(self.engine.manager.is_open, True)
        self.assertEqual(len(self.engine.trade_records), 1)
        self.assertIsNone(self.engine.trade_records[0].exit_time)

        self.engine.on_candle_close(datetime(2026, 7, 27, 9, 45),
                                     {strike: _CE_SAFE}, {strike: Candle(233.0, 240.0, 230.0, 236.0)})
        self.assertTrue(self.engine.manager.is_flat)
        self.assertEqual(len(self.engine.trade_records), 1)
        record = self.engine.trade_records[0]
        self.assertEqual(record.exit_reason, "TARGET")
        self.assertAlmostEqual(record.entry_premium, 206.35)
        self.assertAlmostEqual(record.exit_premium, 238.75)
        self.assertGreater(self.engine.capital.running_pnl, 0)

    def test_dashboard_snapshot_reflects_state(self):
        snap = self.engine.dashboard_snapshot(datetime(2026, 7, 27, 9, 20), 24150.0)
        self.assertEqual(snap.top_strike, self.mapping.top_strike_rounded)
        self.assertEqual(snap.todays_trades, 0)
        self.assertIsNone(snap.current_open_trade)

    def test_end_of_day_summary_does_not_error(self):
        text = self.engine.end_of_day_summary()
        self.assertIn("2026-07-27", text)


if __name__ == "__main__":
    unittest.main()

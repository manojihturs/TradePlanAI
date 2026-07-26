"""Unit tests for strategy.level_capture (Module 1).

No network access required - all data fetching is stubbed via a fake
FirstCandleFetcher, per the module's dependency-injection design.
"""

import unittest
from datetime import date

from strategy.level_capture import (
    LevelCaptureError,
    StrikeLevels,
    compute_atm_strike,
    compute_bottom_strike,
    compute_top_strike,
    generate_strike_range,
    capture_levels,
)


class ComputeAtmStrikeTests(unittest.TestCase):
    def test_rounds_to_nearest_strike(self) -> None:
        self.assertEqual(compute_atm_strike(24132.0, 50), 24150)
        self.assertEqual(compute_atm_strike(24124.9, 50), 24100)

    def test_exact_strike_unchanged(self) -> None:
        self.assertEqual(compute_atm_strike(24150.0, 50), 24150)

    def test_rejects_non_positive_gap(self) -> None:
        with self.assertRaises(LevelCaptureError):
            compute_atm_strike(24150.0, 0)


class ComputeTopBottomStrikeTests(unittest.TestCase):
    def test_top_strike_matches_worked_example(self) -> None:
        # Real example verified against the trader's own spreadsheet:
        # ATM 23900, CE High 158.95, PE Low 125.65 -> Top 23933.30
        top = compute_top_strike(spot_open=23900.0, ce_high_atm=158.95, pe_low_atm=125.65)
        self.assertAlmostEqual(top, 23933.30, places=2)

    def test_bottom_strike_matches_worked_example(self) -> None:
        # Same session: PE High 165, CE Low 129.85 -> Bottom 23864.85
        bottom = compute_bottom_strike(spot_open=23900.0, pe_high_atm=165.0, ce_low_atm=129.85)
        self.assertAlmostEqual(bottom, 23864.85, places=2)

    def test_top_and_bottom_are_not_rounded(self) -> None:
        top = compute_top_strike(spot_open=23900.0, ce_high_atm=158.95, pe_low_atm=125.65)
        self.assertNotEqual(top, round(top / 50) * 50)


class GenerateStrikeRangeTests(unittest.TestCase):
    def test_generates_atm_plus_minus_n(self) -> None:
        strikes = generate_strike_range(atm=24150, strike_gap=50, num_strikes=6)
        self.assertEqual(strikes, tuple(range(23850, 24451, 50)))
        self.assertIn(24150, strikes)
        self.assertEqual(len(strikes), 13)

    def test_zero_strikes_returns_only_atm(self) -> None:
        self.assertEqual(generate_strike_range(24150, 50, 0), (24150,))

    def test_rejects_negative_num_strikes(self) -> None:
        with self.assertRaises(LevelCaptureError):
            generate_strike_range(24150, 50, -1)


class StrikeLevelsValidationTests(unittest.TestCase):
    def test_valid_levels_construct_cleanly(self) -> None:
        levels = StrikeLevels(strike=24150, ce_high=154.0, ce_low=118.85,
                               pe_high=218.0, pe_low=159.55)
        self.assertEqual(levels.strike, 24150)

    def test_ce_high_below_ce_low_raises(self) -> None:
        with self.assertRaises(LevelCaptureError):
            StrikeLevels(strike=24150, ce_high=100.0, ce_low=200.0,
                         pe_high=218.0, pe_low=159.55)

    def test_pe_high_below_pe_low_raises(self) -> None:
        with self.assertRaises(LevelCaptureError):
            StrikeLevels(strike=24150, ce_high=154.0, ce_low=118.85,
                         pe_high=100.0, pe_low=200.0)

    def test_frozen_instance_is_immutable(self) -> None:
        levels = StrikeLevels(strike=24150, ce_high=154.0, ce_low=118.85,
                               pe_high=218.0, pe_low=159.55)
        with self.assertRaises(Exception):
            levels.ce_high = 999.0  # type: ignore[misc]


class CaptureLevelsTests(unittest.TestCase):
    """End-to-end test of the orchestration function with a stub fetcher."""

    def _make_fetcher(self, table):
        """table: {(strike, side): (open, high, low, close)}"""
        def fetch(strike: int, side: str):
            return table[(strike, side)]
        return fetch

    def test_full_capture_matches_worked_example(self) -> None:
        # 2026-07-23 real data: ATM 23900, strike_gap 50, num_strikes 6.
        table = {}
        for strike in generate_strike_range(23900, 50, 6):
            # Arbitrary but internally-consistent placeholder levels for
            # every strike except ATM, which uses the real numbers the
            # Top/Bottom formulas are checked against.
            table[(strike, "CE")] = (100.0, 200.0, 90.0, 150.0)
            table[(strike, "PE")] = (100.0, 200.0, 90.0, 150.0)
        table[(23900, "CE")] = (140.0, 158.95, 129.85, 150.0)
        table[(23900, "PE")] = (140.0, 165.0, 125.65, 150.0)

        result = capture_levels(
            session_date=date(2026, 7, 23),
            spot_open=23900.0,
            strike_gap=50,
            num_strikes=6,
            fetch_first_candle=self._make_fetcher(table),
        )

        self.assertEqual(result.atm, 23900)
        self.assertAlmostEqual(result.top_strike, 23933.30, places=2)
        self.assertAlmostEqual(result.bottom_strike, 23864.85, places=2)
        self.assertEqual(len(result.levels), 13)
        self.assertEqual(result.get_levels(23900).ce_high, 158.95)

    def test_missing_strike_raises_lookup_error(self) -> None:
        table = {}
        for strike in generate_strike_range(23900, 50, 6):
            table[(strike, "CE")] = (100.0, 200.0, 90.0, 150.0)
            table[(strike, "PE")] = (100.0, 200.0, 90.0, 150.0)

        result = capture_levels(
            session_date=date(2026, 7, 23),
            spot_open=23900.0,
            strike_gap=50,
            num_strikes=6,
            fetch_first_candle=self._make_fetcher(table),
        )
        with self.assertRaises(LevelCaptureError):
            result.get_levels(99999)

    def test_fetch_failure_raises_level_capture_error(self) -> None:
        def failing_fetch(strike: int, side: str):
            raise ConnectionError("simulated network failure")

        with self.assertRaises(LevelCaptureError):
            capture_levels(
                session_date=date(2026, 7, 23),
                spot_open=23900.0,
                strike_gap=50,
                num_strikes=6,
                fetch_first_candle=failing_fetch,
            )


if __name__ == "__main__":
    unittest.main()

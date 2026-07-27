"""Unit tests for the postmarket package's pure-logic modules.

No network or file I/O - builds SessionData directly in memory.
"""

import unittest
from datetime import date, datetime

from postmarket.data_sources import (
    LevelUsageRecord, RejectedSignalRecord, SessionData, TradeRecord,
)
from postmarket.data_health import DataHealthReport, ReconnectEvent, build_data_health_report
from postmarket.health_score import compute_health_score
from postmarket.signal_review import build_signal_review
from postmarket.strategy_validation import build_strategy_validation
from postmarket.trade_review import BOUNDARY_DISTANCE_THRESHOLD, build_trade_review


def _session(trades=None, rejected=None, level_usage=None, atm=23950, log_lines=None):
    return SessionData(
        session_date=date(2026, 7, 28), xlsx_path=None, log_path=None, atm=atm,
        daily_summary={}, trades=trades or [], rejected_signals=rejected or [],
        level_usage=level_usage or [], log_lines=log_lines or [],
    )


def _trade(strike, side="CE", entry=100.0, target=120.0, stop=80.0, pnl=200.0,
           entry_time=datetime(2026, 7, 28, 9, 25), exit_time=datetime(2026, 7, 28, 9, 45)):
    return TradeRecord(
        strike=strike, side=side, entry_time=entry_time, entry_premium=entry,
        target=target, stop_loss=stop, trailing_stop_loss=stop, exit_time=exit_time,
        exit_premium=target, exit_reason="TARGET", pnl_rupees=pnl,
    )


class TradeReviewTests(unittest.TestCase):
    def test_distance_computed_from_atm(self):
        session = _session(trades=[_trade(23950)], atm=23950)
        rows = build_trade_review(session)
        self.assertEqual(rows[0].distance_from_atm, 0)
        self.assertFalse(rows[0].flagged_boundary)

    def test_boundary_strike_flagged(self):
        session = _session(trades=[_trade(23650)], atm=23950)  # distance 6
        rows = build_trade_review(session)
        self.assertEqual(rows[0].distance_from_atm, 6)
        self.assertGreaterEqual(rows[0].distance_from_atm, BOUNDARY_DISTANCE_THRESHOLD)
        self.assertTrue(rows[0].flagged_boundary)

    def test_missing_atm_yields_unknown_distance(self):
        session = _session(trades=[_trade(23950)], atm=None)
        rows = build_trade_review(session)
        self.assertIsNone(rows[0].distance_from_atm)
        self.assertFalse(rows[0].flagged_boundary)


class SignalReviewTests(unittest.TestCase):
    def test_counts_and_distribution(self):
        rejected = [
            RejectedSignalRecord(datetime(2026, 7, 28, 9, 25), 23950, "CE", "already in position"),
            RejectedSignalRecord(datetime(2026, 7, 28, 9, 30), 23900, "PE", "level already completed"),
        ]
        summary = build_signal_review(_session(rejected=rejected, atm=23950))
        self.assertEqual(summary.total_rejected, 2)
        self.assertEqual(summary.reason_counts["already in position"], 1)
        self.assertEqual(summary.distance_distribution["0"], 1)
        self.assertEqual(summary.distance_distribution["1"], 1)

    def test_repeated_pattern_detected(self):
        rejected = [
            RejectedSignalRecord(datetime(2026, 7, 28, 9, 25), 23650, "CE", "level already completed")
            for _ in range(3)
        ]
        summary = build_signal_review(_session(rejected=rejected))
        self.assertEqual(len(summary.repeated_patterns), 1)
        self.assertEqual(summary.repeated_patterns[0][3], 3)


class StrategyValidationTests(unittest.TestCase):
    def test_no_findings_for_clean_session(self):
        session = _session(
            trades=[_trade(23950, entry=100.0, target=120.0, stop=80.0)],
            level_usage=[LevelUsageRecord(23950, "TOP", "CE", "USED")],
        )
        findings = build_strategy_validation(session)
        self.assertEqual(findings, [])

    def test_boundary_strike_flagged_as_warning(self):
        session = _session(trades=[_trade(23650, entry=100.0, target=120.0, stop=80.0)], atm=23950)
        findings = build_strategy_validation(session)
        categories = [f.category for f in findings]
        self.assertIn("boundary_strike_trade", categories)

    def test_scale_asymmetry_flagged(self):
        # up_gap=100, down_gap=5 -> ratio 20x
        session = _session(trades=[_trade(23950, entry=100.0, target=200.0, stop=95.0)], atm=23950)
        findings = build_strategy_validation(session)
        categories = [f.category for f in findings]
        self.assertIn("premium_scale_anomaly", categories)

    def test_duplicate_trade_flagged(self):
        t = _trade(23950)
        session = _session(trades=[t, t])
        findings = build_strategy_validation(session)
        categories = [f.category for f in findings]
        self.assertIn("duplicate_trade", categories)

    def test_unexpected_level_state_flagged(self):
        session = _session(level_usage=[LevelUsageRecord(23950, "TOP", "CE", "CORRUPTED")])
        findings = build_strategy_validation(session)
        categories = [f.category for f in findings]
        self.assertIn("unexpected_level_state", categories)


class DataHealthTests(unittest.TestCase):
    def test_no_reconnects_when_log_clean(self):
        report = build_data_health_report(_session(log_lines=[
            "2026-07-28 09:20:00,000 [INFO] DASHBOARD time=09:20:00 spot=None",
        ]))
        self.assertEqual(report.reconnect_events, [])
        self.assertTrue(report.recovered_all)

    def test_reconnect_detected_and_recovery_measured(self):
        lines = [
            "2026-07-28 09:20:00,000 [ERROR] Poll iteration failed (continuing): timeout",
            "2026-07-28 09:20:25,000 [INFO] DASHBOARD time=09:20:25 spot=None",
        ]
        report = build_data_health_report(_session(log_lines=lines), poll_seconds=20)
        self.assertEqual(len(report.reconnect_events), 1)
        self.assertAlmostEqual(report.reconnect_events[0].seconds_to_next_success, 25.0)
        self.assertFalse(report.reconnect_events[0].likely_missed_candles)

    def test_long_gap_flags_likely_missed_candles(self):
        lines = [
            "2026-07-28 09:20:00,000 [ERROR] Poll iteration failed (continuing): timeout",
            "2026-07-28 09:25:00,000 [INFO] DASHBOARD time=09:25:00 spot=None",
        ]
        report = build_data_health_report(_session(log_lines=lines), poll_seconds=20)
        self.assertTrue(report.reconnect_events[0].likely_missed_candles)


class HealthScoreTests(unittest.TestCase):
    def test_all_pass_when_clean(self):
        score = compute_health_score(DataHealthReport([], True), [])
        self.assertEqual(score.overall_status, "PASS")

    def test_review_on_recovered_reconnect(self):
        events = [ReconnectEvent(None, "timeout", 25.0, False)]
        score = compute_health_score(DataHealthReport(events, True), [])
        self.assertEqual(score.data_feed_health, "REVIEW")
        self.assertEqual(score.overall_status, "REVIEW")

    def test_fail_on_critical_strategy_finding(self):
        from postmarket.strategy_validation import ValidationFinding
        findings = [ValidationFinding("duplicate_trade", "dup", "CRITICAL")]
        score = compute_health_score(DataHealthReport([], True), findings)
        self.assertEqual(score.strategy_health, "FAIL")
        self.assertEqual(score.overall_status, "FAIL")


if __name__ == "__main__":
    unittest.main()

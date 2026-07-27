"""Tests for the rules.categories re-export."""

from __future__ import annotations

from trading_engine.domain.rule_reference import RuleCategory as DomainRuleCategory
from trading_engine.rules.categories import RuleCategory


class TestReExport:
    def test_is_the_same_object_as_the_domain_enum(self) -> None:
        # Not a copy - a re-export. Two separate enums would risk
        # silent drift between trading_engine.domain and
        # trading_engine.rules.
        assert RuleCategory is DomainRuleCategory

    def test_member_set_matches_the_bible_taxonomy(self) -> None:
        expected = {
            "CORE",
            "PHILOSOPHY",
            "WEEKLY_FUTURE",
            "FIRST_CANDLE",
            "STRIKE",
            "TREND",
            "STATE",
            "CONTROL_ZONE",
            "FLOW",
            "OPPONENT",
            "ENTRY",
            "EXIT",
            "REVERSAL",
            "DECAY",
            "PREMIUM",
            "RISK",
            "VALIDATION",
            "MATH",
            "UNKNOWN",
        }
        assert {member.name for member in RuleCategory} == expected

    def test_strike_member_accessible_via_rules_package(self) -> None:
        assert RuleCategory.STRIKE.name == "STRIKE"

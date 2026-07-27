"""Shared fixtures for the Strategy Engine Skeleton test suite.

Reuses the Rule Framework test doubles from ``tests/rules/conftest.py``
(``FakeRule``, ``make_rule_reference``) and adds engine-specific test
doubles - rules that raise, for exercising the Pipeline's stopping
behaviour. No trading-meaningful logic anywhere in this module.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.rule_reference import RuleReference
from trading_engine.domain.session_state import SessionState
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.exceptions import RuleExecutionError
from trading_engine.rules.outcome import RuleExecutionResult, RuleOutcome
from trading_engine.rules.registry import RuleRegistry

from ..rules.conftest import FakeRule, make_rule_reference


@pytest.fixture
def valid_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def another_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def valid_datetime() -> datetime:
    return datetime(2026, 7, 3, 9, 20, 0)  # noqa: DTZ001


@pytest.fixture
def sample_market_context(
    valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
) -> MarketContext:
    return MarketContext(valid_uuid, another_uuid, valid_datetime)


@pytest.fixture
def sample_session_state(valid_uuid: uuid.UUID) -> SessionState:
    return SessionState(valid_uuid)


@pytest.fixture
def sample_execution_context(
    sample_market_context: MarketContext, sample_session_state: SessionState
) -> RuleExecutionContext:
    return RuleExecutionContext(sample_market_context, sample_session_state)


@pytest.fixture
def sample_rule_reference() -> RuleReference:
    return make_rule_reference()


@pytest.fixture
def populated_registry() -> RuleRegistry:
    registry = RuleRegistry()
    registry.register(FakeRule(make_rule_reference("STRIKE-001"), outcome=RuleOutcome.PASS))
    registry.register(FakeRule(make_rule_reference("TREND-001"), outcome=RuleOutcome.UNKNOWN))
    registry.register(FakeRule(make_rule_reference("REVERSAL-001"), outcome=RuleOutcome.FAIL))
    return registry


class FrameworkExceptionRule(FakeRule):
    """A rule whose evaluate() always raises a Rule Framework exception."""

    def evaluate(self, context: RuleExecutionContext) -> RuleExecutionResult:
        raise RuleExecutionError("Simulated fatal framework exception - not a real rule.")


class BuggyRule(FakeRule):
    """A rule whose evaluate() always raises an unexpected, non-framework exception."""

    def evaluate(self, context: RuleExecutionContext) -> RuleExecutionResult:
        raise ValueError("Simulated unexpected bug - not a real rule.")

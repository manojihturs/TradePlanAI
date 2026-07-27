"""Shared fixtures for the Calculator Framework test suite.

Provides only generic, structurally-valid values and a minimal
concrete :class:`~trading_engine.calculators.base.AbstractCalculator`
test double (``FakeCalculator``) - no trading-meaningful mathematics,
consistent with the Calculator Framework itself containing none.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from trading_engine.calculators.base import AbstractCalculator
from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.result import CalculationResult, CalculationStatus
from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.rule_reference import (
    ConfidenceLevel,
    RuleCategory,
    RuleReference,
    RuleStatus,
)
from trading_engine.domain.session_state import SessionState


@pytest.fixture
def valid_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def another_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def valid_datetime() -> datetime:
    return datetime(2026, 7, 3, 9, 20, 0)  # noqa: DTZ001


def make_rule_reference(rule_id: str = "STRIKE-001") -> RuleReference:
    return RuleReference(
        rule_id=rule_id,
        category=RuleCategory.STRIKE,
        status=RuleStatus.DRAFT,
        confidence=ConfidenceLevel.MEDIUM,
        evidence_count=2,
    )


@pytest.fixture
def sample_rule_reference() -> RuleReference:
    return make_rule_reference()


@pytest.fixture
def sample_market_context(
    valid_uuid: uuid.UUID, another_uuid: uuid.UUID, valid_datetime: datetime
) -> MarketContext:
    return MarketContext(valid_uuid, another_uuid, valid_datetime)


@pytest.fixture
def sample_session_state(valid_uuid: uuid.UUID) -> SessionState:
    return SessionState(valid_uuid)


@pytest.fixture
def sample_calculation_context(
    sample_market_context: MarketContext, sample_session_state: SessionState
) -> CalculationContext:
    return CalculationContext(sample_market_context, sample_session_state)


class FakeCalculator(AbstractCalculator):
    """A minimal concrete AbstractCalculator - not a real calculator.

    ``calculate()`` always returns a fixed, caller-configurable
    result; it performs no calculation of any kind.
    """

    def __init__(
        self,
        calculator_id: str = "FAKE-CALCULATOR",
        name: str = "Fake Calculator",
        description: str = "A test double, not a real calculator.",
        success: bool = True,
        status: CalculationStatus = CalculationStatus.SUCCESS,
    ) -> None:
        super().__init__(calculator_id, name, description)
        self._success = success
        self._status = status

    def calculate(self, context: CalculationContext) -> CalculationResult:
        return CalculationResult(
            calculation_id=uuid.uuid4(),
            calculator_id=self.calculator_id,
            success=self._success,
            status=self._status,
        )


class NonConformingCalculator:
    """An object that does not satisfy the Calculator protocol (missing methods)."""

    def id(self) -> str:
        return "NOT-A-REAL-CALCULATOR"

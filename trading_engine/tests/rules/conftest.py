"""Shared fixtures for the Rule Framework test suite.

Provides only generic, structurally-valid values and a minimal
concrete :class:`~trading_engine.rules.base.AbstractRule` test double
(``FakeRule``) - no trading-meaningful rule logic, consistent with the
Rule Framework itself containing none.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from trading_engine.domain.evidence_reference import EvidenceLevel, EvidenceReference
from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.rule_reference import (
    ConfidenceLevel,
    RuleCategory,
    RuleReference,
    RuleStatus,
)
from trading_engine.domain.session_state import SessionState
from trading_engine.rules.base import AbstractRule
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.outcome import RuleExecutionResult, RuleOutcome


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
def sample_evidence_reference() -> EvidenceReference:
    return EvidenceReference(
        evidence_id="EVID-001",
        level=EvidenceLevel.ORIGINAL_TRANSCRIPT,
        description="Original strategy statement.",
    )


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


class FakeRule(AbstractRule):
    """A minimal concrete AbstractRule - not a real trading rule.

    ``evaluate()`` always returns a fixed, caller-configurable
    outcome; it performs no calculation of any kind.
    """

    _UNSET = object()

    def __init__(
        self,
        reference: RuleReference | None = _UNSET,  # type: ignore[assignment]
        name: str = "Fake Rule",
        description: str = "A test double, not a trading rule.",
        outcome: RuleOutcome = RuleOutcome.UNKNOWN,
    ) -> None:
        if reference is FakeRule._UNSET:
            reference = make_rule_reference()
        super().__init__(reference, name, description)  # type: ignore[arg-type]
        self._outcome = outcome

    def evaluate(self, context: RuleExecutionContext) -> RuleExecutionResult:
        return RuleExecutionResult(
            result_id=uuid.uuid4(),
            rule=self.reference,
            outcome=self._outcome,
            reason="Fixed test-double outcome; no calculation performed.",
        )


@pytest.fixture
def fake_rule(sample_rule_reference: RuleReference) -> FakeRule:
    return FakeRule(sample_rule_reference)


class NonConformingRule:
    """An object that does not satisfy the Rule protocol (missing methods)."""

    def id(self) -> str:
        return "NOT-A-REAL-RULE-001"

"""Conformance tests for interfaces.qualification_engine.

Verifies only the Protocol shape and stub convention - the sustain/
breach test itself remains MISSING INFORMATION and is not implemented
here.
"""

from __future__ import annotations

import pytest

from core.exceptions import UnresolvedBusinessRuleError
from interfaces.qualification_engine import QualificationEngine


class _StubQualificationEngine:
    def evaluate(self, tp_state: object) -> bool:
        raise UnresolvedBusinessRuleError(
            "Qualification sustain/breach test is MISSING INFORMATION "
            "(Specification Section 20 item 3)."
        )


def test_stub_satisfies_protocol() -> None:
    assert isinstance(_StubQualificationEngine(), QualificationEngine)


def test_object_without_evaluate_does_not_satisfy_protocol() -> None:
    class NotAQualificationEngine:
        pass

    assert not isinstance(NotAQualificationEngine(), QualificationEngine)


def test_stub_raises_unresolved_business_rule_error() -> None:
    engine: QualificationEngine = _StubQualificationEngine()
    with pytest.raises(UnresolvedBusinessRuleError, match="MISSING INFORMATION"):
        engine.evaluate(object())

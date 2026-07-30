"""Conformance tests for interfaces.orb_engine.

Verifies only the Protocol shape - the real implementation and its
own tests live in ``src/orb_engine/``.
"""

from __future__ import annotations

from interfaces.orb_engine import ORBEngine
from orb_engine.orb_engine import ORBEngine as RealORBEngine


def test_real_engine_satisfies_protocol() -> None:
    assert isinstance(RealORBEngine(), ORBEngine)


def test_object_without_calculate_does_not_satisfy_protocol() -> None:
    class NotAnEngine:
        pass

    assert not isinstance(NotAnEngine(), ORBEngine)

"""QualificationEngine: interface only.

Traceability
------------
Specification Sections 7-8: the sustain/breach test itself depends on
the same unresolved competitor-identity gap as
``interfaces.tp_engine.TPEngine`` (Section 20 item 3), plus
external-invalidation handling (news/budget/war/natural disaster,
Section 7) has no detection mechanism specified anywhere. This
interface defines only the method shape a future implementation must
satisfy. Do NOT implement.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class QualificationEngine(Protocol):
    """Evaluates whether a strike's TP is currently "qualified"
    (sustaining against its competitor level) - Specification
    Sections 7-8."""

    def evaluate(self, tp_state: object) -> bool:
        """Evaluate the current qualification state.

        ``tp_state`` is typed ``object`` for the same reason given in
        ``interfaces.tp_engine.TPEngine.update`` - no concrete
        ``TPState`` shape is defined in this sprint.

        Raises:
            core.exceptions.UnresolvedBusinessRuleError: always, until
                the sustain/breach test's competitor identity
                (Specification Section 20 item 3) and
                external-invalidation handling are resolved and a
                real implementation replaces the stub.
        """
        ...  # pragma: no cover

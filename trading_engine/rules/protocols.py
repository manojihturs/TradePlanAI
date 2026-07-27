"""The Rule contract: the structural protocol every rule implementation satisfies.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``, which describes
the Rule Registry, Rule Evaluation Pipeline, and Rule Results in terms
of "a registered rule implementation" without specifying that
implementation's shape at the architecture level - defining that shape
concretely is this Milestone 4.2 module's job.

Deliberately generic: this protocol makes no reference to Strike,
TrendPoint, Opponent, Edge, or Reversal. Every confirmed rule in
``docs/RULE_INDEX.md`` (STRIKE-001, TREND-001/002/003, OPPONENT-001,
REVERSAL-001) is simply "a rule" at this layer - which domain concepts
a given rule reads is that rule's own concern, expressed only once its
mathematics is known (Milestone 4.3+), not something the contract
itself should assume or constrain.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from trading_engine.domain.evidence_reference import EvidenceReference
from trading_engine.rules.categories import RuleCategory
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.outcome import RuleExecutionResult


@runtime_checkable
class Rule(Protocol):
    """The structural contract every rule implementation must satisfy.

    A ``typing.Protocol`` rather than an ``abc.ABC``: per
    ``docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md``, this lets any
    object with the right methods - a plain class, a
    :class:`~trading_engine.rules.base.AbstractRule` subclass, or even
    a test double - be treated as a Rule without a forced inheritance
    relationship, matching "rules evolve without changing unrelated
    code" (the guiding constraint of
    ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``).

    ``@runtime_checkable`` allows :func:`isinstance` checks against
    this protocol (used by
    :class:`~trading_engine.rules.registry.RuleRegistry` to reject
    objects that do not structurally satisfy it) - note that per
    ``typing`` semantics this checks method *presence* only, not
    parameter/return types or behaviour.
    """

    def id(self) -> str:
        """Return this rule's Rule ID, exactly as assigned in
        ``docs/RULE_INDEX.md`` (e.g. ``"STRIKE-001"``)."""
        ...

    def name(self) -> str:
        """Return a short, human-readable name for this rule."""
        ...

    def category(self) -> RuleCategory:
        """Return this rule's fixed category, per
        ``docs/TRADINGVIEW_STRATEGY_BIBLE.md``'s Category Taxonomy."""
        ...

    def description(self) -> str:
        """Return a short, human-readable description of what this
        rule evaluates."""
        ...

    def required_evidence(self) -> tuple[EvidenceReference, ...]:
        """Return the EvidenceReference(s) that justify this rule's
        existence/behaviour, per ``docs/TRACEABILITY_MATRIX.md``."""
        ...

    def evaluate(self, context: RuleExecutionContext) -> RuleExecutionResult:
        """Evaluate this rule against the supplied execution context
        and return exactly one result.

        No default/expected behaviour is specified here - what a rule
        does when evaluated is entirely up to its own implementation,
        which for every rule in ``docs/RULE_INDEX.md`` today remains
        Unknown or Partially Known mathematics (Milestone 4.3+ scope).
        """
        ...

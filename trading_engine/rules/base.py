"""AbstractRule: an optional shared base for concrete rule implementations.

Traceability notes
-------------------
Per Milestone 4.2's instruction to prefer ``typing.Protocol`` and use
``abc.ABC`` "only when Protocol is insufficient": :class:`.protocols.Rule`
alone is sufficient to define the *contract*, but offers no shared
*implementation* - every concrete rule (Milestone 4.3+) would otherwise
reimplement identical identity-method plumbing (``id()``, ``name()``,
``category()``, ``description()``, ``required_evidence()``) by hand.
``AbstractRule`` exists only to remove that duplication; it is not
required by the framework - a class satisfying :class:`.protocols.Rule`
structurally, without inheriting from ``AbstractRule``, is equally
valid.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from trading_engine.domain.evidence_reference import EvidenceReference
from trading_engine.domain.rule_reference import RuleReference
from trading_engine.rules.categories import RuleCategory
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.exceptions import RuleRegistrationError
from trading_engine.rules.outcome import RuleExecutionResult


class AbstractRule(ABC):
    """A convenience base class implementing the identity portion of
    the :class:`~trading_engine.rules.protocols.Rule` contract.

    Stores a :class:`~trading_engine.domain.rule_reference.RuleReference`
    (for ``id()``/``category()`` and traceability back to
    ``docs/RULE_INDEX.md``), a caller-supplied ``name``/``description``
    (the RuleReference itself carries no name or description field),
    and the EvidenceReference(s) this rule requires. Subclasses need
    only implement :meth:`evaluate`.

    Rule References
        None directly - a generic base usable by any rule.

    Attributes:
        reference: The underlying RuleReference identifying this rule.
    """

    def __init__(
        self,
        reference: RuleReference,
        name: str,
        description: str,
        required_evidence: tuple[EvidenceReference, ...] = (),
    ) -> None:
        if reference is None:
            raise RuleRegistrationError("AbstractRule.reference must not be None.")

        if not name or not name.strip():
            raise RuleRegistrationError("AbstractRule.name must not be blank.")

        if not description or not description.strip():
            raise RuleRegistrationError("AbstractRule.description must not be blank.")

        self.reference = reference
        self._name = name
        self._description = description
        self._required_evidence = required_evidence

    def id(self) -> str:
        """Return this rule's Rule ID, from :attr:`reference`."""
        return self.reference.rule_id

    def name(self) -> str:
        """Return this rule's caller-supplied short name."""
        return self._name

    def category(self) -> RuleCategory:
        """Return this rule's category, from :attr:`reference`."""
        return self.reference.category

    def description(self) -> str:
        """Return this rule's caller-supplied description."""
        return self._description

    def required_evidence(self) -> tuple[EvidenceReference, ...]:
        """Return the EvidenceReference(s) this rule requires."""
        return self._required_evidence

    @abstractmethod
    def evaluate(self, context: RuleExecutionContext) -> RuleExecutionResult:
        """Evaluate this rule against the supplied execution context.

        Left abstract deliberately - no rule in ``docs/RULE_INDEX.md``
        has known mathematics yet (Milestone 4.3+ scope). Subclasses
        implement this once a rule's evaluation logic is evidenced.
        """
        ...

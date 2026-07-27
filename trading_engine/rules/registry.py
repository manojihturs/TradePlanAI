"""RuleRegistry: the Rule ID -> rule implementation lookup.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule
Registry"): "A lookup from Rule ID ... to a registered rule
implementation ... A registry keyed by Rule ID means a new rule is
added by registering it, not by modifying the engine's own code."
This module implements exactly that lookup - registration, duplicate
rejection, and lookup by ID/category - and nothing more. It performs
**no evaluation**; see ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``
("Rule Evaluation Pipeline") for where evaluation itself is
architected (a later milestone).
"""

from __future__ import annotations

from trading_engine.rules.categories import RuleCategory
from trading_engine.rules.exceptions import DuplicateRuleError, RuleRegistrationError
from trading_engine.rules.protocols import Rule


class RuleRegistry:
    """A Rule ID -> Rule lookup, with duplicate-ID rejection.

    Rule References
        None directly - a generic container for any object satisfying
        :class:`~trading_engine.rules.protocols.Rule`.

    Traceability requirement
        Per ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``, every
        registered rule carries its own Rule ID/category identity via
        :meth:`~trading_engine.rules.protocols.Rule.id` and
        :meth:`~trading_engine.rules.protocols.Rule.category`, so this
        registry's contents can eventually be cross-checked against
        ``docs/RULE_INDEX.md`` (not implemented in this milestone).
    """

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    def register(self, rule: Rule) -> None:
        """Register a rule under its own ``id()``.

        Raises:
            RuleRegistrationError: if ``rule`` is ``None``, does not
                structurally satisfy :class:`~trading_engine.rules.protocols.Rule`,
                or its ``id()`` is blank.
            DuplicateRuleError: if a rule is already registered under
                the same Rule ID.
        """
        if rule is None:
            raise RuleRegistrationError("Cannot register a rule that is None.")

        if not isinstance(rule, Rule):
            raise RuleRegistrationError(
                f"{rule!r} does not satisfy the Rule protocol "
                "(missing one or more required methods)."
            )

        rule_id = rule.id()
        if not rule_id or not rule_id.strip():
            raise RuleRegistrationError("A rule's id() must not be blank.")

        if rule_id in self._rules:
            raise DuplicateRuleError(
                f"Rule ID {rule_id!r} is already registered - Rule IDs are "
                "permanent and unique once assigned, per docs/RULE_INDEX.md."
            )

        self._rules[rule_id] = rule

    def get(self, rule_id: str) -> Rule:
        """Look up a registered rule by its exact Rule ID.

        Raises:
            RuleRegistrationError: if no rule is registered under
                ``rule_id``.
        """
        try:
            return self._rules[rule_id]
        except KeyError as exc:
            raise RuleRegistrationError(
                f"No rule is registered under Rule ID {rule_id!r}."
            ) from exc

    def by_category(self, category: RuleCategory) -> tuple[Rule, ...]:
        """Return every registered rule belonging to ``category``, in
        registration order."""
        return tuple(rule for rule in self._rules.values() if rule.category() == category)

    def execution_order(self) -> tuple[Rule, ...]:
        """Return every registered rule in the order the Pipeline
        should evaluate them.

        # TODO (RULE_ENGINE_ARCHITECTURE): docs/RULE_INDEX.md's
        # "Depends On"/"Referenced By" columns define a dependency
        # graph among rules (e.g. TREND-002 depends on TREND-001) that
        # the true evaluation order must respect - "a rule is never
        # evaluated before a rule it depends on." That graph is not
        # represented anywhere in this framework yet (Milestone 4.3+
        # scope: reading dependency data and topologically sorting by
        # it). This method currently returns registration order only,
        # which is not guaranteed to respect that dependency graph.
        """
        return tuple(self._rules.values())

    def all_rules(self) -> tuple[Rule, ...]:
        """Return every registered rule, in registration order."""
        return tuple(self._rules.values())

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules

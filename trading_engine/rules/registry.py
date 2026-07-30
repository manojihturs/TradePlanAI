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

import uuid
from collections.abc import Callable
from datetime import datetime

from trading_engine.diagnostics.events import DependencyMissing, DependencyResolved, RuleRegistered
from trading_engine.diagnostics.sink import DiagnosticsSink, NullDiagnosticsSink
from trading_engine.rules.categories import RuleCategory
from trading_engine.rules.dependencies import depends_on, is_well_formed_rule_id
from trading_engine.rules.exceptions import (
    CircularDependencyError,
    DuplicateRuleError,
    RuleRegistrationError,
    UnresolvedDependencyError,
)
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

    def register(self, rule: Rule, diagnostics_sink: DiagnosticsSink | None = None) -> None:
        """Register a rule under its own ``id()``.

        Args:
            rule: The rule to register.
            diagnostics_sink: Where to emit a
                :class:`~trading_engine.diagnostics.events.RuleRegistered`
                event on success. ``None`` (the default) means no
                event is emitted - registration commonly happens
                before any
                :class:`~trading_engine.engine.engine_configuration.EngineConfiguration`
                exists, so this is opt-in per call rather than tied to
                that configuration's ``logging_enabled`` flag (see
                ``research/analysis/EXECUTION_LOGGING_REPORT.md``).

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

        sink = diagnostics_sink if diagnostics_sink is not None else NullDiagnosticsSink()
        sink.emit(
            RuleRegistered(
                event_id=uuid.uuid4(),
                occurred_at=datetime.now(),  # noqa: DTZ005
                rule_id=rule_id,
                total_registered=len(self._rules),
            )
        )

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

    def execution_order(
        self,
        dependency_resolver: Callable[[str], tuple[str, ...]] | None = None,
        diagnostics_sink: DiagnosticsSink | None = None,
    ) -> tuple[Rule, ...]:
        """Return every registered rule in dependency-respecting
        execution order: "a rule is never evaluated before a rule it
        depends on" (``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``,
        "Rule Evaluation Pipeline").

        Dependency data comes from
        :func:`trading_engine.rules.dependencies.depends_on`, which
        mirrors ``docs/RULE_INDEX.md``'s "Depends On" column verbatim
        (see that module's docstring for exactly what is - and is
        deliberately not - represented). Pass ``dependency_resolver``
        to substitute a different source of dependency data (used by
        this framework's own tests; production callers should rely on
        the default).

        Ordering is computed via Kahn's algorithm (repeatedly removing
        rules with no unresolved dependencies) with a **deterministic
        tie-break**: among rules simultaneously ready to run, the one
        registered earliest is placed first. Passing the same
        registration sequence through this method always yields the
        same order.

        Args:
            dependency_resolver: See above.
            diagnostics_sink: Where to emit a
                :class:`~trading_engine.diagnostics.events.DependencyResolved`
                event on success, or a
                :class:`~trading_engine.diagnostics.events.DependencyMissing`
                event before raising on failure. ``None`` (the
                default) means no event is emitted.
                :class:`~trading_engine.engine.strategy_engine.StrategyEngine`
                passes its resolved,
                ``EngineConfiguration.logging_enabled``-respecting
                sink here on every run - see
                ``research/analysis/EXECUTION_LOGGING_REPORT.md``.

        Raises:
            UnresolvedDependencyError: if a registered rule declares a
                dependency Rule ID that is either structurally
                malformed (does not match the ``<CATEGORY>-<NNN>``
                convention) or well-formed but not itself registered
                in this registry.
            CircularDependencyError: if the registered rules'
                dependencies form a cycle, making no valid order
                possible.
        """
        sink = diagnostics_sink if diagnostics_sink is not None else NullDiagnosticsSink()
        resolver = dependency_resolver if dependency_resolver is not None else depends_on
        registration_order = list(self._rules.keys())
        registered_ids = set(self._rules)

        dependencies: dict[str, tuple[str, ...]] = {}
        for rule_id in registration_order:
            deduplicated: list[str] = []
            for dependency_id in resolver(rule_id):
                if dependency_id not in deduplicated:
                    deduplicated.append(dependency_id)
            dependencies[rule_id] = tuple(deduplicated)

        for rule_id, rule_dependencies in dependencies.items():
            for dependency_id in rule_dependencies:
                if not is_well_formed_rule_id(dependency_id):
                    sink.emit(
                        DependencyMissing(
                            event_id=uuid.uuid4(),
                            occurred_at=datetime.now(),  # noqa: DTZ005
                            rule_id=rule_id,
                            dependency_id=dependency_id,
                            reason="unsupported dependency",
                        )
                    )
                    raise UnresolvedDependencyError(
                        f"Rule {rule_id!r} declares a dependency on "
                        f"{dependency_id!r}, which does not match the "
                        "<CATEGORY>-<NNN> Rule ID convention defined in "
                        "docs/RULE_INDEX.md (unsupported dependency)."
                    )
                if dependency_id not in registered_ids:
                    sink.emit(
                        DependencyMissing(
                            event_id=uuid.uuid4(),
                            occurred_at=datetime.now(),  # noqa: DTZ005
                            rule_id=rule_id,
                            dependency_id=dependency_id,
                            reason="missing dependency",
                        )
                    )
                    raise UnresolvedDependencyError(
                        f"Rule {rule_id!r} depends on {dependency_id!r}, "
                        "which is not registered in this registry "
                        "(missing dependency). Register it before "
                        "requesting an execution order."
                    )

        in_degree = {rule_id: len(dependencies[rule_id]) for rule_id in registration_order}
        dependents: dict[str, list[str]] = {rule_id: [] for rule_id in registration_order}
        for rule_id, rule_dependencies in dependencies.items():
            for dependency_id in rule_dependencies:
                dependents[dependency_id].append(rule_id)

        ready = [rule_id for rule_id in registration_order if in_degree[rule_id] == 0]
        ordered_ids: list[str] = []
        while ready:
            ready.sort(key=registration_order.index)
            current = ready.pop(0)
            ordered_ids.append(current)
            for dependent_id in dependents[current]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    ready.append(dependent_id)

        if len(ordered_ids) != len(registration_order):
            unresolved = sorted(set(registration_order) - set(ordered_ids))
            for rule_id in unresolved:
                sink.emit(
                    DependencyMissing(
                        event_id=uuid.uuid4(),
                        occurred_at=datetime.now(),  # noqa: DTZ005
                        rule_id=rule_id,
                        dependency_id=", ".join(unresolved),
                        reason="circular dependency",
                    )
                )
            raise CircularDependencyError(
                "A circular dependency was detected among registered "
                f"rules: {', '.join(unresolved)}. No valid execution "
                "order exists."
            )

        sink.emit(
            DependencyResolved(
                event_id=uuid.uuid4(),
                occurred_at=datetime.now(),  # noqa: DTZ005
                execution_order=tuple(ordered_ids),
            )
        )

        return tuple(self._rules[rule_id] for rule_id in ordered_ids)

    def all_rules(self) -> tuple[Rule, ...]:
        """Return every registered rule, in registration order."""
        return tuple(self._rules.values())

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules

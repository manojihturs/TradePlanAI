"""Rule dependency metadata, sourced strictly from docs/RULE_INDEX.md.

Traceability notes
-------------------
Every entry in :data:`RULE_DEPENDENCIES` is copied verbatim from the
"Depends On" column of ``docs/RULE_INDEX.md``'s Index table
(Milestone 3.1/3.2 ledger, unchanged since). This module introduces no
new dependency relationship and infers nothing: where
``docs/RULE_INDEX.md`` reads "none yet," the corresponding entry here
is an empty tuple.

Explicitly NOT represented here
    ``research/analysis/RULE_DEPENDENCY_GRAPH.md`` and
    ``research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md``
    establish that STRIKE-001's strike selection depends on a Weekly
    Future computation - but ``docs/RULE_INDEX.md``'s own ledger still
    reads ``STRIKE-001 | ... | Depends On: none yet`` (a
    documentation-lag discrepancy flagged by
    ``research/analysis/REPOSITORY_CHANGE_PROPOSAL.md`` but never
    applied to the ledger). Per this milestone's "Do NOT modify
    repository documentation" and "Do NOT introduce unsupported
    dependencies" rules, that edge is deliberately not added here.
    Weekly Future also has no Rule ID of its own (it is ENT-010, a
    Candidate Entity, not a confirmed rule per ``docs/RULE_INDEX.md``)
    - a Rule-ID-keyed dependency graph has no node to represent it as
    even if the edge were added. See
    ``research/analysis/DEPENDENCY_VALIDATION_REPORT.md`` for the full
    reasoning.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

#: Mirrors the Rule ID convention enforced by
#: ``trading_engine.domain.rule_reference.RuleReference`` - duplicated
#: locally rather than imported, consistent with this package's
#: existing pattern of self-contained modules (e.g. each placeholder
#: calculator defines its own local ``RuleReference`` constants).
_RULE_ID_PATTERN = re.compile(r"^[A-Z_]+-\d{3}$")

#: Rule ID -> the dependency Rule ID(s) ``docs/RULE_INDEX.md``'s
#: "Depends On" column lists for it, verbatim. Every rule row present
#: in that document's Index table is present here, including rules
#: whose own "Depends On" reads "none yet" (mapped to an empty tuple)
#: - this table is deliberately exhaustive over the 8 confirmed Rule
#: IDs, not merely the ones with a non-empty dependency list.
RULE_DEPENDENCIES: Mapping[str, tuple[str, ...]] = {
    "STRIKE-001": (),
    "TREND-001": (),
    "TREND-002": ("TREND-001",),
    "TREND-003": ("TREND-001", "OPPONENT-001"),
    "OPPONENT-001": ("TREND-001", "OPPONENT-002", "OPPONENT-003"),
    "OPPONENT-002": (),
    "OPPONENT-003": (),
    "REVERSAL-001": (),
}


def depends_on(rule_id: str) -> tuple[str, ...]:
    """Return the declared dependency Rule ID(s) for ``rule_id``, per
    ``docs/RULE_INDEX.md``.

    Returns an empty tuple for any ``rule_id`` not present in
    :data:`RULE_DEPENDENCIES` (e.g. a rule not yet reflected in
    ``docs/RULE_INDEX.md``) - this is not an error condition on its
    own; it means no dependency is currently evidenced for that rule.
    Duplicate entries within a single rule's dependency list are
    preserved here exactly as declared - deduplication and validation
    are :class:`~trading_engine.rules.registry.RuleRegistry`'s
    responsibility when building an execution order, not this lookup
    function's.
    """
    return RULE_DEPENDENCIES.get(rule_id, ())


def is_well_formed_rule_id(rule_id: str) -> bool:
    """Return whether ``rule_id`` matches the ``<CATEGORY>-<NNN>``
    convention defined in ``docs/RULE_INDEX.md``."""
    return bool(_RULE_ID_PATTERN.match(rule_id))

"""Interfaces for business rules that remain MISSING INFORMATION.

Traceability
------------
Every Protocol in this package corresponds to a Critical gap in
``research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md``
Section 20: the Weekly Future formula, the ATM strike-selection rule,
the TP Engine's competitor identity, the Qualification test's
external-invalidation handling, and the Stop Loss rule. None of these
are implemented here - only their method *shape*, so that downstream
modules (``models``, ``events``, a future ``entry``/``exit``) can be
built and tested against an injected stub today, per
``research/architecture/IMPLEMENTATION_ROADMAP.md``'s "Unblocking
Strategy."

Calling any of these interfaces' methods on a real (non-stub)
implementation before its business rule is resolved is a
programming error - implementations should raise
``core.exceptions.UnresolvedBusinessRuleError`` until then.
"""

from __future__ import annotations

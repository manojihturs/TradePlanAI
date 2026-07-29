"""Diagnostics: structured, infrastructure-level execution events.

Traceability notes
-------------------
A foundational package with **zero dependency** on
:mod:`trading_engine.rules`, :mod:`trading_engine.engine`, or
:mod:`trading_engine.calculators` - the reverse is true instead: those
packages depend on this one to emit diagnostic events, mirroring
:mod:`trading_engine.domain`'s own "zero third-party dependencies"
placement at the base of the dependency direction described in
``docs/architecture/SOLUTION_STRUCTURE.md``.

This package carries **no trading data**. Every event defined in
:mod:`.events` is limited to structural/identity information (Rule
IDs, timestamps, counts, exception type names, the framework-level
:class:`~trading_engine.rules.outcome.RuleOutcome` name as a plain
string) - never a computed value such as a strike price, premium, or
any other business-meaningful number. No calculator's
``computed_values`` mapping is ever passed into a diagnostic event.
"""

from __future__ import annotations

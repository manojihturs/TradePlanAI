"""Rule Framework: contracts, registry, and evaluation-pipeline scaffolding.

See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` for the
architecture this package implements. This package defines **how**
rules integrate with the engine - identity contract (:mod:`.protocols`),
an optional shared base for concrete rule authors (:mod:`.base`),
outcome/result shapes (:mod:`.outcome`), the execution input wrapper
(:mod:`.context`), registration (:mod:`.registry`), and the framework's
own exceptions (:mod:`.exceptions`).

This package contains **no trading logic, no rule mathematics, and no
strategy code**. Every one of the 6 confirmed rules in
``docs/RULE_INDEX.md`` still has ``Mathematical Definition: Unknown``
or ``Partially Known`` - this framework only makes it possible to
register and route to a rule's implementation once that mathematics is
known (a later milestone), without the framework itself changing
shape.
"""

from __future__ import annotations

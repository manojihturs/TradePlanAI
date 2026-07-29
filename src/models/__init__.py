"""Value objects for the strategy engine.

Every model here traces to ``research/architecture/DATA_DICTIONARY.md``
and, transitively, to
``research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md`` v1.1.
Fields whose computation is MISSING INFORMATION in the Specification
are simply omitted here (e.g. ``WeeklyFuture`` carries ``high``/``low``
as opaque values with no formula), never guessed.

Depends only on ``core`` (enums, exceptions) - never on ``events``,
``trade_manager``, ``replay``, or ``interfaces``.
"""

from __future__ import annotations

"""RuleExecutionContext: the wrapper handed to a rule's evaluate() call.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule
Evaluation Pipeline", step 1: "Assemble Market Context for the current
evaluation step"). The architecture names ``MarketContext`` and
``SessionState`` as the Pipeline's two inputs. ``RuleExecutionContext``
wraps both of those Milestone 4.1 domain objects into a single value a
:class:`~trading_engine.rules.protocols.Rule` can accept, plus two
framework-only additions with no Rule Bible citation:

- ``configuration``: an open, untyped mapping so a future concrete
  rule can be parameterised (e.g. a lookback window) without the
  framework guessing what configuration any rule needs today - no
  rule's evidence currently specifies configurable parameters.
- ``clock``: an injectable time source (defaults to ``datetime.now``)
  so a future Replay Engine (Milestone 4.4+) can supply a deterministic
  or historical clock instead of wall-clock time, without changing this
  type's shape.

Neither addition encodes any trading behaviour.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.session_state import SessionState
from trading_engine.rules.exceptions import RuleExecutionError


@dataclass(frozen=True)
class RuleExecutionContext:
    """Everything a :class:`~trading_engine.rules.protocols.Rule` needs
    to evaluate itself once.

    A thin wrapper, not a new source of data - it does not compute or
    derive anything from ``market_context``/``session_state``, and
    carries no default configuration values (an empty mapping is the
    only structural default, not a guessed rule parameter).

    Attributes:
        market_context: The read-only Market Context snapshot for this
            evaluation step.
        session_state: The current, accumulating Session State.
        configuration: Optional, rule-defined configuration values.
            Untyped and empty by default - no rule's evidenced
            behaviour currently requires configuration.
        clock: A callable returning the "current" time, defaulting to
            ``datetime.now``. Exists so a future Replay Engine can
            substitute a historical/deterministic time source.
    """

    market_context: MarketContext
    session_state: SessionState
    configuration: Mapping[str, Any] = field(default_factory=dict)
    clock: Callable[[], datetime] = datetime.now

    def __post_init__(self) -> None:
        if self.market_context is None:
            raise RuleExecutionError("RuleExecutionContext.market_context must not be None.")

        if self.session_state is None:
            raise RuleExecutionError("RuleExecutionContext.session_state must not be None.")

    # TODO (RULE_ENGINE_ARCHITECTURE): Whether a rule may mutate
    # Session State directly, or must return an update for the
    # Pipeline to apply, is not specified by
    # docs/architecture/RULE_ENGINE_ARCHITECTURE.md ("Apply any
    # resulting Session State updates" - mechanism unstated). This
    # wrapper only carries the current SessionState; it defines no
    # update mechanism.

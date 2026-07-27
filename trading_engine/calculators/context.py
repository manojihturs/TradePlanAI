"""CalculationContext: the wrapper handed to a calculator's calculate() call.

Traceability notes
-------------------
The Calculator Framework counterpart of
:class:`trading_engine.rules.context.RuleExecutionContext`, at the
mathematical layer instead of the rule-evaluation layer. Per the
Milestone 4.3A instruction: "No broker references. No replay
references." - this wrapper carries only the same two Milestone 4.1
domain inputs RuleExecutionContext carries (MarketContext,
SessionState), plus open configuration and a fixed calculation
timestamp. No entry in ``docs/RULE_INDEX.md`` specifies what
configuration a calculation needs; ``configuration`` therefore remains
untyped and empty by default, same rationale as
``RuleExecutionContext.configuration``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from trading_engine.calculators.exceptions import CalculationError
from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.session_state import SessionState


@dataclass(frozen=True)
class CalculationContext:
    """Everything a :class:`~trading_engine.calculators.protocols.Calculator`
    needs to calculate itself once.

    A thin wrapper, not a new source of data - it does not compute or
    derive anything from ``market_context``/``session_state``. Unlike
    :class:`trading_engine.rules.context.RuleExecutionContext` (which
    carries an injectable ``clock`` callable),
    ``calculation_timestamp`` is a fixed value supplied by the caller -
    the moment the calculation was requested, not a live time source.

    Attributes:
        market_context: The read-only Market Context snapshot this
            calculation runs against.
        session_state: The current, accumulating Session State.
        configuration: Optional, calculator-defined configuration
            values. Untyped and empty by default - no calculator's
            evidenced behaviour currently requires configuration.
        calculation_timestamp: The moment this calculation was
            requested.
    """

    market_context: MarketContext
    session_state: SessionState
    configuration: Mapping[str, Any] = field(default_factory=dict)
    calculation_timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if self.market_context is None:
            raise CalculationError("CalculationContext.market_context must not be None.")

        if self.session_state is None:
            raise CalculationError("CalculationContext.session_state must not be None.")

        if self.calculation_timestamp is None:
            raise CalculationError("CalculationContext.calculation_timestamp must not be None.")

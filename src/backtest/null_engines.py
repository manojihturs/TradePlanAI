"""NeverTriggersStopLoss / NeverTriggersTrailingStop: structural placeholders only.

Traceability
------------
Stop Loss and Trailing Stop remain blocked - no SL basis, trail
activation, or trail step has been supplied by the Product Owner (see
``research/incoming/stop_loss_session3_intake_2026-07-31.md``,
``trailing_stop_session4_intake_2026-07-31.md``, both still blank
templates). ``exit_engine.exit_engine.ExitEngine`` requires real
:class:`~interfaces.stop_loss_engine.StopLossEngine`/
:class:`~interfaces.trailing_stop_engine.TrailingStopEngine`
instances at construction (non-optional) - injecting the real stub
implementations would raise
:class:`~core.exceptions.UnresolvedBusinessRuleError` on every single
candle, halting the pipeline immediately after Target/Competitor
checks miss, per this project's own established test convention
(``tests/exit_engine/test_exit_engine.py``'s own
``pytest.raises(UnresolvedBusinessRuleError, ...)`` assertion against
the real stubs).

These two classes exist ONLY so a backtest/paper-trading harness can
construct a runnable ``ExitEngine`` without inventing SL/Trailing
Stop logic: ``check()`` always returns ``False`` - "not hit" - so a
position can only ever close via the Target or Competitor legs, which
ARE confirmed business logic. This is a null-object pattern, not a
business rule: it supplies no threshold, no formula, no behaviour
beyond "never fire." A position that would need real SL/Trailing
logic to close simply stays open until Target/Competitor closes it or
the backtest run ends - never silently closed by an invented rule.

Not for live trading. Not for paper trading against real capital.
Backtest/harness use only, until real Stop Loss/Trailing Stop
evidence arrives and these are replaced with real implementations.
"""

from __future__ import annotations

from models.market_snapshot import MarketSnapshot
from models.trade_position import TradePosition


class NeverTriggersStopLoss:
    """A :class:`~interfaces.stop_loss_engine.StopLossEngine` stand-in
    that never reports the Stop Loss condition as met.

    See module docstring - a null object, not a business rule.
    """

    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        _ = (position, snapshot)  # unused - see module docstring
        return False


class NeverTriggersTrailingStop:
    """A :class:`~interfaces.trailing_stop_engine.TrailingStopEngine`
    stand-in that never reports the Trailing Stop condition as met.

    See module docstring - a null object, not a business rule.
    """

    def check(self, position: TradePosition, snapshot: MarketSnapshot) -> bool:
        _ = (position, snapshot)  # unused - see module docstring
        return False

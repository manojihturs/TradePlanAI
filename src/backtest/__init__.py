"""backtest: harness for running the CONFIRMED src/ pipeline over historical
(today: synthetic) data end to end - Weekly Future through Exit
(Target/Competitor legs only).

Traceability
------------
See ``docs/BUSINESS_LOGIC_FLOW.md`` for the confirmed flow this
package drives. Deliberately excludes Qualification, Stop Loss,
Trailing Stop, and Decision Engine synthesis - all four remain blocked
pending Product Owner evidence (see
``research/specifications/business_engine_portfolio.md``). Nothing in
this package invents a business rule for any of them;
``backtest.null_engines`` documents exactly how the blocked
Stop Loss/Trailing Stop legs are stood in for structurally, without
supplying real behaviour.
"""

from __future__ import annotations

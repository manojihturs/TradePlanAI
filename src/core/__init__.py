"""Foundational package: enums, exceptions, domain events, protocols,
and the Sprint 1 state machine.

Nothing in ``core`` imports from ``models``, ``events``,
``trade_manager``, ``replay``, or ``interfaces`` - every other
package depends on ``core``, never the reverse.
"""

from __future__ import annotations

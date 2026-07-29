"""EventRecorder: captures every domain event published by the EventBus.

Depends on ``core`` only. No global state - every instance owns its
own recorded-event list, injected an ``EventBusProtocol`` at
construction.
"""

from __future__ import annotations

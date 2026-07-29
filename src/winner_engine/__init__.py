"""WinnerEngine: candle-by-candle CE/PE reference-level touch detection.

Depends on ``core`` and ``models``. Stateless evaluator - the caller
(a future replay/live driver) is responsible for invoking it once per
candle, per Specification Section 9 ("Winner is evaluated candle by
candle").
"""

from __future__ import annotations

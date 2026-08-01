"""QualificationEngine: dual-crossover qualification detection.

Depends on ``core`` and ``models``. Stateless evaluator - the caller
is responsible for invoking it once per candle, per anchor
(Top/Bottom), mirroring ``winner_engine``'s own calling convention.
"""

from __future__ import annotations

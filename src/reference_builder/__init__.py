"""Builds the complete strike reference ladder from first-candle
CE/PE OHLC.

Depends on ``core`` and ``models`` only. Does not implement Weekly
Future, Strike Selection, TP, Qualification, Winner, Entry, or Exit -
this package only turns already-selected strikes' first-5-minute
candle data (Specification Rule 1, CONFIRMED) into
:class:`~models.reference_level.ReferenceLevel` objects.
"""

from __future__ import annotations

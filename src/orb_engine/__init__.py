"""orb_engine: computes Opening Range Breakout classification.

Traceability
------------
Sprint: "ORB Engine" (Business Implementation Mode). Opening High/Low
reuse ``models.reference_level.ReferenceLevel``'s already-CONFIRMED
first-5-minute CE/PE values; breakout/breakdown classification is a
standard, industry-generic definition. See
``interfaces.orb_engine.ORBEngine`` and ``research/analysis/TR-001_ANALYSIS.md``
Section 5 for the evidence trail.
"""

from __future__ import annotations

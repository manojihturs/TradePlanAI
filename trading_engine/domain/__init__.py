"""Domain layer: confirmed and Candidate business concepts only.

See ``docs/architecture/DOMAIN_ARCHITECTURE.md`` for the full
responsibility description of every model in this package, and
``docs/architecture/SOLUTION_STRUCTURE.md`` for this layer's place in
the overall architecture ("Depends on: shared only" - in this
milestone, the standard library only; no third-party import belongs in
this package, per ``docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md``
Section 4).

This package contains **no trading logic, no rule evaluation, and no
mathematical formulas**. Every model is a structural data shape only.
Wherever business behaviour depends on evidence that does not yet
exist, the corresponding module carries a ``# TODO (<RULE-ID>)``
comment rather than a guessed implementation.
"""

from __future__ import annotations


class DomainValidationError(ValueError):
    """Raised when a domain model's constructor receives data that
    fails its structural invariants (e.g. a required identifier is
    empty, a price is not positive).

    This exception exists to make structural-validation failures
    distinguishable from generic Python errors and from any future
    trading-rule violation (which would be raised by the Rule Engine,
    not by the Domain layer - see
    ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``). Raising this
    exception never encodes a trading rule or calculation - only
    structural data validation (e.g. "Strike price > 0",
    "TrendPoint value cannot be negative", "Evidence ID cannot be
    blank").
    """


__all__ = ["DomainValidationError"]

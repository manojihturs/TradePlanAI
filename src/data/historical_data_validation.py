"""HistoricalDataIssue/HistoricalDataIssueKind/HistoricalDataValidation.

Traceability
------------
The five issue kinds match this sprint's own instruction exactly
(missing timestamps, duplicate timestamps, invalid OHLC values,
invalid volume, schema errors) - a structural report, no trading
concept.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, unique

from core.exceptions import ValidationError


@unique
class HistoricalDataIssueKind(Enum):
    """Why one row of a historical data source failed validation."""

    MISSING_TIMESTAMP = "MISSING_TIMESTAMP"
    DUPLICATE_TIMESTAMP = "DUPLICATE_TIMESTAMP"
    INVALID_OHLC = "INVALID_OHLC"
    INVALID_VOLUME = "INVALID_VOLUME"
    SCHEMA_ERROR = "SCHEMA_ERROR"


@dataclass(frozen=True, slots=True)
class HistoricalDataIssue:
    """One validation failure found while loading a historical data
    source.

    Attributes:
        kind: Which :class:`HistoricalDataIssueKind` this is.
        detail: A short, human-readable explanation.
        row_number: The 1-indexed source row this issue concerns, if
            it's row-specific. ``None`` for whole-source issues (e.g.
            a missing required column, or an empty source).
    """

    kind: HistoricalDataIssueKind
    detail: str
    row_number: int | None = None

    def __post_init__(self) -> None:
        if self.kind is None:
            raise ValidationError("HistoricalDataIssue.kind must not be None.")
        if not self.detail or not self.detail.strip():
            raise ValidationError("HistoricalDataIssue.detail must not be blank.")
        if self.row_number is not None and self.row_number < 1:
            raise ValidationError("HistoricalDataIssue.row_number must be at least 1, if set.")


@dataclass(frozen=True, slots=True)
class HistoricalDataValidation:
    """The full validation report for one
    :class:`~data.historical_data_source.HistoricalDataSource` read.

    Attributes:
        issues: Every :class:`HistoricalDataIssue` found, in the
            order encountered. Empty means the source is valid.
    """

    issues: tuple[HistoricalDataIssue, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        """Whether zero issues were found."""
        return len(self.issues) == 0

    def issues_of(self, kind: HistoricalDataIssueKind) -> tuple[HistoricalDataIssue, ...]:
        """Every recorded issue of ``kind``."""
        return tuple(issue for issue in self.issues if issue.kind is kind)

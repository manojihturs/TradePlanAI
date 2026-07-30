"""Tests for data.historical_data_validation."""

from __future__ import annotations

import pytest

from core.exceptions import ValidationError
from data.historical_data_validation import (
    HistoricalDataIssue,
    HistoricalDataIssueKind,
    HistoricalDataValidation,
)


class TestHistoricalDataIssue:
    def test_valid_construction(self) -> None:
        issue = HistoricalDataIssue(
            kind=HistoricalDataIssueKind.SCHEMA_ERROR, detail="bad row", row_number=3
        )

        assert issue.row_number == 3

    def test_none_kind_raises(self) -> None:
        with pytest.raises(ValidationError, match="kind must not be None"):
            HistoricalDataIssue(kind=None, detail="bad row")  # type: ignore[arg-type]

    def test_blank_detail_raises(self) -> None:
        with pytest.raises(ValidationError, match="detail must not be blank"):
            HistoricalDataIssue(kind=HistoricalDataIssueKind.SCHEMA_ERROR, detail="  ")

    def test_zero_row_number_raises(self) -> None:
        with pytest.raises(ValidationError, match="row_number must be at least 1"):
            HistoricalDataIssue(
                kind=HistoricalDataIssueKind.SCHEMA_ERROR, detail="bad row", row_number=0
            )


class TestHistoricalDataValidation:
    def test_valid_when_no_issues(self) -> None:
        validation = HistoricalDataValidation()

        assert validation.is_valid is True

    def test_invalid_when_issues_present(self) -> None:
        validation = HistoricalDataValidation(
            issues=(HistoricalDataIssue(kind=HistoricalDataIssueKind.SCHEMA_ERROR, detail="bad"),)
        )

        assert validation.is_valid is False

    def test_issues_of_filters_by_kind(self) -> None:
        validation = HistoricalDataValidation(
            issues=(
                HistoricalDataIssue(kind=HistoricalDataIssueKind.SCHEMA_ERROR, detail="a"),
                HistoricalDataIssue(kind=HistoricalDataIssueKind.INVALID_VOLUME, detail="b"),
                HistoricalDataIssue(kind=HistoricalDataIssueKind.SCHEMA_ERROR, detail="c"),
            )
        )

        assert len(validation.issues_of(HistoricalDataIssueKind.SCHEMA_ERROR)) == 2
        assert len(validation.issues_of(HistoricalDataIssueKind.INVALID_VOLUME)) == 1
        assert validation.issues_of(HistoricalDataIssueKind.DUPLICATE_TIMESTAMP) == ()

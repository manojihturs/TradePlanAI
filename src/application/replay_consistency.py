"""ReplayConsistencyValidator: detects replay inconsistencies in a ReplayResult.

Traceability
------------
Sprint: "Replay Consistency Validator" (Compact Development Mode) -
observability only, no new business rule. Reads an already-completed
``application.replay_result.ReplayResult`` and checks, per candle,
five structural facts the sprint itself names:

  1. Reference Strike exists      -> ``PipelineContext.reference_strike``
  2. ReferenceLevel exists        -> ``PipelineContext.reference_data`` non-empty
  3. Weekly Future generated      -> ``PipelineContext.weekly_future``
  4. Strike generated             -> ``PipelineContext.selected_strike``
  5. Pipeline completed           -> ``BusinessResult.success``

None of these recompute or reinterpret a business value - each is a
plain presence/success check against fields
``business.stages.weekly_future_stage.WeeklyFutureStage`` (or the
pipeline itself) already wrote. A missing value is reported as an
inconsistency, not silently treated as an error or repaired - this
module only observes and reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from application.replay_result import ReplayResult
from core.exceptions import ValidationError

CHECK_REFERENCE_STRIKE = "reference_strike_exists"
CHECK_REFERENCE_LEVEL = "reference_level_exists"
CHECK_WEEKLY_FUTURE = "weekly_future_generated"
CHECK_STRIKE_SELECTION = "strike_generated"
CHECK_PIPELINE_COMPLETED = "pipeline_completed"


@dataclass(frozen=True, slots=True)
class ReplayConsistencyIssue:
    """One failed consistency check for one candle.

    Attributes:
        candle_timestamp: The candle this issue concerns.
        check: Which check failed - one of the ``CHECK_*`` constants.
        message: A human-readable description of what was missing.
    """

    candle_timestamp: datetime
    check: str
    message: str

    def __post_init__(self) -> None:
        if self.candle_timestamp is None:
            raise ValidationError("ReplayConsistencyIssue.candle_timestamp must not be None.")
        if not self.check or not self.check.strip():
            raise ValidationError("ReplayConsistencyIssue.check must not be blank.")
        if not self.message or not self.message.strip():
            raise ValidationError("ReplayConsistencyIssue.message must not be blank.")


def validate_replay_consistency(result: ReplayResult) -> tuple[ReplayConsistencyIssue, ...]:
    """Check every candle in ``result.business_results`` against the
    five consistency rules named above, returning one
    :class:`ReplayConsistencyIssue` per failed check, in candle order."""
    issues: list[ReplayConsistencyIssue] = []
    for business_result in result.business_results:
        context = business_result.context
        timestamp = context.candle_timestamp

        if context.reference_strike is None:
            issues.append(
                ReplayConsistencyIssue(
                    candle_timestamp=timestamp,
                    check=CHECK_REFERENCE_STRIKE,
                    message="Reference Strike is missing.",
                )
            )
        if not context.reference_data:
            issues.append(
                ReplayConsistencyIssue(
                    candle_timestamp=timestamp,
                    check=CHECK_REFERENCE_LEVEL,
                    message="Reference ladder (ReferenceLevel data) is missing.",
                )
            )
        if context.weekly_future is None:
            issues.append(
                ReplayConsistencyIssue(
                    candle_timestamp=timestamp,
                    check=CHECK_WEEKLY_FUTURE,
                    message="Weekly Future was not generated.",
                )
            )
        if context.selected_strike is None:
            issues.append(
                ReplayConsistencyIssue(
                    candle_timestamp=timestamp,
                    check=CHECK_STRIKE_SELECTION,
                    message="Top/Bottom Strike was not generated.",
                )
            )
        if not business_result.success:
            reason = str(business_result.error) if business_result.error else "UNRESOLVED"
            issues.append(
                ReplayConsistencyIssue(
                    candle_timestamp=timestamp,
                    check=CHECK_PIPELINE_COMPLETED,
                    message=f"Pipeline did not complete: {reason}",
                )
            )

    return tuple(issues)


def render_consistency_report(issues: tuple[ReplayConsistencyIssue, ...]) -> str:
    """Render ``issues`` as a plain multi-line report - one line per
    issue, or a single "no inconsistencies found" line when empty."""
    if not issues:
        return "No inconsistencies found."
    return "\n".join(
        f"{issue.candle_timestamp.isoformat()} [{issue.check}] {issue.message}" for issue in issues
    )

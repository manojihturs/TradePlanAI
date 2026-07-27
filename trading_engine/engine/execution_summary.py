"""ExecutionSummary: aggregate outcome counts for one ExecutionReport.

Traceability notes
-------------------
A pure aggregation over :class:`~trading_engine.rules.outcome.RuleOutcome`
values already present in an
:class:`~trading_engine.engine.execution_report.ExecutionReport` -
counting, not concluding. No trading conclusion is drawn from these
counts (e.g. "N rules PASS-ed" implies nothing about a trading
decision - ``docs/TRADINGVIEW_STRATEGY_BIBLE.md``'s ``ENTRY``/``EXIT``
categories remain empty, so no combination rule over outcomes exists
to apply here).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta

from trading_engine.engine.exceptions import PipelineExecutionError
from trading_engine.engine.execution_report import ExecutionReport
from trading_engine.rules.outcome import RuleOutcome


@dataclass(frozen=True)
class ExecutionSummary:
    """Aggregate RuleOutcome counts for one ExecutionReport.

    Rule References
        None directly - a structural aggregate over already-produced
        RuleExecutionResult outcomes.

    Attributes:
        total_rules: The total number of results summarised (i.e.
            ``len(report.results)``).
        pass_count: How many results had outcome ``PASS``.
        fail_count: How many results had outcome ``FAIL``.
        unknown_count: How many results had outcome ``UNKNOWN``.
        insufficient_evidence_count: How many results had outcome
            ``INSUFFICIENT_EVIDENCE``.
        not_applicable_count: How many results had outcome
            ``NOT_APPLICABLE``.
        duration: The wall-clock duration of the summarised run.
    """

    total_rules: int
    pass_count: int
    fail_count: int
    unknown_count: int
    insufficient_evidence_count: int
    not_applicable_count: int
    duration: timedelta

    def __post_init__(self) -> None:
        counts = (
            self.pass_count,
            self.fail_count,
            self.unknown_count,
            self.insufficient_evidence_count,
            self.not_applicable_count,
        )

        if self.total_rules < 0 or any(count < 0 for count in counts):
            raise PipelineExecutionError("ExecutionSummary counts must not be negative.")

        if sum(counts) != self.total_rules:
            raise PipelineExecutionError(
                "ExecutionSummary per-outcome counts must sum to total_rules."
            )

    @classmethod
    def from_report(cls, report: ExecutionReport) -> ExecutionSummary:
        """Build an ExecutionSummary by counting the RuleOutcome values
        already present in ``report.results``.

        Performs no calculation beyond counting - the outcomes
        themselves were produced by whichever rules evaluated
        (Milestone 4.3 has no implemented rule mathematics, so every
        outcome observed today is UNKNOWN in practice).
        """
        if report is None:
            raise PipelineExecutionError("ExecutionSummary.from_report(report) must not be None.")

        outcome_counts = Counter(result.outcome for result in report.results)
        return cls(
            total_rules=len(report.results),
            pass_count=outcome_counts.get(RuleOutcome.PASS, 0),
            fail_count=outcome_counts.get(RuleOutcome.FAIL, 0),
            unknown_count=outcome_counts.get(RuleOutcome.UNKNOWN, 0),
            insufficient_evidence_count=outcome_counts.get(RuleOutcome.INSUFFICIENT_EVIDENCE, 0),
            not_applicable_count=outcome_counts.get(RuleOutcome.NOT_APPLICABLE, 0),
            duration=report.duration,
        )

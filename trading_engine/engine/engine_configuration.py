"""EngineConfiguration: storage for orchestration-level engine settings.

Traceability notes
-------------------
No entry in ``docs/RULE_INDEX.md`` or ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md``
specifies how a Rule Engine should behave under partial failure, rule
count limits, or logging/dry-run modes - these are orchestration
concerns invented by the Milestone 4.3 instruction itself ("Fail
Fast", "Continue On Error", "Maximum Rule Count", "Logging Enabled",
"Dry Run"), not recovered business rules. Per that instruction, this
module is "Only configuration storage": it validates that the stored
values are internally consistent, but does not itself decide *how*
:class:`~trading_engine.engine.execution_pipeline.ExecutionPipeline`
behaves for every field - see the ``# TODO`` notes on ``logging_enabled``
in :mod:`.execution_pipeline` for the one field this milestone leaves
entirely unwired.
"""

from __future__ import annotations

from dataclasses import dataclass

from trading_engine.diagnostics.sink import DiagnosticsSink
from trading_engine.engine.exceptions import EngineConfigurationError


@dataclass(frozen=True)
class EngineConfiguration:
    """Orchestration-level settings for a
    :class:`~trading_engine.engine.strategy_engine.StrategyEngine` run.

    A pure value object - it stores settings, it does not apply them.
    See :mod:`.execution_pipeline` for which of these fields the
    Pipeline actually reads.

    Attributes:
        fail_fast: If ``True``, an unexpected (non-Rule-Framework)
            exception raised by a rule's ``evaluate()`` immediately
            aborts the run by raising
            :class:`~trading_engine.engine.exceptions.PipelineExecutionError`.
            Mutually exclusive with ``continue_on_error``.
        continue_on_error: If ``True``, an unexpected exception raised
            by a rule's ``evaluate()`` is recorded as an error and
            evaluation continues with the next rule, instead of
            stopping. Mutually exclusive with ``fail_fast``.
        maximum_rule_count: If set, the maximum number of rules the
            Pipeline will evaluate in one run before stopping (recorded
            as a warning, not an error). ``None`` means unbounded. Must
            be a positive integer if set.
        logging_enabled: Whether
            :class:`~trading_engine.rules.registry.RuleRegistry` and
            the Strategy Engine should emit diagnostic events (see
            ``trading_engine/diagnostics/``) for this run. When
            ``False`` (the default), every diagnostic emission point
            is routed to
            :class:`~trading_engine.diagnostics.sink.NullDiagnosticsSink`
            regardless of ``diagnostics_sink``, guaranteeing a true
            no-op.
        dry_run: If ``True``, the Pipeline enumerates the rules it
            would evaluate but does not call any rule's ``evaluate()``
            - no RuleExecutionResult is produced for any rule.
        diagnostics_sink: Where diagnostic events are sent when
            ``logging_enabled`` is ``True``. ``None`` (the default)
            means "use
            :class:`~trading_engine.diagnostics.sink.StandardLoggingDiagnosticsSink`" -
            see
            :meth:`~trading_engine.engine.strategy_engine.StrategyEngine.run`.
            Ignored entirely when ``logging_enabled`` is ``False``.
    """

    fail_fast: bool = False
    continue_on_error: bool = True
    maximum_rule_count: int | None = None
    logging_enabled: bool = False
    dry_run: bool = False
    diagnostics_sink: DiagnosticsSink | None = None

    def __post_init__(self) -> None:
        if self.fail_fast and self.continue_on_error:
            raise EngineConfigurationError(
                "EngineConfiguration.fail_fast and .continue_on_error "
                "cannot both be True - they are contradictory settings."
            )

        if self.maximum_rule_count is not None and self.maximum_rule_count <= 0:
            raise EngineConfigurationError(
                "EngineConfiguration.maximum_rule_count must be a positive " "integer when set."
            )

"""ExecutionPipeline: iterate rules, call evaluate(), collect results.

Traceability notes
-------------------
See ``docs/architecture/RULE_ENGINE_ARCHITECTURE.md`` ("Rule
Evaluation Pipeline"), steps 2-4: "Look up all active ... rules ...
For each rule, evaluate it ... producing zero or one Rule Result per
rule per step. Collect Rule Results into a Decision Object." This
module implements exactly that iterate/call/collect shape at the
orchestration layer - it sequences and collects, it does not decide
what a rule concludes, per that document's "No cross-rule logic
invented" note. Step 5 ("Apply any resulting Session State updates")
and step 1 ("Assemble Market Context") are both out of this module's
scope - the caller (:class:`~trading_engine.engine.strategy_engine.StrategyEngine`)
supplies an already-assembled
:class:`~trading_engine.rules.context.RuleExecutionContext`, and no
Session State mutation happens anywhere in this package.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from trading_engine.engine.engine_configuration import EngineConfiguration
from trading_engine.engine.exceptions import PipelineExecutionError
from trading_engine.rules.context import RuleExecutionContext
from trading_engine.rules.exceptions import RuleFrameworkError
from trading_engine.rules.outcome import RuleExecutionResult
from trading_engine.rules.protocols import Rule


@dataclass(frozen=True)
class PipelineOutcome:
    """The raw collections produced by one
    :meth:`ExecutionPipeline.run` call, before
    :class:`~trading_engine.engine.strategy_engine.StrategyEngine`
    wraps them into an
    :class:`~trading_engine.engine.execution_report.ExecutionReport`.

    A plain data holder - no validation beyond immutability, since it
    is only ever constructed by :meth:`ExecutionPipeline.run` itself.
    """

    rules_executed: tuple[str, ...] = field(default_factory=tuple)
    results: tuple[RuleExecutionResult, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)


class ExecutionPipeline:
    """Iterates a sequence of rules, calls each one's ``evaluate()``,
    and collects the results.

    Rule References
        None directly - operates on whichever rules it is given.

    Responsible only for iterating rules, calling ``evaluate()``,
    collecting results, and stopping on fatal Rule Framework
    exceptions (see :meth:`run`). Contains no ``if strike`` / ``if
    trend`` / ``if reversal`` or other business-logic branch - see the
    Architecture Rule in ``trading_engine/engine/__init__.py``.
    """

    def run(
        self,
        rules: Sequence[Rule],
        context: RuleExecutionContext,
        configuration: EngineConfiguration,
    ) -> PipelineOutcome:
        """Evaluate ``rules`` in order against ``context``.

        Stopping conditions (in the order checked, per rule):

        1. ``configuration.maximum_rule_count`` reached: a warning is
           recorded and iteration stops - not an error.
        2. A Rule Framework exception
           (:class:`~trading_engine.rules.exceptions.RuleFrameworkError`)
           is raised by ``rule.evaluate()``: this is always fatal per
           the Milestone 4.3 instruction ("Stopping on fatal framework
           exceptions") - the error is recorded and iteration stops,
           regardless of ``configuration.fail_fast``/``continue_on_error``.
        3. Any other, unexpected exception is raised by
           ``rule.evaluate()``: not a Rule Framework exception, so not
           covered by rule 2. If ``configuration.fail_fast`` is
           ``True``, this immediately raises
           :class:`~trading_engine.engine.exceptions.PipelineExecutionError`.
           If ``configuration.continue_on_error`` is ``True``, the
           error is recorded and iteration continues with the next
           rule. Otherwise, the error is recorded and iteration stops.

        If ``configuration.dry_run`` is ``True``, no rule's
        ``evaluate()`` is called at all - every rule is recorded into
        ``rules_executed`` with no corresponding result, and a warning
        notes the dry run.
        """
        rules_executed: list[str] = []
        results: list[RuleExecutionResult] = []
        warnings: list[str] = []
        errors: list[str] = []

        for rule in rules:
            if (
                configuration.maximum_rule_count is not None
                and len(rules_executed) >= configuration.maximum_rule_count
            ):
                warnings.append(
                    f"Maximum rule count ({configuration.maximum_rule_count}) reached; "
                    f"stopping before evaluating rule {rule.id()!r}."
                )
                break

            rules_executed.append(rule.id())

            if configuration.dry_run:
                warnings.append(f"Dry run: rule {rule.id()!r} was not evaluated.")
                continue

            try:
                result = rule.evaluate(context)
            except RuleFrameworkError as exc:
                errors.append(f"Fatal framework exception evaluating rule {rule.id()!r}: {exc}")
                break
            except Exception as exc:
                message = f"Unexpected exception evaluating rule {rule.id()!r}: {exc}"
                if configuration.fail_fast:
                    raise PipelineExecutionError(message) from exc
                errors.append(message)
                if configuration.continue_on_error:
                    continue
                break
            else:
                results.append(result)

        return PipelineOutcome(
            rules_executed=tuple(rules_executed),
            results=tuple(results),
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    # TODO (RULE_ENGINE_ARCHITECTURE): configuration.logging_enabled is
    # stored by EngineConfiguration but never read here - no logging
    # format/destination is evidenced anywhere in the reviewed
    # documents, so no logging implementation exists in this
    # milestone.

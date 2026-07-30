# Implementation Readiness

For every module/class from `CLASS_DIAGRAM.md`: READY / PARTIAL /
BLOCKED (this document's own 3-value rubric, distinct from
CLASS_DIAGRAM.md's own READY/PARTIAL/UNKNOWN rubric).

## Rubric reconciliation

The two rubrics are related but not identical, and the mapping is made
explicit here rather than silently used side by side:

- CLASS_DIAGRAM.md's **UNKNOWN** = "no evidence at all exists for the
  class's purpose" (a description of the *evidence state*).
- This document's **BLOCKED** = "cannot be implemented with real logic
  given current evidence" (a description of the *practical
  implementation consequence*).
- In practice, every class marked UNKNOWN in CLASS_DIAGRAM.md is
  BLOCKED here, because an unevidenced purpose cannot be implemented.
  Every class marked PARTIAL in CLASS_DIAGRAM.md is also BLOCKED here
  for its *business-logic* content specifically — the shape/contract
  is implementable now (structurally already built, in most cases),
  but the calculation inside it cannot be, per
  `KNOWLEDGE_DEPENDENCY_MATRIX.md`'s closing finding: "0 of 24 rows...
  are READY." **This document's READY is therefore reserved for pure
  engineering scaffolding that carries no business mathematics at all**
  (registries, protocols, pipelines) — the same items
  `SAFE_IMPLEMENTATION_SCOPE.md`'s "SAFE NOW" section already
  identifies. No class whose purpose is a business calculation is
  marked READY anywhere in this document, matching CLASS_DIAGRAM.md's
  own "READY should be essentially unused here" instruction.

---

| Class | Readiness | Reason | Blocking dependency | Evidence source |
|---|---|---|---|---|
| MarketDataProvider | BLOCKED | No broker/protocol/data-shape evidenced anywhere | FSD Section 13 (Upstox Integration, zero evidence); `IMPLEMENTATION_UNLOCK_SEQUENCE.md` "Not ranked (out of scope)" row | `REALTIME_TRADING_SPECIFICATION.md` §13 |
| OptionChainProvider | BLOCKED | No option-chain data shape evidenced beyond Call/Put first-candle High/Low concept | Same as MarketDataProvider; also depends on MarketDataProvider itself being BLOCKED | `REALTIME_TRADING_SPECIFICATION.md` §2, §13 |
| WeeklyFutureCalculator | BLOCKED | Self-contradictory single worked example; zero of 3 required consistent worked examples exist | Weekly Future High/Low arithmetic (ENT-010) — `IMPLEMENTATION_UNLOCK_SEQUENCE.md` rank 1 (Critical) | `WEEKLY_FUTURE_VERIFICATION.md`; `KNOWLEDGE_DEPENDENCY_MATRIX.md` ENT-010 row |
| StrikeEngine | BLOCKED | Own selection heuristic PARTIALLY READY, but overall NOT READY due to Weekly Future dependency | WeeklyFutureCalculator (above) | `STRIKE_EVIDENCE_SUMMARY.md`; `KNOWLEDGE_GAP_INVENTORY.md` STRIKE-001 row |
| OptionRangeEngine | BLOCKED | Zero repository evidence for range width, ITM/OTM definition, or selection mechanism | Not ranked / zero engineering impact — `IMPLEMENTATION_UNLOCK_SEQUENCE.md` "Not ranked" row | `REALTIME_TRADING_SPECIFICATION.md` §4 |
| PremiumSnapshotEngine | BLOCKED | No CE/PE structure or capture formula evidenced beyond raw observation | Deliberately thin model, `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 179-190 | `REALTIME_TRADING_SPECIFICATION.md` §3; `KNOWLEDGE_GAP_INVENTORY.md` ENT-009 row |
| LevelEngine | BLOCKED | Entire scope and mathematics unevidenced; no rule/entity ID exists for "Level" | Not ranked / zero engineering impact | `REALTIME_TRADING_SPECIFICATION.md` §5 |
| TrendEngine | BLOCKED | TP Low formula unevidenced (Partially Known); "market structure change" trigger fully Unknown; "well below" threshold unquantified | TrendPoint (TP Low) calculation formula (TREND-001) — `IMPLEMENTATION_UNLOCK_SEQUENCE.md` rank 4 (High) | `KNOWLEDGE_GAP_INVENTORY.md` TREND-001/002/003 rows |
| CompetitorEngine | BLOCKED | "Defeat" condition an explicit unresolved Open Question; OPPONENT-002/003 Evidence Count 0 | "Defeat" condition + Opponent High/Low (OPPONENT-001, ENT-005/006/007) — `IMPLEMENTATION_UNLOCK_SEQUENCE.md` rank 5 (High) | `KNOWLEDGE_GAP_INVENTORY.md` OPPONENT-001/002/003 rows |
| WinnerEngine | BLOCKED | Entire concept unevidenced; no rule ID, entity ID, or Bible category exists | Not ranked / zero engineering impact — `IMPLEMENTATION_UNLOCK_SEQUENCE.md` "Not ranked (out of scope)" row | `REALTIME_TRADING_SPECIFICATION.md` §8 |
| TradeEngine (Entry) | BLOCKED | Documented non-rule — Bible ENTRY category empty; entry explicitly framed as "logical," not indicator-based | Not ranked (documented non-rule, not a resolvable evidence gap in the ranked sense) | `REALTIME_TRADING_SPECIFICATION.md` §9 |
| ExitEngine | BLOCKED | Documented non-rule — Bible EXIT category empty; also depends on ReversalCalculator, itself the worst-evidenced rule in the project | Premium behaviour -> Reversal identification method (REVERSAL-001) — `IMPLEMENTATION_UNLOCK_SEQUENCE.md` rank 3 (High) | `REALTIME_TRADING_SPECIFICATION.md` §10; `KNOWLEDGE_GAP_INVENTORY.md` REVERSAL-001 row |
| RiskEngine | BLOCKED | Documented non-rule — explicit, repeated statement that risk sizing is subjective; two inconsistent illustrative figures never reconciled | Not ranked (documented non-rule) | `REALTIME_TRADING_SPECIFICATION.md` §11 |
| PaperTradeEngine | BLOCKED | No paper-trading data shape evidenced; explicitly gated behind Backtest, itself gated behind real rule implementations | "Backtest... Blocked on: Real rule implementations existing" | `IMPLEMENTATION_UNLOCK_SEQUENCE.md` "Long-term, evidence-gated validation activities" |
| DashboardService | PARTIAL (plumbing) / BLOCKED (content) | Read-only wiring to already-existing domain objects is buildable now; layout/cadence/alerting/charting are zero-evidence | Zero repository evidence for dashboard specifics | `REALTIME_TRADING_SPECIFICATION.md` §14 |
| StorageService | BLOCKED (live) / READY (historical precedent only) | No live-storage schema evidenced; `HistoryLoader`'s CSV-reading precedent for historical data is fully built and requires no further evidence | Real-Time Data Requirements (data retention/replay requirements UNKNOWN) | `REALTIME_TRADING_SPECIFICATION.md` §12; `REPLAY_ENGINE_ARCHITECTURE.md` |
| ReplayService (ReplayController) | READY | Already fully built, frozen, evidence-independent — coordinates HistoryLoader/ReplayClock/ReplaySession/StrategyEngine without any business mathematics | None — "Requires Evidence: No" per architecture freeze checklist | `ARCHITECTURE_FREEZE_CHECKLIST.md` row "Registry"/"Execution pipeline"; `REPLAY_ENGINE_ARCHITECTURE.md` |
| StrategyEngine / ExecutionPipeline (supporting infra) | READY | Complete, tested, evidence-independent orchestration; contains no business mathematics by design | None | `ARCHITECTURE_FREEZE_CHECKLIST.md` rows "Strategy engine", "Execution pipeline" |
| RuleRegistry / CalculatorRegistry (supporting infra) | READY | Complete, tested, evidence-independent; topological ordering operates on already-documented dependency structure, not undiscovered mathematics | None | `ARCHITECTURE_FREEZE_CHECKLIST.md` rows "Registry", "Dependency engine" |
| DiagnosticsSink + implementations (supporting infra) | READY | Complete, tested, evidence-independent; zero dependency on rules/engine/calculators | None | `ARCHITECTURE_FREEZE_CHECKLIST.md` row "Diagnostics"; `FRAMEWORK_BASELINE_REPORT.md` Section 2 item 5 |

---

## Readiness summary

| Readiness | Count | Classes |
|---|---|---|
| READY | 5 | ReplayService, StrategyEngine/ExecutionPipeline, RuleRegistry/CalculatorRegistry, DiagnosticsSink group, (StorageService's historical-precedent-only sub-case) |
| PARTIAL | 1 | DashboardService (plumbing only; content BLOCKED) |
| BLOCKED | 14 | MarketDataProvider, OptionChainProvider, WeeklyFutureCalculator, StrikeEngine, OptionRangeEngine, PremiumSnapshotEngine, LevelEngine, TrendEngine, CompetitorEngine, WinnerEngine, TradeEngine, ExitEngine, RiskEngine, PaperTradeEngine, StorageService (live case) |

**Overall: every class whose purpose is a business calculation or a
live-data integration is BLOCKED. Only pre-existing, evidence-
independent engineering scaffolding (already built in Milestones
4.2-6.5 and B1) is READY.** This matches
`KNOWLEDGE_DEPENDENCY_MATRIX.md`'s own closing finding — "0 of 24 rows
... are READY" — extended here to the FSD's live-trading class list:
the same root cause (unresolved or contradictory trading-mathematics
evidence, not missing engineering) blocks every business-logic class
in this blueprint, exactly as it blocks every existing calculator in
`trading_engine/calculators/`.

---

Sources: `research/implementation/CLASS_DIAGRAM.md` (this directory);
`research/analysis/KNOWLEDGE_DEPENDENCY_MATRIX.md`;
`research/analysis/IMPLEMENTATION_UNLOCK_SEQUENCE.md`;
`research/analysis/KNOWLEDGE_GAP_INVENTORY.md`;
`research/analysis/ARCHITECTURE_FREEZE_CHECKLIST.md`;
`research/analysis/FRAMEWORK_BASELINE_REPORT.md`;
`research/analysis/REPLAY_ENGINE_ARCHITECTURE.md`;
`research/specification/REALTIME_TRADING_SPECIFICATION.md` Sections
2-14.

# Implementation Phases

Phase numbering per the milestone brief's own example (Phase 1
Infrastructure ... Phase 10 Integration). Order justified by
`research/analysis/IMPLEMENTATION_UNLOCK_SEQUENCE.md`'s existing
Critical/High/Medium/Low ranking and
`research/analysis/KNOWLEDGE_DEPENDENCY_MATRIX.md`'s dependency chain
— not a newly invented prioritization scheme. SAFE NOW / PARTIALLY
SAFE / BLOCKED framing reused directly from
`research/analysis/SAFE_IMPLEMENTATION_SCOPE.md` (Milestone 6.0A).

---

## Phase 1 — Infrastructure

**Classification: SAFE NOW.** Already substantially built
(`ARCHITECTURE_FREEZE_CHECKLIST.md`: "9 of 9 subsystems Frozen = Yes")
— `domain/`, `rules/`, `engine/`, `calculators/`, `diagnostics/`,
`replay/`. Remaining SAFE NOW work: the new `market_data/` and `live/`
package shells (empty module scaffolding only — see
IMPLEMENTATION_BLUEPRINT.md §1b), calculator-level test files for the
5 concrete placeholder calculators (`SAFE_IMPLEMENTATION_SCOPE.md`
"Genuinely open, safe-to-do-next"), and a `Rule.depends_on()` protocol
method (currently only the registry's external table knows
dependencies — `FRAMEWORK_BASELINE_REPORT.md` Section 5 item 6, SAFE
mechanical addition).

## Phase 2 — Market Data

**Classification: PARTIALLY SAFE.** The connection/parsing *layer*
(e.g. a generic `MarketDataProvider`/`IOptionProvider` interface shell
and package structure) is evidence-independent scaffolding, following
the same pattern `HistoryLoader` already establishes for historical
CSV parsing (`REPLAY_ENGINE_ARCHITECTURE.md`). The moment any specific
broker, endpoint, or authentication mechanism is implemented, this
phase becomes **BLOCKED** — FSD Section 13: "Zero mentions anywhere...
of any specific broker, REST API, WebSocket protocol, or
authentication mechanism." No content can be filled in without new,
currently-nonexistent evidence.

## Phase 3 — Weekly Future / Strike Engine

**Classification: BLOCKED.** Per
`IMPLEMENTATION_UNLOCK_SEQUENCE.md` rank 1-2 (Critical): "Weekly
Future High/Low arithmetic (ENT-010)... highest-impact,
lowest-remaining-effort item," and "External 'Complete Calculation
Video for Weekly Future'... the single most concrete, lowest-effort
acquisition action." Both `weekly_future_calculator.py` and
`strike_calculator.py` already exist, structurally correct, "simply
waiting for a formula to fill their `calculate()` bodies"
(`FRAMEWORK_BASELINE_REPORT.md` Section 7) — the calculators
themselves need no further engineering, only evidence.

## Phase 4 — Premium Snapshot / Level Engine

**Classification: PARTIALLY SAFE for Premium (already exists as a
thin value holder), BLOCKED for any "capture formula" or Level Engine
content.** `Premium` (`trading_engine/domain/premium.py`) is already
built and does not require further evidence to exist as a value
holder. Filling in any CE/PE-specific structure, a capture cadence, or
the Level Engine's own scope would require evidence
`KNOWLEDGE_GAP_INVENTORY.md` Section 3 (ENT-009 row) confirms does not
exist ("no rule defines Premium as a first-class concept yet").

## Phase 5 — Trend Engine / Competitor Engine

**Classification: BLOCKED.** Per `IMPLEMENTATION_UNLOCK_SEQUENCE.md`
ranks 3-5 (High): TrendPoint (TP Low) calculation formula
(TREND-001), "defeat" condition + Opponent High/Low (OPPONENT-001,
ENT-005/006/007). Step 3 of that document's roadmap notes TREND-001
"unblocks the largest raw count of dependent rules... but does not
make any of them fully READY by itself" — resolving it alone would not
complete this phase; OPPONENT-002/003 (Evidence Count 0) remain "the
furthest from READY of any item in this list."

## Phase 6 — Winner Engine

**Classification: BLOCKED, and not ranked in
`IMPLEMENTATION_UNLOCK_SEQUENCE.md`'s Task 6a table at all** — the
document's "Not ranked (out of scope)" row explicitly lists Winner
Engine among the "zero-repository-evidence items introduced by this
milestone's own user-supplied workflow, not previously ranked by any
prior milestone." No engineering scaffolding beyond a class shell
(see CLASS_DIAGRAM.md §10) can meaningfully precede evidence here,
since even the concept's existence is undocumented outside this
milestone's workflow.

## Phase 7 — Entry / Exit / Risk Engine

**Classification: BLOCKED, but by a documented non-rule rather than a
mere evidence gap.** FSD Sections 9-11 each document an explicit,
repeated statement in TR-001 that entry/exit/risk sizing are
"logical"/personal judgments, not fixed formulas. Per
`IMPLEMENTATION_UNLOCK_SEQUENCE.md`'s "After all evidence steps"
section, even resolving every other rule's mathematics would not by
itself close this phase, since "no cross-rule synthesis/combination
logic is evidenced or designed for the Decision Object" — the same
architectural gap that blocks final Decision production blocks a
completed Entry/Exit/Risk chain.

## Phase 8 — Option Range Engine

**Classification: BLOCKED, out-of-scope-for-ranking per
`IMPLEMENTATION_UNLOCK_SEQUENCE.md`'s "Not ranked" row** — same
category as Winner Engine, Real-Time Data Requirements, Upstox
Integration, and Live Dashboard: "zero-repository-evidence items...
not previously ranked by any prior milestone." A direct grep of
TR-001.md for "ITM"/"OTM" returns zero matches (FSD Section 4).

## Phase 9 — Dashboard

**Classification: PARTIALLY SAFE — plumbing-without-content is SAFE
NOW, content is BLOCKED.** A `DashboardService` class shell that reads
already-existing domain objects (Strike, Premium, SessionState — see
DATA_MODEL_BLUEPRINT.md §13) is evidence-independent wiring, no
different in kind from `ReplayController`'s existing pattern of
orchestrating already-built domain/engine layers without adding
business logic. Layout, refresh cadence, alerting, and charting
library choices remain BLOCKED — FSD Section 14: "Zero mentions of any
dashboard/UI specification anywhere in `docs/` or `research/`."

## Phase 10 — Integration

**Classification: BLOCKED indefinitely pending the same synthesis gap
noted in Phase 7.** `IMPLEMENTATION_UNLOCK_SEQUENCE.md`'s closing
section: "no cross-rule synthesis/combination logic is evidenced or
designed for the Decision Object (confirmed in code:
`domain/decision.py` line 105's TODO)... This is not fixed by
resolving any single rule's mathematics — it requires its own,
separate evidence." Replay-based integration testing with test-double
rules is separately available today (see below) but "produces no
trading-relevant validation until the steps above close"
(`IMPLEMENTATION_UNLOCK_SEQUENCE.md` "Long-term, evidence-gated
validation activities").

---

## Summary table

| Phase | Name | Classification |
|---|---|---|
| 1 | Infrastructure | SAFE NOW |
| 2 | Market Data | PARTIALLY SAFE (connection/parsing layer SAFE, broker specifics BLOCKED) |
| 3 | Weekly Future / Strike Engine | BLOCKED |
| 4 | Premium Snapshot / Level Engine | PARTIALLY SAFE (Premium value holder exists, formula/scope BLOCKED) |
| 5 | Trend Engine / Competitor Engine | BLOCKED |
| 6 | Winner Engine | BLOCKED (unranked — zero evidence for the concept itself) |
| 7 | Entry / Exit / Risk Engine | BLOCKED (documented non-rule + synthesis gap) |
| 8 | Option Range Engine | BLOCKED (unranked — zero evidence) |
| 9 | Dashboard | PARTIALLY SAFE (plumbing SAFE, content BLOCKED) |
| 10 | Integration | BLOCKED (synthesis/Decision-Object gap) |

**Separately available today, not tied to any phase above (per
`IMPLEMENTATION_UNLOCK_SEQUENCE.md` "Long-term, evidence-gated
validation activities"):** Replay validation (Milestone 4.5) "can be
exercised with test-double rules even before real mathematics exist" —
`trading_engine/replay/` already supports this today, using the
`context_factory` seam `REPLAY_ENGINE_ARCHITECTURE.md` describes.
Backtest and Paper Trading remain explicitly gated behind real rule
implementations existing.

---

Sources: `research/analysis/IMPLEMENTATION_UNLOCK_SEQUENCE.md`
(Task 6a ranking, Task 6b roadmap);
`research/analysis/KNOWLEDGE_DEPENDENCY_MATRIX.md`;
`research/analysis/SAFE_IMPLEMENTATION_SCOPE.md`;
`research/analysis/FRAMEWORK_BASELINE_REPORT.md`;
`research/analysis/ARCHITECTURE_FREEZE_CHECKLIST.md`;
`research/specification/REALTIME_TRADING_SPECIFICATION.md` Sections
4, 8-14.

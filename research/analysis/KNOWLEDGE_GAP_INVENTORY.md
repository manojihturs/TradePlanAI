# Knowledge Gap Inventory

Milestone K1 (Phase K: Knowledge Reconstruction). Consolidation-only
document: no new evidence is asserted, no formula or threshold is
invented. Task 1 (Rules) and Task 3 (Entities) are consolidated from
existing analysis docs, cross-checked for currency; Task 2
(Calculators) is freshly re-verified by reading the current source
files directly (`trading_engine/calculators/*.py`), not merely cited
from prior reports.

Where sources disagree, the newest/most rigorous verdict is used and
the override is stated explicitly. The single most important currency
note for this whole document: **`research/analysis/WEEKLY_FUTURE_VERIFICATION.md`
(Phase E1) is the most recent verdict on Weekly Future and supersedes
the older "PARTIALLY READY" verdict** found in
`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`, `ENTITY_DEPENDENCY_GRAPH.md`,
and `KNOWLEDGE_READINESS_DASHBOARD.md`. Phase E1 applied a stricter,
explicit rubric (three internally consistent worked examples required)
and found zero — its verdict is **NOT READY**, overriding "PARTIALLY
READY" wherever the two disagree below.

Sources found and read: `KNOWLEDGE_READINESS_DASHBOARD.md`,
`RULE_DEPENDENCY_GRAPH.md`, `ENTITY_DEPENDENCY_GRAPH.md`,
`FOUNDATIONAL_KNOWLEDGE_MAP.md`, `EXTERNAL_EVIDENCE_BACKLOG.md`,
`EVIDENCE_ACQUISITION_ROADMAP.md`, `WEEKLY_FUTURE_VERIFICATION.md`,
`STRIKE_EVIDENCE_SUMMARY.md`, `FRAMEWORK_BASELINE_REPORT.md`,
`docs/RULE_INDEX.md`, plus direct reads of all 6
`trading_engine/calculators/*.py` files and a grep-based pass over all
`trading_engine/domain/*.py` files for `class`/`TODO`/dataclass field
markers. Sources referenced in the task brief but not independently
re-read in full for this document (`IMPLEMENTATION_BLOCKERS.md`,
`SAFE_IMPLEMENTATION_SCOPE.md`, `IMPLEMENTATION_PRIORITY.md`,
`WEEKLY_FUTURE_EVIDENCE_TABLE.md`, `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`,
`STRIKE_EVIDENCE_TABLE.md`, `ARCHITECTURE_FREEZE_CHECKLIST.md`,
`RULE_DEPENDENCY_ENGINE_REPORT.md`, `DEPENDENCY_VALIDATION_REPORT.md`,
`docs/TRADINGVIEW_STRATEGY_BIBLE.md`, `docs/architecture/DOMAIN_ARCHITECTURE.md`)
exist at their listed paths and are cited indirectly, quoted through
the docs above, which themselves cite them directly — all exist in
`research/analysis/` or `docs/` per the directory listing taken at the
start of this task.

---

## Section 1 — Rules

One row per Rule ID (STRIKE-001, TREND-001, TREND-002, TREND-003,
OPPONENT-001, OPPONENT-002, OPPONENT-003, REVERSAL-001), using the most
recent verdict available.

| Rule ID | Status | Reason (cited) |
|---|---|---|
| STRIKE-001 | **Own evidence: PARTIALLY READY** (`STRIKE_EVIDENCE_SUMMARY.md` "Recommended Readiness Verdict": "upgraded confidence from the previous PARTIALLY READY verdict, but still short of READY" — strike-selection heuristic, top/bottom pairing, and nearest-strike rounding are evidence-grounded). **BUT downstream-blocked to NOT READY** because its own upstream input, Weekly Future High/Low, is NOT READY per `WEEKLY_FUTURE_VERIFICATION.md` (Phase E1, the most recent verdict, superseding the older Weekly Future PARTIALLY READY verdict). These are two distinct facts and are not conflated: STRIKE-001's own selection-heuristic evidence is materially further along than most other rules in this project, but the rule as a whole cannot be implemented end-to-end until Weekly Future is resolved (`FOUNDATIONAL_KNOWLEDGE_MAP.md` "Critical Blockers": "the only missing piece is a clean, verifiable Call/Put→Weekly-Future-High/Low formula"). |
| TREND-001 | NOT READY | Mathematical Definition: Partially Known — "no formula connecting Strike to a TP Low value" is evidenced (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 131; `FOUNDATIONAL_KNOWLEDGE_MAP.md` DAG Section 2). No new evidence-acquisition attempt has touched TREND-001 since Milestone 3.2 (`RULE_DEPENDENCY_GRAPH.md`: "they do not discuss TREND-001"). |
| TREND-002 | NOT READY | Mathematical Definition: Unknown; the "market structure change" trigger is itself Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 159; `docs/DOMAIN_MODEL.md` lines 93-95). No deeper-evidence doc addresses TREND-002 at all (`RULE_DEPENDENCY_GRAPH.md`). |
| TREND-003 | NOT READY | Mathematical Definition: Unknown; "well below" not quantified (`docs/TERMINOLOGY.md` lines 112-113). Also transitively blocked: depends on BOTH TREND-001 (Partially Known) AND OPPONENT-001 (Unknown, itself blocked by OPPONENT-002/003) per `docs/RULE_INDEX.md` row 33 / `docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 194. |
| OPPONENT-001 | NOT READY | Mathematical Definition: Unknown; the "defeat" condition is an explicit unresolved Open Question (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 235, lines 344-350). Also depends on TREND-001, OPPONENT-002, OPPONENT-003 (`docs/RULE_INDEX.md` row 34), all themselves unresolved. |
| OPPONENT-002 | NOT READY | Status: Awaiting Evidence, Evidence Count 0, "no behaviour defined" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 244-248; `docs/RULE_INDEX.md` row 35). TR-001 did not define it. |
| OPPONENT-003 | NOT READY | Status: Awaiting Evidence, Evidence Count 0, "no behaviour defined" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 250-254; `docs/RULE_INDEX.md` row 36). TR-001 did not define it. |
| REVERSAL-001 | NOT READY | Mathematical Definition: Unknown; "which specific premium behaviour constitutes identification is not established anywhere" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 286; `docs/DOMAIN_MODEL.md` lines 168-171). No natural-language rule shape has been stated anywhere yet (`FOUNDATIONAL_KNOWLEDGE_MAP.md` item 3) — the one rule with literally zero rule-shape evidence, as opposed to malformed/self-contradictory evidence. |

**Overall: 0 of 8 Rule IDs are READY. 0 are fully PARTIALLY READY
end-to-end** — STRIKE-001 has PARTIALLY READY evidence for its own
selection mechanism specifically, but is NOT READY overall due to its
Weekly Future dependency. All 8 rules are currently non-implementable.

---

## Section 2 — Calculators (fresh code verification)

All 6 calculator files in `trading_engine/calculators/` were read
directly for this document (not merely cited from prior reports),
cross-checked against `FRAMEWORK_BASELINE_REPORT.md`'s own
Milestone-6.5 code read, which reached the same conclusion
independently.

**Uniformity finding: confirmed, no exception found.** Every one of
the 6 `calculate()` methods does nothing but raise `NotImplementedError`
immediately, with only a `# TODO (<RULE-ID>)` comment preceding the
raise — no arithmetic, no conditional logic, no partial computation
exists in any of them. This matches `FRAMEWORK_BASELINE_REPORT.md`
Section 2, item 1's own finding exactly. The task brief's instruction
to "flag explicitly if ANY calculator has logic beyond raising
NotImplementedError" — flagged here: **none does.**

| Calculator File | Inputs (per docstring/`supported_rules()`) | Outputs | Unknown Mathematics (verbatim TODO) | Unknown Variables | Missing Evidence (cited) |
|---|---|---|---|---|---|
| `weekly_future_calculator.py` | Call option first-candle High/Low, Put option first-candle High/Low, ATM strike (per module docstring, lines 20-22) | Weekly Future High/Low (would feed STRIKE-001) | `"TODO (STRIKE-001): Weekly Future mathematics awaiting evidence."` (line 93; full comment block lines 83-92) | The Call/Put→Weekly-Future-High/Low combination formula; the Low-side sign-flip rule for all four (Call-High vs Put-Low)/(Put-High vs Call-Low) orderings | `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker" items 1-3; superseded readiness verdict now NOT READY per `WEEKLY_FUTURE_VERIFICATION.md` |
| `strike_calculator.py` | First Candle (per module docstring, referencing `docs/RULE_INDEX.md` STRIKE-001) | Selected Strike (ENT-001) | `"TODO (STRIKE-001): Strike mathematics awaiting evidence."` (line 57; comment lines 54-56) | The calculation connecting a session's First Candle to the resulting selected Strike | `docs/TRADINGVIEW_STRATEGY_BIBLE.md` Open Questions: "selected based on the first candle — selected how?" |
| `trend_calculator.py` | TrendPoint / Strike context, "market structure" change signal (per module docstring, TREND-001/TREND-002) | Updated Trend Point Low value | `"TODO (TREND-001): Trend mathematics awaiting evidence. How a Trend Point Low is computed, and how TREND-002's 'market structure change' is detected, are both Unknown."` (lines 62-64) | The TP Low value formula (TREND-001); the market-structure-change detection trigger (TREND-002) | `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 82-88; `docs/DOMAIN_MODEL.md` lines 93-95 |
| `opponent_calculator.py` | Opponent (ENT-005), Opponent High/Low (ENT-006/007) (per module docstring, OPPONENT-001/002/003) | "Defeated" opponent outcome | `"TODO (OPPONENT-001): Opponent mathematics awaiting evidence. What constitutes 'defeating' an opponent, and how Opponent High/Low (OPPONENT-002/003) are computed, are both Unknown."` (lines 72-74) | The "defeat" condition definition; Opponent High computation (OPPONENT-002); Opponent Low computation (OPPONENT-003) | `docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 344-350; `docs/RULE_INDEX.md` rows 35-36 (Evidence Count 0 both) |
| `reversal_calculator.py` | Premium (ENT-009) behaviour (per module docstring, REVERSAL-001) | Reversal identification (ENT-008) | `"TODO (REVERSAL-001): Reversal mathematics awaiting evidence. Which specific premium behaviour identifies a reversal is Unknown."` (lines 55-57) | Which specific premium behaviour constitutes reversal identification | `docs/DOMAIN_MODEL.md` lines 168-171; `docs/STATE_MACHINE.md` lines 148-150 (all entry conditions UNKNOWN) |
| `edge_calculator.py` | Current Strike's TrendPoint + Opponent's TrendPoint (per module docstring, TREND-003) | Edge condition evaluation (not a stored entity) | `"TODO (TREND-003): Edge mathematics awaiting evidence. How 'staying well below the strike' is quantified, for either TrendPoint, is Unknown."` (lines 56-58) | The "well below" threshold quantification; the Edge comparison formula itself | `docs/TERMINOLOGY.md` lines 112-113; `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 210-213 |

No calculator was found to have logic beyond the raise — this holds
uniformly across all 6 files, confirmed by direct line-level reading
plus cross-check against `FRAMEWORK_BASELINE_REPORT.md`'s independent
Milestone-6.5 verification of the same files.

---

## Section 3 — Entities

ENT-001 through ENT-014 plus UNK-001, per `docs/architecture/DOMAIN_ARCHITECTURE.md`
and `ENTITY_DEPENDENCY_GRAPH.md`, cross-checked against the actual
`trading_engine/domain/*.py` files (grep pass over `class`, `TODO`,
and dataclass-field markers performed for this document) for the 9
entities that have a domain file.

| Entity | Domain file? | Known/Unknown/Blocked | Missing attributes | Missing calculations |
|---|---|---|---|---|
| ENT-001 Strike | Yes — `domain/strike.py` (`class Strike`, `@dataclass(frozen=True)`) | Blocked | No price-value type, expiry, or option-side attribute evidenced (`docs/DOMAIN_MODEL.md` lines 37-38); code confirms only structural fields plus `# TODO (STRIKE-001)` at line 56 | The First-Candle→Strike selection calculation (`strike.py` line 56 TODO, verbatim: "The calculation connecting a session's First Candle to the resulting selected Strike" is unevidenced) |
| ENT-002 First Candle | No dedicated domain file — raw input, not a domain entity in code | Unknown | Exact time-window definition (session open? fixed time? duration?) Unknown (`docs/DOMAIN_MODEL.md` lines 52-55) | N/A — not computed, an input |
| ENT-003 TrendPoint (TP Low) | Yes — `domain/trend_point.py` (`class TrendPoint`) | Blocked | Code confirms two TODOs: line 77 "TODO (TREND-001): The formula that produces a TrendPoint's [value]" and line 79 "TODO (TREND-002): What constitutes 'market structure changes'" | The TP Low base-value formula (TREND-001); the update-trigger detection (TREND-002) |
| ENT-004 Market Structure | No dedicated domain file — referenced only as TREND-002's trigger condition | Unknown | "What constitutes 'market structure'... not defined" (`docs/DOMAIN_MODEL.md` lines 93-95) | N/A — not computed, an undefined signal |
| ENT-005 Opponent | Yes — `domain/opponent.py` (`class Opponent`) | Blocked | Code confirms `high`/`low` are documented in-file as "Reserved attribute slot only" (lines 50, 52) with 3 TODOs (lines 69, 72, 74) covering "defeat" math (OPPONENT-001) and Opponent High/Low zero-behaviour (OPPONENT-002/003) | The "defeat" condition math; Opponent High computation; Opponent Low computation. Relationship of "Opponent" to "competitor" elsewhere in repo also unconfirmed (`docs/TERMINOLOGY.md` lines 78-84) |
| ENT-006 Opponent High | Represented as a field (`Opponent.high`) inside `domain/opponent.py`, not its own file | Blocked | Reserved slot only, per in-code docstring; `FRAMEWORK_BASELINE_REPORT.md` Section 2 item 2 confirms `Opponent.high`/`Opponent.low` "are stored fields that are never read or compared in production code" | OPPONENT-002 computation, Evidence Count 0 |
| ENT-007 Opponent Low | Same file as ENT-006 (`Opponent.low` field) | Blocked | Same as ENT-006 | OPPONENT-003 computation, Evidence Count 0 |
| ENT-008 Reversal | No dedicated domain file (Reversal itself is not a class; represented via `Premium`/state machine) | Blocked | Identification method Unknown (`docs/DOMAIN_MODEL.md` lines 168-171) | Which premium behaviour constitutes identification |
| ENT-009 Premium | Yes — `domain/premium.py` (`class Premium`) | Blocked | Code docstring explicitly states: "No rule defines Premium as a first-class concept yet... CE/PE-specific structure now would be inventing attributes" (lines 6-9); one TODO at line 50 for REVERSAL-001 | Which contract (CE, PE, or both) Premium refers to; the reversal-identification rule itself |
| ENT-010 Weekly Future | **No domain file** — not represented as a `trading_engine/domain/*.py` class at all; exists only as a Candidate entity in documentation | **Blocked, and its readiness verdict has changed.** Originally framed as "Candidate, reserved, inactive... no computation designed" (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 242-246). `ENTITY_DEPENDENCY_GRAPH.md` and `KNOWLEDGE_READINESS_DASHBOARD.md` record an intermediate upgrade to **PARTIALLY READY** (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`, Milestone 5.0B). **This is superseded** by `WEEKLY_FUTURE_VERIFICATION.md` (Phase E1, most recent, stricter rubric): verdict is now **NOT READY** — zero of the required three internally consistent worked examples exist; the one worked example self-contradicts (91→81→82 addend; two different Low values "268"/26168 for the same candle; a Low numerically exceeding the High). This document treats Phase E1 as authoritative per the task's own instruction to prefer the newest, most rigorous verdict | Inputs are named (Call/Put first-candle High/Low/Close, ATM strike) but no working formula exists — see Task 2 above (`weekly_future_calculator.py`) |
| ENT-011 MidPoint | **No domain file** | Unknown/reserved (Candidate) | Top/Bottom strike are not themselves confirmed Domain objects yet (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 248-253) | Not integrated into any dependency chain; no rule depends on it |
| ENT-012 TriggerPoint | **No domain file** | Unknown/reserved (Candidate) | Described narratively with one worked example only, no computation evidenced (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 255-258) | Not integrated into any dependency chain |
| ENT-013 SellersPerspective | **No domain file** | Unknown/reserved (Candidate) | Named alternative analytical lens, structurally parallel to but not merged with TrendPoint (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 260-265) | Not integrated into any dependency chain |
| ENT-014 OpeningRange | **No domain file** | Unknown/reserved (Candidate) | First-5-minute-candle high/low on Spot chart, explicitly distinct from Future-based TrendPoint system (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 267-272); `STRIKE_EVIDENCE_SUMMARY.md` separately excludes a similar spot-chart mention (line 3479 of TR-001) as a "psychological/directional-discipline aid," reinforcing it is a distinct, unmerged concept | Not integrated into any dependency chain |
| UNK-001 IVL Level | **No domain file** | Unknown, isolated | "Confirmed not present in the Bible, Domain Model, or State Machine"; used repeatedly in TR-001 (lines 45, 1308-1309, 1389, 1586) as if already defined, but never defined (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 278-286) | No extension point is deliberately designed for it, since designing one would require understanding not yet evidenced |

**Entities with a real domain/*.py file:** ENT-001, ENT-003, ENT-005
(covers ENT-006/ENT-007 as fields), ENT-009 — 4 dedicated files
covering 6 of the 15 rows above (`domain/strike.py`,
`domain/trend_point.py`, `domain/opponent.py`, `domain/premium.py`).
**Entities with NO domain file, as instructed to state explicitly:**
ENT-002, ENT-004, ENT-008, ENT-010, ENT-011, ENT-012, ENT-013,
ENT-014, and UNK-001 — 9 of the 15. This matches
`FRAMEWORK_BASELINE_REPORT.md`'s file inventory (11 domain files total,
several of which are framework classes such as `Decision`,
`MarketContext`, `MarketSession`, `SessionState`, `DomainEvent`,
`EvidenceReference`, `RuleReference` rather than one-per-Candidate-entity
files).

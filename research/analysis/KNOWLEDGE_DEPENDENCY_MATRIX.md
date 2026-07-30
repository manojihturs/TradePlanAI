# Knowledge Dependency Matrix

Milestone K1 (Phase K: Knowledge Reconstruction). Consolidates the
evidenced dependency chain (Task 4) and a single knowledge-gap matrix
across every Rule ID, Entity, Weekly Future, and Decision (Task 5).
Evidence-only: every arrow and every matrix cell cites a source
document, or the actual code file for the freshly-verified
Implementation Exists / Mathematics Exists columns. Where the primary
chain diagram (`FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 2) already
distinguishes evidenced vs. architectural-only edges, that distinction
is reused here rather than re-derived.

**Currency note, carried forward from `KNOWLEDGE_GAP_INVENTORY.md`:**
Weekly Future's readiness verdict used throughout this document is
**NOT READY**, per `WEEKLY_FUTURE_VERIFICATION.md` (Phase E1, the most
recent and strictest-rubric verdict), which supersedes the older
PARTIALLY READY verdict in `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` /
`ENTITY_DEPENDENCY_GRAPH.md` / `KNOWLEDGE_READINESS_DASHBOARD.md`.

---

## Task 4 — Full Dependency Chain, With WHY

### Chain A: Weekly Future → Strike → TrendPoint → {TREND-002, TREND-003, OPPONENT-001} → [architectural] Decision

```
Call Option first-candle OHLC   ─┐
Put Option first-candle OHLC    ─┼──▶ Weekly Future High/Low (ENT-010)
ATM Strike (anchor)             ─┘
        │
        │ EVIDENCED — STRIKE-001's strike-selection mechanism is anchored
        │ to the Weekly Future first-candle High/Low: "our strike price
        │ always starts based on the Future... the Future's high and low
        │ [are] the candle's high and low" (STRIKE_EVIDENCE_TABLE.md row
        │ 10; STRIKE_EVIDENCE_SUMMARY.md "Repeated Behaviour"), rounded to
        │ the nearest listed strike (STRIKE_EVIDENCE_TABLE.md rows 11, 12,
        │ 14). NOTE — this is a documentation-lag discrepancy against the
        │ ledger: docs/RULE_INDEX.md row 30 and TRADINGVIEW_STRATEGY_BIBLE.md
        │ line 105 both still record STRIKE-001's "Depends On" as "none
        │ yet" (the older, pre-5.0A/5.0B framing). RULE_DEPENDENCY_GRAPH.md
        │ explicitly flags this as a documentation-lag gap, not a
        │ contradiction to silently resolve, and trading_engine/rules/
        │ dependencies.py deliberately follows the ledger's "none yet"
        │ rather than encode the undocumented edge (FRAMEWORK_BASELINE_
        │ REPORT.md Section 6, "Known Intentional Limitations").
        ▼
Strike selection (STRIKE-001) → Strike (ENT-001)
        │
        │ EVIDENCED (partial) — "every analysed strike maintains..." a
        │ Trend Point Low (docs/TRADINGVIEW_STRATEGY_BIBLE.md line 117-118),
        │ i.e. a TrendPoint belongs to a selected Strike
        │ (docs/DOMAIN_MODEL.md lines 72-73). No formula connecting the
        │ Strike's price to the TP Low's initial value is evidenced —
        │ Mathematical Definition: Partially Known
        │ (docs/TRADINGVIEW_STRATEGY_BIBLE.md line 131).
        ▼
TrendPoint / TP Low (TREND-001) → ENT-003
        │
        ├───────────────┬─────────────────────────┐
        │ EVIDENCED      │ EVIDENCED                │ EVIDENCED
        │ docs/RULE_     │ docs/RULE_INDEX.md row 33 │ docs/RULE_INDEX.md row 34
        │ INDEX.md row 32│ / TRADINGVIEW_STRATEGY_   │ / TRADINGVIEW_STRATEGY_
        │ / TRADINGVIEW_ │ BIBLE.md line 194:        │ BIBLE.md line 241:
        │ STRATEGY_      │ "Depends On: TREND-001,   │ "Depends On: TREND-001,
        │ BIBLE.md line  │ OPPONENT-001" —reflected  │ OPPONENT-002, OPPONENT-003"
        │ 165: "Depends  │ in trading_engine/rules/  │ — reflected in
        │ On: TREND-001" │ dependencies.py's         │ trading_engine/rules/
        │ — reflected in │ RULE_DEPENDENCIES table   │ dependencies.py's
        │ trading_engine/│ (Milestone 6.3)           │ RULE_DEPENDENCIES table
        │ rules/         │                           │ (Milestone 6.3)
        │ dependencies.py│                           │
        ▼                ▼                           ▼
   TREND-002         TREND-003                  OPPONENT-001
   (Dynamic TP Low   (Edge Detection —          (Next Opponent Defeat)
   Adjustment)       requires BOTH TREND-001
                     AND OPPONENT-001, see
                     below)
                          ▲                           │
                          │ EVIDENCED — TREND-003's    │ EVIDENCED — OPPONENT-001's
                          │ second Depends-On entry     │ own Depends-On list
                          │ (OPPONENT-001) means it      │ additionally includes
                          │ waits on OPPONENT-001's own  │ OPPONENT-002, OPPONENT-003
                          │ output, not just TREND-001's │ (docs/RULE_INDEX.md row 34)
                          │ (docs/RULE_INDEX.md row 33)  │
                          └───────────────────────────────┘
                                          │
                                          │ ARCHITECTURAL, NOT
                                          │ RULE-MATHEMATICS-EVIDENCED —
                                          │ "no synthesis logic... is
                                          │ designed, because no such
                                          │ combination rule is evidenced
                                          │ anywhere in the reviewed
                                          │ documents"
                                          │ (docs/architecture/RULE_ENGINE_
                                          │ ARCHITECTURE.md lines 155-169,
                                          │ quoted verbatim in
                                          │ FOUNDATIONAL_KNOWLEDGE_MAP.md
                                          │ Section 1 "Terminal Concepts")
                                          ▼
                                    [Decision Object]
```

OPPONENT-001 has its own upstream, evidenced dependency chain worth
stating explicitly (it is not just a leaf that TREND-003 waits on):
`Opponent (ENT-005) → Opponent High (ENT-006, via placeholder
OPPONENT-002) + Opponent Low (ENT-007, via placeholder OPPONENT-003) →
feed OPPONENT-001`, per `docs/DOMAIN_MODEL.md` lines 111-119 and
`docs/RULE_INDEX.md` rows 34-36 ("Depends On: TREND-001, OPPONENT-002,
OPPONENT-003"). OPPONENT-002/003 are each Awaiting Evidence with
Evidence Count 0 (`docs/RULE_INDEX.md` rows 35-36) — this is an
EVIDENCED dependency (the ledger states it), even though the content
of OPPONENT-002/003 themselves is entirely unevidenced.

### Chain B: Premium → REVERSAL-001 → [architectural] Decision

```
Premium (ENT-009, raw/foundational, no rule computes it —
docs/DOMAIN_MODEL.md lines 180-194)
        │
        │ EVIDENCED — REVERSAL-001 "Depends On: none yet" per
        │ docs/RULE_INDEX.md row 37 / docs/TRADINGVIEW_STRATEGY_BIBLE.md
        │ line 292 (i.e. Premium is consumed directly, not via another
        │ rule); consumption relationship stated in docs/DOMAIN_MODEL.md
        │ lines 168-171 and lines 191.
        ▼
Reversal identification (REVERSAL-001) → Reversal (ENT-008)
        │
        │ ARCHITECTURAL, NOT RULE-MATHEMATICS-EVIDENCED — no synthesis
        │ rule combining Reversal with TREND-003/Edge or OPPONENT-001 is
        │ evidenced anywhere (docs/architecture/RULE_ENGINE_ARCHITECTURE.md
        │ lines 125-128, 163-169, cited by FOUNDATIONAL_KNOWLEDGE_MAP.md
        │ Section 2 DAG). Reversal is also the one confirmed "Impossible
        │ Transition" in the project — no direct assumption-based entry
        │ into REVERSAL_IDENTIFIED (docs/STATE_MACHINE.md lines 158-163).
        ▼
[Decision Object] — same architectural placeholder as Chain A; both
chains converge on the same unevidenced synthesis point.
```

### Summary of evidenced vs. architectural-only edges

Per `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 2's own established
distinction, every edge above is one of:

- **EVIDENCED** — a specific document states the dependency directly
  (a "Depends On" ledger entry, a direct transcript quote, or an
  explicit entity-relationship statement in `docs/DOMAIN_MODEL.md`).
- **ARCHITECTURAL, NOT RULE-MATHEMATICS-EVIDENCED** — the architecture
  layer (`docs/architecture/RULE_ENGINE_ARCHITECTURE.md`) provides a
  placeholder destination (the Decision Object) that Rule Results would
  eventually feed, but no combination/synthesis rule is evidenced
  anywhere. Both Chain A and Chain B terminate at this same
  architectural-only node — the "Decision" row in the matrix below
  reflects this.

---

## Task 5 — Knowledge Gap Matrix

Columns exactly as specified. "Implementation Exists" and "Mathematics
Exists" were freshly verified by reading `trading_engine/domain/*.py`
and `trading_engine/calculators/*.py` directly for this document (see
`KNOWLEDGE_GAP_INVENTORY.md` Sections 2-3 for the full per-file
findings); both are confirmed uniformly negative — no exception found
anywhere in the codebase.

| Knowledge Item | Repository Exists | Evidence Exists | Implementation Exists | Mathematics Exists | Ready | Blocking Item |
|---|---|---|---|---|---|---|
| STRIKE-001 | Yes — `calculators/strike_calculator.py`, `domain/strike.py` | Partial — own selection heuristic PARTIALLY READY (`STRIKE_EVIDENCE_SUMMARY.md`), cite | No — `calculate()` raises `NotImplementedError` unconditionally (`strike_calculator.py:57`) | No — no formula present anywhere in file | NOT READY (downstream-blocked; see Section 1 above for the own-evidence-vs-overall distinction) | Weekly Future High/Low arithmetic (NOT READY, `WEEKLY_FUTURE_VERIFICATION.md`) |
| TREND-001 | Yes — `calculators/trend_calculator.py`, `domain/trend_point.py` | Partial — Mathematical Definition "Partially Known" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 131) | No — `calculate()` raises `NotImplementedError` unconditionally (`trend_calculator.py:65`) | No | NOT READY | TP Low value formula unevidenced (`trend_point.py:77` TODO) |
| TREND-002 | Yes — `calculators/trend_calculator.py` (shared file), `domain/trend_point.py` | No — Mathematical Definition Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 159) | No — same `calculate()` as TREND-001, raises unconditionally | No | NOT READY | "Market structure change" trigger definition (Unknown, `docs/DOMAIN_MODEL.md` lines 93-95) |
| TREND-003 | Yes — `calculators/edge_calculator.py` | No — Mathematical Definition Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 188) | No — `calculate()` raises `NotImplementedError` unconditionally (`edge_calculator.py:59`) | No | NOT READY | Compound: "well below" threshold unquantified AND depends on TREND-001 AND OPPONENT-001, both unresolved |
| OPPONENT-001 | Yes — `calculators/opponent_calculator.py`, `domain/opponent.py` | No — "defeat" is an explicit unresolved Open Question (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 344-350) | No — `calculate()` raises `NotImplementedError` unconditionally (`opponent_calculator.py:75`) | No | NOT READY | "Defeat" condition undefined + OPPONENT-002/003 both Evidence Count 0 |
| OPPONENT-002 | Yes — `calculators/opponent_calculator.py` (shared file), `Opponent.high` field | No — Evidence Count 0, Awaiting Evidence (`docs/RULE_INDEX.md` row 35) | No | No | NOT READY | No behaviour defined at all; TR-001 did not define it |
| OPPONENT-003 | Yes — `calculators/opponent_calculator.py` (shared file), `Opponent.low` field | No — Evidence Count 0, Awaiting Evidence (`docs/RULE_INDEX.md` row 36) | No | No | NOT READY | No behaviour defined at all; TR-001 did not define it |
| REVERSAL-001 | Yes — `calculators/reversal_calculator.py`, `domain/premium.py` | No — no rule shape stated at all (`docs/DOMAIN_MODEL.md` lines 168-171) | No — `calculate()` raises `NotImplementedError` unconditionally (`reversal_calculator.py:58`) | No | NOT READY | Premium-behaviour-to-reversal identification rule entirely unevidenced |
| ENT-001 Strike | Yes — `domain/strike.py` | Partial (via STRIKE-001's own evidence) | No — dataclass fields only, TODO at line 56 | No | NOT READY | Selection formula from First Candle unevidenced |
| ENT-002 First Candle | No — raw input, no domain file | Partial — WHICH candle conceptually resolved (Weekly Future's first candle, `STRIKE_EVIDENCE_SUMMARY.md` Conflicts item 2), exact time-window Unknown | N/A — not a computed entity | No | NOT READY | Exact time-window definition (`docs/DOMAIN_MODEL.md` lines 52-55) |
| ENT-003 TrendPoint | Yes — `domain/trend_point.py` | Partial — Mathematical Definition Partially Known | No — TODOs at lines 77, 79 | No | NOT READY | Value formula (TREND-001) + update trigger (TREND-002) |
| ENT-004 Market Structure | No domain file | No — "what constitutes market structure... not defined" | N/A | No | NOT READY | Fully Unknown trigger definition |
| ENT-005 Opponent | Yes — `domain/opponent.py` | No — relationship to Strike/"competitor" Unknown | No — TODOs at lines 69, 72, 74 | No | NOT READY | "Competitor" relationship clarification + defeat math |
| ENT-006 Opponent High | Yes — field in `domain/opponent.py`, reserved slot only | No — Evidence Count 0 (OPPONENT-002) | No — never read/compared in production code (`FRAMEWORK_BASELINE_REPORT.md` Section 2 item 2) | No | NOT READY | OPPONENT-002 undefined |
| ENT-007 Opponent Low | Yes — field in `domain/opponent.py`, reserved slot only | No — Evidence Count 0 (OPPONENT-003) | No — never read/compared in production code | No | NOT READY | OPPONENT-003 undefined |
| ENT-008 Reversal | No dedicated domain file | No — identification method Unknown | N/A | No | NOT READY | Premium→Reversal rule unevidenced |
| ENT-009 Premium | Yes — `domain/premium.py` | No — "no rule yet defines Premium as a first-class concept" | No — TODO at line 50 | No | NOT READY | Which contract (CE/PE/both); reversal rule itself |
| ENT-010 Weekly Future | No domain file (Candidate only) | No — NOT READY per `WEEKLY_FUTURE_VERIFICATION.md` (supersedes older PARTIALLY READY) | No — `weekly_future_calculator.py` raises `NotImplementedError` unconditionally (line 93) | No | NOT READY | Self-contradictory arithmetic; missing "Complete Calculation Video" |
| ENT-011 MidPoint | No domain file (Candidate) | No — no rule/entity evidenced to depend on it | N/A | No | NOT READY (unranked — no engineering impact per `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 4) | Top/Bottom strike not confirmed Domain objects |
| ENT-012 TriggerPoint | No domain file (Candidate) | No — one narrative example only, no computation | N/A | No | NOT READY (unranked) | No computation evidenced at all |
| ENT-013 SellersPerspective | No domain file (Candidate) | No — named lens only, not integrated | N/A | No | NOT READY (unranked) | Not merged with TrendPoint framework; no rule evidenced |
| ENT-014 OpeningRange | No domain file (Candidate) | No — distinct from TrendPoint system, unmerged | N/A | No | NOT READY (unranked) | Not integrated into any dependency chain |
| UNK-001 IVL Level | No domain file | No — used but never defined anywhere in TR-001 | N/A | No | NOT READY (unranked, isolated) | Concept itself undefined; no extension point designed deliberately |
| Weekly Future (own row) | No domain file — Candidate entity only | No — NOT READY, `WEEKLY_FUTURE_VERIFICATION.md` Phase E1 (supersedes PARTIALLY READY) | No — `weekly_future_calculator.py:93` | No | **NOT READY** | Self-contradictory Call/Put→High/Low arithmetic; zero of 3 required consistent worked examples exist; missing external "Complete Calculation Video" |
| Decision | No domain file for synthesis logic — `domain/decision.py`'s `Decision`/`RuleEvaluationResult` classes exist as containers only | No — "no such combination rule is evidenced anywhere in the reviewed documents" (`docs/architecture/RULE_ENGINE_ARCHITECTURE.md` lines 155-169) | Partial/No — `Decision` and `RuleEvaluationResult` dataclasses exist as structural containers (`domain/decision.py`), but the TODO at line 105 confirms: "No synthesis/combination logic across multiple RuleEvaluationResults evidenced"; nothing populates them with real rule outcomes | No | NOT READY | Every upstream Rule ID is NOT READY, AND the cross-rule combination/synthesis logic itself is architecturally unevidenced (a second, independent blocker beyond just "wait for the rules") |

**Summary: 0 of 24 rows (8 rules + 15 entities/candidates + Decision)
are READY or fully PARTIALLY READY.** Every calculator's
`calculate()` method raises `NotImplementedError` unconditionally with
no exception found (Repository Exists is Yes/Partial for every row
with a code file; Implementation Exists is No throughout; Mathematics
Exists is No throughout) — this matches `FRAMEWORK_BASELINE_REPORT.md`
Section 2 item 1's own independent Milestone-6.5 finding exactly.

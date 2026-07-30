# Knowledge Readiness Dashboard

One row per mathematical concept with its own readiness verdict
established in the analysis docs. Evidence-only; every cell cites its
source. See footnote¹ on Evidence Count methodology (STRIKE-001 and
Weekly Future specifically).

| Concept | READY / PARTIALLY READY / NOT READY | Confidence | Evidence Count | Independent Sources | Last Updated Milestone |
|---|---|---|---|---|---|
| Weekly Future (ENT-010) | PARTIALLY READY (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` readiness verdict, line 5) | Low (Derived from TR-001 only) — `docs/EVIDENCE_MATRIX.md` ENT-010 row | 1¹ — `docs/EVIDENCE_MATRIX.md` ENT-010 row ("1 \| TR-001 transcript only") | No — single transcript, single speaker/channel; not independently corroborated (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker" item 3: only source is the absent external video) | Milestone 5.0B (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`, `WEEKLY_FUTURE_EVIDENCE_TABLE.md`) |
| STRIKE-001 | PARTIALLY READY — "upgraded confidence... but still short of READY" (`STRIKE_EVIDENCE_SUMMARY.md` "Recommended Readiness Verdict") | Medium — `docs/RULE_INDEX.md` row 30, `docs/EVIDENCE_MATRIX.md` STRIKE-001 row | 2¹ — ledger's official value (`docs/RULE_INDEX.md` row 30, `docs/EVIDENCE_MATRIX.md`); NOT 14, per `REPOSITORY_CHANGE_PROPOSAL.md` Section 4 item 2's explicit "should NOT be bumped to 14" finding — see footnote¹ | No — `STRIKE_EVIDENCE_SUMMARY.md` "Independent Sources": "No — this is not independent evidence... one person's repeated, largely self-consistent narration... not multiple independent confirmations of a rule" | Milestone 5.0A (`STRIKE_EVIDENCE_TABLE.md`, `STRIKE_EVIDENCE_SUMMARY.md`) |
| TREND-001 | NOT READY — Mathematical Definition: Partially Known, but "no formula connecting Strike to a TP Low value" evidenced (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 131; `FOUNDATIONAL_KNOWLEDGE_MAP.md` DAG Section 2) | Medium — `docs/RULE_INDEX.md` row 31, `docs/EVIDENCE_MATRIX.md` TREND-001 row | 2 — `docs/EVIDENCE_MATRIX.md` TREND-001 row (original statement + TR-001 transcript, per Milestone 3.2 note) | N/A — no new evidence acquisition attempted for TREND-001 by Milestones 5.0A/5.0B/5.1 (`RULE_DEPENDENCY_GRAPH.md` TREND-001 "Depends On (deeper evidence)": "No evidenced dependency found... they do not discuss TREND-001") | Milestone 3.2 (`docs/RULE_INDEX.md`, `docs/EVIDENCE_MATRIX.md`) — untouched by 5.0A/5.0B/5.1 |
| TREND-002 | NOT READY — Mathematical Definition: Unknown; trigger ("market structure change") itself Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 159; `docs/DOMAIN_MODEL.md` lines 93-95) | Medium — `docs/RULE_INDEX.md` row 32, `docs/EVIDENCE_MATRIX.md` TREND-002 row | 2 — `docs/EVIDENCE_MATRIX.md` TREND-002 row | N/A — no new evidence acquisition attempted (`RULE_DEPENDENCY_GRAPH.md` TREND-002: "no deeper evidence doc... addresses TREND-002 at all") | Milestone 3.2 — untouched by 5.0A/5.0B/5.1 |
| TREND-003 | NOT READY — Mathematical Definition: Unknown; "well below" not quantified; also transitively blocked by TREND-001 and OPPONENT-001 (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 188; `docs/TERMINOLOGY.md` lines 112-113) | Medium — `docs/RULE_INDEX.md` row 33, `docs/EVIDENCE_MATRIX.md` TREND-003 row | 2 — `docs/EVIDENCE_MATRIX.md` TREND-003 row | N/A — no new evidence acquisition attempted (`RULE_DEPENDENCY_GRAPH.md` TREND-003: "Consistent — no discrepancy found," no deeper-evidence doc addresses it) | Milestone 3.2 — untouched by 5.0A/5.0B/5.1 |
| OPPONENT-001 | NOT READY — Mathematical Definition: Unknown; "defeat" condition an explicit unresolved Open Question (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 235, lines 344-350) | Medium — `docs/RULE_INDEX.md` row 34, `docs/EVIDENCE_MATRIX.md` OPPONENT-001 row | 2 — `docs/EVIDENCE_MATRIX.md` OPPONENT-001 row | N/A — no new evidence acquisition attempted (`RULE_DEPENDENCY_GRAPH.md` OPPONENT-001: "Consistent — no discrepancy found," neither deeper-evidence doc discusses it) | Milestone 3.2 — untouched by 5.0A/5.0B/5.1 |
| OPPONENT-002 | NOT READY — Awaiting Evidence, "no behaviour defined" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 244-248; `docs/RULE_INDEX.md` row 35) | Unknown — `docs/RULE_INDEX.md` row 35 ("-"), `docs/EVIDENCE_MATRIX.md` OPPONENT-002 row | 0 — `docs/RULE_INDEX.md` row 35, `docs/EVIDENCE_MATRIX.md` OPPONENT-002 row | N/A — no new evidence acquisition attempted; TR-001 did not define it (`docs/RULE_INDEX.md` row 35 Notes) | Milestone 3.2 (placeholder never updated) — untouched by 5.0A/5.0B/5.1 |
| OPPONENT-003 | NOT READY — Awaiting Evidence, "no behaviour defined" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 250-254; `docs/RULE_INDEX.md` row 36) | Unknown — `docs/RULE_INDEX.md` row 36 ("-"), `docs/EVIDENCE_MATRIX.md` OPPONENT-003 row | 0 — `docs/RULE_INDEX.md` row 36, `docs/EVIDENCE_MATRIX.md` OPPONENT-003 row | N/A — no new evidence acquisition attempted; TR-001 did not define it (`docs/RULE_INDEX.md` row 36 Notes) | Milestone 3.2 (placeholder never updated) — untouched by 5.0A/5.0B/5.1 |
| REVERSAL-001 | NOT READY — Mathematical Definition: Unknown; "which specific premium behaviour constitutes identification is not established anywhere" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 286; `docs/DOMAIN_MODEL.md` lines 168-171) | Medium — `docs/RULE_INDEX.md` row 37, `docs/EVIDENCE_MATRIX.md` REVERSAL-001 row | 2 — `docs/EVIDENCE_MATRIX.md` REVERSAL-001 row | N/A — no new evidence acquisition attempted (`RULE_DEPENDENCY_GRAPH.md` REVERSAL-001: "No evidenced dependency found... neither STRIKE_EVIDENCE_* nor WEEKLY_FUTURE_* discusses REVERSAL-001") | Milestone 3.2 — untouched by 5.0A/5.0B/5.1 |
| Edge / Edge Detection (TREND-003's output — listed separately per `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 194-213 treating it as a distinct condition, not a stored entity) | NOT READY — "No evidenced further consumer found," modeled only as a comparison condition, not a stored entity; depends on both TREND-001 and OPPONENT-001 being resolved (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 194-213; `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 1 "Intermediate Concepts") | Unknown/no dedicated Mathematical Definition entry of its own — piggybacks on TREND-003's Medium confidence and Unknown Mathematical Definition (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 188; `docs/EVIDENCE_MATRIX.md` Mathematical Definitions table: "_none yet_") | 0 (no dedicated Mathematical Definitions row exists — `docs/EVIDENCE_MATRIX.md` "Mathematical Definitions" table: "`MATHEMATICAL_SPECIFICATION.md` has no entries - Phase 2 has not started") | N/A — no new evidence acquisition attempted; not separately investigated by any milestone (`FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 4 "Not ranked" note: "subsumed by item 4's TREND-003 dependency chain") | Milestone 3.2 (via TREND-003) — untouched by 5.0A/5.0B/5.1 |

## Footnote 1 — Evidence Count distinction for STRIKE-001

STRIKE-001's Evidence Count in this dashboard is **2**, the ledger's
official value (`docs/RULE_INDEX.md` row 30; `docs/EVIDENCE_MATRIX.md`
STRIKE-001 row), **not** the raw count of 14 within-transcript
occurrences documented in `STRIKE_EVIDENCE_TABLE.md`. `docs/EVIDENCE_MATRIX.md`'s
Confidence Policy explicitly defines Evidence Count as "the number of
**independent evidence sources**... not the number of other artifacts
that reference this one. An artifact cited by four different rules but
ultimately traceable to a single conversational statement still has
Evidence Count = 1." `REPOSITORY_CHANGE_PROPOSAL.md` Section 4 item 2
states this explicitly as a "should NOT be made" change: "Do NOT bump
STRIKE-001's Evidence Count from 2 to 14 as if each of the 14
within-transcript occurrences were an independent source." The 14
occurrences all trace to the single file TR-001.md, single speaker,
single channel (`STRIKE_EVIDENCE_SUMMARY.md` "Independent Sources").

The same distinction applies to Weekly Future (ENT-010): its Evidence
Count of 1 (`docs/EVIDENCE_MATRIX.md` ENT-010 row) reflects one
independent source (TR-001), not the 15 within-transcript occurrences
catalogued in `WEEKLY_FUTURE_EVIDENCE_TABLE.md`.

# Evidence Matrix

The single source of truth for traceability across the entire
TradingView strategy reconstruction effort. Every artifact that exists
anywhere in `/docs` or the repo-root recovery documents
(`TRADINGVIEW_HIDDEN_RULES.md`, `TRADINGVIEW_REQUIREMENTS_RECOVERY.md`)
has exactly one row here. This document creates no new business rules,
modifies no existing rule, and infers no trading logic - it only
tracks what already exists and how confident/mature each artifact is.

## Supported Artifact Types

- **Business Rule** - an entry in `TRADINGVIEW_STRATEGY_BIBLE.md`
- **Business Entity** - an entry in `DOMAIN_MODEL.md`
- **Terminology** - an entry in `TERMINOLOGY.md`
- **Mathematical Definition** - an entry in `MATHEMATICAL_SPECIFICATION.md`
- **State** - an entry in `STATE_MACHINE.md`
- **Event** - a discrete occurrence distinct from a State (none defined yet)
- **Transcript** - a saved source file in `/research/transcripts`
- **Unknown Concept** - referenced somewhere but not yet classified as any of the above

## Confidence Policy

| Evidence Count | Confidence |
|---:|---|
| 0 | Unknown |
| 1 | Low |
| 2 | Medium |
| 3-4 | High |
| 5+ | Confirmed |

"Evidence Count" here means the number of **independent evidence
sources** (distinct transcripts, distinct manual observations, etc. -
see `KNOWLEDGE_SOURCES.md`'s evidence levels), not the number of other
artifacts that reference this one. An artifact cited by four different
rules but ultimately traceable to a single conversational statement
still has Evidence Count = 1. Cross-artifact citation is tracked
separately, under "Referenced By."

## Status Policy

`Draft` -> `Candidate` -> `Defined` -> `Validated` -> `Implemented` ->
`Backtested` -> `Paper Verified` -> `Production`, with `Deprecated`
reachable from any state.

| Status | Meaning |
|---|---|
| `Draft` | Recorded from evidence, not yet cross-checked |
| `Candidate` | Cross-checked, proposed for formalisation |
| `Defined` | Mathematically/formally defined (unambiguous) |
| `Validated` | Confirmed consistent across sufficient independent evidence |
| `Implemented` | Present in code |
| `Backtested` | Validated against historical data |
| `Paper Verified` | Confirmed in live paper trading |
| `Production` | Live, real-money active |
| `Deprecated` | Superseded or withdrawn |

Note: the existing placeholder rules (OPPONENT-002, OPPONENT-003) use
a status of "Awaiting Evidence" in `TRADINGVIEW_STRATEGY_BIBLE.md` and
`RULE_INDEX.md`, predating this policy. That status does not map
cleanly onto the list above (it is earlier than `Draft`, which implies
some recorded content). Per this milestone's instruction not to modify
existing rules, their original status is preserved as-is in the
source documents; this matrix records them with a `Notes` flag rather
than silently reclassifying them into `Draft`.

---

## Matrix

### Business Rules

| Artifact ID | Type | Name | Evidence Count | Evidence Sources | Confidence | Status | First Seen | Last Updated | Depends On | Referenced By | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| STRIKE-001 | Business Rule | Initial Strike Selection | 2 | Conversational statement + TR-001 transcript | Medium | Draft | 2026-07-27 | 2026-07-28 | none | ENT-001, TERM-001, SM-001 | No | No | No | No | Mathematical Definition Unknown |
| TREND-001 | Business Rule | Trend Point Low (TP Low) | 2 | Conversational statement + TR-001 transcript | Medium | Draft | 2026-07-27 | 2026-07-28 | none | TREND-002, TREND-003, OPPONENT-001, ENT-003, TERM-003, SM-002 | No | No | No | No | Mathematical Definition Partially Known |
| TREND-002 | Business Rule | Dynamic TP Low Adjustment | 2 | Conversational statement + TR-001 transcript | Medium | Draft | 2026-07-27 | 2026-07-28 | TREND-001 | ENT-004 | No | No | No | No | Mathematical Definition Unknown |
| TREND-003 | Business Rule | Edge Detection | 2 | Conversational statement + TR-001 transcript | Medium | Draft | 2026-07-27 | 2026-07-28 | TREND-001, OPPONENT-001 | TERM-006 | No | No | No | No | Bible's prior Medium/policy Low discrepancy (see old Notes below) is now resolved - both read Medium at Evidence Count 2 |
| OPPONENT-001 | Business Rule | Next Opponent Defeat | 2 | Conversational statement + TR-001 transcript | Medium | Draft | 2026-07-27 | 2026-07-28 | TREND-001, OPPONENT-002, OPPONENT-003 | TREND-003, ENT-005, TERM-004 | No | No | No | No | Mathematical Definition Unknown |
| OPPONENT-002 | Business Rule | Opponent High (placeholder) | 0 | none | Unknown | Awaiting Evidence (pre-Draft, see policy note above) | 2026-07-27 | 2026-07-27 | none | OPPONENT-001, ENT-006, TERM-005 | No | No | No | No | Placeholder only - no behaviour defined; TR-001 did not define this |
| OPPONENT-003 | Business Rule | Opponent Low (placeholder) | 0 | none | Unknown | Awaiting Evidence (pre-Draft, see policy note above) | 2026-07-27 | 2026-07-27 | none | OPPONENT-001, ENT-007, TERM-005 | No | No | No | No | Placeholder only - no behaviour defined; TR-001 did not define this |
| REVERSAL-001 | Business Rule | Reversal Identification | 2 | Conversational statement + TR-001 transcript | Medium | Draft | 2026-07-27 | 2026-07-28 | none | ENT-008, TERM-007, SM-005 | No | No | No | No | Mathematical Definition Unknown |

**Note on TREND-003 (historical, resolved Milestone 3.2):** Before
TR-001 was added, `TRADINGVIEW_STRATEGY_BIBLE.md` recorded Confidence
as `Medium` at Evidence Count 1 (policy value would have been `Low`).
With TR-001 now counted as a second independent source, Evidence Count
is 2 for all six rules and the policy-correct Confidence is `Medium`
across the board - both the Bible and this matrix now agree without
either being overwritten arbitrarily.

### Business Entities

| Artifact ID | Type | Name | Evidence Count | Evidence Sources | Confidence | Status | First Seen | Last Updated | Depends On | Referenced By | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ENT-001 | Business Entity | Strike | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | STRIKE-001, TREND-001, TREND-003, OPPONENT-001, TERM-002, SM-001 | No | No | No | No | |
| ENT-002 | Business Entity | First Candle | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | STRIKE-001, TERM-001 | No | No | No | No | |
| ENT-003 | Business Entity | Trend Point Low (TP Low) | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | TREND-001, TREND-002, TREND-003, OPPONENT-001, TERM-003, SM-002 | No | No | No | No | |
| ENT-004 | Business Entity | Market Structure | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | TREND-002 | No | No | No | No | Not yet a `TERMINOLOGY.md` entry - flagged in `DOMAIN_MODEL.md` |
| ENT-005 | Business Entity | Opponent | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | OPPONENT-001, TREND-003, TERM-004, SM-003 | No | No | No | No | Open question whether same concept as "competitor" in `strategy/exit_signal.py` - not assumed |
| ENT-006 | Business Entity | Opponent High | 0 | none | Unknown | Draft | 2026-07-27 | 2026-07-27 | none | OPPONENT-002, TERM-005 | No | No | No | No | Mirrors OPPONENT-002 placeholder |
| ENT-007 | Business Entity | Opponent Low | 0 | none | Unknown | Draft | 2026-07-27 | 2026-07-27 | none | OPPONENT-003, TERM-005 | No | No | No | No | Mirrors OPPONENT-003 placeholder |
| ENT-008 | Business Entity | Reversal | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | REVERSAL-001, TERM-007, SM-005 | No | No | No | No | |
| ENT-009 | Business Entity | Premium | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | REVERSAL-001 | No | No | No | No | Not yet a `TERMINOLOGY.md` entry - flagged in `DOMAIN_MODEL.md` |
| ENT-010 | Business Entity | Weekly Future | 1 | TR-001 transcript only | Low (Derived from TR-001 only) | **Candidate** | 2026-07-28 | 2026-07-28 | none | none yet | No | No | No | No | Not promoted to a Rule. See `research/analysis/TR-001_ANALYSIS.md` Section 5. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. |
| ENT-011 | Business Entity | Mid Point | 1 | TR-001 transcript only | Low (Derived from TR-001 only) | **Candidate** | 2026-07-28 | 2026-07-28 | none | none yet | No | No | No | No | Not promoted to a Rule. See `research/analysis/TR-001_ANALYSIS.md` Section 3.6. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. |
| ENT-012 | Business Entity | Trigger Point | 1 | TR-001 transcript only | Low (Derived from TR-001 only) | **Candidate** | 2026-07-28 | 2026-07-28 | none | none yet | No | No | No | No | Not promoted to a Rule. See `research/analysis/TR-001_ANALYSIS.md` Section 5. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. |
| ENT-013 | Business Entity | Sellers' Perspective | 1 | TR-001 transcript only | Low (Derived from TR-001 only) | **Candidate** | 2026-07-28 | 2026-07-28 | none | none yet | No | No | No | No | Not promoted to a Rule. See `research/analysis/TR-001_ANALYSIS.md` Section 5. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. |
| ENT-014 | Business Entity | Opening Range | 1 | TR-001 transcript only | Low (Derived from TR-001 only) | **Candidate** | 2026-07-28 | 2026-07-28 | none | none yet | No | No | No | No | Not promoted to a Rule. See `research/analysis/TR-001_ANALYSIS.md` Section 5. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. |

### Terminology

| Artifact ID | Type | Name | Evidence Count | Evidence Sources | Confidence | Status | First Seen | Last Updated | Depends On | Referenced By | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TERM-001 | Terminology | First Candle | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | STRIKE-001, ENT-002 | No | No | No | No | |
| TERM-002 | Terminology | Strike | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | STRIKE-001, ENT-001 | No | No | No | No | |
| TERM-003 | Terminology | Trend Point Low (TP Low) | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | TREND-001, TREND-002, TREND-003, ENT-003 | No | No | No | No | |
| TERM-004 | Terminology | Opponent | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | OPPONENT-001, TREND-003, ENT-005 | No | No | No | No | |
| TERM-005 | Terminology | Opponent High / Opponent Low | 0 | none | Unknown | Draft | 2026-07-27 | 2026-07-27 | none | OPPONENT-002, OPPONENT-003, ENT-006, ENT-007 | No | No | No | No | Covers both placeholders in one terminology entry |
| TERM-006 | Terminology | Edge (Edge Detection) | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | TREND-003 | No | No | No | No | |
| TERM-007 | Terminology | Reversal | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | REVERSAL-001, ENT-008 | No | No | No | No | |

### Mathematical Definitions

| Artifact ID | Type | Name | Evidence Count | Evidence Sources | Confidence | Status | First Seen | Last Updated | Depends On | Referenced By | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| _none yet_ | | | | | | | | | | | | | | | `MATHEMATICAL_SPECIFICATION.md` has no entries - Phase 2 has not started |

### States

| Artifact ID | Type | Name | Evidence Count | Evidence Sources | Confidence | Status | First Seen | Last Updated | Depends On | Referenced By | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SM-001 | State | STRIKE_SELECTED | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | none | No | No | No | No | Derived from STRIKE-001; entry/exit conditions Unknown per `STATE_MACHINE.md` |
| SM-002 | State | TREND_TRACKING | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | SM-001 (hypothesised ordering only) | none | No | No | No | No | Derived from TREND-001/002; entry/exit conditions Unknown |
| SM-003 | State | OPPONENT_ENGAGEMENT | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | SM-001 (hypothesised ordering only) | SM-004 (hypothesised) | No | No | No | No | Derived from OPPONENT-001; entry/exit conditions Unknown |
| SM-004 | State | OPPONENT_DEFEATED | 0 | none - inferred from OPPONENT-001's wording, not directly evidenced | Unknown | Draft | 2026-07-27 | 2026-07-27 | SM-003 (hypothesised) | none | No | No | No | No | Flagged in `STATE_MACHINE.md` as a hypothesis, not a confirmed state |
| SM-005 | State | REVERSAL_IDENTIFIED | 1 | Conversational statement (no saved transcript) | Low | Draft | 2026-07-27 | 2026-07-27 | none | none | No | No | No | No | Derived from REVERSAL-001; entry/exit conditions Unknown |

### Events

| Artifact ID | Type | Name | Evidence Count | Evidence Sources | Confidence | Status | First Seen | Last Updated | Depends On | Referenced By | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| _none yet_ | | | | | | | | | | | | | | | No artifact in the project has yet been classified as a discrete Event distinct from a State |

### Transcripts

| Artifact ID | Type | Name | Evidence Count | Evidence Sources | Confidence | Status | First Seen | Last Updated | Depends On | Referenced By | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TR-001 | Transcript | TR-001 (YouTube transcript, Tamil, ~11 daily segments) | 1 | Original YouTube transcript (Evidence Level 1 per `KNOWLEDGE_SOURCES.md`) | High | Draft | 2026-07-28 | 2026-07-28 | none | STRIKE-001, TREND-001, TREND-002, TREND-003, OPPONENT-001, REVERSAL-001, ENT-010, ENT-011, ENT-012, ENT-013, ENT-014 | No | No | No | No | See `research/analysis/TR-001_ANALYSIS.md` for full extraction. Video Title/URL still UNKNOWN per transcript metadata header. |

### Unknown Concepts

| Artifact ID | Type | Name | Evidence Count | Evidence Sources | Confidence | Status | First Seen | Last Updated | Depends On | Referenced By | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UNK-001 | Unknown Concept | IVL Level | 1 | TR-001 transcript only | Low (Derived from TR-001 only) | Draft | 2026-07-28 | 2026-07-28 | none | none yet | No | No | No | No | Used repeatedly in TR-001 (e.g. lines 45, 1308-1309, 1389, 1586) as if already defined, but never defined anywhere in the transcript. Highest-priority open question from `research/analysis/TR-001_ANALYSIS.md` Section 14. Not a Rule, not an Entity - genuinely unclassified pending a defining source. |

---

## Summary

| Artifact Type | Count | Confirmed | Validated | Implemented |
|---|---:|---:|---:|---:|
| Business Rule | 8 | 0 | 0 | 0 |
| Business Entity | 14 | 0 | 0 | 0 |
| Terminology | 7 | 0 | 0 | 0 |
| Mathematical Definition | 0 | 0 | 0 | 0 |
| State | 5 | 0 | 0 | 0 |
| Event | 0 | - | - | - |
| Transcript | 1 | - | - | - |
| Unknown Concept | 1 | - | - | - |
| **Total** | **36** | **0** | **0** | **0** |

**Milestone 3.2 update (2026-07-28):** 6 Business Rules moved from
Evidence Count 1 (Low) to 2 (Medium) via TR-001. 5 new Business Entity
candidates added (ENT-010 through ENT-014, all Status=Candidate,
Confidence="Low (Derived from TR-001 only)" - not promoted to Rules).
1 Transcript row added (TR-001). 1 Unknown Concept row added (IVL
Level).

## Maintenance rule

Every time a new artifact is added to `TRADINGVIEW_STRATEGY_BIBLE.md`,
`DOMAIN_MODEL.md`, `TERMINOLOGY.md`, `MATHEMATICAL_SPECIFICATION.md`,
`STATE_MACHINE.md`, or `/research/transcripts`, a corresponding row
must be added here in the same change. This matrix is not
regenerated from scratch - it is maintained incrementally, so
`First Seen` dates stay accurate.

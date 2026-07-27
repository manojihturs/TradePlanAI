# Traceability Matrix

Traces every business artifact in the project from its origin source,
through evidence, to every other artifact type that relates to it, and
its implementation lifecycle. This is a different cut of the same
underlying data as `EVIDENCE_MATRIX.md` (which tracks confidence and
status per artifact) - this document instead tracks the *chain*: Origin
Source -> Evidence -> Rule/Entity/Terminology/Math/State/Event ->
Implementation. No new business rules are created, no existing
documentation is modified, and no relationship is inferred beyond what
the source documents already state - unstated relationships are
recorded as `UNKNOWN`, not guessed.

## Supported Artifact Types

Rule · Entity · Terminology · Transcript · Mathematical Definition ·
State · Event · Source Evidence

## Evidence ID assignment

No formal Evidence ID existed before this document. Assigning one to
each already-referenced evidence statement is a mechanical
bookkeeping step, not new evidence - every `EVID-NNN` below points to
the exact same statement already cited (verbatim, where quoted) in
`TRADINGVIEW_STRATEGY_BIBLE.md`. No new evidence is introduced.

| Evidence ID | Origin Source | Content (as already recorded in the Bible) |
|---|---|---|
| EVID-001 | User conversational statement (session 2026-07-27) - not saved to `/research` | "The strike price is selected based on the first candle." / "...First candle... 24050..." |
| EVID-002 | User conversational statement (session 2026-07-27) - not saved to `/research` | "The TP Low is repeatedly marked and updated during market progression." / "Every analysed strike maintains a Trend Point Low..." |
| EVID-003 | User conversational statement (session 2026-07-27) - not saved to `/research` | "TP Low is not static. When market structure changes, TP Low is converted to a new value." |
| EVID-004 | User conversational statement (session 2026-07-27) - not saved to `/research` | "When both current and opponent TP Lows remain well below the selected strike, probability of price moving below that strike is significantly reduced." |
| EVID-005 | User conversational statement (session 2026-07-27) - not saved to `/research` | "Repeated references to 'Next Opponent Defeat'." / "A strike progresses only after defeating the next opponent." |
| EVID-006 | User conversational statement (session 2026-07-27) - not saved to `/research` | "A reversal is not assumed. It must be identified through premium behaviour." |
| EVID-007 | TR-001 transcript (`/research/transcripts/TR-001.md`) - Evidence Level 1 per `KNOWLEDGE_SOURCES.md` | Independent confirmation of STRIKE-001, TREND-001, TREND-002, TREND-003, OPPONENT-001, and REVERSAL-001, recurring across ~11 daily segments within the transcript - see `research/analysis/TR-001_ANALYSIS.md` Sections 3.1-3.5 for exact quotes/line ranges per rule. Counted as ONE independent evidence source (the transcript as a whole), not one per daily segment, per the Confidence Policy's source-based (not reference-based) counting. |

No Evidence ID exists for OPPONENT-002 or OPPONENT-003 (Opponent
High/Low) - both are placeholders with zero supporting evidence, per
`RULE_INDEX.md`. TR-001 did not define them either.

---

## Matrix

### Rules

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| STRIKE-001 | Initial Strike Selection | Rule | User statement + TR-001 transcript | EVID-001, EVID-007 | UNKNOWN (no other rule cites STRIKE-001 in `Depends On`) | ENT-001, ENT-002 | TERM-001, TERM-002 | UNKNOWN | SM-001 | UNKNOWN | No | No | No | No | Evidence Count now 2 (Milestone 3.2) |
| TREND-001 | Trend Point Low (TP Low) | Rule | User statement + TR-001 transcript | EVID-002, EVID-007 | TREND-002 (dependent), TREND-003 (dependent), OPPONENT-001 (dependent) | ENT-003 | TERM-003 | UNKNOWN | SM-002 | UNKNOWN | No | No | No | No | Evidence Count now 2 (Milestone 3.2) |
| TREND-002 | Dynamic TP Low Adjustment | Rule | User statement + TR-001 transcript | EVID-003, EVID-007 | TREND-001 (depends on) | ENT-004 | UNKNOWN (Market Structure not in Terminology) | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Evidence Count now 2 (Milestone 3.2) |
| TREND-003 | Edge Detection | Rule | User statement + TR-001 transcript | EVID-004, EVID-007 | TREND-001 (depends on), OPPONENT-001 (depends on) | UNKNOWN (no dedicated "Edge" entity in `DOMAIN_MODEL.md`) | TERM-006 | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Evidence Count now 2 (Milestone 3.2); see Disconnected Artifacts summary |
| OPPONENT-001 | Next Opponent Defeat | Rule | User statement + TR-001 transcript | EVID-005, EVID-007 | TREND-001 (depends on), TREND-003 (dependent), OPPONENT-002 (depends on), OPPONENT-003 (depends on) | ENT-005 | TERM-004 | UNKNOWN | SM-003, SM-004 (SM-004 hypothesised only) | UNKNOWN | No | No | No | No | Evidence Count now 2 (Milestone 3.2) |
| OPPONENT-002 | Opponent High (placeholder) | Rule | none | none | OPPONENT-001 (referencing rule) | ENT-006 | TERM-005 | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Zero evidence - placeholder; TR-001 did not define this |
| OPPONENT-003 | Opponent Low (placeholder) | Rule | none | none | OPPONENT-001 (referencing rule) | ENT-007 | TERM-005 | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Zero evidence - placeholder; TR-001 did not define this |
| REVERSAL-001 | Reversal Identification | Rule | User statement + TR-001 transcript | EVID-006, EVID-007 | UNKNOWN (no other rule cites REVERSAL-001) | ENT-008, ENT-009 | TERM-007 | UNKNOWN | SM-005 | UNKNOWN | No | No | No | No | Evidence Count now 2 (Milestone 3.2) |

### Entities

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ENT-001 | Strike | Entity | User statement | EVID-001 | STRIKE-001, TREND-001, TREND-003, OPPONENT-001 | UNKNOWN | TERM-002 | UNKNOWN | SM-001 | UNKNOWN | No | No | No | No | |
| ENT-002 | First Candle | Entity | User statement | EVID-001 | STRIKE-001 | UNKNOWN | TERM-001 | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | |
| ENT-003 | Trend Point Low (TP Low) | Entity | User statement | EVID-002 | TREND-001, TREND-002, TREND-003, OPPONENT-001 | UNKNOWN | TERM-003 | UNKNOWN | SM-002 | UNKNOWN | No | No | No | No | |
| ENT-004 | Market Structure | Entity | User statement | EVID-003 | TREND-002 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Not in `TERMINOLOGY.md` - see Disconnected Artifacts summary |
| ENT-005 | Opponent | Entity | User statement | EVID-005 | OPPONENT-001, TREND-003 | ENT-006, ENT-007 (High/Low as attributes) | TERM-004 | UNKNOWN | SM-003, SM-004 | UNKNOWN | No | No | No | No | |
| ENT-006 | Opponent High | Entity | none | none | OPPONENT-002 | ENT-005 | TERM-005 | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Zero evidence |
| ENT-007 | Opponent Low | Entity | none | none | OPPONENT-003 | ENT-005 | TERM-005 | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Zero evidence |
| ENT-008 | Reversal | Entity | User statement | EVID-006 | REVERSAL-001 | UNKNOWN | TERM-007 | UNKNOWN | SM-005 | UNKNOWN | No | No | No | No | |
| ENT-009 | Premium | Entity | User statement | EVID-006 | REVERSAL-001 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Not in `TERMINOLOGY.md` - see Disconnected Artifacts summary |
| ENT-010 | Weekly Future | Entity (**Candidate**) | TR-001 transcript | EVID-007 | none | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Not promoted to a Rule. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. See `research/analysis/TR-001_ANALYSIS.md` Section 5. |
| ENT-011 | Mid Point | Entity (**Candidate**) | TR-001 transcript | EVID-007 | none | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Not promoted to a Rule. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. See `research/analysis/TR-001_ANALYSIS.md` Section 3.6. |
| ENT-012 | Trigger Point | Entity (**Candidate**) | TR-001 transcript | EVID-007 | none | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Not promoted to a Rule. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. See `research/analysis/TR-001_ANALYSIS.md` Section 5. |
| ENT-013 | Sellers' Perspective | Entity (**Candidate**) | TR-001 transcript | EVID-007 | none | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Not promoted to a Rule. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. See `research/analysis/TR-001_ANALYSIS.md` Section 5. |
| ENT-014 | Opening Range | Entity (**Candidate**) | TR-001 transcript | EVID-007 | none | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Not promoted to a Rule. Not yet in `DOMAIN_MODEL.md`/`TERMINOLOGY.md`. See `research/analysis/TR-001_ANALYSIS.md` Section 5. |

### Terminology

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TERM-001 | First Candle | Terminology | User statement | EVID-001 | STRIKE-001 | ENT-002 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | |
| TERM-002 | Strike | Terminology | User statement | EVID-001 | STRIKE-001 | ENT-001 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | |
| TERM-003 | Trend Point Low (TP Low) | Terminology | User statement | EVID-002 | TREND-001, TREND-002, TREND-003 | ENT-003 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | |
| TERM-004 | Opponent | Terminology | User statement | EVID-005 | OPPONENT-001, TREND-003 | ENT-005 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | |
| TERM-005 | Opponent High / Opponent Low | Terminology | none | none | OPPONENT-002, OPPONENT-003 | ENT-006, ENT-007 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Zero evidence |
| TERM-006 | Edge (Edge Detection) | Terminology | User statement | EVID-004 | TREND-003 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | No dedicated Entity - see Disconnected Artifacts summary |
| TERM-007 | Reversal | Terminology | User statement | EVID-006 | REVERSAL-001 | ENT-008 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | |

### Mathematical Definitions

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| _none yet_ | | | | | | | | | | | | | | | `MATHEMATICAL_SPECIFICATION.md` has no entries |

### States

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SM-001 | STRIKE_SELECTED | State | User statement | EVID-001 | STRIKE-001 | ENT-001 | UNKNOWN | UNKNOWN | UNKNOWN (possible successor: SM-002, SM-003 - hypothesised only, per `STATE_MACHINE.md`) | UNKNOWN | No | No | No | No | |
| SM-002 | TREND_TRACKING | State | User statement | EVID-002 | TREND-001, TREND-002 | ENT-003 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | |
| SM-003 | OPPONENT_ENGAGEMENT | State | User statement | EVID-005 | OPPONENT-001 | ENT-005 | UNKNOWN | UNKNOWN | SM-004 (hypothesised successor) | UNKNOWN | No | No | No | No | |
| SM-004 | OPPONENT_DEFEATED | State | none - inferred, not directly evidenced | none | OPPONENT-001 (inferred from wording only) | ENT-005 | UNKNOWN | UNKNOWN | SM-003 (hypothesised predecessor) | UNKNOWN | No | No | No | No | Hypothesis only - see `STATE_MACHINE.md` |
| SM-005 | REVERSAL_IDENTIFIED | State | User statement | EVID-006 | REVERSAL-001 | ENT-008 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | |

### Events

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| _none yet_ | | | | | | | | | | | | | | | No artifact has been classified as a discrete Event |

### Transcripts

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TR-001 | TR-001 (YouTube transcript, Tamil, ~11 daily segments) | Transcript | Original YouTube transcript, Evidence Level 1 | EVID-007 | STRIKE-001, TREND-001, TREND-002, TREND-003, OPPONENT-001, REVERSAL-001 | ENT-010, ENT-011, ENT-012, ENT-013, ENT-014 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | See `research/analysis/TR-001_ANALYSIS.md`. Video Title/URL still UNKNOWN per its metadata header. |

### Source Evidence

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EVID-001 | First candle -> strike selection statement | Source Evidence | User statement | (is itself the evidence) | STRIKE-001 | ENT-001, ENT-002 | TERM-001, TERM-002 | UNKNOWN | SM-001 | UNKNOWN | n/a | n/a | n/a | n/a | Not saved to `/research/transcripts` |
| EVID-002 | TP Low marking/updating statement | Source Evidence | User statement | (is itself the evidence) | TREND-001 | ENT-003 | TERM-003 | UNKNOWN | SM-002 | UNKNOWN | n/a | n/a | n/a | n/a | Not saved to `/research/transcripts` |
| EVID-003 | TP Low market-structure-change statement | Source Evidence | User statement | (is itself the evidence) | TREND-002 | ENT-004 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | n/a | n/a | n/a | n/a | Not saved to `/research/transcripts` |
| EVID-004 | Edge Detection statement | Source Evidence | User statement | (is itself the evidence) | TREND-003 | UNKNOWN | TERM-006 | UNKNOWN | UNKNOWN | UNKNOWN | n/a | n/a | n/a | n/a | Not saved to `/research/transcripts` |
| EVID-005 | Next Opponent Defeat statement | Source Evidence | User statement | (is itself the evidence) | OPPONENT-001 | ENT-005 | TERM-004 | UNKNOWN | SM-003 | UNKNOWN | n/a | n/a | n/a | n/a | Not saved to `/research/transcripts` |
| EVID-006 | Reversal identification statement | Source Evidence | User statement | (is itself the evidence) | REVERSAL-001 | ENT-008, ENT-009 | TERM-007 | UNKNOWN | SM-005 | UNKNOWN | n/a | n/a | n/a | n/a | Not saved to `/research/transcripts` |
| EVID-007 | TR-001 transcript (whole-source evidence) | Source Evidence | TR-001 (`/research/transcripts/TR-001.md`) | (is itself the evidence) | STRIKE-001, TREND-001, TREND-002, TREND-003, OPPONENT-001, REVERSAL-001 | ENT-010, ENT-011, ENT-012, ENT-013, ENT-014 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | n/a | n/a | n/a | n/a | Saved to `/research/transcripts/TR-001.md`. Counted as one source per the Confidence Policy, not one per daily segment within it. |

### Unknown Concepts

| Artifact ID | Artifact Name | Artifact Type | Origin Source | Evidence ID(s) | Related Rule(s) | Related Entity(s) | Related Terminology | Related Math Definition | Related State(s) | Related Event(s) | Implementation | Validation | Backtest | Production | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UNK-001 | IVL Level | Unknown Concept | TR-001 transcript | EVID-007 | none | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | No | No | No | No | Used repeatedly in TR-001 without ever being defined. See `research/analysis/TR-001_ANALYSIS.md` Section 14. |

---

## Disconnected Artifacts Summary

**Updated (Milestone 3.2):** TR-001 is now a saved transcript (no
longer "0 saved transcripts" as noted below at the time of original
writing), and 5 new Candidate entities (ENT-010 through ENT-014) plus
1 Unknown Concept (IVL Level) were added - none promoted to Rules. The
six Bible rules now each cite two Evidence IDs (their original
statement plus EVID-007/TR-001) instead of one.

No artifact in the current project has **zero** relationships to any
other artifact - every row above traces back to at
least one Evidence ID and at least one Rule (except the newly added
Candidates and Unknown Concept, which correctly show `none`/`UNKNOWN`
for Related Rule(s) since they are not part of any rule yet - this is
expected, not an error). However, the following
gaps exist where a relationship that would normally be expected is
`UNKNOWN` rather than populated, and are worth surfacing explicitly
rather than leaving buried in the table:

1. **TERM-006 (Edge / Edge Detection)** has no corresponding entry in
   `DOMAIN_MODEL.md` - it exists as a Rule (TREND-003) and a
   Terminology entry, but not as a Business Entity. Whether "Edge"
   should be modeled as its own entity, or is correctly just a
   condition rather than a thing, is unresolved.

2. **ENT-004 (Market Structure)** and **ENT-009 (Premium)** both exist
   as Business Entities but have no corresponding `TERMINOLOGY.md`
   entry - flagged previously in `DOMAIN_MODEL.md`'s own "Entities NOT
   modeled" caveats and repeated here since it produces a real gap in
   this traceability chain (Entity -> Terminology is `UNKNOWN` for
   both).

3. **OPPONENT-002 / OPPONENT-003 / ENT-006 / ENT-007 / TERM-005** form
   a fully self-consistent but entirely evidence-free cluster - every
   relationship among them is populated (they correctly reference each
   other), but none of them has an Evidence ID, an Origin Source, or a
   Related Rule outside this cluster. This is a "connected but
   floating" cluster, not a disconnected artifact, but it cannot be
   traced back to any actual evidence until OPPONENT-002/003 are
   defined.

4. **SM-004 (OPPONENT_DEFEATED)** is the only State with no Evidence
   ID at all - it is connected to OPPONENT-001 and ENT-005 only by
   inference (as already flagged in `STATE_MACHINE.md`), not by direct
   evidence.

5. **Mathematical Definitions and Events** are entirely empty
   categories - not disconnected artifacts (there are none to
   disconnect), but a structural gap: no artifact in the project has
   yet been formalised mathematically or classified as a discrete
   event, so both `Related Math Definition` and `Related Event(s)`
   columns read `UNKNOWN` for every single row in the matrix without
   exception.

None of the above are treated as errors - they are the expected shape
of a project with 6 original evidence statements, 1 saved transcript
(TR-001), and 5 unpromoted candidates. This summary exists so gaps are
visible and trackable, not silently absorbed into `UNKNOWN` cells
scattered across the table.

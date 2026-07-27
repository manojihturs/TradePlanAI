# TRADINGVIEW_STRATEGY_BIBLE.md

## Metadata
- Video ID:
- Source:
- Transcript Date:
- Analysis Version: 2 (refactored rule ID/category/lifecycle scheme - see `CHANGELOG` note at bottom)

---

## Category Taxonomy (fixed)

Every rule belongs to exactly one of the following categories, or
`UNKNOWN` until enough evidence exists to classify it. This list is
fixed and is not to grow ad hoc as new rules are added - a rule that
doesn't fit is filed under `UNKNOWN` and flagged in Open Questions,
not given a new category on the spot.

`CORE` · `PHILOSOPHY` · `WEEKLY_FUTURE` · `FIRST_CANDLE` · `STRIKE` ·
`TREND` · `STATE` · `CONTROL_ZONE` · `FLOW` · `OPPONENT` · `ENTRY` ·
`EXIT` · `REVERSAL` · `DECAY` · `PREMIUM` · `RISK` · `VALIDATION` ·
`MATH` · `UNKNOWN`

## Rule ID convention

`<CATEGORY>-<NNN>`, e.g. `TREND-001`, `STRIKE-001`, `OPPONENT-001`.
Numbering is sequential per category, not globally shared. IDs are
permanent once assigned - a rule is never renumbered, even if its
category assignment is later found to be wrong (in that case, mark it
superseded and create a new ID in the correct category, cross-linked).

## Rule lifecycle fields (every rule uses this template)

```
<CATEGORY>-<NNN>

Title:
Description / Business Rule:
Evidence:
Transcript Quote:

Category:            <one of the fixed categories above>
Status:               Draft | Under Review | Validated | Superseded
Confidence:           Low | Medium | High
Evidence Count:       <number of independent sources supporting this rule>
Transcript Sources:   <list, or "none saved yet">
Mathematical Definition: Unknown | Partially Known | Known
Implementation:       No | In Progress | Yes
Validation:           No | Yes
Backtested:           No | Yes
Production:           No | Yes

Depends On:           <rule IDs this rule requires, or "none yet">
Referenced By:        <rule IDs that reference this rule, or "none yet">
```

`Status` starts at `Draft` for every newly recorded rule and only
advances as evidence accumulates - it is not to be set to `Validated`
based on confidence alone.

---

## CORE

---

## PHILOSOPHY

---

## WEEKLY_FUTURE

---

## FIRST_CANDLE

---

## STRIKE

### STRIKE-001
Title:
Initial Strike Selection

Description / Business Rule:
The initial analysis begins by selecting a strike based on the first candle.

Evidence:
The strike price is selected based on the first candle.

Transcript Quote:
"...First candle... 24050..."

Category:            STRIKE
Status:               Draft
Confidence:           Medium
Evidence Count:       2
Transcript Sources:   TR-001 (/research/transcripts/TR-001.md) - see research/analysis/TR-001_ANALYSIS.md Section 3.1
Mathematical Definition: Unknown
Implementation:       No
Validation:           No
Backtested:           No
Production:           No

Depends On:           none yet
Referenced By:        none yet

---

## TREND

### TREND-001
Title:
Trend Point Low (TP Low)

Description / Business Rule:
Every analysed strike maintains a Trend Point Low. This value changes
dynamically as the trend evolves.

Evidence:
The TP Low is repeatedly marked and updated during market progression.

Transcript Quote:
(none provided yet - statement given directly, not quoted from a saved transcript)

Category:            TREND
Status:               Draft
Confidence:           Medium
Evidence Count:       2
Transcript Sources:   TR-001 (/research/transcripts/TR-001.md) - see research/analysis/TR-001_ANALYSIS.md Section 3.2
Mathematical Definition: Partially Known
Implementation:       No
Validation:           No
Backtested:           No
Production:           No

Depends On:           none yet
Referenced By:        TREND-002, TREND-003, OPPONENT-001

### TREND-002
Title:
Dynamic TP Low Adjustment

Description / Business Rule:
TP Low is not static. When market structure changes, TP Low is
converted to a new value.

Evidence:
(as stated by user)

Transcript Quote:
(none provided yet)

Category:            TREND
Status:               Draft
Confidence:           Medium
Evidence Count:       2
Transcript Sources:   TR-001 (/research/transcripts/TR-001.md) - see research/analysis/TR-001_ANALYSIS.md Section 3.2 (live TP Low update demonstrated at lines 70-77)
Mathematical Definition: Unknown
Implementation:       No
Validation:           No
Backtested:           No
Production:           No

Depends On:           TREND-001
Referenced By:        none yet

### TREND-003
Title:
Edge Detection

Description / Business Rule:
When both current and opponent TP Lows remain well below the selected
strike, probability of price moving below that strike is significantly
reduced.

Evidence:
(as stated by user)

Transcript Quote:
(none provided yet)

Category:            TREND
Status:               Draft
Confidence:           Medium
Evidence Count:       2
Transcript Sources:   TR-001 (/research/transcripts/TR-001.md) - see research/analysis/TR-001_ANALYSIS.md Section 3.5 (closest explicit definition found in TR-001, lines 84-87)
Mathematical Definition: Unknown
Implementation:       No
Validation:           No
Backtested:           No
Production:           No

Depends On:           TREND-001, OPPONENT-001
Referenced By:        none yet

---

## STATE

### STATE-001
Description:
Possible Transitions:

---

## CONTROL_ZONE

---

## FLOW

---

## OPPONENT

### OPPONENT-001
Title:
Next Opponent Defeat

Description / Business Rule:
A strike progresses only after defeating the next opponent.

Evidence:
Repeated references to "Next Opponent Defeat"

Transcript Quote:
(none provided yet)

Category:            OPPONENT
Status:               Draft
Confidence:           Medium
Evidence Count:       2
Transcript Sources:   TR-001 (/research/transcripts/TR-001.md) - see research/analysis/TR-001_ANALYSIS.md Section 3.3
Mathematical Definition: Unknown
Implementation:       No
Validation:           No
Backtested:           No
Production:           No

Depends On:           TREND-001, OPPONENT-002, OPPONENT-003
Referenced By:        TREND-003

### OPPONENT-002
Title:
Opponent High

Status:               Awaiting Evidence

### OPPONENT-003
Title:
Opponent Low

Status:               Awaiting Evidence

---

## ENTRY

---

## EXIT

---

## REVERSAL

### REVERSAL-001
Title:
Reversal Identification

Description / Business Rule:
A reversal is not assumed. It must be identified through premium behaviour.

Evidence:
(as stated by user)

Transcript Quote:
(none provided yet)

Category:            REVERSAL
Status:               Draft
Confidence:           Medium
Evidence Count:       2
Transcript Sources:   TR-001 (/research/transcripts/TR-001.md) - see research/analysis/TR-001_ANALYSIS.md Section 3.4
Mathematical Definition: Unknown
Implementation:       No
Validation:           No
Backtested:           No
Production:           No

Depends On:           none yet
Referenced By:        none yet

---

## DECAY

---

## PREMIUM

---

## RISK

---

## VALIDATION

---

## MATH

---

## UNKNOWN

---

## Mathematical Candidates

---

## Open Questions

- UPDATED (Milestone 3.2): STRIKE-001, TREND-001, TREND-002,
  TREND-003, OPPONENT-001, and REVERSAL-001 are now each additionally
  backed by `TR-001` (`/research/transcripts/TR-001.md`), a saved
  transcript - see `research/analysis/TR-001_ANALYSIS.md`. Each rule's
  original conversational-statement source remains unsaved, but
  Evidence Count now reflects 2 independent sources (the original
  statement + TR-001) per rule, per the Confidence Policy in
  `docs/EVIDENCE_MATRIX.md`. Confidence updated from High/Medium
  (pre-policy values) to Medium for all six, matching the policy's
  Evidence-Count-2 = Medium mapping - this is a downward correction for
  five of the six rules (previously recorded as High without
  policy justification) and resolves the TREND-003 discrepancy
  previously flagged in `EVIDENCE_MATRIX.md`.
- STRIKE-001: "selected based on the first candle" - selected *how*?
  The quoted fragment ("...First candle... 24050...") shows a
  resulting strike (24050) but not the calculation connecting the
  first candle to that strike.
- OPPONENT-001: "opponent" is not yet defined (see `TERMINOLOGY.md`).
  Is it the same concept as "competitor" used elsewhere in this
  project (the opposite-side CE/PE contract), or something distinct?
  Also unclear what mathematically constitutes "defeating" the next
  opponent. "Opponent High" (OPPONENT-002) and "Opponent Low"
  (OPPONENT-003) are now reserved as placeholder rule IDs - Awaiting
  Evidence, no behaviour defined.
- TREND-001/002/003: "Trend Point Low" is not yet defined
  mathematically - computed from the strike's own data, or derived
  from another strike/ladder? TREND-003 introduces "opponent TP Low"
  without yet clarifying how "well below" is measured (fixed distance,
  relative threshold, or qualitative only).
- RESOLVED (Milestone 3.2): TREND-003's Confidence was previously
  lower (Medium) than the other five rules (High) with no policy
  justification for either value. All six are now Medium, consistent
  with Evidence Count 2 under the Confidence Policy.

---

## Conflicting Statements

---

## Assumptions (if any)

None unless explicitly marked.

---

## Refactor note

Analysis Version 2: rule IDs migrated from the `RULE-<CATEGORY>-<NNN>`
format to `<CATEGORY>-<NNN>`; fixed category taxonomy introduced;
lifecycle fields (Status, Evidence Count, Transcript Sources,
Implementation/Validation/Backtested/Production) and dependency
tracking (Depends On / Referenced By) added to every rule. No new
rules were extracted during this refactor. Old IDs -> new IDs:
`RULE-STRIKE-001` -> `STRIKE-001`; `RULE-TP-001` -> `TREND-001`;
`RULE-DYN-001` -> `TREND-002`; `RULE-EDGE-001` -> `TREND-003`;
`RULE-OPP-002` -> `OPPONENT-001`; `RULE-REV-001` -> `REVERSAL-001`.

# Domain Model

Every business entity mentioned in `TRADINGVIEW_STRATEGY_BIBLE.md`
(Version 2, 6 rules), modeled as a static domain concept only - no
behaviour, no state transitions, no new rules. This document answers
"what things exist in this business domain," not "what do they do" or
"how do they change" (see `STATE_MACHINE.md` v0.1 for the latter,
frozen as Draft, and not extended by this document).

## Format

```
### Entity Name

Description:
Attributes:           <only attributes directly evidenced; "Unknown" otherwise>
Related Rules:         <rule IDs that mention this entity>
Related Terminology:   <TERMINOLOGY.md entries, if any>
Evidence Level:        <per KNOWLEDGE_SOURCES.md, or "not yet sourced">
Status:                Confirmed | Partial | Unknown
```

---

### Strike

Description:
A tradable options strike price - the subject of analysis once
selected (STRIKE-001).

Attributes:
- Selected via a strike-selection process referencing the first candle
  (STRIKE-001) - the selection mechanism itself is Unknown.
- Associated with its own Trend Point Low (TREND-001).
- Associated with an Opponent, which it must "defeat" to progress
  (OPPONENT-001).
- No other attributes (e.g. strike price value type, expiry, option
  side) are evidenced yet.

Related Rules:         STRIKE-001, TREND-001, TREND-003, OPPONENT-001
Related Terminology:   Strike
Evidence Level:        not yet sourced
Status:                Partial

---

### First Candle

Description:
A candle used as the basis for initial strike selection (STRIKE-001).

Attributes:
Unknown - which candle (session open, a fixed time, a specific
duration) is not established. Only a worked example exists (a
resulting strike, 24050), not the candle's own defining attributes.

Related Rules:         STRIKE-001
Related Terminology:   First Candle
Evidence Level:        not yet sourced
Status:                Unknown

---

### Trend Point Low (TP Low)

Description:
A per-strike reference value, described as being repeatedly marked and
updated as the market/trend progresses (TREND-001), and as non-static -
converting to a new value when market structure changes (TREND-002).

Attributes:
- Belongs to a specific strike (one TP Low per analysed strike,
  TREND-001).
- Value changes over time (TREND-001, TREND-002).
- Referenced in comparison to an "opponent" TP Low (TREND-003),
  implying an Opponent entity also has its own TP Low.
- Precise calculation/formula: Unknown.

Related Rules:         TREND-001, TREND-002, TREND-003, OPPONENT-001
Related Terminology:   Trend Point Low (TP Low)
Evidence Level:        not yet sourced
Status:                Partial

---

### Market Structure

Description:
Referenced only as the trigger condition for TP Low updating
(TREND-002: "when market structure changes, TP Low is converted to a
new value").

Attributes:
Unknown - what constitutes "market structure," and what specifically
counts as a "change" to it, are not defined by any current rule.

Related Rules:         TREND-002
Related Terminology:   (none yet - not currently a TERMINOLOGY.md entry)
Evidence Level:        not yet sourced
Status:                Unknown

---

### Opponent

Description:
An entity associated with a strike that must be "defeated" for the
strike to progress (OPPONENT-001). Possesses its own TP Low, compared
against the current strike's TP Low (TREND-003).

Attributes:
- Has a "High" and a "Low" (OPPONENT-002, OPPONENT-003 - both
  Awaiting Evidence, no behaviour defined).
- Has a TP Low comparable to the current strike's TP Low (TREND-003).
- Relationship to "Strike" (e.g. whether the Opponent is itself
  another strike, the opposite-side CE/PE contract, or a distinct
  concept) is Unknown - see `TERMINOLOGY.md`'s open question on
  whether this is the same concept as "competitor" used elsewhere in
  this project. Not assumed equal without confirming evidence.

Related Rules:         OPPONENT-001, OPPONENT-002, OPPONENT-003, TREND-003
Related Terminology:   Opponent, Opponent High / Opponent Low
Evidence Level:        not yet sourced
Status:                Unknown

---

### Opponent High

Description:
Referenced as a dependency of OPPONENT-001, alongside TP Low and
Opponent Low. No behaviour or definition recorded - placeholder rule
OPPONENT-002 is Awaiting Evidence.

Attributes:
Unknown.

Related Rules:         OPPONENT-002 (placeholder), OPPONENT-001 (referencing rule)
Related Terminology:   Opponent High / Opponent Low
Evidence Level:        not yet sourced
Status:                Unknown

---

### Opponent Low

Description:
Referenced as a dependency of OPPONENT-001, alongside TP Low and
Opponent High. No behaviour or definition recorded - placeholder rule
OPPONENT-003 is Awaiting Evidence.

Attributes:
Unknown.

Related Rules:         OPPONENT-003 (placeholder), OPPONENT-001 (referencing rule)
Related Terminology:   Opponent High / Opponent Low
Evidence Level:        not yet sourced
Status:                Unknown

---

### Reversal

Description:
A change in market direction that, per REVERSAL-001, is never assumed
by default and must instead be identified through premium behaviour.

Attributes:
- Identification method: tied to "premium behaviour" (see Premium
  entity below) - the specific behaviour is Unknown.
- No other attributes evidenced.

Related Rules:         REVERSAL-001
Related Terminology:   Reversal
Evidence Level:        not yet sourced
Status:                Partial

---

### Premium

Description:
Referenced only indirectly, as the basis for identifying a Reversal
(REVERSAL-001: "identified through premium behaviour"). No rule yet
defines Premium itself as a first-class concept (e.g. which
contract's premium, CE, PE, or both).

Attributes:
Unknown.

Related Rules:         REVERSAL-001
Related Terminology:   (none yet - not currently a TERMINOLOGY.md entry)
Evidence Level:        not yet sourced
Status:                Unknown

---

## Entities NOT modeled

No entities from the existing Python implementation (e.g. `Candle`,
`PremiumMapping`, `Position`, `LevelState`) are included here, even
though analogous concepts may eventually turn out to correspond to
entities above (e.g. "Premium" here vs. `strategy/entry_signal.py`'s
`Candle.close`). Per the project's standing rule, the existing
implementation is LEVEL 3 evidence (a prior interpretation) and is not
used to fill in attributes or definitions here - any correspondence
between this domain model and the existing code is a `GAP_ANALYSIS.md`
question, not a `DOMAIN_MODEL.md` one.

## Summary table

| Entity | Status | Related Rules |
|---|---|---|
| Strike | Partial | STRIKE-001, TREND-001, TREND-003, OPPONENT-001 |
| First Candle | Unknown | STRIKE-001 |
| Trend Point Low (TP Low) | Partial | TREND-001, TREND-002, TREND-003, OPPONENT-001 |
| Market Structure | Unknown | TREND-002 |
| Opponent | Unknown | OPPONENT-001, OPPONENT-002, OPPONENT-003, TREND-003 |
| Opponent High | Unknown | OPPONENT-002, OPPONENT-001 |
| Opponent Low | Unknown | OPPONENT-003, OPPONENT-001 |
| Reversal | Partial | REVERSAL-001 |
| Premium | Unknown | REVERSAL-001 |

No entity above is `Confirmed` - none has enough evidence yet. This
table will be revised as `/research` gains actual sourced material.

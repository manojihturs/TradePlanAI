# Terminology

Every trading term used across `TRADINGVIEW_STRATEGY_BIBLE.md` and
`MATHEMATICAL_SPECIFICATION.md` is defined exactly once here, so the
same term is never interpreted two different ways in different parts
of the documentation. A term's definition here reflects only what the
evidence has actually established - where the evidence is incomplete,
the definition says so explicitly rather than filling the gap.

## Format

```
### Term

Definition:
Evidence Level:      (1-4, per KNOWLEDGE_SOURCES.md, or "not yet sourced")
Used By:              <rule IDs>
Status:               Confirmed | Partial | Unknown
```

---

### First Candle

Definition:
The candle used as the basis for initial strike selection (STRIKE-001).
Which specific candle (session open, a fixed time, a specific
duration) is not yet established - the only evidence so far is a
worked example naming a resulting strike (24050), not the calculation
itself.

Evidence Level:       not yet sourced (statement given directly, no saved transcript)
Used By:              STRIKE-001
Status:               Unknown

---

### Strike

Definition:
A tradable options strike price, selected as the subject of analysis
per STRIKE-001. General trading term, not itself in need of
strategy-specific definition beyond how it is selected (see
STRIKE-001) and how it relates to Trend Point Low / Opponent concepts
(see below).

Evidence Level:       not yet sourced
Used By:              STRIKE-001, TREND-001, TREND-003, OPPONENT-001
Status:               Partial

---

### Trend Point Low (TP Low)

Definition:
A per-strike reference value that is repeatedly marked and updated as
the market/trend progresses (TREND-001). It is not static - it
converts to a new value when market structure changes (TREND-002). The
precise calculation of what value it takes, and exactly what "market
structure changes" means as a trigger for updating it, are not yet
established.

Evidence Level:       not yet sourced
Used By:              TREND-001, TREND-002, TREND-003, OPPONENT-001
Status:               Partial

---

### Opponent

Definition:
Not yet established. Referenced in OPPONENT-001 ("defeating the next
opponent") and TREND-003 ("opponent TP Low"), implying each
strike/trade has an associated "opponent" with its own TP Low and
High/Low values, but no direct statement yet defines what this
opponent is.

Open question: is this the same concept as "competitor" used elsewhere
in this project (the opposite-side CE/PE contract at the same strike,
per `strategy/exit_signal.py`'s Competitor Exit and
`INVESTIGATIONS.md` #9/#11/#13)? This is a plausible hypothesis only
(would be Evidence Level 4 if recorded) - not confirmed by any direct
statement about the original strategy, and not to be assumed equal
without confirming evidence.

Evidence Level:       not yet sourced
Used By:              OPPONENT-001, TREND-003
Status:               Unknown

---

### Opponent High / Opponent Low

Definition:
Referenced as dependencies of OPPONENT-001 (alongside TP Low).
Placeholder rule IDs (OPPONENT-002, OPPONENT-003) have been reserved
for these terms so the dependency graph stays complete, but no
behaviour or definition has been recorded - awaiting evidence.

Evidence Level:       not yet sourced
Used By:              OPPONENT-001 (dependency); own rule IDs: OPPONENT-002 (Opponent High), OPPONENT-003 (Opponent Low)
Status:               Unknown

---

### Edge (Edge Detection)

Definition:
A condition (TREND-003) where both the current strike's and the
opponent's TP Lows remain "well below" the selected strike, said to
significantly reduce the probability of price moving below that
strike. "Well below" is not yet quantified (no fixed distance,
percentage, or threshold established).

Evidence Level:       not yet sourced
Used By:              TREND-003
Status:               Partial

---

### Reversal

Definition:
A change in market direction. Per REVERSAL-001, a reversal is never
assumed by default - it must be identified through premium behaviour.
Which specific premium behaviour constitutes identification is not yet
established.

Evidence Level:       not yet sourced
Used By:              REVERSAL-001
Status:               Partial

---

## Status

All terms above are `Unknown` or `Partial` - none are `Confirmed` yet.
This document will grow as transcripts and other sources are added to
`/research` and cross-referenced against these definitions.

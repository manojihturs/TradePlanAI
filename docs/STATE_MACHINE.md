# State Machine

The original strategy's states and evidenced transitions between them,
derived strictly from `TRADINGVIEW_STRATEGY_BIBLE.md`. Per the
project's evidence-only rule, this is NOT a complete state machine -
it is only as complete as the current rule set (6 rules, 0 saved
transcripts) allows. Fields with no supporting rule are marked
`UNKNOWN - insufficient evidence` rather than filled in.

## Status

**Incomplete by necessity.** No transcript has been saved to
`/research/transcripts` yet - every rule so far traces to a statement
given directly in conversation (see each rule's `Transcript Sources`
field in `RULE_INDEX.md`, all currently "none saved yet"). This
document will be substantially rebuilt once real transcript evidence
is available; treat everything below as a skeleton, not a
specification.

## States derivable from current evidence

Each state below is only included because a specific Bible rule
implies its existence. No state is added on the basis of "this seems
like it should exist."

---

### STATE: STRIKE_SELECTED

**Description:**
A strike has been chosen as the subject of analysis, based on the
first candle (STRIKE-001). This is the earliest state implied by any
current rule - what (if anything) precedes it is not evidenced.

**Entry Conditions:**
UNKNOWN - insufficient evidence. STRIKE-001 states selection happens
"based on the first candle" but not the precise triggering condition
(e.g. candle close, a specific price relationship, session open time).

**Exit Conditions:**
UNKNOWN - insufficient evidence.

**Next Possible States:**
Presumably leads toward TREND_TRACKING and/or OPPONENT_ENGAGEMENT
(TREND-001 and OPPONENT-001 both describe behaviour "per analysed
strike," implying a selected strike is a precondition) - not
confirmed by any direct statement about ordering.

**Impossible Transitions:**
UNKNOWN - insufficient evidence.

**Supporting rule(s):** STRIKE-001

---

### STATE: TREND_TRACKING

**Description:**
A selected strike's Trend Point Low (TP Low) is being actively
tracked and is subject to updates (TREND-001). Whether this is a
distinct state from STRIKE_SELECTED, or an attribute that exists
concurrently with other states, is not established - modeled here as
a separate state only because TP Low is described as something that
changes over time, which implies some ongoing condition.

**Entry Conditions:**
UNKNOWN - insufficient evidence.

**Exit Conditions:**
UNKNOWN - insufficient evidence. TREND-002 states TP Low "converts to
a new value when market structure changes," but does not establish
whether that conversion is an exit from this state, a transition
within it, or unrelated to state boundaries at all.

**Next Possible States:**
UNKNOWN - insufficient evidence.

**Impossible Transitions:**
UNKNOWN - insufficient evidence.

**Supporting rule(s):** TREND-001, TREND-002

---

### STATE: OPPONENT_ENGAGEMENT

**Description:**
A strike is being evaluated against its "next opponent" (OPPONENT-001)
- implied to be a precondition for progression, but the mechanics of
engagement itself are not described.

**Entry Conditions:**
UNKNOWN - insufficient evidence.

**Exit Conditions:**
Possibly "opponent defeated" (see OPPONENT_DEFEATED below), per
OPPONENT-001's phrase "progresses only after defeating the next
opponent" - but "defeating" is not mathematically defined (see
`TERMINOLOGY.md`, `Opponent` entry).

**Next Possible States:**
OPPONENT_DEFEATED (hypothesised only - not directly stated).

**Impossible Transitions:**
UNKNOWN - insufficient evidence.

**Supporting rule(s):** OPPONENT-001 (also depends on OPPONENT-002 and
OPPONENT-003, both placeholders - Awaiting Evidence)

---

### STATE: OPPONENT_DEFEATED

**Description:**
Implied end-state of OPPONENT_ENGAGEMENT, per OPPONENT-001's wording
that a strike "progresses only after defeating the next opponent" -
this state name and its existence are inferred from that phrasing, not
directly named in any evidence. Flagged as a hypothesis, not a
confirmed state.

**Entry Conditions:**
UNKNOWN - insufficient evidence (depends on OPPONENT-002/OPPONENT-003
definitions, both Awaiting Evidence).

**Exit Conditions:**
UNKNOWN - insufficient evidence.

**Next Possible States:**
Possibly relates to TREND-003 (Edge Detection), which is evaluated in
terms of "current and opponent TP Lows" - but no direct statement
connects OPPONENT_DEFEATED to TREND-003.

**Impossible Transitions:**
UNKNOWN - insufficient evidence.

**Supporting rule(s):** OPPONENT-001 (inferred only)

---

### STATE: REVERSAL_IDENTIFIED

**Description:**
A reversal has been confirmed through premium behaviour, per
REVERSAL-001's explicit statement that reversal is "not assumed" and
"must be identified through premium behaviour." What premium behaviour
specifically constitutes identification is not established.

**Entry Conditions:**
UNKNOWN - insufficient evidence (the "premium behaviour" referenced in
REVERSAL-001 is not further specified anywhere yet).

**Exit Conditions:**
UNKNOWN - insufficient evidence.

**Next Possible States:**
UNKNOWN - insufficient evidence.

**Impossible Transitions:**
The only transition-level statement any current rule makes: a
reversal is explicitly stated to never be entered by assumption alone
(REVERSAL-001) - i.e. there is no direct "assume reversal" transition
into this state from any other state. This is the one negative/
impossible-transition rule the evidence actually supports.

**Supporting rule(s):** REVERSAL-001

---

## States NOT included

No `FLAT`, `IN_POSITION`, `ENTRY`, or `EXIT` states are modeled here,
even though the existing Python implementation
(`strategy/position_manager.py`) has a FLAT/OPEN model and the current
Bible has empty `ENTRY`/`EXIT`/`STATE` category sections. Per the
project's standing rule, the existing implementation is LEVEL 3
evidence (a prior interpretation) and is not assumed to reflect the
original strategy's actual state structure - no state is added here on
that basis alone.

## Diagram

Not drawn yet. A state diagram requires confirmed transitions between
states; with 4 of 5 states above having `UNKNOWN` entry/exit
conditions and one transition (OPPONENT_ENGAGEMENT ->
OPPONENT_DEFEATED) only hypothesised, a diagram at this point would
visually imply more certainty than the evidence supports.

## What is needed to complete this document

- At least one saved transcript in `/research/transcripts` describing
  the sequence of market conditions the strategy actually walks
  through, ideally narrated in the author's own words with enough
  detail to state concrete entry/exit conditions per state.
- Definitions for OPPONENT-002 (Opponent High) and OPPONENT-003
  (Opponent Low), currently Awaiting Evidence.
- Clarification of what "premium behaviour" identifies a reversal
  (REVERSAL-001).
- Explicit confirmation of state ordering (e.g. does STRIKE_SELECTED
  always precede TREND_TRACKING and OPPONENT_ENGAGEMENT, or can they
  occur independently/concurrently?).

## Traceability

Every state above cites the Bible rule(s) it derives from. No state,
condition, or transition appears here without a corresponding rule ID
or an explicit `UNKNOWN` marker.

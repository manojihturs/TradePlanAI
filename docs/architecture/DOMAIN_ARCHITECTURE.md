# Domain Architecture

> **Milestone 4.0R note:** Implementation technology pivoted from
> C#/.NET to Python — see `docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md`.
> No domain responsibility, Rule ID, or Entity ID below changed as a
> result; only language-specific wording was updated.

Describes the responsibility of every confirmed and candidate domain
object, and nothing else — no behaviour, no calculations, no
implementation-language syntax. Every object below cites the Rule
ID(s)/Entity ID(s) it is derived from. Where the underlying
mathematics or exact triggering condition is `Unknown` (per
`TRADINGVIEW_STRATEGY_BIBLE.md` and `docs/DOMAIN_MODEL.md`), this
document names an **extension point** — a place in the architecture
reserved for that behaviour once evidenced — rather than guessing at
it.

## Status key

- **Confirmed** — backed by Bible rules with Evidence Count ≥ 2 (all
  six current rules, per `RULE_INDEX.md`)
- **Candidate** — from `research/analysis/TR-001_ANALYSIS.md`, added
  to `EVIDENCE_MATRIX.md`/`TRACEABILITY_MATRIX.md` as `Status =
  Candidate`, not promoted into the Bible or Domain Model
- **Unknown** — referenced but never defined (IVL Level only)

---

## Strike — Confirmed

**Entity ID:** ENT-001. **Supporting Rules:** STRIKE-001, TREND-001,
TREND-003, OPPONENT-001.

**Responsibility:** Represents a tradable options strike price that
has become the subject of analysis for a session. Per `DOMAIN_MODEL.md`,
a Strike is associated with its own Trend Point (TREND-001) and with
an Opponent it must "defeat" to progress (OPPONENT-001).

**Known attributes:** None beyond its role as the analysis subject —
no strike-price data type, expiry, or option-side attribute is
evidenced (`DOMAIN_MODEL.md` explicitly states this).

**Extension point:** *Strike selection mechanism.* STRIKE-001 states a
strike is "selected based on the first candle" but the exact
calculation connecting the first candle to a resulting strike is an
open question (`TRADINGVIEW_STRATEGY_BIBLE.md` Open Questions). The
architecture reserves a pluggable **strike-selection strategy** seam
in `Application` (see `RULE_ENGINE_ARCHITECTURE.md`) rather than
hardcoding any candidate formula.

---

## First Candle — Confirmed

**Entity ID:** ENT-002. **Supporting Rule:** STRIKE-001.

**Responsibility:** Represents the candle used as the basis for
initial Strike selection. Its precise definition (session-open candle,
a fixed duration, etc.) is `Unknown` per `DOMAIN_MODEL.md` — only that
such a candle exists and feeds Strike selection.

**Extension point:** The concrete candle-selection window (open time,
duration) is left as a configuration/extension point, not a fixed
value, until evidenced.

---

## TrendPoint (Trend Point Low / TP Low) — Confirmed

**Entity ID:** ENT-003. **Supporting Rules:** TREND-001, TREND-002,
TREND-003, OPPONENT-001.

**Responsibility:** A per-Strike reference value that is marked and
can be updated ("converted to a new value") when market structure
changes (TREND-002). Every analysed Strike maintains exactly one
TrendPoint at a time (TREND-001). Also referenced in comparison to an
Opponent's own TrendPoint (TREND-003 — "Edge" condition).

**Known attributes:** Belongs to exactly one Strike; its value changes
over time; comparable to another TrendPoint belonging to an Opponent.

**Extension point:** *TrendPoint calculation and update trigger.*
Neither the formula producing a TrendPoint's value, nor the precise
definition of "market structure changes" that triggers an update
(TREND-002), is evidenced (`Mathematical Definition: Partially Known`
in the Bible for TREND-001, `Unknown` for TREND-002). The architecture
represents TrendPoint as a value that can be read and (separately)
updated, without designing the update algorithm itself.

---

## Opponent — Confirmed

**Entity ID:** ENT-005. **Supporting Rules:** OPPONENT-001, TREND-003.

**Responsibility:** An entity associated with a Strike that must be
"defeated" for that Strike to progress (OPPONENT-001). Possesses its
own TrendPoint, comparable against the current Strike's TrendPoint
(TREND-003, the Edge condition).

**Known attributes:** Has a High and a Low (see below); has a
TrendPoint of its own.

**Open question carried into the architecture:** Whether "Opponent" is
the same concept as "competitor" already implemented elsewhere in this
repository (`strategy/exit_signal.py`'s Competitor Exit) is explicitly
unconfirmed (`TERMINOLOGY.md`). **This architecture does not assume
they are the same** — the `domain` package's Opponent object is
designed as its own concept, not wired to or modeled after the
existing Python `strategy/` package's competitor logic, even though
both now happen to be implemented in Python. Proximity of language is
not evidence of conceptual equivalence.

**Extension point:** *"Defeat" condition.* What mathematically
constitutes one Strike/side "defeating" its Opponent is `Unknown`
(Bible Open Questions). The architecture provides a place to express a
defeat evaluation (see Rule Engine architecture) without defining what
that evaluation checks.

---

## Opponent High / Opponent Low — Awaiting Evidence

**Entity IDs:** ENT-006, ENT-007. **Placeholder Rules:** OPPONENT-002,
OPPONENT-003 (`Status: Awaiting Evidence`, Evidence Count 0 in
`RULE_INDEX.md`).

**Responsibility:** Attributes of Opponent referenced by OPPONENT-001
as dependencies, but with zero recorded behaviour.

**Architectural treatment:** Modeled only as reserved attribute slots
on Opponent (a High value and a Low value), with **no defined
computation**. No extension point is designed beyond "a place these
values could eventually be read from," since there is not yet enough
evidence to know what kind of extension point (a formula? a lookup? an
external reference?) would even be appropriate. Building anything more
concrete here would mean guessing — explicitly disallowed.

---

## Market Structure — Confirmed (as a trigger reference only)

**Entity ID:** ENT-004. **Supporting Rule:** TREND-002.

**Responsibility:** Referenced only as the trigger condition for
TrendPoint updates ("when market structure changes, TP Low is
converted to a new value"). Not yet a `TERMINOLOGY.md` entry
(disconnected artifact per `M3_3_REPOSITORY_VALIDATION.md`).

**Extension point:** Represented architecturally as an abstract
"change signal" that TrendPoint's update mechanism can listen for —
without defining what that signal actually detects, since "what
constitutes market structure" and "what counts as a change to it" are
both `Unknown` (`DOMAIN_MODEL.md`).

---

## Reversal — Confirmed

**Entity ID:** ENT-008. **Supporting Rule:** REVERSAL-001.

**Responsibility:** A change in market direction that is never assumed
by default — REVERSAL-001 states it "must be identified through
premium behaviour." Represents an identified/confirmed state, not a
default/assumed one.

**Extension point:** *Identification method.* Which specific premium
behaviour constitutes identification is `Unknown` (`DOMAIN_MODEL.md`,
`STATE_MACHINE.md`'s `REVERSAL_IDENTIFIED` state — all entry
conditions marked `UNKNOWN — insufficient evidence`). The architecture
reserves a Reversal-identification extension point in the Rule
Engine, deliberately without a default "assume reversal" path — this
absence is itself evidenced (`STATE_MACHINE.md`'s one confirmed
"Impossible Transition": no direct assumption-based entry into
`REVERSAL_IDENTIFIED`).

---

## Premium — Confirmed (thin)

**Entity ID:** ENT-009. **Supporting Rule:** REVERSAL-001.

**Responsibility:** Referenced only indirectly, as the basis for
identifying a Reversal. No rule defines Premium as a first-class
concept yet (which contract, CE/PE/both — `DOMAIN_MODEL.md`). Not yet
a `TERMINOLOGY.md` entry.

**Architectural treatment:** Modeled as a minimal value holder only —
deliberately thin, since adding CE/PE-specific structure now would be
inventing attributes the evidence doesn't yet support.

---

## Edge — Confirmed as a condition, not (yet) an entity

**Supporting Rule:** TREND-003. **Terminology:** TERM-006.

**Important distinction carried from the Traceability review:** Edge
has no dedicated Domain Model entity (`M3_3_REPOSITORY_VALIDATION.md`
Warning/Disconnected-Artifact #1 — flagged as unresolved whether Edge
should be modeled as its own thing or is correctly just a condition).
This architecture treats Edge as a **condition evaluated over two
TrendPoints** (a Strike's own TrendPoint and its Opponent's
TrendPoint), not as a standalone stored object — consistent with
TREND-003's wording ("when both... remain well below the selected
strike"). If future evidence establishes Edge needs its own identity
(e.g. it persists, has a lifecycle, is referenced elsewhere
independently of the comparison that produced it), this would become
a Domain object at that point — not before.

**Extension point:** The comparison itself ("well below") has no
quantified threshold (`TERMINOLOGY.md`) — represented as an
evaluable-but-unimplemented condition.

---

## MarketSession — Architectural container (not a cited entity)

No Rule ID or Entity ID directly names "MarketSession." It is included
here as an architectural necessity: `STRIKE_SELECTED` is described in
`STATE_MACHINE.md` as "the earliest state implied by any current
rule," and TR-001's own structure is ~11 independent daily analyses,
implying every confirmed rule and state operates *within* a session
scope that resets daily. `STATE_MACHINE.md` does not evidence session
lifecycle rules beyond this implication, so MarketSession is
represented only as a scope/container that holds one day's Strikes,
TrendPoints, and States — with no lifecycle behaviour (start/end
triggers, reset rules) designed, since none is evidenced.

---

## Candidate objects (from TR-001, not promoted)

Each of the following exists only as an Entity row in
`EVIDENCE_MATRIX.md`/`TRACEABILITY_MATRIX.md` (`Status: Candidate`,
`Confidence: Low (Derived from TR-001 only)`). None has a corresponding
Bible rule. Per Milestone 4.0's instruction, these get **extension
points, not implementations** — placeholders the architecture can grow
into if/when promoted, never active in the Rule Engine's evaluation
path until they are.

### WeeklyFuture (Candidate) — ENT-010
Per `TR-001_ANALYSIS.md` Section 5: described as the *primary* basis
for level-setting in TR-001, but not officially published — reconstructed
via premium analysis. Reserved as a possible future reference-data
source; no computation designed.

### MidPoint (Candidate) — ENT-011
Per `TR-001_ANALYSIS.md` Section 3.6: arithmetic midpoint between a
Top strike and Bottom strike, used as an ad hoc intermediate
confirmation gate in at least two observed instances. Reserved as a
possible derived value once (and if) Top/Bottom strike concepts are
themselves confirmed as Domain objects (they are not, currently).

### TriggerPoint (Candidate) — ENT-012
Per `TR-001_ANALYSIS.md` Section 5: a price point where a "big player"
reaction is said to occur, described narratively with one worked
example only. Reserved as a possible future Rule Engine signal type.

### SellersPerspective (Candidate) — ENT-013
Per `TR-001_ANALYSIS.md` Section 5: a named alternative analytical
lens (option-seller viewpoint) distinct from the buyer-oriented
TrendPoint framework. Reserved as a possible alternative
evaluation strategy, structurally parallel to but not merged with the
TrendPoint-based rules.

### OpeningRange (Candidate) — ENT-014
Per `TR-001_ANALYSIS.md` Section 5: first-5-minute-candle high/low
used specifically on the Spot chart, described as distinct from the
Future-based TrendPoint system. Reserved as a possible alternative
First-Candle-adjacent concept, not merged with `First Candle` above
since the transcript itself treats them as separate methodologies.

---

## Unknown Concepts (explicitly excluded from Domain objects)

### IVL Level — Unknown
Per `M3_3_REPOSITORY_VALIDATION.md` (Candidate Promotion Check,
Section 9): confirmed **not present** in the Bible, Domain Model, or
State Machine, and this document does **not** introduce it either. No
extension point is designed for IVL Level — designing one would imply
enough understanding to know what kind of placeholder is appropriate,
which the evidence does not support (`TR-001_ANALYSIS.md` Section 14).
It remains tracked only in `EVIDENCE_MATRIX.md`/`TRACEABILITY_MATRIX.md`
as `UNK-001` until a defining source exists.

---

## Summary table

| Domain object | Status | Entity ID | Rule(s) | Extension point designed? |
|---|---|---|---|---|
| Strike | Confirmed | ENT-001 | STRIKE-001 | Yes — selection strategy |
| First Candle | Confirmed | ENT-002 | STRIKE-001 | Yes — candle window |
| TrendPoint | Confirmed | ENT-003 | TREND-001/002/003 | Yes — calc + update trigger |
| Opponent | Confirmed | ENT-005 | OPPONENT-001, TREND-003 | Yes — defeat evaluation |
| Opponent High/Low | Awaiting Evidence | ENT-006/007 | OPPONENT-002/003 | Attribute slot only |
| Market Structure | Confirmed (thin) | ENT-004 | TREND-002 | Yes — abstract change signal |
| Reversal | Confirmed | ENT-008 | REVERSAL-001 | Yes — identification method |
| Premium | Confirmed (thin) | ENT-009 | REVERSAL-001 | Minimal value holder |
| Edge | Confirmed (condition) | (none — see above) | TREND-003 | Yes — comparison, no threshold |
| MarketSession | Architectural only | (none) | (implied) | Container only |
| WeeklyFuture | Candidate | ENT-010 | (none) | Reserved, inactive |
| MidPoint | Candidate | ENT-011 | (none) | Reserved, inactive |
| TriggerPoint | Candidate | ENT-012 | (none) | Reserved, inactive |
| SellersPerspective | Candidate | ENT-013 | (none) | Reserved, inactive |
| OpeningRange | Candidate | ENT-014 | (none) | Reserved, inactive |
| IVL Level | Unknown | UNK-001 | (none) | None — deliberately absent |

# Entity Dependency Graph

Evidence-only synthesis covering the 9 Confirmed entities (ENT-001
through ENT-009), the 5 Candidate entities (ENT-010 through ENT-014),
and the 1 Unknown Concept (UNK-001). Every cell cites its source
document. Where the newer, more detailed evidence docs (specifically
`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` for Weekly Future) supersede the
original "Candidate, reserved, inactive" framing in
`docs/architecture/DOMAIN_ARCHITECTURE.md`, this is flagged explicitly
as an upgrade, not silently substituted.

## Summary Table

| Entity ID | Name | Produced By | Consumed By | Mathematical Definition Status | Status Source |
|---|---|---|---|---|---|
| ENT-001 | Strike | STRIKE-001 (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 29-49) | TREND-001, TREND-003, OPPONENT-001 (`docs/DOMAIN_MODEL.md` line 40) | Unknown — "selection mechanism itself is Unknown" (`docs/DOMAIN_MODEL.md` lines 32-33); selection formula partially resolved by deeper evidence to be Weekly-Future-High/Low rounding (`research/analysis/STRIKE_EVIDENCE_SUMMARY.md`, "PARTIALLY READY" verdict) but not fully verified | `docs/DOMAIN_MODEL.md` Status: Partial |
| ENT-002 | First Candle | Not produced by any rule; a raw market-data window fed into STRIKE-001 | STRIKE-001 (`docs/DOMAIN_MODEL.md` line 57) | Unknown — "which candle... is not established" (`docs/DOMAIN_MODEL.md` lines 52-55); deeper evidence resolves WHICH candle it conceptually is (the Weekly Future's first candle, not raw spot — `STRIKE_EVIDENCE_SUMMARY.md` Conflicts item 2) but not its exact time-window definition | `docs/DOMAIN_MODEL.md` Status: Unknown |
| ENT-003 | TrendPoint (TP Low) | TREND-001 (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 68-71) | TREND-002, TREND-003, OPPONENT-001 (`docs/DOMAIN_MODEL.md` line 79) | Partially Known — per TREND-001's Bible field (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 131); update trigger (TREND-002) is separately Unknown | `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 82-88 |
| ENT-004 | Market Structure | Not produced by any rule; referenced only as TREND-002's trigger condition | TREND-002 (`docs/DOMAIN_MODEL.md` line 97) | Unknown — "what constitutes 'market structure'... not defined" (`docs/DOMAIN_MODEL.md` lines 93-95) | `docs/DOMAIN_MODEL.md` Status: Unknown |
| ENT-005 | Opponent | Not produced by any rule; associated with a Strike (relationship Unknown — see below) | OPPONENT-001, TREND-003 (`docs/DOMAIN_MODEL.md` line 121) | Unknown — relationship to Strike (same strike? opposite CE/PE contract? distinct concept?) is Unknown, and explicitly not assumed equal to "competitor" elsewhere in the repo (`docs/DOMAIN_MODEL.md` lines 115-119; `docs/TERMINOLOGY.md` lines 78-84) | `docs/DOMAIN_MODEL.md` Status: Unknown |
| ENT-006 | Opponent High | OPPONENT-002 (placeholder, Awaiting Evidence) | OPPONENT-001 (as a dependency) | Unknown — "no behaviour or definition recorded" (`docs/DOMAIN_MODEL.md` lines 130-133) | `docs/DOMAIN_MODEL.md` Status: Unknown |
| ENT-007 | Opponent Low | OPPONENT-003 (placeholder, Awaiting Evidence) | OPPONENT-001 (as a dependency) | Unknown — "no behaviour or definition recorded" (`docs/DOMAIN_MODEL.md` lines 147-150) | `docs/DOMAIN_MODEL.md` Status: Unknown |
| ENT-008 | Reversal | REVERSAL-001 (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 158-165) | Nothing evidenced consumes it further — terminal per current evidence | Unknown — identification method ("which specific premium behaviour") Unknown (`docs/DOMAIN_MODEL.md` lines 168-171) | `docs/DOMAIN_MODEL.md` Status: Partial |
| ENT-009 | Premium | Not produced by any rule; a raw/observed market quantity | REVERSAL-001 (`docs/DOMAIN_MODEL.md` line 191) | Unknown — "no rule yet defines Premium itself as a first-class concept" (`docs/DOMAIN_MODEL.md` lines 183-186) | `docs/DOMAIN_MODEL.md` Status: Unknown |
| ENT-010 | Weekly Future | Not produced by any Rule ID (no rule cites it in Depends On — `docs/architecture/RULE_ENGINE_ARCHITECTURE.md` lines 185-190); computed by the speaker from Call+Put first-candle option OHLC data per transcript, not by any confirmed Bible rule | STRIKE-001 selection process, per deeper evidence (`STRIKE_EVIDENCE_TABLE.md` rows 8, 10, 11, 12, 14) — **not** reflected in the original Candidate/"reserved, inactive" framing, which shows no Related Rule(s) (`docs/EVIDENCE_MATRIX.md` row for ENT-010: "Referenced By: none yet") | **UPGRADED STATUS — see discrepancy note below.** Originally "Candidate, reserved, inactive," extension point undesigned (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 242-246, 304). The newer `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` shows this is materially more developed: inputs are named (Call/Put first-candle High/Low/Close + ATM strike), the combination rule is stated in natural language, but the arithmetic is self-contradictory and no clean worked example exists (readiness verdict: "PARTIALLY READY") | `docs/architecture/DOMAIN_ARCHITECTURE.md` (original) vs. `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` (upgrade) — see discrepancy note |
| ENT-011 | MidPoint | Not produced by any Rule ID | Described as "an ad hoc intermediate confirmation gate" (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 248-253); no rule consumes it | Unknown/reserved — "possible derived value once (and if) Top/Bottom strike concepts are themselves confirmed as Domain objects (they are not, currently)" (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 251-253) | `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 248-253; `research/analysis/TR-001_ANALYSIS.md` Section 3.6 |
| ENT-012 | TriggerPoint | Not produced by any Rule ID | None evidenced | Unknown/reserved — "described narratively with one worked example only" (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 255-258) | `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 255-258; `research/analysis/TR-001_ANALYSIS.md` Section 5 |
| ENT-013 | SellersPerspective | Not produced by any Rule ID | None evidenced | Unknown/reserved — "a named alternative analytical lens... distinct from the buyer-oriented TrendPoint framework" (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 260-265) | `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 260-265; `research/analysis/TR-001_ANALYSIS.md` Section 5 |
| ENT-014 | OpeningRange | Not produced by any Rule ID | None evidenced | Unknown/reserved — "first-5-minute-candle high/low used specifically on the Spot chart, described as distinct from the Future-based TrendPoint system" (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 267-272); STRIKE_EVIDENCE_SUMMARY.md's full-file review separately excluded a spot-chart first-5-minute-candle mention (line 3479) as "psychological/directional-discipline aid rather than for strike selection" (`research/analysis/STRIKE_EVIDENCE_SUMMARY.md` line 9), reinforcing that this is a distinct, not-merged concept | `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 267-272; `research/analysis/TR-001_ANALYSIS.md` Section 5 |
| UNK-001 | IVL Level | Not produced by anything evidenced | None evidenced | Unknown — "confirmed not present in the Bible, Domain Model, or State Machine"; used repeatedly in TR-001 "as if already defined" but never defined (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 278-286; `docs/EVIDENCE_MATRIX.md` row UNK-001, citing TR-001 lines 45, 1308-1309, 1389, 1586) | `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 276-286 |

## Discrepancy flagged: Weekly Future (ENT-010) status upgrade

`docs/architecture/DOMAIN_ARCHITECTURE.md` (lines 242-246, and summary
table line 304) frames Weekly Future as: "described as the *primary*
basis for level-setting in TR-001, but not officially published —
reconstructed via premium analysis. Reserved as a possible future
reference-data source; **no computation designed**." This framing
predates Milestone 5.0B.

The later `research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md` and
`research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` show this
entity is materially further along than "reserved, inactive, no
computation designed" suggests:
- Its required **inputs are explicitly named**: Call option first-candle
  High, Put option first-candle Low (for the High side); Put option
  first-candle High, Call option first-candle Low (for the Low side);
  plus the day's ATM strike (`WEEKLY_FUTURE_EVIDENCE_TABLE.md` rows
  WF-7 through WF-14).
- The **combination rule is stated in natural language**, including a
  conditional sign-flip rule for the Low side
  (`WEEKLY_FUTURE_EVIDENCE_TABLE.md` row WF-14; `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
  "Root blocker" intro paragraph: "The transcript explains the INTENDED
  mechanism... clearly enough in natural language that the general
  shape of the rule is not in doubt").
- However, the arithmetic itself is **not verifiable**: self-corrected
  numbers (91→81→82 for the same subtraction), an unexplained jump
  from a stated difference of "18" to a final answer of "268," two
  different Low values given for the same computation (≈26268 vs.
  26168), and a computed Low that is numerically higher than the
  computed High for the same candle — none of which the speaker
  resolves (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker"
  items 1-3; `WEEKLY_FUTURE_EVIDENCE_TABLE.md` "CONTRADICTORY
  ARITHMETIC" section).
- The readiness verdict in `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` is
  explicitly **"PARTIALLY READY"**, a materially more precise status
  than DOMAIN_ARCHITECTURE.md's blanket "Candidate, reserved,
  inactive, no computation designed."

This document treats this as an **upgrade in evidentiary detail, not a
contradiction to silently resolve** — DOMAIN_ARCHITECTURE.md was
accurate at the time it was written (no computation had yet been
evidenced for Weekly Future), and the newer research files supersede
it with specifics the architecture doc does not yet reflect. Whoever
next updates `docs/architecture/DOMAIN_ARCHITECTURE.md`'s ENT-010
section should incorporate this PARTIALLY READY finding rather than
leaving the "no computation designed" framing as if it were still
current.

## Per-Entity Detail

### ENT-001 — Strike
Produced by STRIKE-001. Consumed by TREND-001, TREND-003, OPPONENT-001
(`docs/DOMAIN_MODEL.md` line 40). No attributes beyond its role as
analysis subject are evidenced — no price-value type, expiry, or
option-side attribute (`docs/DOMAIN_MODEL.md` lines 37-38). Selection
mechanism traced in `RULE_DEPENDENCY_GRAPH.md`'s STRIKE-001 entry.

### ENT-002 — First Candle
Not produced by a rule (raw input). Consumed only by STRIKE-001.
`docs/DOMAIN_MODEL.md` lines 52-55 records the candle's own defining
attributes (session open? fixed time? duration?) as Unknown. The
deeper evidence resolves the conceptual identity question (it is the
Weekly Future's first candle, per `STRIKE_EVIDENCE_TABLE.md` row 14's
"decisive reconciliation": the raw NIFTY spot candle and the computed
Weekly Future candle for the same period can even point in opposite
directions) but does not resolve the exact time-window definition.

### ENT-003 — TrendPoint (TP Low)
Produced by TREND-001. Consumed by TREND-002, TREND-003, OPPONENT-001
(`docs/DOMAIN_MODEL.md` line 79). Belongs to exactly one Strike; value
changes over time; comparable to an Opponent's own TrendPoint
(`docs/DOMAIN_MODEL.md` lines 72-76). Mathematical Definition:
Partially Known for the base value (TREND-001), Unknown for the update
trigger (TREND-002) — `docs/architecture/DOMAIN_ARCHITECTURE.md` lines
82-88.

### ENT-004 — Market Structure
Not produced by a rule; referenced only as TREND-002's trigger
condition (`docs/DOMAIN_MODEL.md` lines 86-95). Not yet a
`TERMINOLOGY.md` entry — flagged as a disconnected artifact
(`research/reviews/M3_3_REPOSITORY_VALIDATION.md`, referenced via
`docs/architecture/DOMAIN_ARCHITECTURE.md` line 148). Represented
architecturally only as an abstract "change signal" (`docs/architecture/DOMAIN_ARCHITECTURE.md`
lines 150-154).

### ENT-005 — Opponent
Not produced by a rule; consumed by OPPONENT-001 and TREND-003
(`docs/DOMAIN_MODEL.md` line 121). Has a High and Low (ENT-006/007)
and its own TrendPoint (`docs/DOMAIN_MODEL.md` lines 111-114). Whether
"Opponent" is the same concept as "competitor" elsewhere in this repo
is explicitly an open, unconfirmed question
(`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 104-112;
`docs/TERMINOLOGY.md` lines 78-84) — this document does not assume
equivalence.

### ENT-006 — Opponent High
Produced (nominally) by placeholder rule OPPONENT-002, Awaiting
Evidence, Evidence Count 0 (`docs/RULE_INDEX.md` row 35). Consumed by
OPPONENT-001 as a stated dependency (`docs/DOMAIN_MODEL.md` lines
128-133). Modeled only as a reserved attribute slot with no defined
computation (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines
122-138).

### ENT-007 — Opponent Low
Symmetric to ENT-006: produced (nominally) by placeholder rule
OPPONENT-003, Awaiting Evidence, Evidence Count 0
(`docs/RULE_INDEX.md` row 36). Consumed by OPPONENT-001. Reserved
attribute slot only (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines
122-138).

### ENT-008 — Reversal
Produced by REVERSAL-001. No entity or rule evidenced to consume it
further — it is a terminal concept per current evidence (see
FOUNDATIONAL_KNOWLEDGE_MAP.md classification). Represents an
identified/confirmed state, never a default/assumed one
(`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 158-176). The one
confirmed "Impossible Transition" in the whole project attaches here:
no direct assumption-based entry into REVERSAL_IDENTIFIED
(`docs/STATE_MACHINE.md` lines 158-163).

### ENT-009 — Premium
Not produced by a rule; a raw/observed quantity. Consumed by
REVERSAL-001 as the basis for reversal identification
(`docs/DOMAIN_MODEL.md` lines 180-194). No rule defines Premium as a
first-class concept (which contract — CE, PE, or both — is
unresolved). Not yet a `TERMINOLOGY.md` entry
(`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 179-190).

### ENT-010 — Weekly Future (Candidate)
See discrepancy note above. Not tied to any confirmed Rule ID; its
Referenced-By field in `docs/EVIDENCE_MATRIX.md` reads "none yet," yet
the deeper STRIKE_EVIDENCE_* research establishes it is, in practice,
the actual computational basis for STRIKE-001's selection mechanism —
a relationship not yet reflected back into the Bible/RULE_INDEX.md/
EVIDENCE_MATRIX.md ledger documents (see also RULE_DEPENDENCY_GRAPH.md's
STRIKE-001 discrepancy note, which is the same underlying gap viewed
from the rule side).

### ENT-011 — MidPoint (Candidate)
Arithmetic midpoint between a Top strike and Bottom strike, used as an
ad hoc intermediate confirmation gate in at least two observed
instances (`research/analysis/TR-001_ANALYSIS.md` Section 3.6, per
`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 248-253). Reserved,
inactive; Top/Bottom strike are not themselves confirmed Domain
objects yet.

### ENT-012 — TriggerPoint (Candidate)
A price point where a "big player" reaction is said to occur,
described narratively with one worked example only
(`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 255-258;
`research/analysis/TR-001_ANALYSIS.md` Section 5). No computation
evidenced.

### ENT-013 — SellersPerspective (Candidate)
A named alternative analytical lens (option-seller viewpoint) distinct
from the buyer-oriented TrendPoint framework
(`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 260-265;
`research/analysis/TR-001_ANALYSIS.md` Section 5). Reserved as a
possible alternative evaluation strategy, structurally parallel to but
not merged with TrendPoint-based rules.

### ENT-014 — OpeningRange (Candidate)
First-5-minute-candle high/low used specifically on the Spot chart,
explicitly distinct from the Future-based TrendPoint system
(`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 267-272;
`research/analysis/TR-001_ANALYSIS.md` Section 5). Reinforced by
`STRIKE_EVIDENCE_SUMMARY.md`'s full-file review, which separately
excluded a spot-chart first-5-minute-candle mention as a
"psychological/directional-discipline aid rather than for strike
selection" (line 9) — confirming the transcript itself treats
OpeningRange and First Candle (ENT-002) as separate methodologies, not
merged concepts.

### UNK-001 — IVL Level
Used repeatedly in TR-001 (lines 45, 1308-1309, 1389, 1586 per
`docs/EVIDENCE_MATRIX.md` row UNK-001) as if already defined, but never
defined anywhere in the transcript. Confirmed absent from the Bible,
Domain Model, and State Machine (`docs/architecture/DOMAIN_ARCHITECTURE.md`
lines 278-286). No extension point is designed — deliberately, since
designing one would require understanding not yet evidenced
(`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 282-284).

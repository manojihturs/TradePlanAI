# Foundational Knowledge Map

Evidence-only synthesis, built on `RULE_DEPENDENCY_GRAPH.md` and
`ENTITY_DEPENDENCY_GRAPH.md` (both in this same directory). Every
classification, DAG edge, blocker claim, and ranking cites its source.
Edges not directly evidenced by a source document are explicitly
labeled "architectural, not rule-mathematics-evidenced" rather than
presented with the same confidence as an evidenced data dependency.

## 1. Classification

### Foundational Concepts
(Raw market data; nothing evidenced depends on prior computed
knowledge.)

- **Call option first-candle OHLC data** — raw input named in
  `research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md` rows WF-5, WF-7
  ("Call is 153, 113").
- **Put option first-candle OHLC data** — raw input, same source, row
  WF-8.
- **ATM strike price** (day's chosen anchor) — raw/observed input,
  `WEEKLY_FUTURE_EVIDENCE_TABLE.md` row WF-7 ("I've taken the 150
  Call/Put").
- **Premium (ENT-009)** — referenced only as raw observed data feeding
  REVERSAL-001; "no rule yet defines Premium itself as a first-class
  concept" (`docs/DOMAIN_MODEL.md` lines 180-194) — nothing evidenced
  computes Premium from anything else in this project.
- **First Candle (ENT-002)** — the raw candle window itself (its exact
  time-window definition is Unknown, but it is evidenced as an input,
  not a computed output — `docs/DOMAIN_MODEL.md` lines 47-60).
- **Market Structure (ENT-004)** — referenced only as an external
  trigger signal, not computed from anything else evidenced
  (`docs/DOMAIN_MODEL.md` lines 86-100).

### Intermediate Concepts
(Computed from foundational concepts; feed further computation.)

- **Weekly Future High/Low (ENT-010, Candidate)** — computed from
  Call+Put first-candle OHLC + ATM strike
  (`research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
  "Dependency chain" section); feeds Strike selection
  (`STRIKE_EVIDENCE_TABLE.md` rows 10, 11, 12, 14).
- **Strike (ENT-001)** — produced by STRIKE-001 from the Weekly Future
  High/Low (deeper evidence) or "the first candle" (ledger's own
  framing); feeds TrendPoint, Opponent engagement
  (`docs/DOMAIN_MODEL.md` line 40).
- **TrendPoint / TP Low (ENT-003)** — produced by TREND-001 from a
  Strike; feeds TREND-002 (its own update), TREND-003 (Edge
  comparison), OPPONENT-001 (`docs/DOMAIN_MODEL.md` line 79).
- **Opponent (ENT-005), Opponent High/Low (ENT-006/007)** — associated
  with a Strike; feed OPPONENT-001's "defeat" evaluation and TREND-003's
  comparison (`docs/DOMAIN_MODEL.md` lines 104-159).
- **Edge condition (TREND-003 output)** — computed by comparing two
  TrendPoints; modeled as a condition, not a stored entity
  (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 194-213). No
  evidenced further consumer found, but it is architecturally intended
  to feed a future trading decision (see Terminal Concepts note below)
  — flagged as architectural, not evidenced.
- **MidPoint (ENT-011, Candidate)** — arithmetic midpoint of Top/Bottom
  strike, used as "an ad hoc intermediate confirmation gate"
  (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 248-253) — by its
  own description an intermediate, not terminal, concept, though what
  it feeds beyond "confirmation" is not further evidenced.

### Terminal Concepts
(Represent an end decision/output; nothing evidenced consumes them
further.)

- **Reversal (ENT-008)** — produced by REVERSAL-001; no rule or entity
  evidenced to consume it further (`docs/DOMAIN_MODEL.md` lines
  162-176). It "represents an identified/confirmed state," and the
  Bible's ENTRY/EXIT rule categories are both still empty
  (`docs/architecture/RULE_ENGINE_ARCHITECTURE.md` lines 159-161), so
  no evidenced downstream trading action exists yet.
- **OPPONENT-001's "defeated" outcome** — described as enabling Strike
  "progression," but what progression consists of, and whether
  anything consumes the OPPONENT_DEFEATED state beyond a hypothesised
  (not confirmed) link to TREND-003, is unresolved
  (`docs/STATE_MACHINE.md` lines 112-137). Effectively terminal by
  current evidence.
- **Decision Object** — per `docs/architecture/RULE_ENGINE_ARCHITECTURE.md`
  lines 155-169, this is architecturally where Rule Results
  (including Edge/TREND-003 and Reversal/REVERSAL-001) would
  eventually feed a trading decision — but "no synthesis logic... is
  designed, because no such combination rule is evidenced anywhere in
  the reviewed documents." This is labeled **architectural, not
  rule-mathematics-evidenced** — it is the architecture's placeholder
  for a terminal node, not an evidenced data dependency.
- **TriggerPoint (ENT-012), SellersPerspective (ENT-013), OpeningRange
  (ENT-014)** — each described narratively with no evidenced consumer
  (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 255-272);
  effectively terminal/isolated by current evidence, not integrated
  into any dependency chain.
- **UNK-001 (IVL Level)** — used repeatedly but never defined; neither
  produces nor is evidenced to be produced by anything
  (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 276-286) — isolated,
  not part of any evidenced chain at all.

## 2. Knowledge DAG (evidenced chain, ROOT → LEAF)

```
Call Option first-candle OHLC  ─┐
Put Option first-candle OHLC   ─┼─→ Weekly Future High/Low
ATM Strike (anchor)            ─┘   [ENT-010, Candidate — PARTIALLY READY;
                                      arithmetic self-contradictory, see
                                      WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md]
                                         │
                                         │ (evidenced: STRIKE_EVIDENCE_TABLE.md
                                         │  rows 10, 11, 12, 14 — "nearest
                                         │  listed strike" rounding, with
                                         │  bullish/bearish top-bottom
                                         │  selection and a Doji second-
                                         │  candle fallback, row 13)
                                         ▼
                                  Strike selection (STRIKE-001)
                                  [ENT-001 — Mathematical Definition: Unknown
                                   per Bible; deeper evidence PARTIALLY READY]
                                         │
                                         │ (evidenced only as "every analysed
                                         │  strike maintains..." — no formula
                                         │  connecting Strike to a TP Low
                                         │  value; docs/TRADINGVIEW_STRATEGY_BIBLE.md
                                         │  line 131 "Partially Known")
                                         ▼
                                  TrendPoint / TP Low (TREND-001)
                                  [ENT-003 — Mathematical Definition:
                                   Partially Known]
                                         │
                       ┌─────────────────┼─────────────────────┐
                       │                 │                     │
                       ▼                 ▼                     ▼
              TREND-002 (Dynamic   TREND-003 (Edge         OPPONENT-001
              TP Low Adjustment)   Detection — requires     (Next Opponent
              [Mathematical Def:   both own + Opponent's    Defeat)
              Unknown; trigger =   TP Low; "well below"     [Mathematical
              "market structure    not quantified;          Def: Unknown;
              change," itself      Mathematical Def:        also depends on
              Unknown]             Unknown]                 OPPONENT-002/003,
                                        ▲                    both Awaiting
                                        │                    Evidence]
                                        └────────────────────┘
                                     (TREND-003 depends on OPPONENT-001's
                                      output per docs/RULE_INDEX.md row 33)

  Opponent (ENT-005) [relationship to Strike Unknown; not assumed
  equal to "competitor" elsewhere in repo] ─→ Opponent High (ENT-006,
  via placeholder OPPONENT-002) + Opponent Low (ENT-007, via
  placeholder OPPONENT-003) ─→ feed OPPONENT-001 [both Awaiting
  Evidence, Evidence Count 0]

Premium (ENT-009, raw/foundational) ─→ Reversal (REVERSAL-001)
[ENT-008 — Mathematical Definition: Unknown; the one confirmed
"Impossible Transition" in the project: no direct assumption-based
entry into REVERSAL_IDENTIFIED, docs/STATE_MACHINE.md lines 158-163]
                                         │
                                         │ (architectural, not
                                         │  rule-mathematics-evidenced —
                                         │  no synthesis rule combining
                                         │  Reversal with TREND-003/Edge
                                         │  or OPPONENT-001 is evidenced
                                         │  anywhere; RULE_ENGINE_ARCHITECTURE.md
                                         │  lines 125-128, 163-169)
                                         ▼
                              [Decision Object — architectural
                               placeholder only, no combination logic
                               evidenced; ENTRY/EXIT Bible categories
                               both empty]
```

Isolated/unintegrated candidates (no evidenced edge into or out of the
main chain above): MidPoint (ENT-011), TriggerPoint (ENT-012),
SellersPerspective (ENT-013), OpeningRange (ENT-014), IVL Level
(UNK-001) — each exists only as a standalone Candidate/Unknown entry
per `docs/EVIDENCE_MATRIX.md`, with "none yet"/"UNKNOWN" in its
Related Rule(s) column, and is not wired into the Rule Engine pipeline
(`docs/architecture/RULE_ENGINE_ARCHITECTURE.md` lines 185-190).

## 3. Critical Blockers

For each unresolved/Unknown mathematical concept in the DAG above, this
section states what becomes implementable if that ONE concept were
fully resolved to READY — and what does NOT become unblocked as a
result, citing why.

### Blocker: Weekly Future High/Low arithmetic (ENT-010)
**If resolved:** STRIKE-001 becomes fully READY. The downstream
nearest-strike rounding and bullish/bearish top-bottom selection (with
the Doji-first-candle second-candle fallback) are already evidenced at
a "PARTIALLY READY... suitable for a documented feature spec and
prototype implementation" level (`research/analysis/STRIKE_EVIDENCE_SUMMARY.md`
"Recommended Readiness Verdict") — the only missing piece is a clean,
verifiable Call/Put→Weekly-Future-High/Low formula
(`research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root
blocker" items 1-2).
**What does NOT unblock:** TREND-001/002/003 remain blocked — their
own Mathematical Definition is separately Unknown/Partially Known, not
downstream of Weekly Future (`docs/TRADINGVIEW_STRATEGY_BIBLE.md`
lines 131, 159, 188). OPPONENT-001/002/003 remain blocked — no
evidenced dependency links Opponent concepts to Weekly Future at all.
REVERSAL-001 remains fully unaffected — no evidenced dependency on
Strike selection or Weekly Future anywhere in the reviewed documents.

### Blocker: TrendPoint (TP Low) calculation formula (ENT-003, TREND-001)
**If resolved:** TREND-001 becomes READY (assuming Strike is already
selected). This also removes one of TREND-002's, TREND-003's, and
OPPONENT-001's stated dependencies (`docs/RULE_INDEX.md` rows 32-34),
but does not make any of them READY by itself.
**What does NOT unblock:** TREND-002 additionally needs "market
structure change" defined (separately Unknown, `docs/DOMAIN_MODEL.md`
lines 93-95) — resolving TREND-001 alone does not resolve this second,
independent unknown. TREND-003 additionally needs the "well below"
threshold quantified (`docs/TERMINOLOGY.md` lines 112-113) and needs
OPPONENT-001 (and, transitively, Opponent High/Low) resolved too —
TREND-003 depends on BOTH TREND-001 and OPPONENT-001 per
`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 194, so resolving TREND-001
alone leaves TREND-003 still blocked by OPPONENT-001. OPPONENT-001
additionally needs the "defeat" condition and OPPONENT-002/003 resolved
— resolving TREND-001 alone does not touch any of these.

### Blocker: "Market structure change" trigger definition (ENT-004, TREND-002)
**If resolved:** TREND-002 becomes READY, but only once TREND-001's TP
Low base-value formula is also resolved (TREND-002 depends on
TREND-001, `docs/RULE_INDEX.md` row 32) — resolving the trigger alone,
with TREND-001 still Partially Known, leaves TREND-002 partially
blocked.
**What does NOT unblock:** No other rule lists TREND-002 as a
dependency (`docs/RULE_INDEX.md` row 32, "Referenced By: none yet") —
resolving this concept has no evidenced downstream effect beyond
TREND-002 itself.

### Blocker: "Well below" threshold quantification + Edge definition (TREND-003)
**If resolved:** TREND-003 still does NOT become READY by itself,
because it also depends on TREND-001 (Partially Known) and OPPONENT-001
(Unknown, itself blocked by OPPONENT-002/003) per
`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 194. Quantifying "well
below" alone resolves only one of TREND-003's several blockers.
**What does NOT unblock:** No rule lists TREND-003 as a dependency
either (`docs/RULE_INDEX.md` row 33, "Referenced By: none yet") — it is
evidenced as a leaf-ward concept in the current DAG, not a blocker for
anything else.

### Blocker: "Defeat" condition definition + Opponent High/Low (OPPONENT-001, ENT-005/006/007)
**If resolved (all three together — they are co-dependent per
`docs/RULE_INDEX.md` row 34):** OPPONENT-001 becomes READY (assuming
TREND-001 is also resolved, since OPPONENT-001 depends on TREND-001
too). This would in turn remove one of TREND-003's two blockers (see
above), though TREND-003 would still need "well below" quantified and
TREND-001 resolved to be fully READY.
**What does NOT unblock:** STRIKE-001, TREND-002, and REVERSAL-001 are
all evidenced as having no dependency on OPPONENT-001 or Opponent
concepts (`docs/RULE_INDEX.md` rows 30, 32, 37) — none of them is
affected by resolving this blocker.

### Blocker: Opponent relationship to Strike ("competitor" question, ENT-005)
**If resolved:** Clarifies OPPONENT-001, TREND-003, and the Opponent
entity's own attributes, but does not by itself supply the "defeat"
condition's mathematics or Opponent High/Low's values — those are
separate, additional Unknowns (`docs/TRADINGVIEW_STRATEGY_BIBLE.md`
lines 344-350; `docs/architecture/DOMAIN_ARCHITECTURE.md` lines
104-119). This is a definitional clarification, not itself sufficient
to make OPPONENT-001 READY.
**What does NOT unblock:** Nothing becomes fully READY from this alone
— it removes ambiguity but not a missing formula.

### Blocker: Premium behaviour → Reversal identification method (REVERSAL-001, ENT-008/009)
**If resolved:** REVERSAL-001 becomes READY. Per
`docs/RULE_INDEX.md` row 37, no other rule lists REVERSAL-001 as a
dependency ("Referenced By: none yet") and REVERSAL-001 itself depends
on nothing else ("Depends On: none yet") — this is the single most
self-contained blocker in the project: resolving it unblocks exactly
one rule and nothing else, but that one rule becomes immediately and
fully READY with no further transitive blockers.
**What does NOT unblock:** No effect on STRIKE-001, TREND-001/002/003,
or OPPONENT-001/002/003 — no evidenced dependency in either direction.

### Blocker: External "Complete Calculation Video for Weekly Future" (source-level, not a rule/entity)
**If obtained:** Directly supplies the missing clean worked example
for the Weekly Future High/Low blocker above (`research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
"Root blocker" item 3: "the speaker himself points to twice as the
authoritative source... not part of `research/transcripts/TR-001.md`
and, per the directory listing, does not exist anywhere else in this
repository"). This is not a mathematical concept per se but the single
most direct evidence-acquisition action available — obtaining it would
most directly resolve the Weekly Future blocker (top of this list) and
therefore, transitively, would make STRIKE-001 READY.

## 4. Top 10 Highest-Value Missing Concepts

Ranked by (a) how many other rules/entities are blocked by the concept
becoming known, per the Critical Blockers analysis above, weighted by
(b) how close the concept already is to READY — partially-evidenced
concepts needing one more piece of evidence rank above totally-Unknown
concepts needing everything, since they are lower-effort/higher-impact
acquisition targets. Only genuinely evidenced concepts are listed; the
repository does not evidence more than the following 7 distinct
missing-concept blockers, so this list is not padded to 10.

1. **Weekly Future High/Low arithmetic (ENT-010).** Highest-impact,
   lowest-remaining-effort item in the project. Unblocks STRIKE-001
   fully (its downstream steps are already "PARTIALLY READY... suitable
   for a documented feature spec and prototype implementation" per
   `research/analysis/STRIKE_EVIDENCE_SUMMARY.md`). The gap is narrow
   and specific: one clean, self-consistent worked example plus a
   general sign-flip rule statement
   (`research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root
   blocker" items 1-2) — not a from-scratch investigation. Ranked #1
   because it is both close to READY (natural-language rule already
   stated, inputs already named) and unblocks the earliest node in the
   evidenced DAG (Strike selection, which everything else in the
   project sits downstream of conceptually, per the DAG in Section 2).

2. **The external "Complete Calculation Video for Weekly Future."**
   Ranked #2, immediately behind item 1, because it is the single most
   concrete, lowest-effort **acquisition action** (find and transcribe
   one named, referenced video — `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
   "Root blocker" item 3) that would most directly resolve item 1. It
   is listed separately from item 1 because it is an evidence-source
   action, not a mathematical concept, but it is the most actionable
   single next step in the whole project per the evidence.

3. **Premium behaviour → Reversal identification method (REVERSAL-001,
   ENT-008/009).** Ranked #3: fully self-contained (no other rule
   depends on it, and it depends on nothing else — `docs/RULE_INDEX.md`
   row 37), so resolving it converts exactly one rule from Unknown to
   fully READY with zero transitive blockers remaining. Lower-ranked
   than items 1-2 only because, unlike Weekly Future, no natural-language
   rule shape has been stated anywhere yet ("which specific premium
   behaviour constitutes identification is not established," `docs/DOMAIN_MODEL.md`
   lines 168-171) — this is a totally-Unknown concept, not a
   partially-evidenced one, so it requires more net-new evidence
   acquisition than item 1 despite unblocking a comparable amount.

4. **TrendPoint (TP Low) calculation formula (ENT-003, TREND-001).**
   Ranked #4: unblocks the largest number of dependent rules by raw
   count (TREND-002, TREND-003, OPPONENT-001 all list TREND-001 as a
   dependency, `docs/RULE_INDEX.md` row 31) — more than any other
   single concept in the project. Ranked below items 1-3 because (a)
   it does not make any of those three dependents fully READY by
   itself (each has an additional, independent blocker — see Critical
   Blockers section), so its immediate payoff is partial, and (b) its
   Mathematical Definition is "Partially Known," meaning some
   groundwork exists but materially less than Weekly Future's
   already-stated natural-language formula.

5. **"Defeat" condition + Opponent High/Low (OPPONENT-001,
   ENT-005/006/007).** Ranked #5: resolves 3 co-dependent unknowns at
   once (`docs/RULE_INDEX.md` row 34's three Depends-On entries) and
   would remove one of TREND-003's two blockers. Ranked below TP Low
   because OPPONENT-002/003 have Evidence Count 0 and Status "Awaiting
   Evidence" (`docs/RULE_INDEX.md` rows 35-36) — the furthest from
   READY of any concept in this list, requiring net-new evidence
   acquisition from scratch, not refinement of existing evidence.

6. **Opponent's relationship to Strike / "competitor" question
   (ENT-005).** Ranked #6: a definitional clarification only — it does
   not supply a formula and does not by itself make OPPONENT-001
   READY (see Critical Blockers), so its direct unblocking value is
   lower than items 1-5. Ranked above items 7 because it is
   comparatively cheap to resolve (a single clarifying statement would
   settle it, per the explicit open question already framed in
   `docs/TERMINOLOGY.md` lines 78-84) relative to the fully-Unknown
   items below it.

7. **"Market structure change" trigger definition (ENT-004,
   TREND-002).** Ranked #7 (lowest): unblocks only one rule
   (`docs/RULE_INDEX.md` row 32, "Referenced By: none yet") and even
   that rule remains additionally blocked by TREND-001's own Partially
   Known status. Ranked last because it has both the smallest blocked-
   rule count of any evidenced concept and requires resolving a fully
   Unknown concept ("what constitutes market structure... not defined,"
   `docs/DOMAIN_MODEL.md` lines 93-95) with no existing partial
   evidence to build from, unlike item 1.

**Not ranked (out of scope for this list):** "Well below" threshold
quantification for TREND-003 was considered but not given a separate
rank — it is subsumed by item 4's TREND-003 dependency chain (TREND-003
needs both TREND-001 and OPPONENT-001 resolved regardless, so
quantifying "well below" alone would not make TREND-003 READY even if
resolved in isolation, per the Critical Blockers analysis). IVL Level
(UNK-001), MidPoint (ENT-011), TriggerPoint (ENT-012),
SellersPerspective (ENT-013), and OpeningRange (ENT-014) were not
ranked because no rule or entity is evidenced to depend on any of
them (`docs/EVIDENCE_MATRIX.md` rows for ENT-011 through ENT-014 and
UNK-001 all show "none yet"/"UNKNOWN" for Related Rule(s)) — resolving
them would not unblock anything else in the currently-evidenced graph,
so they carry zero "engineering impact" under this ranking's own
stated criterion, however interesting they may be on their own terms.

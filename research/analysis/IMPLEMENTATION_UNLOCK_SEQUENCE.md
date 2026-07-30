# Implementation Unlock Sequence

Milestone K1 (Phase K: Knowledge Reconstruction). Consolidates a
Critical/High/Medium/Low ranking of every gap (Task 6) and a concrete
"if X resolved, then Y becomes possible" roadmap (Task 6 second half).
The ranking logic is reused, not re-derived, from
`FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 4's existing Top-7 ranking (the
document itself notes the repository evidences only 7 distinct
missing-concept blockers, "not padded to 10"); this document only
re-expresses that ranking in Critical/High/Medium/Low terms and adds
the roadmap framing requested for Milestone K1.

**Currency note:** Weekly Future is treated throughout as **NOT READY**
per `WEEKLY_FUTURE_VERIFICATION.md` (Phase E1, most recent, strictest
rubric), which supersedes the older PARTIALLY READY verdict in
`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`. As discussed in the dedicated
section below, this status change does not reorder the ranking —
Weekly Future was already ranked #1 — but it does strengthen the
justification for that #1 ranking.

---

## Task 6a — Ranked Gaps (Critical / High / Medium / Low)

Ranking basis, reused directly from `FOUNDATIONAL_KNOWLEDGE_MAP.md`
Section 4: number of downstream rules/entities/calculators blocked,
weighted by proximity to READY (partially-evidenced gaps needing one
more piece rank above totally-Unknown gaps needing everything, since
they are lower-effort/higher-impact acquisition targets).

| Rank | Gap | Severity | Basis (from `FOUNDATIONAL_KNOWLEDGE_MAP.md` #) |
|---|---|---|---|
| 1 | Weekly Future High/Low arithmetic (ENT-010) | **Critical** | #1 — "Highest-impact, lowest-remaining-effort item in the project," unblocks STRIKE-001 fully once resolved; blocks the earliest node in the evidenced DAG that everything else sits downstream of conceptually |
| 2 | External "Complete Calculation Video for Weekly Future" (source-acquisition action, not a concept) | **Critical** | #2 — the single most concrete, lowest-effort acquisition action that would most directly resolve rank 1; named explicitly, by title, twice, by the speaker (TR-001 lines 816, 2467) |
| 3 | Premium behaviour → Reversal identification method (REVERSAL-001) | **High** | #3 — fully self-contained (no other rule depends on it, it depends on nothing else), so resolving it converts exactly one rule to fully READY with zero transitive blockers; ranked below 1-2 only because no natural-language rule shape exists yet at all (more net-new evidence required) |
| 4 | TrendPoint (TP Low) calculation formula (TREND-001, ENT-003) | **High** | #4 — unblocks the largest raw count of dependent rules (TREND-002, TREND-003, OPPONENT-001 all list it as a dependency), but does not make any of them fully READY by itself, so its immediate payoff is partial |
| 4 (tie/subsumed) | TREND-002 "market structure change" trigger definition | **Medium** | Part of item 4's chain per `FOUNDATIONAL_KNOWLEDGE_MAP.md`; independently ranked #7 on its own (see row 7 below) since it has the smallest blocked-rule count |
| — (not separately ranked) | TREND-003 "well below" threshold + Edge definition | **Medium** | Explicitly not given a separate rank in `FOUNDATIONAL_KNOWLEDGE_MAP.md` — subsumed by item 4's chain, since TREND-003 needs BOTH TREND-001 and OPPONENT-001 regardless of this threshold |
| 5 | "Defeat" condition + Opponent High/Low (OPPONENT-001, ENT-005/006/007) | **High** | #5 — resolves 3 co-dependent unknowns at once and removes one of TREND-003's two blockers; ranked below TP Low because OPPONENT-002/003 have Evidence Count 0, the furthest from READY of any item in this list |
| 6 | Opponent's relationship to Strike / "competitor" question (ENT-005) | **Medium** | #6 — a definitional clarification only, does not supply a formula or make OPPONENT-001 READY by itself; ranked above item 7 only because it is comparatively cheap to resolve |
| 7 | "Market structure change" trigger definition (ENT-004, TREND-002) | **Low** | #7 (lowest) — unblocks only one rule (TREND-002), and even that rule remains additionally blocked by TREND-001's own Partially Known status; smallest blocked-rule count of any evidenced concept |

**Not ranked / zero engineering impact (explicitly out of scope for
this ranking, per `FOUNDATIONAL_KNOWLEDGE_MAP.md`'s own "Not ranked"
note):** IVL Level (UNK-001), MidPoint (ENT-011), TriggerPoint
(ENT-012), SellersPerspective (ENT-013), OpeningRange (ENT-014) — no
rule or entity is evidenced to depend on any of them, so resolving
them would not unblock anything else in the currently-evidenced graph.

### Does Weekly Future's status change (PARTIALLY READY → NOT READY) reorder the ranking?

**No — the order is unchanged, but the justification for rank #1 is
now stronger.** Weekly Future (rank 1) and its acquisition action
(rank 2) were already ranked highest under the PARTIALLY READY
verdict, based on downstream-impact and proximity-to-READY reasoning.
The Phase E1 downgrade to NOT READY:

- **Does not change the impact side of the ranking** — Weekly Future
  still unblocks STRIKE-001 fully once resolved, exactly as before; no
  new rule or entity becomes newly blocked or unblocked by this status
  change alone (`WEEKLY_FUTURE_VERIFICATION.md` only re-assesses
  Weekly Future's own readiness under a stricter rubric, it does not
  touch the dependency graph itself).
- **Sharpens the "what's missing" specification on the effort side** —
  Phase E1's stricter rubric makes the acquisition target more
  concrete and falsifiable: not just "one clean example" but
  specifically "three internally consistent worked examples," with
  explicit reject-triggers now documented (arithmetic contradicts
  itself, multiple conflicting values exist, outputs cannot be
  reproduced — all three confirmed present in the existing single
  example per `WEEKLY_FUTURE_VERIFICATION.md`'s "Reject-evidence
  triggers" section). This strengthens, rather than weakens, the case
  for treating this as the highest-priority, best-specified acquisition
  target in the entire backlog — the gap is now more precisely
  characterized, not larger.
- Therefore this document keeps Weekly Future and its companion
  acquisition action at ranks 1 and 2, consistent with
  `FOUNDATIONAL_KNOWLEDGE_MAP.md`'s original Top-7 ranking, per the
  task's own instruction to reuse rather than re-rank from scratch.

---

## Task 6b — Unlock Roadmap: "If X Resolved, Then Y Becomes Possible"

This roadmap is framed in the spirit of `EXTERNAL_EVIDENCE_BACKLOG.md`
(same underlying gaps, same citations) but sequenced as an ordered
series of unlock steps rather than a flat table. It explicitly starts
from the Phase E1/E2 finding that **no new evidence has been acquired**
since the last acquisition attempt — Phase E1 (`WEEKLY_FUTURE_
VERIFICATION.md`) searched for the "Complete Calculation Video" and
found nothing (web search failed with a tool error, not a "no results"
outcome, and no new file exists in `research/videos/` or
`research/transcripts/` beyond `TR-001.md`); Phase E2's own
conclusion, per the task brief, was likewise that no new usable
evidence exists. Because of this, the roadmap's first step is
unchanged from what it was before Phase E1/E2 ran — those two phases
confirmed the target rather than replacing it.

### Step 1 (Critical — start here). Locate the "Complete Calculation Video for Weekly Future."

- **If resolved:** Supplies the missing clean, internally-consistent
  worked example(s) — Phase E1's stricter rubric specifically requires
  three (`WEEKLY_FUTURE_VERIFICATION.md` "Evidence acceptance
  criteria" row "at least three internally consistent worked
  examples"). This would move Weekly Future (ENT-010) from NOT READY
  toward READY.
- **Then Y becomes possible:** STRIKE-001 becomes fully READY —
  `weekly_future_calculator.py` and `strike_calculator.py` already
  exist, structurally correct, "simply waiting for a formula to fill
  their `calculate()` bodies" (`FRAMEWORK_BASELINE_REPORT.md` Section
  7). STRIKE-001's own downstream selection-heuristic evidence
  (nearest-strike rounding, bullish/bearish top-bottom pairing) is
  already at a "PARTIALLY READY... suitable for a documented feature
  spec and prototype implementation" level (`STRIKE_EVIDENCE_SUMMARY.md`),
  so this is the only remaining piece for that rule specifically.
- **What does NOT become possible yet:** TREND-001/002/003 and
  OPPONENT-001/002/003 remain blocked — their own Mathematical
  Definitions are separately Unknown/Partially Known, not downstream
  of Weekly Future. REVERSAL-001 is fully unaffected — no evidenced
  dependency on Strike selection anywhere. (`FOUNDATIONAL_KNOWLEDGE_
  MAP.md` "Blocker: Weekly Future High/Low arithmetic," "What does NOT
  unblock.")
- **Confirmed still the correct starting point post-Phase-E1/E2:** no
  alternative source was found; the video remains named, twice, by
  title, by the speaker, inside the existing transcript — still the
  single most concrete, targeted acquisition action in the backlog
  (`EVIDENCE_ACQUISITION_ROADMAP.md` "Recommendation" section, items
  1-4).

### Step 2 (High). Acquire a stated rule connecting observed Premium behaviour to reversal identification (REVERSAL-001).

- **If resolved:** REVERSAL-001 becomes READY immediately — it is the
  single most self-contained gap in the project: "Depends On: none
  yet" and "Referenced By: none yet" (`docs/RULE_INDEX.md` row 37),
  so resolving it has zero transitive blockers on either side.
- **Then Y becomes possible:** `reversal_calculator.py`'s `calculate()`
  body can be filled in without waiting on any other gap in this
  roadmap — this can, in principle, run in parallel with Step 1 rather
  than after it, since neither blocks the other.
- **What does NOT become possible yet:** No effect on STRIKE-001,
  TREND-001/002/003, or OPPONENT-001/002/003 — no evidenced dependency
  in either direction (`FOUNDATIONAL_KNOWLEDGE_MAP.md` "Blocker:
  Premium behaviour → Reversal identification method," "What does NOT
  unblock").
- **Effort note:** Higher research effort than Step 1 despite similar
  impact, because "no natural-language rule shape has been stated
  anywhere yet" for Reversal — this is a totally-Unknown concept,
  unlike Weekly Future's already-stated (if unreliable) natural-language
  formula (`FOUNDATIONAL_KNOWLEDGE_MAP.md` item 3).

### Step 3 (High). Acquire the TrendPoint (TP Low) calculation formula (TREND-001, ENT-003).

- **If resolved (assuming a Strike is already selected, i.e. Step 1
  has also landed):** TREND-001 becomes READY. This removes one of
  three stated dependencies each for TREND-002, TREND-003, and
  OPPONENT-001 (`docs/RULE_INDEX.md` rows 32-34).
- **Then Y becomes possible:** None of TREND-002/003/OPPONENT-001
  becomes READY from this alone — each has at least one additional,
  independent blocker (see Steps 4-5 below). This step's payoff is
  partial by itself, but it is a necessary precondition for all three.
- **What does NOT become possible yet:** TREND-002 still needs "market
  structure change" defined (Step 5); TREND-003 still needs "well
  below" quantified AND OPPONENT-001 resolved (Step 4); OPPONENT-001
  still needs the "defeat" condition and OPPONENT-002/003 resolved
  (Step 4).

### Step 4 (High). Acquire the "defeat" condition definition plus Opponent High/Low (OPPONENT-001, ENT-005/006/007), co-dependently.

- **If resolved (all three together, and assuming Step 3/TREND-001 has
  also landed):** OPPONENT-001 becomes READY. This in turn removes one
  of TREND-003's two blockers.
- **Then Y becomes possible:** TREND-003 still needs "well below"
  quantified (see below) and TREND-001 resolved (Step 3) to be fully
  READY — this step alone does not complete TREND-003.
- **What does NOT become possible yet:** STRIKE-001, TREND-002, and
  REVERSAL-001 are all evidenced as having no dependency on OPPONENT-001
  or Opponent concepts (`docs/RULE_INDEX.md` rows 30, 32, 37) — none of
  them is affected by this step.
- **Companion, not separately sequenced (subsumed under this chain per
  `FOUNDATIONAL_KNOWLEDGE_MAP.md`'s "Not ranked" note):** quantifying
  TREND-003's "well below" threshold. Even if quantified in isolation,
  TREND-003 remains blocked until both this step and Step 3 land — so
  it is listed here as a companion to Step 4/Step 3 rather than a
  separate roadmap step.

### Step 5 (Medium). Clarify Opponent's relationship to Strike ("competitor" question, ENT-005).

- **If resolved:** Settles whether "Opponent" is the same Strike, an
  opposite CE/PE contract, or a distinct concept, and whether it
  equals "competitor" elsewhere in the repo (`docs/TERMINOLOGY.md`
  lines 78-84).
- **Then Y becomes possible:** Clarifies OPPONENT-001, TREND-003, and
  the Opponent entity's own attributes — but does not by itself supply
  the "defeat" formula or Opponent High/Low values (those remain
  Step 4's job).
- **What does NOT become possible yet:** Nothing becomes fully READY
  from this alone — it removes ambiguity, not a missing formula.
- **Effort note:** Comparatively cheap — "a single clarifying statement
  would settle it," per the open question already framed in
  `docs/TERMINOLOGY.md`.

### Step 6 (Low). Define TREND-002's "market structure change" trigger.

- **If resolved (assuming Step 3/TREND-001 has also landed):**
  TREND-002 becomes READY.
- **Then Y becomes possible:** Nothing further — no other rule lists
  TREND-002 as a dependency (`docs/RULE_INDEX.md` row 32, "Referenced
  By: none yet"). This is the lowest-impact step in the roadmap.
- **What does NOT become possible yet:** Same caveat as Step 3 in
  reverse — if Step 3 has not landed, resolving this trigger alone
  still leaves TREND-002 partially blocked.

### After all evidence steps: the architectural gap that evidence alone does not close

Even if every step above were completed, one additional, independent
gap remains, per `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 1 "Terminal
Concepts" and `docs/architecture/RULE_ENGINE_ARCHITECTURE.md` lines
155-169: **no cross-rule synthesis/combination logic is evidenced or
designed** for the Decision Object (confirmed in code:
`domain/decision.py` line 105's TODO, "No synthesis/combination logic
across multiple RuleEvaluationResults evidenced"). This is not fixed
by resolving any single rule's mathematics — it requires its own,
separate evidence (e.g., "if TREND-003 holds AND REVERSAL-001 fires,
then...") that no source document in this repository currently
supplies. This is listed here as the final, structurally distinct item
in the roadmap, not folded into any single step above, because
resolving all 8 rules individually still would not make the engine
produce a trading Decision without this additional synthesis evidence.

### Long-term, evidence-gated validation activities (not sequenced ahead of the evidence work above)

Per `EVIDENCE_ACQUISITION_ROADMAP.md` "Long-term" section, reused here
without modification: Replay validation (Milestone 4.5) can be
exercised with test-double rules even before real mathematics exist,
but produces no trading-relevant validation until the steps above
close. Backtest (Milestone 4.7) is explicitly "Blocked on: Real rule
implementations existing." Paper trading (Milestone 4.8) follows
Backtest in the roadmap's sequence. None of these are re-sequenced
ahead of the evidence-acquisition steps above; they remain gated
behind them exactly as `EVIDENCE_ACQUISITION_ROADMAP.md` already
states.

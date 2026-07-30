# Evidence Acquisition Roadmap

Evidence-only synthesis, organized into four tiers. Every action below
is grounded in a specific open question already documented in
`research/analysis/*.md` or `docs/*.md`. No web search, outside
trading knowledge, or invented evidence source is used. Companion
document: `EXTERNAL_EVIDENCE_BACKLOG.md` (per-gap detail table);
`KNOWLEDGE_READINESS_DASHBOARD.md` (per-concept status).

## Immediate

**Action: locate and transcribe the "Complete Calculation Video for
Weekly Future."**

The speaker in TR-001 references this video by name twice, as the
authoritative source for the Weekly Future High/Low arithmetic that
his own on-camera worked example fails to demonstrate cleanly:
- "வீக்லி ஃியூச்சர் கால்குலேஷன் வீடியோ" at TR-001 line 816
- "கம்ப்ளீட் டுடோரியல் கம்ப்ளீட் கால்குலேஷன் வீடியோ ஃபார் வீக்லி
  ஃியூச்சர்" at TR-001 line 2467

(both citations per `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root
blocker" item 3). Per that same document, this video "is not part of
`research/transcripts/TR-001.md` and, per the directory listing, does
not exist anywhere else in this repository (`research/videos/` and the
rest of `research/transcripts/` contain only `.gitkeep`)."

Specific open questions from `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
this acquisition should resolve:
1. A single worked example carried out correctly and consistently from
   stated inputs to stated output — no self-correction (the transcript's
   own example self-corrects 91→81 mid-calculation), no unexplained
   jump from a stated "difference = 18" to a final "answer = 268," and
   no two conflicting numbers ("268" vs "26168") for what is described
   as the same Low value ("Root blocker" item 1).
2. An explicit, general statement of the Low-side sign-flip rule
   covering all four possible orderings of (Call-High vs Put-Low) and
   (Put-High vs Call-Low), rather than the single specific case
   narrated ad hoc in TR-001 ("Root blocker" item 2).
3. Confirmation of whether the Weekly Future Close computation's
   simple-addition-with-no-sign-flip pattern (the one clean,
   internally-consistent piece of arithmetic already in TR-001, per
   the "Weekly Future Close" section) generalizes, or whether High/Low
   genuinely require the conditional logic while Close does not — the
   existing transcript "does not explain why."

This is ranked #1/#2 in `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 4's
Top-10 (only 7 genuinely evidenced) ranking specifically because it is
"the single most concrete, lowest-effort acquisition action... that
would most directly resolve item 1" (the Weekly Future arithmetic
itself).

## Short-term

Acquiring additional videos (by the same speaker/channel, "Trade Plan,"
per `STRIKE_EVIDENCE_SUMMARY.md` "Independent Sources" section, which
is the only channel identity evidenced in this repository) that would
confirm or extend each concept below. For each, what a new transcript
would need to show to move the concept toward READY:

- **Weekly Future.** Needs the clean worked example and general
  sign-flip statement described under Immediate above — the specific
  missing piece per `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`'s "Root
  blocker" section and `ENTITY_DEPENDENCY_GRAPH.md`'s ENT-010 row
  ("PARTIALLY READY").
- **Strike Selection (STRIKE-001).** Needs independent verification of
  the exact Call/Put-option-derived arithmetic for Weekly-Future
  High/Low (since STRIKE-001's own downstream nearest-strike-rounding
  step is already evidenced as not the blocker, per
  `RULE_DEPENDENCY_GRAPH.md` STRIKE-001 "Blocked By"), and independent
  cross-checking of the Doji-first-candle second-candle-fallback rule,
  which currently "appears only once and is not cross-checked against
  other examples in the file" (`STRIKE_EVIDENCE_SUMMARY.md` "Remaining
  Unknowns").
- **Trend Point (TREND-001/002/003).** Needs a stated formula
  connecting a selected Strike to a TP Low value — currently "no
  formula connecting Strike to a TP Low value" is evidenced
  (`FOUNDATIONAL_KNOWLEDGE_MAP.md` DAG Section 2, TrendPoint node) —
  plus, separately, a definition of "market structure change" for
  TREND-002 (`RULE_DEPENDENCY_GRAPH.md` TREND-002 "Blocked By": "the
  trigger condition itself is Unknown") and a quantified "well below"
  threshold for TREND-003 (`docs/TERMINOLOGY.md` lines 112-113, cited
  in `RULE_DEPENDENCY_GRAPH.md` TREND-003 "Blocked By").
- **Opponent (OPPONENT-001/002/003).** Needs a mathematical statement
  of the "defeat" condition (currently an explicit unresolved Open
  Question, `docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 344-350) and
  actual computations for Opponent High/Low, both currently Awaiting
  Evidence with Evidence Count 0 (`docs/RULE_INDEX.md` rows 35-36).
- **Reversal (REVERSAL-001).** Needs a stated natural-language rule
  connecting observed Premium behaviour to reversal identification —
  currently "which specific premium behaviour constitutes
  identification is not established anywhere" (`docs/DOMAIN_MODEL.md`
  lines 168-171), the one concept in the project with no rule shape
  stated at all yet (`FOUNDATIONAL_KNOWLEDGE_MAP.md` item 3).

## Medium-term

**The independent-source problem.** `STRIKE_EVIDENCE_SUMMARY.md`'s
"Independent Sources" section states plainly: **"No — this is not
independent evidence... one person's repeated, largely self-consistent
narration of one methodology across many different example trading
days — not multiple independent confirmations of a rule."** All 14
STRIKE-001 occurrences and all 15 Weekly Future occurrences currently
trace to the single file TR-001.md, single speaker, single channel
("Trade Plan"). Per `docs/EVIDENCE_MATRIX.md`'s Confidence Policy,
"Evidence Count... means the number of independent evidence sources...
not the number of other artifacts that reference this one. An artifact
cited by four different rules but ultimately traceable to a single
conversational statement still has Evidence Count = 1." This is why
`REPOSITORY_CHANGE_PROPOSAL.md` Section 4 item 2 explicitly recommends
**against** bumping STRIKE-001's Evidence Count from 2 to 14.

For a newly acquired source to count as genuinely independent under
this policy, it would need to be a distinct transcript — a different
speaker, or the same speaker on a materially separate occasion not
already folded into TR-001 — not merely another passage within the
same file. Medium-term acquisition should specifically target:
- **Repeated mathematical examples** from a distinct source, to
  corroborate (not just re-narrate) the Weekly Future High/Low formula
  once a first clean example exists (per Immediate above).
- **Contradictory mathematical examples** — actively checking whether
  a new source's worked arithmetic agrees with or conflicts with the
  first clean example, since the existing single source is already
  internally self-contradictory (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
  "Root blocker" items 1-3) and a second source could either resolve
  or compound that inconsistency.
- Applying the same independent-source scrutiny to any newly-found
  Reversal/Opponent/TrendPoint material, so those concepts are not
  later mis-recorded the same way `REPOSITORY_CHANGE_PROPOSAL.md`
  Section 4 item 2 warns against for STRIKE-001.

## Long-term

Once — and only once — a rule's mathematics is actually implementable
(per the Immediate/Short-term/Medium-term evidence work above), the
following validation activities become applicable. These are gated
behind the evidence work, not parallel to it: `IMPLEMENTATION_ROADMAP.md`
Milestone 4.7 (Backtest) is explicitly "**Blocked on:** Real rule
implementations existing (i.e., a future milestone that evidences and
implements at least one rule's actual mathematics) — without that, a
backtest run produces no meaningful trading-relevant output, only
proof that the pipeline mechanics work."

- **Replay validation** — `trading_engine.replay` (Milestone 4.5),
  which "feed[s] historical candle/tick data through the Rule
  Evaluation Pipeline one step at a time." Per the roadmap, this can be
  validated end-to-end using test-double rules even before real rule
  logic exists, but produces no trading-relevant validation of the
  Weekly Future/Strike/TrendPoint/Opponent/Reversal mathematics
  themselves until the evidence gaps above are closed.
- **Historical/backtest validation** — `trading_engine.backtest`
  (Milestone 4.7), which runs the Replay Engine against real historical
  data to "produc[e] Decision Objects across a full session/dataset."
  Explicitly blocked on real rule implementations per the roadmap
  quote above.
- **Paper trading** — Milestone 4.8 (Paper Trading), the next stage
  after Backtest in the roadmap's sequence, "Confirmed in live paper
  trading" per `docs/EVIDENCE_MATRIX.md`'s Status Policy ladder
  (`Backtested` → `Paper Verified`).

The eventual consumers of the evidence acquired above are
`trading_engine/engine/` (specifically `strategy_engine.py` and
`execution_pipeline.py`, which already exist per the repository's file
listing) together with the `replay`/`backtest` packages named in
`IMPLEMENTATION_ROADMAP.md` Milestones 4.5 and 4.7 — this roadmap does
not propose building or modifying any of them now; it only names them
as the destination once the mathematics is evidenced.

## Recommendation

**Acquire the "Complete Calculation Video for Weekly Future" first.**

Justification, using only repository evidence:

1. It is ranked #1 and #2 (as concept and as acquisition-action
   respectively) in `FOUNDATIONAL_KNOWLEDGE_MAP.md` Section 4's Top-10
   (7 genuinely evidenced) ranking — explicitly described as "the
   single most concrete, lowest-effort acquisition action... that
   would most directly resolve item 1," itself "the highest-impact,
   lowest-remaining-effort item in the project."
2. Per `FOUNDATIONAL_KNOWLEDGE_MAP.md`'s "Critical Blockers" section,
   resolving the Weekly Future arithmetic "unblocks STRIKE-001 fully" —
   because STRIKE-001's downstream nearest-strike rounding and
   bullish/bearish top-bottom selection are already evidenced at a
   "PARTIALLY READY... suitable for a documented feature spec and
   prototype implementation" level (`STRIKE_EVIDENCE_SUMMARY.md`
   "Recommended Readiness Verdict"); the Weekly Future arithmetic is
   the only remaining piece.
3. Unlike every other gap in the backlog (TrendPoint, Opponent,
   Reversal, market-structure-change, "well below"), this is the only
   gap in the project where the target source is named explicitly, by
   title, by the speaker himself, twice, inside the existing transcript
   (`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker" item 3) —
   every other gap would require open-ended search for an
   unidentified additional source, whereas this one is a targeted,
   named acquisition.
4. It directly unblocks a calculator that already exists in the
   codebase: `trading_engine/calculators/strike_calculator.py` — per
   `FOUNDATIONAL_KNOWLEDGE_MAP.md`'s Critical Blockers section, no
   other single acquisition in the backlog converts an existing
   calculator's upstream dependency to READY with this little
   additional evidence required (one clean worked example plus one
   general sign-flip statement, not a from-scratch investigation).

By contrast, the next-ranked item — Premium→Reversal identification
(#3) — while fully self-contained and immediately unblocking
`trading_engine/calculators/reversal_calculator.py`, requires
substantially more net-new evidence acquisition because "no
natural-language rule shape has been stated anywhere yet"
(`FOUNDATIONAL_KNOWLEDGE_MAP.md` item 3) — there is no analogous named,
locatable source to point to, unlike the Weekly Future video.

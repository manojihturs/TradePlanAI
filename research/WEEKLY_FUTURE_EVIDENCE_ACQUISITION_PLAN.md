# Weekly Future — Evidence Acquisition Plan

**Status:** the repository's internal evidence is exhausted (see `WEEKLY_FUTURE_BLOCKER_REPORT.md`, `research/analysis/NEW_EVIDENCE_REPORT.md`, and this session's own evidence review). This is a practical plan for what to go find, not a search — no web search was performed, no formula is proposed or implied anywhere below.

---

## 1. Missing Evidence Checklist

Every unresolved rule blocking `WeeklyFutureCalculator`, per `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §20 and `WEEKLY_FUTURE_BLOCKER_REPORT.md` §3:

- [ ] Weekly Future High formula (exact, reproducible, single value — not 3 conflicting values as in `TR-001.md`)
- [ ] Weekly Future Low formula (same standard)
- [ ] A general statement of the sign-flip rule covering all 4 possible orderings of (Call-High vs. Put-Low) and (Put-High vs. Call-Low) — `TR-001.md` only narrates one ordering
- [ ] Confirmation of what data feeds the formula (first-candle OHLC only, or something else — a separate weekly-futures instrument's own price?)
- [ ] Why "High" and "Low" are computed from a single first candle at all (the underlying mechanism, not just the arithmetic)
- [ ] Recalculation cadence — once per session, or intraday
- [ ] Rounding/precision rule beyond the one ad hoc instance (149.6 → 150)

## 2. Required Source Material

| Rule | Preferred Source | Acceptable Alternative | Minimum Evidence Required |
|---|---|---|---|
| High/Low formula | The "Complete Calculation Video for Weekly Future" — named twice by the speaker himself, `TR-001.md` lines 816 and 2467 | ≥3 independently consistent worked examples from an equivalent-priority source (same speaker/channel, or a written companion doc) | One example carried through correctly and consistently, start to finish, with no self-correction and no two different numbers for the same value |
| Sign-flip rule (general) | Same video | A written/spoken statement covering all 4 input orderings, not just the one demonstrated | An explicit general rule, or ≥3 examples collectively covering all 4 orderings |
| Data source for the calculation | Same video | A direct written clarification from the domain owner | One unambiguous statement of what data feeds High/Low |
| Recalculation cadence | Same video | Direct clarification from the domain owner | One unambiguous statement (once/day vs. intraday) |
| Rounding rule | Same video | ≥2 examples showing the same rounding behavior | A stated rule, or consistent behavior across ≥2 independent examples |

## 3. Search Strategy

Practical search queries, grouped by channel. These are starting points, not guarantees — refine based on what each platform actually surfaces.

**YouTube** (the speaker's own channel, "Trade Plan," is the first place to check for a video list before searching generally):
- `"Weekly Future Calculation" Trade Plan`
- `"Weekly Future Complete Calculation"`
- `வீக்லி ஃியூச்சர் கால்குலேஷன்` (Tamil, matching the exact phrase spoken in `TR-001.md`)
- `கம்ப்ளீட் கால்குலேஷன் வீடியோ ஃபார் வீக்லி ஃியூச்சர்` (Tamil, matching the exact second reference)
- `"Weekly Future Formula" options trading Tamil`

**Google:**
- `"Weekly Future" NIFTY options strike selection formula`
- `site:youtube.com "Weekly Future Calculation" Trade Plan`
- `"Weekly Future" premium analysis Tamil trading`

**Trading communities (forums, Discord, subreddits):**
- Search for the channel/speaker name directly (per `STRIKE_EVIDENCE_SUMMARY.md`'s "Independent Sources" note identifying the channel as "Trade Plan")
- `"Weekly Future" calculation NIFTY strike selection` in options-trading-focused communities

**Telegram** (public channel/group search):
- Search for the same channel name if it maintains a Telegram presence
- `"Weekly Future" calculation formula` in Tamil options-trading groups

**Documentation / PDFs:**
- Check for any downloadable course material, PDF notes, or slide decks the same channel may have published alongside its videos
- `"Weekly Future" filetype:pdf NIFTY options`

## 4. Validation Checklist

New material must pass every item below before it can move `weekly_future/` off BLOCKED — matches `research/EVIDENCE_INTAKE_PROCESS.md`'s existing verification checklist, restated here for this specific rule:

- [ ] Contains at least one full numerical worked example, start to finish
- [ ] Internally consistent — no self-correction that leaves two different final numbers unreconciled
- [ ] Repeatable — the same method, applied to a second, independent input set, produces a result consistent with the stated rule (not just one lucky example)
- [ ] No contradictions with previously confirmed rules (Rule 1: first-5-minute-candle input; Rule 2: Target/Support/Competitor mapping; Rule 3: no tie-break needed)
- [ ] Sufficient to reproduce the calculation programmatically without guessing any step

A source that fails any item stays in `research/incoming/` per `EVIDENCE_INTAKE_PROCESS.md`'s NEEDS MORE EVIDENCE disposition — it does not partially unblock implementation.

## 5. Repository Integration Plan

| New material type | Goes to |
|---|---|
| Video file, or a transcript of one | `research/transcripts/` (transcribe first, matching `TR-001.md`'s format) — raw video itself, if kept, under `research/videos/` |
| Written worked examples, PDFs, slide decks | `research/incoming/` first, per `EVIDENCE_INTAKE_PROCESS.md`'s intake lifecycle, then `research/processed/` or `research/verified/` per its classification |
| This plan's own search results log (what was checked, what was found, what wasn't) | Append to `research/evidence_log.md` as a new row, regardless of outcome — including "searched, found nothing" rows, so future sessions don't repeat the same search |

Every new source must go through `research/EVIDENCE_INTAKE_PROCESS.md` in full (Extraction → Verification → Cross-check → Classification → Specification Update → Implementation Approval) before touching `WEEKLY_FUTURE_BLOCKER_REPORT.md`'s verdict — do not shortcut intake even if the new material looks obviously clean.

## 6. Stop Condition

`weekly_future/` moves from **BLOCKED** to **READY FOR IMPLEMENTATION** only when:

1. New source material has passed every item in Section 4's Validation Checklist, **and**
2. It has gone through `research/EVIDENCE_INTAKE_PROCESS.md`'s full intake lifecycle and reached ACCEPTED per its own 5-condition Implementation Gate, **and**
3. `WEEKLY_FUTURE_BLOCKER_REPORT.md` (or a successor document) is updated to record the new verdict — DELAY is not silently abandoned, it is formally superseded.

Until all three hold, no session should attempt to implement `WeeklyFutureCalculator`, run the Sprint Gate readiness review, or use `prompts/02_BUSINESS_ENGINE_IMPLEMENTATION.md` for this engine — re-running the review against the same evidence will only reproduce this same conclusion.

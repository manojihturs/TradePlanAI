# Qualification Engine — Formal Scoring Pass (2026-08-01)

**Status:** Documentation only. Scores the evidence accumulated in `research/incoming/qualification_session1_intake_2026-07-31.md`, `stop_loss_session3_intake_2026-07-31.md`, `trailing_stop_session4_intake_2026-07-31.md`, and `daily_data_2026-07-31.md` against `research/specifications/evidence_acceptance_checklist.md`, item by item, honestly — including where it doesn't pass.

**Scope of this scoring:** the core Qualification/Entry rule — Entry = a marked level S, Target = S+1, Competitor Exit = touch of S-1, Stop Loss = S-1 (CE side confirmed) — sourced from the 13-level marked ladder (anchor ± 6), gated by an underlying-trend pre-check and a simultaneous dual crossover. This is now the best-evidenced version of QUAL-007's answer. Stop Loss (Session 3) and Trailing Stop (Session 4) are scored separately at the end, since they're distinct engines with their own checklists.

---

## Checklist — Qualification / Entry / Target / Competitor Exit

- [x] **Minimum three worked examples.** **PASS.** 4 independent dated examples exist: 22-July, 29-July, 30-July, 31-July 2026 — 16 individual trade rows total. Exceeds the minimum of three.

- [x] **Consistent outputs.** **PASS, for the core structure.** Every one of the 16 trades follows the same shape without exception: Entry at a marked level, Target = the next marked level in the trade's direction, Competitor Exit = touch of the opposite-side level at the prior rung, SL = the prior rung on the trade's own side. The self-verifying arithmetic (`Total = Captured points × 65`) holds exactly on all 16 rows — a strong, independent internal-consistency signal that this isn't coincidental agreement.

- [~] **No conflicting documentation.** **PASS for the substantive rule; one small open item remains.** Both contradictions originally found in this evidence set are now resolved: (1) the same-strike vs. adjacent-strike competitor question — resolved 2026-08-01, the competitor is any marked level, not fixed to one strike; (2) the 29-July 24150 discrepancy (165.8/116 vs. 137.3/141) — resolved 2026-08-01, Product Owner confirmed 165.8/116 is correct. **Not fully closed:** 31-July's Trade 1 has a minor textual mismatch between its Entry/Exit reason prose (names strike 24300) and its own Ref Label columns (name strike 24350) — flagged in Worked Example 4 as likely a transcription slip, not a business-rule contradiction, since it doesn't affect any of the actual traded numbers. Recorded, not yet explicitly confirmed by the Product Owner as immaterial.

- [x] **Replay validation possible.** **PASS.** The rule's inputs (per-strike CE/PE candle data, a marked-level ladder) are exactly what `src/backtest/`'s existing Upstox connector and `ReferenceBuilder` already fetch and compute today — confirmed directly, not hypothetically, by the two live backtest runs already performed against 30-July-2026 real data this session.

- [x] **Counter example provided, or explicitly marked UNKNOWN.** **PASS (retroactively closed, 2026-08-01).** No Worked Example originally had an explicit "Counter Example" field filled in. Closed by formally labeling data already supplied, not by requesting anything new: 22-July's Trade 3 ("CE Resistance hit first" at 101.6, neither Target nor SL) is now recorded as Worked Example 1's Counter Example — a real instance where the standard Target/SL/Competitor pattern did not simply hold.

- [x] **No unresolved `Unknown` on a required input or output.** **PASS (2026-08-01).** Both remaining Unknowns closed: (1) PE-side SL confirmed ("PE side same as CE, S+1"). (2) The `WinnerEngine` scope question — resolved using a real example already in the data (30-July's 24250-TOP Row 1 vs Row 2, where Row 2's entry level came from a different strike than its competitor level) — Product Owner confirmed directly: **"yes, correct, use the wider ladder."** Also newly clarified: the premiums actually watched for crossing are only Top's and Bottom's own CE/PE (four streams), not all 13 strikes' own premiums — the wider ladder supplies the levels crossed, not the streams watched.

---

## Score: 6 of 6 checked

## Verdict

**Evidence Complete.** Per `evidence_acceptance_checklist.md`'s own scoring rule ("All boxes checked → Evidence Complete → proceed to Approval"), the core Qualification/Entry/Target/Competitor Exit/Stop Loss rule now clears every item on the checklist. This is the first engine in this project (since Weekly Future) to reach this verdict through the full evidence framework built for exactly this purpose.

**The confirmed rule, stated precisely:**
- Anchor: Top Strike and Bottom Strike (Weekly Future formula, already confirmed and implemented).
- Ladder: for each anchor, capture the first-5-minute CE/PE High/Low across anchor ± 6 strikes (13 levels), with roles assigned per the General Rule Statement (Top: CE↔PE Low, PE↔CE High; Bottom: CE↔PE High, PE↔CE Low).
- Watched premiums: only Top's own CE/PE and Bottom's own CE/PE — four streams, not all 13 strikes' own premiums.
- Entry trigger: an underlying-trend pre-check, then a simultaneous dual crossover — the watched premium crosses a marked level from anywhere in the wider ladder (not fixed to the entry strike's own band), confirmed in the trend-implied direction.
- Target = S+1 (the next marked level in the trade's direction); Competitor Exit = touch of S-1 (opposite side); Stop Loss = S-1 same side (`CE(S-1)`/`PE(S+1)`) — both sides confirmed.
- Trailing Stop = minimum 3 points, step ratio 2 points of trail per 5 points of favorable premium movement (Session 4 — separately scored, still Evidence Partial pending activation trigger and cost figures).

**Implementation nuance worth flagging before Sprint 10, not a blocker to this verdict:** "S+1"/"S-1" here means the next/prior marked level *in the assigned ladder sequence*, which — per the 30-July Row 1/Row 2 example — can correspond to a different physical strike than simple adjacent-strike arithmetic would suggest, especially across sequential re-entries. This is more nuanced than Rule 2's fixed adjacent-strike model and should be designed deliberately, not assumed identical to Rule 2's mechanics.

## What this scoring does NOT cover

- **Stop Loss as its own engine (Session 3):** Evidence Complete for the SL rule itself, same as reflected above — this is now folded into the Evidence Complete verdict for the core rule, since SL is part of it.
- **Trailing Stop (Session 4):** still **Evidence Partial** — the +3 minimum and the 5-points-in/2-points-of-trail step ratio are stated, but the activation trigger and the brokerage/exchange/tax figures needed to compute "+3 net" precisely are still missing.
- **The "market closed (no level touched)" exit type** and the deferred "standard pivot points" (Resistance) concept remain unscored — new scope beyond QUAL-007's original blocker. Pivot points explicitly deferred by the Product Owner; the forced-close exit type has not been discussed either way and should be a deliberate decision (model it as a fifth `ExitEngine` condition, or treat it as an operational/session-end concern outside the engine) before Sprint 10 designs around it.
- **Two small, non-blocking loose ends**: explicit Product Owner confirmation on the minor 31-July strike-label mismatch (24300 vs 24350 in prose vs. Ref Label columns), and formal Rule ID bookkeeping in `docs/RULE_INDEX.md` (QUAL-007 exists; QUAL-001/002/010 and the new SL/TSL-specific IDs should be updated to reflect this verdict before implementation).

## Recommendation

Per `product_owner_evidence_process.md`'s Decision Matrix, an Evidence Complete outcome proceeds to **Approval** — the user's explicit go-ahead — not an automatic unblock. **This scoring recommends Sprint 10 (Qualification Engine) becomes eligible to start**, contingent on: (1) the Product Owner's explicit approval to proceed, (2) a deliberate decision on the "market closed" exit type and the S+1/S-1-as-ladder-position implementation nuance noted above, and (3) updating `docs/RULE_INDEX.md`/`docs/GAP_ANALYSIS.md` to reflect QUAL-007's new status before writing code, per `evidence_traceability_standard.md`'s five-link chain.

# Qualification Engine — Remaining Unknowns After Forensic Re-Audit

**Status:** Documentation only. Per the forensic prompt's instruction: "If evidence is missing, state exactly which artifact would be required."

---

## The blocker

**QUAL-007 — TP-stage competitor identity.** After re-searching every category the prompt named (research/, docs/, legacy strategy/trading_engine code and comments, TradingView references, Markdown, transcripts, archived folders, database schemas, replay outputs, CSV/Excel/JSON exports, screenshots, notes), no artifact anywhere in the repository names, defines, or gives a worked example of the competitor used in the TP High / TP Low sustain tests (`STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7).

## What was checked and found empty or inapplicable

- **Database schemas** — `orb_levels.db`'s only table (`session_date`, `strike`, `side`, `first_open`, `first_high`, `first_low`, `first_close`, `first_volume`) has no TP, qualification, or competitor-related column.
- **Old replay outputs / CSV / Excel / JSON exports** — every `.xlsx` file in the repository belongs to the legacy ORB Ladder system, unrelated to TP/Qualification.
- **Screenshots** — none exist in the project; the only image files anywhere in the repo tree are vendored library assets under `.venv/`.
- **Legacy code comments** (`strategy/exit_signal.py`, `premium_mapping.py`, `trading_engine/`) — define only the Exit-stage competitor (confirmed, out of scope for QUAL-007 per the conflict matrix).
- **Raw transcript** (`research/transcripts/TR-001.md`) — re-read directly (not just its analysis document); all opponent/competitor references map to concepts already captured (`OPPONENT-001`, `TREND-003`), none new.

## Exact artifact that would resolve this

Following the same evidentiary bar that resolved Weekly Future (`research/evidence_log.md`, 2026-07-30 row — accepted on the strength of 3 independently consistent, Product-Owner-supplied worked examples), closing QUAL-007 requires:

1. **A Product-Owner- or strategy-owner-supplied worked example** (transcript, note, or document) that names the TP-stage competitor explicitly for at least one concrete date/strike, showing:
   - Which specific strike/level was used as "competitor PE Low" / "competitor CE High" (for TP High) and "competitor PE High" / "competitor CE Low" (for TP Low) in that instance.
   - Enough surrounding data (the Top Strike or Bottom Strike's own CE/PE prices, and the competitor's values) to let the qualification outcome be independently recomputed and checked, the same way the Weekly Future formula was verified.
2. **At least 2 further independent examples** that are mutually consistent with the first — matching the Acceptance Criteria already on record in `QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` §4 (≥3 independent worked examples, no two implying conflicting rules).
3. Ideally, the same source should also state (or the examples should make derivable) whether the competitor changes during replay (Q3) and whether TP High/TP Low share one competitor or have distinct ones (Q6) — both currently unaddressed by any existing artifact.

Absent such an artifact, this audit finds no basis to proceed, and reaffirms the prior sprint's **Recommendation C (Blocked Pending Evidence)** — this forensic pass did not change that conclusion, but it does substantially raise confidence that the gap is genuine and not merely under-searched.

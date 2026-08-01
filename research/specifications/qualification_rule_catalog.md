# Qualification Engine — Rule Catalogue

**Status:** Documentation only. Every rule below is built directly from `qualification_evidence.md` — no rule here states anything beyond what that document's quotes support. Rule IDs are new (`QUAL-###`), except where a rule already has an ID from `docs/TRADINGVIEW_STRATEGY_BIBLE.md`/`TERMINOLOGY.md` (e.g. `TREND-003`), in which case the existing ID is reused rather than duplicated.

---

### QUAL-001 — TP High Sustain Test

- **Status: CONFIRMED (2026-08-01)** — see `qualification_engine_scoring_2026-08-01.md`, Evidence Complete verdict.
- **Description:** Top Strike qualifies while its own CE and PE premiums cross a marked level anywhere on the wider 13-level ladder (anchor ± 6), in the direction confirmed by the underlying trend, simultaneously (CE crosses a PE-derived level, PE crosses a CE-derived level).
- **Inputs:** Top Strike's own current CE price, current PE price; the wider marked-level ladder (CE High/PE Low per level for the Top-anchored roles); underlying trend direction.
- **Outputs:** Entry confirmation (side, entry level S), Target (S+1), Competitor Exit trigger (touch of S-1), Stop Loss (S-1 same side).
- **Dependencies:** Strike Selection (Top Strike, already resolved); the marked-level ladder (`ReferenceBuilder`, already implemented).
- **Evidence source:** `research/incoming/qualification_session1_intake_2026-07-31.md` (General Rule Statement, Entry Trigger Rule, Entry/Target/SL/TSL Clarification, 4 dated worked examples, 16 trade rows).
- **Confidence:** HIGH — Evidence Complete, 6/6 `evidence_acceptance_checklist.md` items pass.

### QUAL-002 — TP Low Sustain Test

- **Status: CONFIRMED (2026-08-01)** — mirrors QUAL-001, same evidence base.
- **Description:** Bottom Strike qualifies under the mirrored mapping (CE↔PE High, PE↔CE Low), same crossing/trend/ladder mechanism as QUAL-001.
- **Inputs/Outputs/Dependencies:** Same shape as QUAL-001, mirrored to the Bottom anchor.
- **Evidence source:** Same as QUAL-001.
- **Confidence:** HIGH — Evidence Complete.

### QUAL-003 — Qualification Is Current-State, Not Predictive

- **Description:** A qualified state describes the market's current condition only. It carries no forward-looking claim and is not permanent.
- **Inputs:** N/A (a stated property of QUAL-001/QUAL-002's output, not an input).
- **Outputs:** N/A.
- **Dependencies:** QUAL-001, QUAL-002.
- **Evidence source:** `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7 ("Qualification is NOT future prediction... Never assume qualification is permanent").
- **Confidence:** HIGH.

### QUAL-004 — External-Event Invalidation

- **Description:** News, Budget, War, or Natural Disaster events may invalidate a currently-qualified state.
- **Inputs:** An external event of one of the four named types (detection mechanism unspecified).
- **Outputs:** Invalidation of the current qualification state (mechanism unspecified).
- **Dependencies:** QUAL-001, QUAL-002.
- **Evidence source:** `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7.
- **Confidence:** HIGH that this is named as a real behavior; **UNKNOWN** for any implementable detection mechanism — "no detection mechanism is specified anywhere" (`research/specifications/QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` §2).

### QUAL-005 — Partial vs. Complete Trend Point Disqualification

- **Description:** A strike that already qualified as a Trend Point does not lose that status merely because price re-tests near its intraday low ("Partial Disqualification"). Full loss of status ("Complete Disqualification") requires both (a) the intraday low breaking, AND (b) the same-strike opposite-side TP Low being reached, in the same window.
- **Inputs:** Current strike's intraday low; current strike's opposite-side TP Low.
- **Outputs:** One of two disqualification severities (Partial / Complete), or no disqualification.
- **Dependencies:** QUAL-001/QUAL-002 (extends the sustain test with a two-tier loss condition); relates to TREND-002/OPPONENT-001 per the source analysis.
- **Evidence source:** `research/analysis/TR-001_ANALYSIS.md` §3.7.
- **Confidence:** MEDIUM — one clear, extended quote, single transcript segment, not yet corroborated by a second independent source.

### QUAL-006 — Qualification/TP Are Not Confirmed as Separate Computations

- **Description:** The source material never separates "TP" and "Qualification" into two distinct rule sets or engines — "TP qualifies" (QUAL-001/QUAL-002) is the only concept given. Whether a downstream implementation should therefore be one engine or two is unresolved.
- **Inputs:** N/A — this is a structural/architectural question, not a runtime rule.
- **Outputs:** N/A.
- **Dependencies:** QUAL-001, QUAL-002.
- **Evidence source:** `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` §8; `BUSINESS_WORKFLOW_SPECIFICATION.md` Stage 6.
- **Confidence:** UNKNOWN (explicitly an open question in both source documents, not a stated rule either way).

### QUAL-007 — Competitor Identity for the Sustain Test — RESOLVED (2026-08-01)

- **Status: CONFIRMED, no longer BLOCKING.** The project's longest-standing blocker. Resolved through a Product Owner evidence session (`research/incoming/qualification_session1_intake_2026-07-31.md`), formally scored Evidence Complete in `qualification_engine_scoring_2026-08-01.md`.
- **Description:** The competitor for QUAL-001/QUAL-002's sustain test is **any marked level on the wider 13-level ladder** (anchor Top/Bottom ± 6 strikes), not a fixed single strike — confirmed by a real example (30-July-2026, 24250-TOP Row 1 vs Row 2) where the entry level and competitor level belonged to different strikes within the same trade. This is confirmed **distinct** from the already-implemented Exit-stage Rule 2 competitor (`PE(S-1)`/`CE(S+1)`, adjacent strike) — the specification's original warning not to conflate the two was correct; they are genuinely different mechanisms, not the same one under different names.
- **Inputs:** The full marked-level ladder (already built by `ReferenceBuilder`, unchanged); Top's/Bottom's own CE/PE premiums (the only streams watched); underlying trend direction (new input, not previously modeled anywhere in `src/`).
- **Outputs:** Which specific ladder level was crossed (the "S" position), used to derive Target (S+1) and Competitor Exit trigger (touch of S-1).
- **Dependencies:** No longer blocks QUAL-001/QUAL-002 — this rule now unblocks them.
- **Evidence source:** `research/incoming/qualification_session1_intake_2026-07-31.md` (General Rule Statement, Entry Trigger Rule, Entry/Target/SL/TSL Clarification, 4 dated worked examples); `research/incoming/daily_data_2026-07-31.md`.
- **Confidence:** HIGH — Evidence Complete, 6/6 checklist items pass.

### QUAL-008 — Qualification → Winner Detection Dependency (Process Question)

- **Description:** Whether a qualified TP state is required (gates) before Winner Detection may trigger an entry signal. The specification describes Winner Detection (candle-level CE/PE touches against reference levels) with no mention of TP/Qualification state as an input, and the already-built `WinnerEngine` has zero code dependency on `TPEngine`/`QualificationEngine`. Two independent readings (business-spec-only, and code-architecture-only) reached the same conclusion from opposite directions.
- **Inputs:** N/A — this is a workflow/dependency question, not a runtime rule.
- **Outputs:** N/A.
- **Dependencies:** Affects how QUAL-001/QUAL-002's output (if ever implemented) would be wired to Winner Detection/Entry — or whether it would be wired at all.
- **Evidence source:** `BUSINESS_WORKFLOW_SPECIFICATION.md`, transition table and "Does the architecture support this workflow?" section.
- **Confidence:** MEDIUM-leaning-"no dependency exists" — "PARTIALLY, leaning NO" per the source document's own explicit rating; not a confirmed rule either way.

### QUAL-009 — Single Active Trade (Entry Prerequisite, Confirmed, Independent of Qualification)

- **Description:** Only one trade may be active at any time. While a trade is active, any new Winner/Entry signal is ignored outright — not queued, not deferred, and no state is retained about the ignored signal.
- **Inputs:** Current trade-active state.
- **Outputs:** Accept or ignore a new entry signal.
- **Dependencies:** None on QUAL-001 through QUAL-008 — this rule is independently confirmed and does not require Qualification to be resolved.
- **Evidence source:** `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` §10, CONFIRMED v1.1 Rule 4.
- **Confidence:** HIGH (CONFIRMED status).

### QUAL-010 — Edge Detection / "Well Below" Threshold (Related, Not a Qualification Rule Itself)

- **Description:** When both the current strike's and the opponent's TP Lows remain "well below" the selected strike, this is said to significantly reduce the probability of price moving below that strike. Related to, but distinct from, QUAL-005's Complete Disqualification condition.
- **Inputs:** Current strike's TP Low, opponent's TP Low, selected strike price.
- **Outputs:** A qualitative probability-reduction signal (no numeric output defined).
- **Dependencies:** TREND-003 (existing rule ID, reused here rather than duplicated); relates to QUAL-005.
- **Evidence source:** `docs/TERMINOLOGY.md`, "Edge (Edge Detection)".
- **Confidence:** MEDIUM for the concept's existence; **UNKNOWN** for "well below" itself — "not yet quantified (no fixed distance, percentage, or threshold established)."

### QUAL-011 — End-of-Session Forced Close ("Market Closed, No Level Touched")

- **Status: CONFIRMED as a real, real event; DESIGN DECISION made on where it lives (not itself new business-rule evidence).**
- **Description:** A trade still open when the trading session ends is closed at whatever price is current, having never hit Target/Competitor/SL/TSL. Found repeatedly in the 29/30-July trade logs (`qualification_session1_intake_2026-07-31.md`, Worked Examples 2-3), exit reason recorded verbatim as "market closed (No level touched)."
- **Design decision (2026-08-01):** implemented as **session-boundary orchestration**, not a fifth `ExitEngine` condition. `ExitEngine.evaluate()` is a pure per-candle check with no awareness of session start/end — none of its four existing conditions are time-based, and giving it a fifth, time-based one would be a different kind of concern bolted onto a currently-uniform interface. Instead, `BacktestRunner`/`ReplayRunner` (already session-scoped orchestrators) are responsible for forcing a close on any position still open after the last candle of the session — mirroring exactly how the harness already separates "engine scope" from "orchestration scope" for the `NeverTriggersStopLoss`/`NeverTriggersTrailingStop` null-objects.
- **Inputs:** The position still open at the final candle; that candle's own price.
- **Outputs:** A closed `TradePosition` with a new `ExitReason` (e.g. `SESSION_END`) distinct from the four already defined.
- **Dependencies:** None on QUAL-001/002/007 — orthogonal to the qualification/entry rule itself, only relevant to how any trade (regardless of how it qualified) is guaranteed to close by end of day.
- **Evidence source:** `research/incoming/qualification_session1_intake_2026-07-31.md`, Worked Examples 2 and 3 (4 occurrences across 2 days).
- **Confidence:** HIGH that the event is real; this entry documents an implementation-scope decision, not a new business rule requiring further evidence.

---

## Rule Count

**11 rules catalogued** (QUAL-001 through QUAL-011). Of these:
- **3 are CONFIRMED and now implementable**: QUAL-001, QUAL-002 (the sustain test itself), unblocked by QUAL-007 (also now CONFIRMED).
- **1** is a confirmed, already-implementable rule independent of the rest (QUAL-009).
- **1** is a scoped design decision, not new business-rule evidence (QUAL-011).
- **7** are either genuine unresolved gaps (QUAL-006, QUAL-007, QUAL-008) or partially-evidenced supporting concepts with no operational threshold (QUAL-003, QUAL-004, QUAL-005, QUAL-010).

No rule in this catalogue estimates a threshold, infers a missing identity, or assumes an unstated dependency — every "Dependencies"/"Description" field above traces directly to a quote in `qualification_evidence.md`.

# Qualification Engine — Rule Catalogue

**Status:** Documentation only. Every rule below is built directly from `qualification_evidence.md` — no rule here states anything beyond what that document's quotes support. Rule IDs are new (`QUAL-###`), except where a rule already has an ID from `docs/TRADINGVIEW_STRATEGY_BIBLE.md`/`TERMINOLOGY.md` (e.g. `TREND-003`), in which case the existing ID is reused rather than duplicated.

---

### QUAL-001 — TP High Sustain Test

- **Description:** Top Strike's TP qualifies as "TP High" while its CE price remains above the competitor's PE Low, and its PE price remains below the competitor's CE High.
- **Inputs:** Top Strike's own current CE price, current PE price; competitor's PE Low, competitor's CE High.
- **Outputs:** A qualification state (shape undecided — see QUAL-006).
- **Dependencies:** Strike Selection (Top Strike, already resolved); the competitor's identity (unresolved — see Gap Analysis).
- **Evidence source:** `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7.
- **Confidence:** HIGH (logical form) / the rule as a whole is not implementable without QUAL-006/QUAL-007.

### QUAL-002 — TP Low Sustain Test

- **Description:** Bottom Strike's TP qualifies as "TP Low" while its CE price remains above the competitor's PE High, and its PE price remains below the competitor's CE Low. Mirrors QUAL-001.
- **Inputs:** Bottom Strike's own current CE price, current PE price; competitor's PE High, competitor's CE Low.
- **Outputs:** A qualification state (shape undecided — see QUAL-006).
- **Dependencies:** Strike Selection (Bottom Strike, already resolved); the competitor's identity (unresolved).
- **Evidence source:** `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7.
- **Confidence:** HIGH (logical form) / not implementable without QUAL-006/QUAL-007.

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

### QUAL-007 — Competitor Identity for the Sustain Test (BLOCKING)

- **Description:** QUAL-001/QUAL-002 require a "competitor" strike/level, but the only confirmed competitor mapping in this project (`STRATEGY_FUNCTIONAL_SPECIFICATION.md` Rule 2) is explicitly scoped to a **Winner's entry strike** for the **Exit Engine** (`PE(S-1)`/`CE(S+1)`) — a different, post-Winner stage. The specification explicitly warns against assuming this Exit-stage pattern also defines the pre-Winner TP competitor.
- **Inputs:** N/A — this is the missing input itself.
- **Outputs:** N/A.
- **Dependencies:** Blocks QUAL-001 and QUAL-002 entirely; nothing in this catalogue can be implemented while this is unresolved.
- **Evidence source:** `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7 MISSING INFORMATION note; `research/specifications/QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` §2.
- **Confidence:** N/A (this rule *is* the gap, not a stated rule).

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

---

## Rule Count

**10 rules catalogued** (QUAL-001 through QUAL-010). Of these:
- **2** are directly-implementable test *shapes* but blocked by a shared missing input (QUAL-001, QUAL-002 — blocked by QUAL-007).
- **1** is a confirmed, already-implementable rule independent of the rest (QUAL-009).
- **7** are either genuine unresolved gaps (QUAL-006, QUAL-007, QUAL-008) or partially-evidenced supporting concepts with no operational threshold (QUAL-003, QUAL-004, QUAL-005, QUAL-010).

No rule in this catalogue estimates a threshold, infers a missing identity, or assumes an unstated dependency — every "Dependencies"/"Description" field above traces directly to a quote in `qualification_evidence.md`.

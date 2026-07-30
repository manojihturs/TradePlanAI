# Repository Change Proposal

**Status: PROPOSAL ONLY.** This document describes changes someone else
would later apply to the ledger/architecture docs. Nothing outside this
file has been modified to produce it. Every proposed change below cites
a specific `research/analysis/*.md` file/section as its evidence; where
evidence is thin, ambiguous, or single-source, that is stated explicitly
rather than glossed over.

---

## Section 1: Summary

Milestones 5.0/5.0A/5.0B/5.1 collectively re-mined `research/transcripts/TR-001.md`
for evidence on STRIKE-001 and on the "Weekly Future" concept the ledger
currently treats as an inert Candidate entity, and then built a
knowledge-graph layer over the results:

- **Milestone 5.0** (initial STRIKE-001 audit) concluded the repository
  had evidence that "strike selection is based on the first candle" but
  not the underlying mathematics — verdict **NOT READY**.
- **Milestone 5.0A** re-mined the full 4245-line transcript and found
  **14 genuine occurrences** of the strike-selection mechanism (vs. the
  1 quote currently recorded in the Bible/Rule Index), and discovered
  that the mechanism is not self-contained: it depends on a **Weekly
  Future** first-candle High/Low, a concept the ledger's Candidate
  Entity list (`ENT-010`) currently frames as "reserved, inactive."
  Verdict upgraded to **PARTIALLY READY**
  (`research/analysis/STRIKE_EVIDENCE_SUMMARY.md`).
- **Milestone 5.0B** dug into the Weekly Future calculation itself and
  found 15 occurrences establishing the *inputs* (Call/Put first-candle
  High/Low/Close, the day's ATM strike) and the *shape* of the
  combination rule, but the transcript's own worked-example arithmetic
  is internally inconsistent (a self-corrected subtraction, an
  unexplained jump from "difference = 18" to "answer = 268," two
  different values given for the same Low, and a computed Low that
  ends up numerically above the computed High for the same candle) and
  twice points to an external "Complete Calculation Video" that is not
  present anywhere in this repository. Verdict: **PARTIALLY READY**
  (`research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`).
- **Milestone 5.1** built `RULE_DEPENDENCY_GRAPH.md`,
  `ENTITY_DEPENDENCY_GRAPH.md`, and `FOUNDATIONAL_KNOWLEDGE_MAP.md`,
  which formally flag that `RULE_INDEX.md`'s "STRIKE-001 Depends On:
  none yet" is now stale relative to the newly-evidenced Weekly-Future
  dependency, and that `ENT-010` (Weekly Future) is materially more
  evidenced (named inputs, a stated rule shape, a real if broken
  arithmetic attempt, explicit "this is a taught formula" language from
  the speaker) than its current "Candidate... no defined computation"
  framing suggests.

**Why the ledger docs are out of sync:** `RULE_INDEX.md`,
`TRADINGVIEW_STRATEGY_BIBLE.md`, `EVIDENCE_MATRIX.md`,
`TRACEABILITY_MATRIX.md`, and `docs/architecture/DOMAIN_ARCHITECTURE.md`
were all last substantively updated at Milestone 3.2, on the strength of
a single Bible-quote-plus-one-transcript-pass reading of TR-001 (1
occurrence per rule, "Depends On: none yet" for STRIKE-001, Weekly
Future recorded as an inert Candidate with "no defined computation").
Milestones 5.0/5.0A/5.0B/5.1 re-read the same transcript far more
thoroughly and produced qualitatively new findings — an occurrence count
increase, a real (if unverified) dependency edge, and a real (if
unverified) computation shape for Weekly Future — none of which have
been written back into the ledger documents themselves. This proposal
is that write-back, presented as changes for review rather than applied
directly.

---

## Section 2: Per-document proposed changes

### docs/RULE_INDEX.md

| Current Entry (verbatim quote + location) | Proposed New Entry (verbatim proposed text) | Reason | Evidence | Risk |
|---|---|---|---|---|
| `| STRIKE-001 | Initial strike selection is based on the first candle | STRIKE | Draft | Medium | 2 | none yet | none yet |` (Index table, row 30) | `| STRIKE-001 | Initial strike selection is based on the first candle | STRIKE | Draft | Medium | 2 | Weekly Future first-candle High/Low (unverified arithmetic) | none yet |` | Milestone 5.1 explicitly flags this "Depends On: none yet" as stale relative to the newly-evidenced Weekly-Future dependency; three separate transcript quotes establish that "first candle top/bottom" always resolves to the *computed Weekly Future's* first candle, never the raw spot/index candle. | `research/analysis/RULE_DEPENDENCY_GRAPH.md` "Discrepancy flagged: STRIKE-001's 'Depends On'" section and Summary Table row for STRIKE-001; underlying quotes in `research/analysis/STRIKE_EVIDENCE_TABLE.md` rows 10, 11, 14 and `STRIKE_EVIDENCE_SUMMARY.md` Conflicts item 2. | Recording a dependency on an entity (Weekly Future) that is itself only "PARTIALLY READY" with self-contradictory arithmetic could read as if the dependency is settled and computable, when only its *existence*, not its exact formula, is evidenced. The parenthetical "(unverified arithmetic)" is proposed specifically to prevent that misreading — omitting it would be a riskier version of this same change. |
| Notes section (lines 41–50): "Updated (Milestone 3.2): STRIKE-001 ... now have Evidence Count = 2 ... Update Evidence Count and Status together as additional independent sources are added ... do not increase Status without a corresponding increase in Evidence Count or explicit confirmation." | Add a new note: "Updated (Milestone 5.0A): STRIKE-001's transcript occurrence count within TR-001 was re-audited and found to be 14 (not 1) recurring statements of the same mechanism, all from the single TR-001 source. Per the Confidence Policy in `EVIDENCE_MATRIX.md` (Evidence Count = independent sources, not occurrences), this recount does NOT change Evidence Count (still 2: original statement + TR-001 as one source) or Confidence (still Medium). It is recorded here as a Notes-only clarification of source depth, not a ledger-value change." | Without this note, a future editor skimming Milestone 5.0A/B outputs could mistakenly bump Evidence Count to reflect 14, conflating recurrence-within-one-source with independent-source confirmation — the exact distinction `STRIKE_EVIDENCE_SUMMARY.md` itself is careful to draw. | `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Independent Sources" section ("No — this is not independent evidence... one person's repeated... narration... not multiple independent confirmations"); `docs/EVIDENCE_MATRIX.md` Confidence Policy paragraph ("Evidence Count... means the number of independent evidence sources... not the number of...references"). | Low risk if added as written (it deliberately locks in the *conservative* reading). Risk if this note is skipped: a later, less careful update could bump Evidence Count from 2 to 14, which Section 4 below explains should NOT happen. |
| Every other row (TREND-001/002/003, OPPONENT-001/002/003, REVERSAL-001) | No change proposed. | Checked against `RULE_DEPENDENCY_GRAPH.md`'s per-rule detail sections — each one explicitly states "No evidenced dependency found in the STRIKE/WEEKLY_FUTURE evidence docs" or "Consistent — no discrepancy found" for these rules' `Depends On` values. Milestones 5.0A/5.0B/5.1 only investigated STRIKE-001 and Weekly Future; they did not re-mine evidence for TREND-*, OPPONENT-*, or REVERSAL-001. | `research/analysis/RULE_DEPENDENCY_GRAPH.md` per-rule detail sections for TREND-001, TREND-002, TREND-003, OPPONENT-001, OPPONENT-002, OPPONENT-003, REVERSAL-001 (each explicitly says "Consistent" or "No evidenced dependency found"). | None — this is a "no change" finding, listed for completeness so a reviewer doesn't wonder whether these rows were checked. |

### docs/TRADINGVIEW_STRATEGY_BIBLE.md

| Current Entry (verbatim quote + location) | Proposed New Entry (verbatim proposed text) | Reason | Evidence | Risk |
|---|---|---|---|---|
| `Transcript Quote:` / `"...First candle... 24050..."` (STRIKE-001 section, line 91-92) | Add a second field beneath the existing one: `Additional Transcript Occurrences: 14 total genuine occurrences of the strike-selection mechanism identified across TR-001's full 4245 lines (see research/analysis/STRIKE_EVIDENCE_TABLE.md rows 1-14). The originally-quoted fragment ("...First candle... 24050...") remains the Bible's canonical illustrative quote; the additional occurrences are catalogued, not individually quoted here, to avoid bloating the per-rule template.` | The Bible's per-rule template currently implies (via a single quote) that STRIKE-001 rests on one observed instance. Milestone 5.0A shows the same mechanism recurs 14 times, including a generalized "how do you choose the strike" Q&A answer (row 12) and an explicit "this is a formula we already gave" statement (row 11) — materially different evidentiary texture than a single quote suggests, even though it doesn't change the Evidence Count under the source-counting policy. | `research/analysis/STRIKE_EVIDENCE_TABLE.md` rows 1-14; `STRIKE_EVIDENCE_SUMMARY.md` "Evidence Count" and "Repeated Behaviour"/"Repeated Terminology" sections. | If this field is misread as raising Evidence Count or Confidence, it would violate the Confidence Policy's independent-source rule (see Section 4). The proposed field name ("Additional Transcript Occurrences," not "Evidence Count") and explicit sentence tying it back to the unchanged canonical quote are meant to forestall that misread. |
| `Mathematical Definition: Unknown` (line 99) | No change proposed — remains `Unknown`. | Milestone 5.0B's `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` explicitly concludes the mechanism's *shape* is now stated in natural language but the *arithmetic* is not clean or verifiable from the transcript (self-corrected numbers, an unexplained jump from "18" to "268," a Low exceeding a High for the same candle). "Unknown" is still the accurate status; "Partially Known" would overstate what's evidenced. | `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker, stated plainly" section, items 1-3. | Listed as a non-change specifically because the temptation to bump this field (given how much new material exists) is real — see Section 4. |
| `Depends On: none yet` (line 105) | `Depends On: Weekly Future first-candle High/Low (ENT-010) — dependency shape evidenced, exact arithmetic unverified; see research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` | Same underlying discrepancy as the `RULE_INDEX.md` change above — the Bible and `RULE_INDEX.md` are required to stay in sync per `RULE_INDEX.md`'s own opening paragraph ("every rule that appears in either of those documents must have a corresponding row" in the other). Updating only one would reintroduce a cross-document inconsistency of the same kind this proposal is trying to fix. | `research/analysis/RULE_DEPENDENCY_GRAPH.md` Summary Table, STRIKE-001 row, "Depends On (deeper evidence)" column. | Same as the `RULE_INDEX.md` risk above: overstating dependency certainty if the "unverified arithmetic" qualifier is dropped. |

### docs/EVIDENCE_MATRIX.md

| Current Entry (verbatim quote + location) | Proposed New Entry (verbatim proposed text) | Reason | Evidence | Risk |
|---|---|---|---|---|
| `| STRIKE-001 | Business Rule | Initial Strike Selection | 2 | Conversational statement + TR-001 transcript | Medium | Draft | ... | Mathematical Definition Unknown |` (Business Rules table, STRIKE-001 row) | Append to the `Notes` cell only (no numeric field changes): `Mathematical Definition Unknown. Milestone 5.0A re-audit: 14 within-transcript occurrences found (still 1 transcript source; Evidence Count correctly remains 2 per Confidence Policy — see research/analysis/STRIKE_EVIDENCE_SUMMARY.md "Independent Sources: No").` | This is presented as a proposed change specifically to make explicit, in the ledger itself, that the 14-occurrence finding was *considered* and deliberately *not* used to bump Evidence Count — closing the loop Milestone 5.1 opened, without touching the numeric columns. | `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Independent Sources" section; `docs/EVIDENCE_MATRIX.md`'s own Confidence Policy (Evidence Count = independent sources, not occurrences). | Because this only touches the Notes cell, risk is low. The larger risk this row exists to head off — someone else independently deciding to bump Evidence Count to 14 — is discussed under Section 4. |
| `| ENT-010 | Business Entity | Weekly Future | 1 | TR-001 transcript only | Low (Derived from TR-001 only) | **Candidate** | ... | Not promoted to a Rule. See research/analysis/TR-001_ANALYSIS.md Section 5. Not yet in DOMAIN_MODEL.md/TERMINOLOGY.md. |` (Business Entities table, ENT-010 row) | Update the `Notes` cell to: `Not promoted to a Rule. See research/analysis/TR-001_ANALYSIS.md Section 5 and research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md (Milestone 5.0B: named inputs and stated combination rule now evidenced; numeric arithmetic self-contradictory, PARTIALLY READY, not verified). Not yet in DOMAIN_MODEL.md/TERMINOLOGY.md.` Evidence Count/Confidence/Status columns unchanged (still 1 / Low / Candidate). | Milestone 5.0B materially deepened the evidence behind ENT-010 (inputs, rule shape, a real arithmetic attempt) but it is still a single transcript source with unverified numbers — the Notes cell should reflect the deeper evidence exists, while the graduated Status change is proposed separately (with more caution) in Section 3, not silently folded in here. | `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` (whole document, esp. "Root blocker" section). | Understating this change (leaving the Notes cell as-is) hides that new evidence exists; overstating it (bumping Status/Confidence directly in this table) would pre-empt the more careful judgment call laid out in Section 3. The proposed Notes-only update threads that needle. |

### docs/TRACEABILITY_MATRIX.md

| Current Entry (verbatim quote + location) | Proposed New Entry (verbatim proposed text) | Reason | Evidence | Risk |
|---|---|---|---|---|
| Evidence ID table (lines 27-39): last-used ID is `EVID-007` (TR-001 transcript, whole-source). | Add: `| EVID-008 | STRIKE_EVIDENCE_TABLE.md, rows 1-14 (`research/analysis/STRIKE_EVIDENCE_TABLE.md`) | Milestone 5.0A catalogue of the 14 genuine within-TR-001 occurrences of the strike-selection mechanism (superset detail of EVID-007 for STRIKE-001 specifically) |` and `| EVID-009 | WEEKLY_FUTURE_EVIDENCE_TABLE.md, rows WF-1 through WF-15 (`research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md`) | Milestone 5.0B catalogue of the 15 within-TR-001 occurrences establishing Weekly Future's named inputs and stated (but arithmetically unverified) combination rule |` | Per the existing convention ("No formal Evidence ID existed before this document... every EVID-NNN below points to the exact same statement already cited"), the newly-produced evidence-acquisition tables (`STRIKE_EVIDENCE_TABLE.md`, `WEEKLY_FUTURE_EVIDENCE_TABLE.md`) are themselves already-produced, already-cited catalogues that currently have no Evidence ID pointing at them, even though `EVID-007` already covers "TR-001 as a whole." EVID-008/009 would let STRIKE-001's row cite the *specific* deeper catalogue rather than only the whole-transcript EVID-007. | `docs/TRACEABILITY_MATRIX.md` lines 19-39 (ID convention + existing EVID-001..007 table); `research/analysis/STRIKE_EVIDENCE_TABLE.md` and `research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md` (row-level content, not re-derived here — only the already-produced tables are pointed at). | These are proposed as *new rows pointing at already-catalogued material*, not new evidence content, consistent with the instruction not to invent evidence. Risk: if a future editor treats EVID-008/009 as *additional independent evidence* (raising STRIKE-001 or ENT-010's Evidence Count), that would repeat the exact independent-vs-recurring conflation flagged throughout this proposal — the added rows should carry a Notes qualifier making clear they refine/detail EVID-007, not add a new independent source. |
| STRIKE-001 row (Rules table, line 49): `| STRIKE-001 | ... | EVID-001, EVID-007 | UNKNOWN (no other rule cites STRIKE-001 in Depends On) | ENT-001, ENT-002 | ... |` | `| STRIKE-001 | ... | EVID-001, EVID-007, EVID-008 | UNKNOWN (no other rule cites STRIKE-001 in Depends On) | ENT-001, ENT-002, ENT-010 | ... |` (Notes cell to add: "Related Entity(s) now includes ENT-010 (Weekly Future) — see RULE_DEPENDENCY_GRAPH.md discrepancy note; STRIKE-001's own Related Rule(s) column stays UNKNOWN since no other *rule* depends on it, this only affects the entity-level trace.") | STRIKE-001's mechanism is now evidenced (5.0A/5.0B) to consume the Weekly Future entity, which the current row's `Related Entity(s)` column (ENT-001, ENT-002 only) omits. | `research/analysis/RULE_DEPENDENCY_GRAPH.md` STRIKE-001 "Consumes" field: "First Candle (ENT-002, itself resolved to be the Weekly Future's first candle...)"; `STRIKE_EVIDENCE_SUMMARY.md` Conflicts item 2. | Adding ENT-010 here could be read as "STRIKE-001 formally depends on a Confirmed entity" if the accompanying Notes qualifier is dropped — the qualifier is load-bearing, not decorative. |
| ENT-010 row (Entities table, line 71): `| ENT-010 | Weekly Future | Entity (**Candidate**) | TR-001 transcript | EVID-007 | none | UNKNOWN | ... |` | `| ENT-010 | Weekly Future | Entity (**Candidate**) | TR-001 transcript | EVID-007, EVID-009 | STRIKE-001 (consumed by; see RULE_DEPENDENCY_GRAPH.md) | UNKNOWN | ... |` | Symmetric update to the STRIKE-001 row change above — ENT-010's own row currently shows `Related Rule(s): none`, which is now stale given the evidenced (if unverified) consumption relationship. | Same as above; `research/analysis/RULE_DEPENDENCY_GRAPH.md` Summary Table, STRIKE-001 "Depends On (deeper evidence)" column. | Same qualifier risk as above — must stay paired with "PARTIALLY READY, arithmetic unverified" language wherever it appears, or it reads as more settled than it is. |

### docs/architecture/DOMAIN_ARCHITECTURE.md

| Current Entry (verbatim quote + location) | Proposed New Entry (verbatim proposed text) | Reason | Evidence | Risk |
|---|---|---|---|---|
| `### WeeklyFuture (Candidate) — ENT-010` section (lines 242-246): "Per TR-001_ANALYSIS.md Section 5: described as the primary basis for level-setting in TR-001, but not officially published — reconstructed via premium analysis. Reserved as a possible future reference-data source; no computation designed." | `### WeeklyFuture (Candidate — Evidence Deepened) — ENT-010\n\nPer research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md (Milestone 5.0B): named inputs (Call/Put option first-candle High/Low/Close, the day's ATM strike) and a stated combination rule (Call-High/Put-Low difference applied to the ATM strike for the High side; Put-High/Call-Low difference with a conditional sign-flip for the Low side) are now evidenced in natural-language form. The transcript's own worked-example arithmetic is NOT internally consistent (self-corrected subtraction, an unexplained jump from a stated difference to a final answer, two conflicting values given for the same Low, and a computed Low that exceeds the computed High for the same candle — a structural impossibility never flagged as an error by the speaker), and the transcript twice references an external "Complete Calculation Video" not present in this repository. Reserved as a documented, named computation shape — still not activated in the Rule Engine's evaluation path, and still not to be implemented from the transcript's numbers as given.` | `DOMAIN_ARCHITECTURE.md`'s own Status Key defines Candidate as "added... not promoted," which remains correct, but its ENT-010 entry text ("no computation designed" is implied by silence on the topic) predates 5.0B's finding that a computation *shape* — just not verified arithmetic — now exists. The proposed text keeps ENT-010 at Candidate status (see Section 3 for the more careful status-label discussion) while updating the *description* to reflect what's actually known. | `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Dependency chain" and "Root blocker, stated plainly" sections. | The biggest risk in this document specifically: if an implementer reads "combination rule... now evidenced" and skips straight to coding it without reading the "NOT internally consistent" clause, they would ship an unverified/wrong formula. The proposed wording front-loads the blocking caveat in the same paragraph as the positive finding, not in a separate section that could be skipped. |
| Summary table (line 304): `| WeeklyFuture | Candidate | ENT-010 | (none) | Reserved, inactive |` | `| WeeklyFuture | Candidate (inputs/shape evidenced, arithmetic unverified) | ENT-010 | STRIKE-001 (consumed by, unverified) | Reserved, inactive |` | The summary table's terse "(none)" Rule(s) column and bare "Candidate" status both understate what Milestone 5.1's `RULE_DEPENDENCY_GRAPH.md` and Milestone 5.0B established. | `research/analysis/RULE_DEPENDENCY_GRAPH.md` Summary Table STRIKE-001 row; `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`. | Table cells are terse by design; there's a real risk that even the proposed parenthetical gets trimmed by a future editor for column width, silently dropping the caveat. Recommend keeping the fuller description-section wording (row above) as the authoritative version and treating the summary table as secondary. |

### docs/TERMINOLOGY.md

| Current Entry (verbatim quote + location) | Proposed New Entry (verbatim proposed text) | Reason | Evidence | Risk |
|---|---|---|---|---|
| No entry exists for "Weekly Future," "Top Strike," "Bottom Strike," or "ATM Strike" anywhere in the document (confirmed: only First Candle, Strike, Trend Point Low, Opponent, Opponent High/Low, Edge, Reversal are defined). | Add new term: `### Weekly Future\n\nDefinition:\nA synthetic instrument, not itself listed/published, reconstructed from Call-option and Put-option first-candle price data plus the day's ATM strike (per research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md). Its first candle's computed High and Low, rounded to the nearest exchange-listed strike, are described as the basis for STRIKE-001's "first candle top/bottom" selection — i.e., "first candle" throughout TR-001 refers to this computed candle, not the raw spot/index candle (research/analysis/STRIKE_EVIDENCE_TABLE.md row 14). The exact Call/Put-to-High/Low combination arithmetic is stated in natural language but not verified — see Weekly Future Calculation dependency analysis.\n\nEvidence Level: TR-001 transcript only (single source)\nUsed By: STRIKE-001 (dependency, not yet reflected as Depends On — see RULE_INDEX.md proposal)\nStatus: Partial (inputs and rule shape known; arithmetic unverified)` | The term is used constitutively across both the 14 STRIKE-001 occurrences and the 15 Weekly-Future-specific occurrences — it is not a passing mention, it is the load-bearing concept both evidence tables organize around — yet `TERMINOLOGY.md`'s own stated purpose ("Every trading term used across the Bible... is defined exactly once here") is currently unmet for it. | `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Repeated Terminology" section (lists "வீக்லி ஃியூச்சர்" / Weekly Future as a consistently-named instrument across 5 of 14 rows); `research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md` (whole document). | Adding a formal Terminology entry for something still `Candidate` at the Entity level is a slight status mismatch worth flagging: Terminology entries elsewhere in this doc correspond to Confirmed-adjacent Rules/Entities. Recommend the "Status: Partial" (not "Confirmed") framing exactly to avoid this looking more settled than ENT-010 itself is proposed to be (Section 3). |
| Same absence for "Top Strike"/"Bottom Strike" specifically. | Optionally fold "Top Strike"/"Bottom Strike" into the same Weekly Future entry as a sub-definition, or add as a second minimal entry, rather than a full separate template: they are directly evidenced as "the nearest listed strike to the computed Weekly Future High/Low respectively" (`STRIKE_EVIDENCE_TABLE.md` row 11). | Recurs by name across at least 6 of 14 STRIKE-001 rows (1, 2, 6, 8, 9, 10, 11, 13, 14 per `STRIKE_EVIDENCE_SUMMARY.md`'s "Repeated Terminology" list) — a genuine, stable, named pair of terms, not ad hoc phrasing. | `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Repeated Terminology" section. | Low risk — this is the most cleanly evidenced of all proposed terminology additions (the nearest-strike-rounding step is explicitly called "not the blocker" in `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`). |
| "ATM Strike" | Not proposed as a standalone new term. | "ATM Strike" appears only as an *input* to the Weekly Future computation (the day's already-known ATM strike), not as a concept the transcript itself defines or explains — it's used as a pre-existing, generically-understood options-trading term, unlike Weekly Future/Top Strike/Bottom Strike which are the speaker's own constructed vocabulary. | `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Dependency chain" section, "Input C" in both the High and Low derivations. | None — this is a deliberate non-proposal, listed so a reviewer doesn't wonder why it was skipped given the other three terms were added. |

### docs/STATE_MACHINE.md

| Current Entry (verbatim quote + location) | Proposed New Entry (verbatim proposed text) | Reason | Evidence | Risk |
|---|---|---|---|---|
| `**Entry Conditions:**\nUNKNOWN - insufficient evidence. STRIKE-001 states selection happens "based on the first candle" but not the precise triggering condition (e.g. candle close, a specific price relationship, session open time).` (STATE: STRIKE_SELECTED, lines 35-38) | No change proposed — remains `UNKNOWN`. Optionally append a citation: "See research/analysis/STRIKE_EVIDENCE_SUMMARY.md and WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md (Milestone 5.0A/5.0B) — these substantially deepen WHAT is computed (Weekly Future first-candle High/Low → nearest strike) but do not resolve the precise triggering INSTANT (e.g., is the first candle's close required, or does the computation run intra-candle) referenced by this Entry Conditions field." | Milestone 5.0A/5.0B's new evidence answers "what value is the strike selection based on," not "at what precise moment/trigger does STRIKE_SELECTED begin." Those are different questions; the new evidence does not touch the latter. Explicitly checked `STRIKE_EVIDENCE_TABLE.md`/`WEEKLY_FUTURE_EVIDENCE_TABLE.md` for any triggering-instant language and found none. | `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` (entirely about the *value* computation, silent on triggering instant); `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` (same). | This is presented as a non-change specifically because the temptation to mark Entry Conditions "Known" now that so much more is documented about STRIKE-001 is real — see Section 4. The optional citation addition carries no status-change risk since it explicitly says the field stays UNKNOWN. |

### docs/DOMAIN_MODEL.md, docs/GAP_ANALYSIS.md, docs/MATHEMATICAL_SPECIFICATION.md

No changes proposed for any of these three documents.

- **`docs/DOMAIN_MODEL.md`**: The "First Candle" entity's Attributes field
  ("Unknown - which candle... is not established. Only a worked example
  exists (a resulting strike, 24050), not the candle's own defining
  attributes") is now known to be incomplete in the same sense as
  `TERMINOLOGY.md`'s First Candle entry — but `DOMAIN_MODEL.md`'s own
  stated scope is "no behaviour... no new rules," and it explicitly
  defers correspondence/refinement questions to `GAP_ANALYSIS.md`. Since
  this project's evidence-only rule requires citing a specific
  discrepancy rather than "this could theoretically be expanded," and
  since the "First Candle = Weekly Future's first candle" resolution is
  already the subject of the `TERMINOLOGY.md` proposal above, adding a
  second, largely-duplicate change here was judged to add ledger-sync
  risk (two documents needing to be kept consistent) without adding new
  information not already captured. Recommend deferring any
  `DOMAIN_MODEL.md` edit until the `TERMINOLOGY.md`/`RULE_INDEX.md`
  changes above are actually applied, at which point `DOMAIN_MODEL.md`
  can cite the finalized Terminology entry rather than restating it.
- **`docs/GAP_ANALYSIS.md`**: Its own Status field states it is "Empty
  - blocked on Phase 1/2... producing enough FORMALISED rules... to
  compare," and its Traceability rule requires every gap to reference a
  Rule ID with `FORMALISED` status. No rule in `RULE_INDEX.md` has
  `FORMALISED` status (the lifecycle only reaches `Draft` currently, per
  `RULE_INDEX.md`'s own Status values table — `FORMALISED` isn't even a
  listed value there, `Validated` is the closest). Milestones 5.0-5.1
  did not change any rule's Status field. No discrepancy found.
- **`docs/MATHEMATICAL_SPECIFICATION.md`**: Its own Status field states
  it is empty "awaiting Phase 1... No rule is formalised here until its
  status in RULE_INDEX.md is CONFIRMED." No rule is `Confirmed`. The new
  Weekly Future arithmetic, even if it were clean, would not meet this
  document's own admission bar while still self-contradictory. No
  discrepancy found — and populating it now would itself be one of the
  "should NOT be made" changes (see Section 4).

---

## Section 3: Promotion candidates

| Candidate | Current | Proposed | Evidence | Risk |
|---|---|---|---|---|
| **STRIKE-001 dependency graph** | `Depends On: none yet` (`RULE_INDEX.md`, `TRADINGVIEW_STRATEGY_BIBLE.md`) | `Depends On: Weekly Future first-candle High/Low (ENT-010) — dependency shape evidenced, exact arithmetic unverified` | `RULE_DEPENDENCY_GRAPH.md` Summary Table + discrepancy section. | Overstating certainty if the "unverified arithmetic" qualifier is dropped in any future edit — see repeated caveat above. |
| **Weekly Future (ENT-010) status** | `Candidate` (`EVIDENCE_MATRIX.md`, `TRACEABILITY_MATRIX.md`, `DOMAIN_ARCHITECTURE.md`) | **Judgment call, no clean promotion recommended.** The Status Policy ladder in `EVIDENCE_MATRIX.md` is `Draft → Candidate → Defined → Validated → ...`. ENT-010 already sits at `Candidate`. The next rung, `Defined`, is described as "Mathematically/formally defined (unambiguous)" — which the arithmetic explicitly is NOT (self-contradictory worked example). Recommendation: **do not move ENT-010 off `Candidate`** on the Status ladder; instead attach a qualifying sub-label at the Notes/description level ("Candidate — inputs and rule shape evidenced, arithmetic unverified"), exactly as proposed in Section 2's `DOMAIN_ARCHITECTURE.md`/`EVIDENCE_MATRIX.md` entries. This is a deliberately conservative recommendation given the ambiguity. | `docs/EVIDENCE_MATRIX.md` Status Policy (`Draft → Candidate → Defined → Validated...`, `Defined` = "unambiguous"); `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker" (arithmetic is not unambiguous). | Promoting to `Defined` would misrepresent the policy's own bar. Leaving completely unchanged would under-communicate the real 5.0B findings — the proposed middle path (qualifying label, same rung) is the balance struck here; a reviewer could reasonably disagree and keep it purely at plain "Candidate" with only the Notes-cell change from Section 2. |
| **Weekly Future — Related Rule(s) / consumption edge** | `none` (`TRACEABILITY_MATRIX.md` ENT-010 row) | `STRIKE-001 (consumed by, unverified)` | `RULE_DEPENDENCY_GRAPH.md` STRIKE-001 "Consumes" field. | Same qualifier-dependency risk as above. |
| **STRIKE-001 Evidence Count** | `2` (`EVIDENCE_MATRIX.md`, `TRADINGVIEW_STRATEGY_BIBLE.md`, `RULE_INDEX.md`) | **No promotion — explicitly recommended to stay at 2.** Not a promotion candidate at all; listed here specifically to state the negative conclusion inline with the other promotion decisions, so a reader scanning this section sees the "no" as clearly as the "yes"es. | `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Independent Sources: No." | See Section 4 for full reasoning — this is the single highest-risk mistake this proposal is trying to prevent. |
| **STRIKE-001 Confidence Level** | `Medium` | No change — `Medium` is the policy-correct value for Evidence Count 2 per `EVIDENCE_MATRIX.md`'s Confidence Policy table (2 → Medium), and Evidence Count is not proposed to change (see above). | `docs/EVIDENCE_MATRIX.md` Confidence Policy table. | None — this follows mechanically once Evidence Count is correctly held at 2. |
| **STRIKE-001 Rule Status** | `Draft` | No change proposed — remains `Draft`. `Under Review` would be a defensible alternative reading ("being actively cross-checked against additional evidence" per `RULE_INDEX.md`'s own Status definitions, which does describe what Milestones 5.0/5.0A/5.0B did), but this proposal recommends against it: `Under Review` in `RULE_INDEX.md`'s lifecycle sits above `Draft`, and moving it would need to be paired with a clear statement of what completes the review — which hasn't happened (the Weekly Future arithmetic is still unresolved). Recommend leaving at `Draft` until that resolves, rather than using `Under Review` as a halfway status that could get stuck there indefinitely. | `docs/RULE_INDEX.md` Status values table; `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`. | This is a genuine judgment call flagged as such — a reasonable reviewer could choose `Under Review` instead. Stated here as ambiguous rather than asserting false certainty either way. |
| **Terminology additions** | Weekly Future, Top Strike, Bottom Strike not defined | Add all three (Weekly Future as primary entry, Top/Bottom Strike as sub-definitions or minimal entries) at `Status: Partial` | `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Repeated Terminology" section. | Low — see Section 2 detail. |
| **New Evidence IDs** | Last used: `EVID-007` | Add `EVID-008` (STRIKE_EVIDENCE_TABLE.md catalogue), `EVID-009` (WEEKLY_FUTURE_EVIDENCE_TABLE.md catalogue) | Existing ID convention in `TRACEABILITY_MATRIX.md`. | Must be clearly marked as detailing/refining EVID-007, not adding independent-source count — see Section 2. |

---

## Section 4: Changes that should NOT be made

1. **Do NOT promote STRIKE-001 to `Validated` or bump its Confidence to
   `High`/`Confirmed`.** The Weekly Future arithmetic it now depends on
   is self-contradictory in the transcript's own worked example: a
   subtraction that is self-corrected on-camera (91 → 81), a jump from a
   stated "difference = 18" straight to a final answer of "268" with no
   shown intermediate step, two different numbers ("268" and "26168")
   given for what is described as the same Low value, and — most
   tellingly — a computed Low that ends up numerically *above* the
   computed High for the same candle, which is structurally impossible
   for a genuine High/Low pair and is never flagged as an error by the
   speaker. `Validated` in `EVIDENCE_MATRIX.md`'s Status Policy means
   "confirmed consistent across sufficient independent evidence" — the
   opposite of what's been found. *(Cite:
   `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`, "Root
   blocker, stated plainly," items 1-3; "Blocking issue #1/#2/#3" under
   "Weekly Future Low requires.")*

2. **Do NOT bump STRIKE-001's Evidence Count from 2 to 14** as if each
   of the 14 within-transcript occurrences were an independent source.
   `EVIDENCE_MATRIX.md`'s own Confidence Policy is explicit: "Evidence
   Count... means the number of independent evidence sources... not the
   number of other artifacts that reference this one. An artifact cited
   by four different rules but ultimately traceable to a single
   conversational statement still has Evidence Count = 1." All 14
   occurrences come from the single TR-001 file, single speaker, single
   channel, single teaching methodology — `STRIKE_EVIDENCE_SUMMARY.md`
   states this outright under "Independent Sources": "**No — this is
   not independent evidence.**" Recurrence within one source
   strengthens confidence *qualitatively* (it shows the speaker is
   consistent, not improvising) but is explicitly defined out of the
   Evidence Count metric by this repository's own policy. *(Cite:
   `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Independent Sources"
   section; `docs/EVIDENCE_MATRIX.md` Confidence Policy paragraph.)*

3. **Do NOT mark ENT-010 (Weekly Future) as `Confirmed`, or move it past
   `Candidate` on the Status ladder to `Defined`.** `Defined` in
   `EVIDENCE_MATRIX.md`'s Status Policy specifically means
   "Mathematically/formally defined (unambiguous)" — the arithmetic is
   the opposite of unambiguous (see item 1 above). The *shape* of the
   rule is now stated in natural language, but the actual numeric
   derivation is not verified even once cleanly in the source material.
   *(Cite: `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
   whole document; `docs/EVIDENCE_MATRIX.md` Status Policy table.)*

4. **Do NOT resolve TREND-001/002/003, OPPONENT-001/002/003, or
   REVERSAL-001's Mathematical Definition status.** Verified directly
   against `research/analysis/RULE_DEPENDENCY_GRAPH.md`'s per-rule
   detail sections: TREND-002, TREND-003, OPPONENT-001, OPPONENT-002,
   OPPONENT-003 each explicitly state "Consistent — no discrepancy
   found" or "No evidenced dependency found," with an explicit note that
   neither `STRIKE_EVIDENCE_TABLE.md`/`STRIKE_EVIDENCE_SUMMARY.md` nor
   `WEEKLY_FUTURE_EVIDENCE_TABLE.md`/`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
   discusses these rules at all. REVERSAL-001's detail section is
   explicit: "No evidenced dependency found in the STRIKE/WEEKLY_FUTURE
   evidence docs (they do not discuss REVERSAL-001) ... which specific
   premium behaviour constitutes identification is not established
   anywhere." None of Milestones 5.0/5.0A/5.0B/5.1 produced new evidence
   for these rules; they are out of scope for this proposal entirely.
   *(Cite: `research/analysis/RULE_DEPENDENCY_GRAPH.md` per-rule detail
   sections for TREND-001/002/003, OPPONENT-001/002/003, REVERSAL-001.)*

5. **Do NOT change SM-001 (`STRIKE_SELECTED`)'s Entry Conditions from
   `UNKNOWN` to any resolved value.** The new evidence answers *what
   value* strike selection computes (Weekly Future first-candle
   High/Low → nearest strike), not *at what precise instant* the
   STRIKE_SELECTED state is entered (candle close vs. some other trigger
   — the original open question in `STATE_MACHINE.md`). Neither
   `STRIKE_EVIDENCE_TABLE.md`/`STRIKE_EVIDENCE_SUMMARY.md` nor
   `WEEKLY_FUTURE_EVIDENCE_TABLE.md`/`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`
   contains language about a specific triggering instant — both are
   entirely about the value computation. *(Cite:
   `docs/STATE_MACHINE.md` lines 35-38; absence confirmed by reviewing
   `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` and
   `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` in full — neither addresses
   triggering timing.)*

6. **Do NOT populate `docs/MATHEMATICAL_SPECIFICATION.md`'s Level Capture
   section with the Weekly Future formula, even in "best effort" form.**
   The document's own admission bar ("No rule is formalised here until
   its status in RULE_INDEX.md is CONFIRMED") is not met by any rule,
   and even setting that bar aside, the specific arithmetic that would
   need to be formalized is the exact thing shown to be self-contradictory
   in item 1/3 above. Writing a "best guess" formula into a document
   whose stated purpose is "precise mathematical notation... no
   ambiguity" would misrepresent the document's own contents as more
   certain than the source material supports. *(Cite:
   `docs/MATHEMATICAL_SPECIFICATION.md` Status section;
   `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md`.)*

7. **Do NOT treat the Doji-candle exception (row 13 of
   `STRIKE_EVIDENCE_TABLE.md` — "when the first candle is directionless,
   defer top/bottom choice to the second candle") as a confirmed general
   rule anywhere in the ledger.** `STRIKE_EVIDENCE_SUMMARY.md`'s own
   "Remaining Unknowns" section flags this explicitly: it "appears once,
   clearly stated, but only once" and "is not independently corroborated
   elsewhere in the file." No proposed change above elevates this beyond
   a documented edge case. *(Cite:
   `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Remaining Unknowns"
   section, second bullet.)*

8. **Do NOT treat the bullish→bottom/bearish→top directional pairing as
   an unconditional formula.** Even though it now recurs in 7 of 14 rows
   (up from 4 of 8 in the partial review), `STRIKE_EVIDENCE_SUMMARY.md`
   itself quotes the speaker's own disclaimer against this: *"நம்ம எங்க
   இருந்து ஸ்டார்ட் பண்ணனும்ன்றது வந்து ரூல் கிடையாது"* ("there is no
   rule for where we start from"). Any ledger update should preserve
   this as a heuristic-with-explicit-speaker-caveat, not a hard rule.
   *(Cite: `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Conflicts"
   item 1.)*

9. **Do NOT resolve the "50-point vs. general nearest-strike rounding"
   question by hardcoding 50 points anywhere.**
   `STRIKE_EVIDENCE_SUMMARY.md`'s "Mathematical Clues" item 3 explicitly
   resolves this the other way — 50 was NIFTY's own strike interval in
   the specific examples, and the actual stated rule is "round to
   nearest listed strike," confirmed with a different 100-point interval
   in two other rows. No proposed change above should imply a fixed
   50-point constant. (This is a "watch for" item rather than a
   currently-present discrepancy — no ledger document currently
   hardcodes 50 points, so nothing needs to change here, but it's worth
   naming as a mistake to avoid when any of the above proposals are
   eventually implemented.) *(Cite:
   `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` "Mathematical Clues"
   item 3.)*

10. **Do NOT populate `docs/GAP_ANALYSIS.md`.** Its own stated
    precondition (rules reaching `FORMALISED`/comparable status) is not
    met by any rule, and none of Milestones 5.0-5.1 changed any rule's
    lifecycle Status field — they added dependency and terminology depth,
    not implementation-readiness. *(Cite: `docs/GAP_ANALYSIS.md`
    "Status" and "Traceability" sections; confirmed no Status field
    changes are proposed anywhere in Section 2/3 above.)*

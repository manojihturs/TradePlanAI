# Rule Dependency Graph

Evidence-only synthesis. Every cell below cites the specific source
document that supports it. Where two sources disagree (the RULE_INDEX.md
ledger vs. the newer STRIKE/WEEKLY_FUTURE evidence-acquisition milestones),
both are stated and the conflict is flagged explicitly rather than
silently resolved. No dependency is asserted without a citation.

## Summary Table

| Rule ID | Depends On (ledger) | Depends On (deeper evidence) | Produces | Consumes | Requires (precondition) | Blocks | Blocked By |
|---|---|---|---|---|---|---|---|
| STRIKE-001 | `none yet` (`docs/RULE_INDEX.md` row 30; `TRADINGVIEW_STRATEGY_BIBLE.md` line 105) | Weekly Future first-candle High/Low (Call+Put option OHLC + ATM strike) — `research/analysis/STRIKE_EVIDENCE_SUMMARY.md` §"Repeated Behaviour"/"Mathematical Clues" item 1; `research/analysis/STRIKE_EVIDENCE_TABLE.md` rows 8, 10, 11, 12, 14; `research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` | Strike (ENT-001) selection | First Candle (ENT-002, itself resolved to be the Weekly Future's first candle per STRIKE_EVIDENCE_SUMMARY.md item "Repeated Behaviour") | STATE: STRIKE_SELECTED is the state this rule's evaluation establishes (`docs/STATE_MACHINE.md` lines 28-33); entry condition into that state is itself `UNKNOWN` | TREND_TRACKING and OPPONENT_ENGAGEMENT states, "presumably" (`docs/STATE_MACHINE.md` lines 44-47, not confirmed) | Weekly Future High/Low arithmetic is not clean/verifiable (`research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root blocker" §1-3); Mathematical Definition: Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 99) |
| TREND-001 | `none yet` (`docs/RULE_INDEX.md` row 31) | No evidenced dependency found beyond a Strike having been selected (implicit; not stated as a formal "Depends On" anywhere) | TrendPoint / TP Low (ENT-003) per Strike | Strike (ENT-001) — "every analysed strike maintains..." (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 117-118) | STATE: TREND_TRACKING, entry conditions `UNKNOWN` (`docs/STATE_MACHINE.md` lines 56-68) | TREND-002, TREND-003, OPPONENT-001 (`docs/RULE_INDEX.md` row 31, "Referenced By") | Mathematical Definition: Partially Known (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 131) — the formula producing a TrendPoint value is not evidenced (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 82-88) |
| TREND-002 | TREND-001 (`docs/RULE_INDEX.md` row 32; `docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 165) | Consistent — no discrepancy found; no deeper evidence doc (STRIKE_EVIDENCE_*/WEEKLY_FUTURE_*) addresses TREND-002 at all | Updated TP Low value ("converts to a new value") | TrendPoint (ENT-003), "Market Structure" change signal (ENT-004) | Trigger = "market structure changes" — trigger condition itself `UNKNOWN` (`docs/DOMAIN_MODEL.md` lines 93-95; `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 150-154) | `none yet` (`docs/RULE_INDEX.md` row 32, "Referenced By") | Mathematical Definition: Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 159); "what constitutes market structure" and "what counts as a change" both Unknown (`docs/DOMAIN_MODEL.md` lines 93-95) |
| TREND-003 | TREND-001, OPPONENT-001 (`docs/RULE_INDEX.md` row 33; `docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 194) | Consistent — no discrepancy found | Edge condition evaluation (not a stored entity — `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 194-213) | Current Strike's TrendPoint + Opponent's TrendPoint (`docs/DOMAIN_MODEL.md` lines 75-76) | No dedicated state; evaluated as a condition over two TrendPoints, not a state transition (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 202-209) | `none yet` (`docs/RULE_INDEX.md` row 33, "Referenced By") | Mathematical Definition: Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 188); "well below" not quantified (`docs/TERMINOLOGY.md` lines 112-113); depends transitively on TREND-001's own Unknown/Partially-Known math and on OPPONENT-001's Unknown "defeat" definition |
| OPPONENT-001 | TREND-001, OPPONENT-002, OPPONENT-003 (`docs/RULE_INDEX.md` row 34; `docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 241) | Consistent — no discrepancy found | "Defeated" opponent outcome, enabling Strike progression | Opponent (ENT-005), Opponent's TrendPoint, Opponent High/Low (ENT-006/007) | STATE: OPPONENT_ENGAGEMENT, entry conditions `UNKNOWN`; exit possibly "opponent defeated" but "defeating" not mathematically defined (`docs/STATE_MACHINE.md` lines 85-99) | TREND-003 (`docs/RULE_INDEX.md` row 34, "Referenced By") | Mathematical Definition: Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 235); "defeat" condition is an unresolved Open Question (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 344-350; `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 114-118); also blocked by OPPONENT-002/003 both being Awaiting Evidence, Evidence Count 0 |
| OPPONENT-002 | `none yet` (`docs/RULE_INDEX.md` row 35) | No evidenced dependency found | Opponent High value (ENT-006) — placeholder, no computation defined (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 122-138) | None evidenced | None evidenced | OPPONENT-001 (`docs/RULE_INDEX.md` row 35, "Referenced By") | Status: Awaiting Evidence, Evidence Count 0 (`docs/RULE_INDEX.md` row 35); "no behaviour defined" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 244-248); TR-001 did not define it (`docs/RULE_INDEX.md` lines 45-47) |
| OPPONENT-003 | `none yet` (`docs/RULE_INDEX.md` row 36) | No evidenced dependency found | Opponent Low value (ENT-007) — placeholder, no computation defined (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 122-138) | None evidenced | None evidenced | OPPONENT-001 (`docs/RULE_INDEX.md` row 36, "Referenced By") | Status: Awaiting Evidence, Evidence Count 0 (`docs/RULE_INDEX.md` row 36); "no behaviour defined" (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 250-254); TR-001 did not define it |
| REVERSAL-001 | `none yet` (`docs/RULE_INDEX.md` row 37; `docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 292) | No evidenced dependency found in STRIKE/WEEKLY_FUTURE docs (they do not discuss REVERSAL-001) | Reversal (ENT-008) identification | Premium (ENT-009) behaviour | STATE: REVERSAL_IDENTIFIED; the one confirmed "Impossible Transition" in the whole project — no direct assumption-based entry (`docs/STATE_MACHINE.md` lines 140-166) | `none yet` (`docs/RULE_INDEX.md` row 37, "Referenced By") | Mathematical Definition: Unknown (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 286); "which specific premium behaviour constitutes identification is not established" (`docs/DOMAIN_MODEL.md` lines 168-171; `docs/STATE_MACHINE.md` lines 148-150) |

## Discrepancy flagged: STRIKE-001's "Depends On"

`docs/RULE_INDEX.md` (row 30) and `docs/TRADINGVIEW_STRATEGY_BIBLE.md`
(line 105) both record STRIKE-001's `Depends On` as **"none yet"** —
this is the ledger's own recorded value and it has not been edited by
this document. However, the later, more detailed evidence-acquisition
work in `research/analysis/STRIKE_EVIDENCE_TABLE.md` and
`research/analysis/STRIKE_EVIDENCE_SUMMARY.md` (Milestone 5.0A) and
`research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md` /
`WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` (Milestone 5.0B) establish, from
direct transcript quotes, that STRIKE-001's strike-selection mechanism
is in fact anchored to a **Weekly Future first-candle High/Low**
(itself computed from Call-option and Put-option first-candle
High/Low/Close data plus the day's ATM strike), rounded to the nearest
listed strike (`STRIKE_EVIDENCE_SUMMARY.md` §"Mathematical Clues" item
1; `STRIKE_EVIDENCE_TABLE.md` rows 10, 11, 12, 14 — e.g. row 10's
direct quote: "our strike price always starts based on the Future...
the Future's high and low [are] the candle's high and low").

This is a **documentation-lag discrepancy**, not a contradiction to be
silently resolved: `docs/RULE_INDEX.md` and the Bible predate the 5.0A/
5.0B evidence-acquisition milestones and have not yet been updated to
reflect the newly-evidenced dependency. As instructed, this document
does not overwrite `docs/RULE_INDEX.md`'s recorded "none yet" — it
records both values side by side in the Summary Table above (ledger
column vs. deeper-evidence column) and flags the gap here for whoever
next updates the ledger.

## Per-Rule Detail

### STRIKE-001 — Initial Strike Selection
- **Depends On (ledger):** none yet — `docs/RULE_INDEX.md` row 30.
- **Depends On (deeper evidence):** Weekly Future first-candle
  High/Low — `research/analysis/STRIKE_EVIDENCE_TABLE.md` row 8
  ("speaker describes computing a synthetic Weekly Future High/Low
  from the first candle's Call option High/Low and Put option
  High/Low"), row 10 ("our strike price always starts based on the
  Future"), row 11 (explicit "formula": Weekly Future first-5-minute
  High/Low → nearest strike = Top/Bottom Strike), row 14 (proves
  "first candle" always means the computed Weekly-Future candle, not
  raw spot). See discrepancy note above.
- **Produces:** Strike (ENT-001) — `docs/architecture/DOMAIN_ARCHITECTURE.md`
  lines 29-49.
- **Consumes:** First Candle (ENT-002) — `docs/DOMAIN_MODEL.md` lines
  47-60 — which the deeper evidence resolves to mean the Weekly
  Future's first candle specifically, per STRIKE_EVIDENCE_SUMMARY.md
  Conflicts item 2.
- **Requires:** No stated precondition beyond the first candle having
  formed; establishes STATE: STRIKE_SELECTED, "the earliest state
  implied by any current rule" (`docs/STATE_MACHINE.md` lines 28-33),
  itself with `UNKNOWN` entry conditions.
- **Blocks:** TREND_TRACKING, OPPONENT_ENGAGEMENT — "presumably," not
  confirmed by direct statement about ordering (`docs/STATE_MACHINE.md`
  lines 44-47).
- **Blocked By:** The Weekly Future High/Low arithmetic is not clean
  or internally consistent in the only available source
  (`research/analysis/WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` "Root
  blocker" section, items 1-3: self-corrected numbers, an unexplained
  jump from "difference=18" to "answer=268," two different Low values
  given for the same computation, and a Low that ends up numerically
  above the High). The transcript twice points to an external, absent
  "Complete Calculation Video for Weekly Future" as the authoritative
  source (`WEEKLY_FUTURE_EVIDENCE_TABLE.md` rows WF-4/WF-6). Bible's
  own Mathematical Definition field for STRIKE-001 reads Unknown
  (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 99).

### TREND-001 — Trend Point Low (TP Low)
- **Depends On (ledger):** none yet — `docs/RULE_INDEX.md` row 31.
- **Depends On (deeper evidence):** No evidenced dependency found in
  the STRIKE/WEEKLY_FUTURE evidence docs (they do not discuss
  TREND-001). Only an implicit dependency on a Strike having been
  selected, per the entity relationship in `docs/DOMAIN_MODEL.md`
  lines 72-73 ("belongs to a specific strike") — not a formal rule
  dependency statement.
- **Produces:** TrendPoint / TP Low value per Strike (ENT-003).
- **Consumes:** Strike (ENT-001).
- **Requires:** STATE: TREND_TRACKING, entry/exit conditions both
  `UNKNOWN — insufficient evidence` (`docs/STATE_MACHINE.md` lines
  66-70).
- **Blocks:** TREND-002, TREND-003, OPPONENT-001 — `docs/RULE_INDEX.md`
  row 31, "Referenced By" column.
- **Blocked By:** Mathematical Definition: Partially Known
  (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 131) — the architecture
  explicitly represents TrendPoint as "a value that can be read and
  (separately) updated, without designing the update algorithm itself"
  because neither the value formula nor the update trigger is
  evidenced (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 82-88).

### TREND-002 — Dynamic TP Low Adjustment
- **Depends On (ledger):** TREND-001 — `docs/RULE_INDEX.md` row 32;
  `docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 165.
- **Depends On (deeper evidence):** Consistent with the ledger; no
  discrepancy found. No STRIKE/WEEKLY_FUTURE evidence doc addresses
  TREND-002.
- **Produces:** An updated TP Low value when triggered.
- **Consumes:** TrendPoint (ENT-003), Market Structure change signal
  (ENT-004).
- **Requires:** Trigger = "market structure changes" — per
  `docs/DOMAIN_MODEL.md` lines 86-100, what constitutes "market
  structure" and what counts as a "change" to it are both `Unknown`.
- **Blocks:** none yet — `docs/RULE_INDEX.md` row 32, "Referenced By."
- **Blocked By:** Mathematical Definition: Unknown
  (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 159); the trigger
  condition itself is Unknown (`docs/architecture/DOMAIN_ARCHITECTURE.md`
  lines 150-154, "represented architecturally as an abstract 'change
  signal' ... without defining what that signal actually detects").

### TREND-003 — Edge Detection
- **Depends On (ledger):** TREND-001, OPPONENT-001 —
  `docs/RULE_INDEX.md` row 33; `docs/TRADINGVIEW_STRATEGY_BIBLE.md`
  line 194.
- **Depends On (deeper evidence):** Consistent with the ledger; no
  discrepancy found.
- **Produces:** An "Edge" condition evaluation — explicitly modeled as
  a condition, not a stored entity (`docs/architecture/DOMAIN_ARCHITECTURE.md`
  lines 194-213).
- **Consumes:** Current Strike's TrendPoint and Opponent's TrendPoint
  (`docs/DOMAIN_MODEL.md` lines 75-76, TREND-003 "implying an Opponent
  entity also has its own TP Low").
- **Requires:** No dedicated state per `docs/STATE_MACHINE.md`;
  `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 202-209 treats it
  purely as a comparison evaluated over two TrendPoints.
- **Blocks:** none yet — `docs/RULE_INDEX.md` row 33, "Referenced By."
- **Blocked By:** Mathematical Definition: Unknown
  (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 188); "well below" has no
  quantified threshold (`docs/TERMINOLOGY.md` lines 112-113,
  `docs/architecture/DOMAIN_ARCHITECTURE.md` lines 210-213); also
  transitively blocked since it depends on TREND-001 (Partially Known)
  and OPPONENT-001 (Unknown, itself blocked by OPPONENT-002/003).

### OPPONENT-001 — Next Opponent Defeat
- **Depends On (ledger):** TREND-001, OPPONENT-002, OPPONENT-003 —
  `docs/RULE_INDEX.md` row 34; `docs/TRADINGVIEW_STRATEGY_BIBLE.md`
  line 241.
- **Depends On (deeper evidence):** Consistent with the ledger; no
  discrepancy found. Neither STRIKE_EVIDENCE_* nor WEEKLY_FUTURE_*
  discusses OPPONENT-001.
- **Produces:** A "defeated" outcome enabling Strike progression.
- **Consumes:** Opponent (ENT-005), the Opponent's own TrendPoint,
  Opponent High/Low (ENT-006/007) as dependencies
  (`docs/DOMAIN_MODEL.md` lines 111-119).
- **Requires:** STATE: OPPONENT_ENGAGEMENT, entry conditions `UNKNOWN`;
  possible exit = "opponent defeated" but "defeating" not
  mathematically defined (`docs/STATE_MACHINE.md` lines 85-99).
- **Blocks:** TREND-003 — `docs/RULE_INDEX.md` row 34, "Referenced By."
- **Blocked By:** Mathematical Definition: Unknown
  (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 235); the "defeat"
  condition is an explicit unresolved Open Question
  (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` lines 344-350); further
  blocked by its own declared dependencies OPPONENT-002 and
  OPPONENT-003, both Awaiting Evidence with Evidence Count 0
  (`docs/RULE_INDEX.md` rows 35-36).

### OPPONENT-002 — Opponent High (placeholder)
- **Depends On (ledger):** none yet — `docs/RULE_INDEX.md` row 35.
- **Depends On (deeper evidence):** No evidenced dependency found.
- **Produces:** Opponent High value (ENT-006) — reserved attribute
  slot only, "no defined computation" (`docs/architecture/DOMAIN_ARCHITECTURE.md`
  lines 122-138).
- **Consumes:** None evidenced.
- **Requires:** None evidenced.
- **Blocks:** OPPONENT-001 — `docs/RULE_INDEX.md` row 35, "Referenced
  By"; also the Rule Engine architecture registers it as "registered
  but inactive," never invoked (`docs/architecture/RULE_ENGINE_ARCHITECTURE.md`
  lines 49-55).
- **Blocked By:** Status: Awaiting Evidence, Evidence Count 0
  (`docs/RULE_INDEX.md` row 35); TR-001 did not define it
  (`docs/RULE_INDEX.md` lines 45-47).

### OPPONENT-003 — Opponent Low (placeholder)
- **Depends On (ledger):** none yet — `docs/RULE_INDEX.md` row 36.
- **Depends On (deeper evidence):** No evidenced dependency found.
- **Produces:** Opponent Low value (ENT-007) — reserved attribute slot
  only (`docs/architecture/DOMAIN_ARCHITECTURE.md` lines 122-138).
- **Consumes:** None evidenced.
- **Requires:** None evidenced.
- **Blocks:** OPPONENT-001 — `docs/RULE_INDEX.md` row 36, "Referenced
  By."
- **Blocked By:** Status: Awaiting Evidence, Evidence Count 0
  (`docs/RULE_INDEX.md` row 36); TR-001 did not define it.

### REVERSAL-001 — Reversal Identification
- **Depends On (ledger):** none yet — `docs/RULE_INDEX.md` row 37;
  `docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 292.
- **Depends On (deeper evidence):** No evidenced dependency found —
  neither STRIKE_EVIDENCE_* nor WEEKLY_FUTURE_* discusses REVERSAL-001
  or Premium/Reversal at all.
- **Produces:** Reversal (ENT-008) identification.
- **Consumes:** Premium (ENT-009) behaviour (`docs/DOMAIN_MODEL.md`
  lines 168-171).
- **Requires:** STATE: REVERSAL_IDENTIFIED. This is the one state in
  the whole project with a confirmed "Impossible Transition": no
  direct assumption-based entry (`docs/STATE_MACHINE.md` lines
  158-163) — evidenced by REVERSAL-001's own wording, "not assumed...
  must be identified through premium behaviour."
- **Blocks:** none yet — `docs/RULE_INDEX.md` row 37, "Referenced By."
- **Blocked By:** Mathematical Definition: Unknown
  (`docs/TRADINGVIEW_STRATEGY_BIBLE.md` line 286); which specific
  premium behaviour constitutes identification is not established
  anywhere (`docs/DOMAIN_MODEL.md` lines 168-171; `docs/STATE_MACHINE.md`
  lines 148-150, all entry conditions marked `UNKNOWN`).

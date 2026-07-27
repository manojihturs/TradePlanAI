# Rule Index

Master index of every individual business rule recovered during this
reconstruction effort. One row per rule. This is the flat,
cross-referenced ledger that `TRADINGVIEW_STRATEGY_BIBLE.md` narrates
and `MATHEMATICAL_SPECIFICATION.md` formalises - every rule that
appears in either of those documents must have a corresponding row
here, and vice versa.

## Rule ID convention

`<CATEGORY>-<NNN>`, numbered sequentially per category (not globally).
See `TRADINGVIEW_STRATEGY_BIBLE.md` for the fixed category taxonomy
and the full per-rule lifecycle template.

## Status values (rule lifecycle)

| Status | Meaning |
|---|---|
| `Awaiting Evidence` | Placeholder only - referenced as a dependency by another rule, but no evidence yet defines its own behaviour |
| `Draft` | Recorded from evidence, not yet cross-checked or reviewed |
| `Under Review` | Being actively cross-checked against additional evidence |
| `Validated` | Confirmed consistent across sufficient independent evidence |
| `Superseded` | Replaced by a later, corrected rule ID - kept for history, not deleted |

## Index

| Rule ID | Short description | Category | Status | Confidence | Evidence Count | Depends On | Referenced By |
|---|---|---|---|---|---|---|---|
| STRIKE-001 | Initial strike selection is based on the first candle | STRIKE | Draft | Medium | 2 | none yet | none yet |
| TREND-001 | Every analysed strike maintains a dynamically-updated Trend Point Low | TREND | Draft | Medium | 2 | none yet | TREND-002, TREND-003, OPPONENT-001 |
| TREND-002 | TP Low is not static - converts to a new value when market structure changes | TREND | Draft | Medium | 2 | TREND-001 | none yet |
| TREND-003 | Both current and opponent TP Lows staying well below the strike reduces probability of price moving below it | TREND | Draft | Medium | 2 | TREND-001, OPPONENT-001 | none yet |
| OPPONENT-001 | A strike progresses only after defeating the next opponent | OPPONENT | Draft | Medium | 2 | TREND-001, OPPONENT-002, OPPONENT-003 | TREND-003 |
| OPPONENT-002 | Opponent High (placeholder - no behaviour defined) | OPPONENT | Awaiting Evidence | - | 0 | none yet | OPPONENT-001 |
| OPPONENT-003 | Opponent Low (placeholder - no behaviour defined) | OPPONENT | Awaiting Evidence | - | 0 | none yet | OPPONENT-001 |
| REVERSAL-001 | A reversal must be identified through premium behaviour, never assumed | REVERSAL | Draft | Medium | 2 | none yet | none yet |

## Notes

**Updated (Milestone 3.2):** STRIKE-001, TREND-001, TREND-002,
TREND-003, OPPONENT-001, and REVERSAL-001 now have Evidence Count = 2
(original statement + TR-001 transcript, see
`research/analysis/TR-001_ANALYSIS.md`) and Confidence = Medium, per
the Confidence Policy in `docs/EVIDENCE_MATRIX.md`. OPPONENT-002 and
OPPONENT-003 remain unchanged (0 evidence, Awaiting Evidence) - TR-001
did not define them. Update Evidence Count and Status together as
additional independent sources are added for each rule; do not
increase Status without a corresponding increase in Evidence Count or
explicit confirmation.

Old rule IDs from before the Analysis Version 2 refactor
(`RULE-STRIKE-001`, `RULE-TP-001`, `RULE-DYN-001`, `RULE-EDGE-001`,
`RULE-OPP-002`, `RULE-REV-001`) are retired - see the Refactor Note at
the bottom of `TRADINGVIEW_STRATEGY_BIBLE.md` for the old-ID -> new-ID
mapping.

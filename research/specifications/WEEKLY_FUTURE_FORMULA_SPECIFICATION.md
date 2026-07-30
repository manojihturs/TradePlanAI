# Weekly Future Formula Specification

**Version:** 1.0
**Status:** AUTHORITATIVE for Weekly Future High/Low and Top/Bottom Strike Selection. Supersedes `research/transcripts/TR-001.md` for these two rules specifically — see §10.
**Source:** Product Owner (User), supplied directly in chat, 2026-07-30. Raw intake record: `research/incoming/weekly_future_formula_2026-07-30.md`. Verified against 3 independent worked examples (§9), zero contradictions.

---

## 1. Inputs

| Input | Description |
|---|---|
| Reference Candle | The first 5-minute candle of the trading day (09:15–09:20) — consistent with Specification Rule 1, already CONFIRMED elsewhere in this project |
| Strike Price (anchor) | The at-the-money-ish strike used as the calculation base — labeled "Today open Approx" in the source data. **UNRESOLVED – Awaiting Strategy Evidence:** the exact rule for selecting this anchor strike (vs. the ATM-selection rule referenced generally in `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §5) is not given by this evidence — the worked examples supply it as a given, not as something computed |
| Call Premium OHLC (first 5-min) | `CE High`, `CE Low` |
| Put Premium OHLC (first 5-min) | `PE High`, `PE Low` |
| Instrument / Expiry | **UNRESOLVED – Awaiting Strategy Evidence** — not stated in this data; strike magnitudes (~24000) are consistent with prior assumptions elsewhere in this project but not confirmed here |

---

## 2. Weekly Future High Formula

**Formula:**

```
Weekly Future High = Strike + (CE High(1st 5-min) − PE Low(1st 5-min))
```

**Step-by-step:**
1. Take the anchor Strike Price.
2. Take the Call option's first-5-minute-candle High.
3. Take the Put option's first-5-minute-candle Low.
4. Compute `CE High − PE Low`.
5. Add that difference to the Strike.

**Example (29-07-2026):** Strike = 24200, CE High = 143.45, PE Low = 128 → `143.45 − 128 = 15.45` → `24200 + 15.45 = 24215.45`.

**Verified:** matches all 3 independent worked examples exactly — see `research/specifications/WEEKLY_FUTURE_CALCULATION_EXAMPLES.md`.

---

## 3. Weekly Future Low Formula

**Formula:**

```
Weekly Future Low = Strike − (PE High(1st 5-min) − CE Low(1st 5-min))
```

**Step-by-step:**
1. Take the anchor Strike Price.
2. Take the Put option's first-5-minute-candle High.
3. Take the Call option's first-5-minute-candle Low.
4. Compute `PE High − CE Low`.
5. Subtract that difference from the Strike.

**Example (29-07-2026):** Strike = 24200, PE High = 165.8, CE Low = 116 → `165.8 − 116 = 49.8` → `24200 − 49.8 = 24150.2`.

**Verified:** matches all 3 independent worked examples exactly.

**Note on the sign-flip question that made `TR-001.md`'s worked example self-contradictory:** this formula is a single, uniform signed subtraction (`Strike − (PE High − CE Low)`), with no separate case needed for which value is larger. In the 28-07-2026 example, `PE High (136.65) < CE Low (180.95)`, making `(PE High − CE Low)` negative — the formula handles this automatically (`24000 − (−44.3) = 24044.3`) without any special-case logic. This resolves the ambiguity `WEEKLY_FUTURE_DEPENDENCY_ANALYSIS.md` flagged about needing a general rule covering all orderings — there is no separate ordering rule; it is one formula.

---

## 4. Top Strike Selection

**Rule:** `Top Strike = round(Weekly Future High / 50) * 50` (nearest multiple of 50).

**Conditions:** None beyond the rounding itself, per this evidence. **UNRESOLVED – Awaiting Strategy Evidence:** tie-breaking behavior exactly at the midpoint between two multiples of 50 (e.g. a value ending in .00 exactly 25 above/below) is not demonstrated in any of the 3 examples.

**Example (29-07-2026):** Weekly Future High = 24215.45 → nearest 50 → Top Strike = 24200.

**Verified:** matches all 3 examples exactly (`round(24215.45/50)*50=24200`; `round(24110.25/50)*50=24100`; `round(23985.70/50)*50=24000`).

---

## 5. Bottom Strike Selection

**Rule:** `Bottom Strike = round(Weekly Future Low / 50) * 50` (nearest multiple of 50).

**Conditions:** Same as §4.

**Example (29-07-2026):** Weekly Future Low = 24150.2 → nearest 50 → Bottom Strike = 24150.

**Verified:** matches all 3 examples exactly (`round(24150.2/50)*50=24150`; `round(24044.3/50)*50=24050`; `round(23924.9/50)*50=23900`).

---

## 6. Entry Rules

**UNRESOLVED – Awaiting Strategy Evidence.** Not supplied by this evidence source. Entry conditions (Buy CE when / Buy PE when / Avoid Trade when) remain governed by the already-CONFIRMED Winner Detection rule (`STRATEGY_FUNCTIONAL_SPECIFICATION.md` §9, Rule 3) — this data does not add or change anything there.

---

## 7. Exit Rules

**UNRESOLVED – Awaiting Strategy Evidence.** Stop Loss and Time Exit remain entirely unstated, matching the existing gap already recorded in `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §20 items 4 and 9–10. This data source does not address them.

---

## 8. Exceptions

**UNRESOLVED – Awaiting Strategy Evidence.** Holiday handling, Gap Up, Gap Down, and Invalid Data behavior are not addressed by this evidence source.

---

## 9. Worked Examples

All 3 dates supplied, fully verified — see `research/specifications/WEEKLY_FUTURE_CALCULATION_EXAMPLES.md` for full step-by-step arithmetic on each. Summary:

| Date | Strike | CE High | PE Low | Weekly Future High | Top Strike | PE High | CE Low | Weekly Future Low | Bottom Strike |
|---|---|---|---|---|---|---|---|---|---|
| 2026-07-29 | 24200 | 143.45 | 128 | 24215.45 | 24200 | 165.8 | 116 | 24150.2 | 24150 |
| 2026-07-28 | 24000 | 218 | 107.75 | 24110.25 | 24100 | 136.65 | 180.95 | 24044.3 | 24050 |
| 2026-07-27 | 23950 | 212.75 | 177.05 | 23985.7 | 24000 | 201.3 | 176.2 | 23924.9 | 23900 |

No "Trade Taken"/"Result" data was supplied alongside these examples — this data source addresses the Weekly Future and Strike Selection calculation only, not the full trade lifecycle.

---

## 10. Notes

- **Recalculation cadence:** all 3 examples compute exactly one Weekly Future High/Low pair per day, from the first 5-minute candle only. This is consistent with — but does not itself newly confirm beyond — the "once per session" interpretation already flagged as one of two open possibilities in `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §20 item 16. Still not an explicit statement either way; treated as supporting, not conclusive.
- **Relationship to `TR-001.md`:** `TR-001.md`'s own worked example (lines 2460–2521) is now understood differently in light of this formula. `TR-001.md` narrates `Strike + (Call-High − Put-Low)` for the High side too (matching this spec's §2 shape) — its actual failure was in the *live spoken arithmetic* (91→81→82, self-correction), not in the underlying rule shape. This specification's High/Low formulas are consistent with what `TR-001.md` was attempting to demonstrate; they are authoritative here because they are independently verified against clean, unambiguous data, not because the underlying rule shape changed.
- **`TR-001.md` reclassified:** per this session's decision, `TR-001.md` moves from "sole source, self-contradictory, blocking" to **historical/background evidence** — still useful for definitional context (e.g. "no official Weekly Future instrument exists," Rule WF-1) but no longer the source consulted for the numeric formula itself. See `research/evidence_log.md` for the logged reclassification.
- **Version history:** v1.0 — initial authoritative version, 2026-07-30, from Product Owner-supplied worked examples.

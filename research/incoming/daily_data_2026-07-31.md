# Daily Data — Product Owner-Supplied Worked Examples (docx, 2026-07-31)

**Source:** `Tradeplan Daily data.docx`, supplied by the Product Owner via chat. Contains a tabular dataset for 3 independent trading days (29-07-2026, 28-07-2026, 27-07-2026) plus 6 embedded TradingView screenshots. Screenshots copied unmodified into `research/incoming/daily_data_screenshots_2026-07-31/`.

**Status:** Real, dated, numeric evidence — the strongest data recorded for QUAL-007 so far. **Not yet fully reconciled** — one genuine numeric discrepancy was found between the docx table and a screenshot label (see below) and is recorded, not resolved, per `EVIDENCE_INTAKE_PROCESS.md`'s "don't pick a winner" rule for conflicting evidence.

---

## Extracted table (verbatim values, transcribed from the docx table)

### 29-07-2026

| | Strike Price (today open approx) | CE High (1st 5min) | PE Low (1st 5min) | FUT High | SP (selected strike) |
|---|---|---|---|---|---|
| Top | 24200 | 143.45 | 128 | 24215.45 | 24200 |

| | Strike Price (today open approx) | PE High (1st 5min) | CE Low (1st 5min) | FUT Low | SP (selected strike) |
|---|---|---|---|---|---|
| Bottom | 24200 | 165.8 | 116 | 24150.2 | 24150 |

### 28-07-2026

| | Strike Price (today open approx) | CE High (1st 5min) | PE Low (1st 5min) | FUT High | SP (selected strike) |
|---|---|---|---|---|---|
| Top | 24000 | 218 | 107.75 | 24110.25 | 24100 |

| | Strike Price (today open approx) | PE High (1st 5min) | CE Low (1st 5min) | FUT Low | SP (selected strike) |
|---|---|---|---|---|---|
| Bottom | 24000 | 136.65 | 180.95 | 24044.3 | 24050 |

### 27-07-2026

| | Strike Price (today open approx) | CE High (1st 5min) | PE Low (1st 5min) | FUT High | SP (selected strike) |
|---|---|---|---|---|---|
| Top | 23950 | 212.75 | 177.05 | 23985.7 | 24000 |

| | Strike Price (today open approx) | PE High (1st 5min) | CE Low (1st 5min) | FUT Low | SP (selected strike) |
|---|---|---|---|---|---|
| Bottom | 23950 | 201.3 | 176.2 | 23924.9 | 23900 |

---

## Cross-check against already-confirmed evidence

**Strong corroboration of the already-confirmed Weekly Future / Strike Selection formula.** For all 3 days, rounding `FUT High` to the nearest multiple of 50 produces exactly the stated Top Strike (SP), and rounding `FUT Low` produces exactly the stated Bottom Strike:

| Date | FUT High → nearest 50 | Stated Top (SP) | Match? | FUT Low → nearest 50 | Stated Bottom (SP) | Match? |
|---|---|---|---|---|---|---|
| 29-07-2026 | 24215.45 → 24200 | 24200 | ✅ | 24150.2 → 24150 | 24150 | ✅ |
| 28-07-2026 | 24110.25 → 24100 | 24100 | ✅ | 24044.3 → 24050 | 24050 | ✅ |
| 27-07-2026 | 23985.7 → 24000 | 24000 | ✅ | 23924.9 → 23900 | 23900 | ✅ |

This is **independent confirmation** of `research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` v1.0's already-accepted rounding rule, from a completely different data source (real Upstox/TradingView-observed data) than the original Product-Owner worked examples that first confirmed it. Strengthens, does not merely repeat, that existing acceptance.

**Confirms the General Rule Statement recorded in `qualification_session1_intake_2026-07-31.md`:** Top strike's own CE High + PE Low, Bottom strike's own PE High + CE Low, are exactly the fields captured here — consistent with "CE - Mark PE Low (Top)" / "PE - Mark CE High (Top)" / etc.

## Discrepancy — RESOLVED (2026-08-01, Product Owner confirmation)

Screenshot `daily_data_screenshots_2026-07-31/29-07-2026_bottom_24150.png` (docx `image2.png`) labels a horizontal reference line on the 24150 chart pair as **"24150PE (ATM) | High: ₹137.3"** and **"24150CE (ATM) | Low: ₹141"**, which did not match the docx table's Bottom row for 29-07-2026 (**PE High = 165.8**, **CE Low = 116**).

**Product Owner confirmed directly: "this is the right one first 5min high and low" — referring to 165.8/116.** The docx table's values are the correct first-5-minute PE High/CE Low for strike 24150 on 29-07-2026. This is also independently supported by `qualification_session1_intake_2026-07-31.md`'s Worked Example 2: the 29-July trade log uses **165.8 as an actual trade Entry price**, consistent with it being the real, tradeable reference level.

**The screenshot's 137.3/141 is not the first-5-minute band.** What it does represent is not fully settled — it may be a later intraday price snapshot, or (per Worked Example 2's own data) 137.3 specifically appears as that trade's **SL value**, which is a *different* marked level (S-1, per the already-confirmed `SL = S-1` rule) than the strike's own first-5-minute band — plausibly not an error at all, just a different, correctly-labeled level that isn't the one this document originally compared it against. Not confirmed as fact, but no longer an open contradiction requiring resolution — the reference-level question itself is closed.

**Do not use either the 165.8/116 pair or the 137.3/141 pair for strike 24150 until the Product Owner clarifies which one (if either) is the correct first-5-minute Bottom reading for 29-07-2026.**

## Additional observations from screenshots (not yet cross-checked into a rule)

- Screenshots show a wider ladder than the "6 ITM/6 OTM" description in the General Rule Statement — `28-07-2026_top_24100.png` shows 8 ITM + 4 OTM levels (12 + ATM = 13 total, but asymmetric 8/4 rather than 6/6). **Open question:** is the ladder always 13 levels with a fixed symmetric 6/6 split, or does it vary? Not enough evidence yet to say.
- Charts show **R1, R2, S1, S2, and a "P" label** drawn directly on specific levels, with Buy/Sell markers on candles. This appears to answer part of Open Question 2 from `qualification_session1_intake_2026-07-31.md` ("which of five roles does a level play") — R1/R2 = resistance levels above ATM, S1/S2 = support levels below, "P" = possibly Pivot, unconfirmed. **Still needed:** the exact rule for which specific level gets which label (R1 vs R2, etc.) — visually it looks like simple ordinal distance from the ATM level, but this is an inference from the screenshot, not a stated rule, and should not be treated as confirmed without asking directly.

---

## Toward the acceptance checklist

This submission, combined with `qualification_session1_intake_2026-07-31.md`'s existing content, now provides:
- **3 independent dated data points** (29/28/27 July 2026) for the Top/Bottom + CE/PE High/Low capture mechanic — clears the "≥3 worked examples" bar **for the reference-level capture rule specifically**.
- Still **0 complete "why did this trade qualify, what was the outcome" narratives** tied to these 3 dates — the docx supplies inputs (the ladder), not qualification decisions or trade outcomes for 28/27 July the way the 22 July example in `qualification_session1_intake_2026-07-31.md` did.
- The unresolved discrepancy above should be closed before treating strike 24150's Bottom values as reliable.

**Recommendation: still short of Evidence Complete for the full Qualification Engine**, but this is the closest this project has been. Next most useful ask: for 28-07 and 27-07 (or any other day), the same "why did this trade qualify / what was entry / target / actual outcome" narrative already captured for 22 July.

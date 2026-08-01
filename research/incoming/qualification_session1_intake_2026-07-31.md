# Session 1 — Qualification Evidence Intake (Product Owner)

**Status:** Blank intake document — to be filled in by/with the Product Owner. Nothing in this file is evidence yet; it becomes evidence only once the fields below are answered. Once filled in, this file moves through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification) and is scored against `research/specifications/evidence_acceptance_checklist.md`.

**Targets:** This session exists to close **QUAL-007** (the TP-stage competitor identity) — the single blocker keeping `QualificationEngine` frozen. See `research/specifications/qualification_remaining_unknowns.md` for exactly what's missing and why: no source anywhere in this repository names, defines, or gives a worked example of the competitor used in the TP High / TP Low sustain tests. This session is the artifact that document said would be required.

**Do not fill in a field with a guess.** If the Product Owner doesn't know or isn't sure, write `UNKNOWN` — an honest "I don't know" is usable input to the intake process; a guessed value is not (it will be classified as an Assumption, not a Confirmed Rule, per `EVIDENCE_INTAKE_PROCESS.md` Section 2).

---

## Instructions for the session

Open **one historical trading day at a time**, and for each, walk through the four questions below while looking at the actual chart/data together with the Product Owner. Repeat for 3–5 separate days — this project's own acceptance bar (`evidence_acceptance_checklist.md`, "minimum three worked examples") requires at least three, and a fourth/fifth is valuable specifically for surfacing a **Counter Example** (a day where the pattern looks different, or doesn't hold).

For each day, capture enough raw detail that someone with no memory of the conversation could independently recompute the qualification decision from what's written here — that's the same bar Weekly Future was held to before its formula was accepted (`WEEKLY_FUTURE_BLOCKER_REPORT.md` §5).

---

## General Rule Statement (Product Owner, supplied in chat, 2026-07-31)

**Status of this section: a conceptual rule statement, not yet a dated Worked Example.** Recorded verbatim per `EVIDENCE_INTAKE_PROCESS.md`'s "quoted verbatim, nothing paraphrased away" rule. This does **not** by itself satisfy the "minimum three worked examples" acceptance bar (`evidence_acceptance_checklist.md`) — no specific date/trade/outcome was walked through, only the general shape of the rule. Worked Examples 1-5 below are still needed with real dated instances before this can move to Implement.

**Verbatim statement:**

> After 9.20AM candle you have to find the top and bottom strike. Then finalize which strike you want to proceed either top or bottom, if possible keep both.
>
> Top Instructions: Mark the top premium price (First 5 minute). CE - Mark PE Low (PE TOP Low price and 6ITM and OTM First 5 minute value) - These levels act as Entry, Target, SL, Support, Resistance. PE - Mark CE High (CE TOP High price and 6ITM and OTM First 5 minute value) - These levels act as Entry, Target, SL, Support, Resistance.
>
> Bottom Instructions: Mark the Bottom premium price (First 5 minute). CE - Mark PE High (PE Bottom High price and 6ITM and OTM First 5 minute value) - These levels act as Entry, Target, SL, Support, Resistance. PE - Mark CE Low (CE Bottom Low price and 6ITM and OTM First 5 minute value) - These levels act as Entry, Target, SL, Support, Resistance.
>
> Then find who is going to win - Based on the market trend.
>
> Now the game starts. If you found the confident trade then its entry point act as a support choose the first resistance as R1 target - this will go upward direction. Meanwhile watch the competitor movement who will going to touch the line first - must go to downward and looks for the next support. When anyone touches the line the trade should exit immediately - means its profit trade.
>
> STL - should be same as previously told (Need 3 points to cover the exchange fee and taxes).

**Cross-check against existing confirmed evidence (per `EVIDENCE_INTAKE_PROCESS.md` Section 4):**

| Statement | Cross-check result |
|---|---|
| "Choose the first resistance as R1 target" (adjacent strike, direction of trade) | **CONFIRMS EXISTING** — matches Specification Rule 2 (v1.1, CONFIRMED), already implemented in `src/position_manager/position_manager.py` |
| "Watch the competitor... exit immediately when touched" | **CONFIRMS EXISTING** — matches Rule 2's Competitor Exit mapping, already implemented in `src/exit_engine/exit_engine.py` |
| "STL... 3 points to cover exchange fee and taxes" | **CONFIRMS EXISTING** — matches the already-confirmed Trailing Stop minimum net quoted in `STRATEGY_FUNCTIONAL_SPECIFICATION.md:246` |
| "CE - Mark PE Low (Top)"; "PE - Mark CE High (Top)"; "CE - Mark PE High (Bottom)"; "PE - Mark CE Low (Bottom)" | **NEW — directly answers QUAL-007.** Word-for-word structural match to `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7's TP High/TP Low sustain test (`CE > competitor PE Low`, `PE < competitor CE High`). Identifies the competitor as the **same strike's own opposite side** (Top or Bottom strike, opposite CE/PE), not the adjacent-strike Rule 2 mapping — the two concepts are now confirmed distinct, exactly as `BUSINESS_ARCHITECTURE.md` had warned they must not be conflated. |

**Real reference ladder pulled for context** (NIFTY, 2026-07-30, Top Strike 24250, Bottom Strike 24200, first 5-minute CE/PE High/Low, all 13 strikes = the "6 ITM and OTM" the statement describes — fetched live via the Upstox backtest harness, `src/backtest/`):

| Strike | CE High | CE Low | PE High | PE Low |
|---|---|---|---|---|
| 23950 | 332.95 | 276.10 | 46.80 | 32.65 |
| 24000 | 291.50 | 236.60 | 63.00 | 41.10 |
| 24050 | 252.00 | 201.85 | 72.90 | 51.50 |
| 24100 | 215.60 | 167.60 | 91.00 | 64.30 |
| 24150 | 181.40 | 137.55 | 108.20 | 80.00 |
| 24200 (Bottom) | 150.00 | 110.30 | 131.60 | 98.30 |
| 24250 (Top) | 121.50 | 87.00 | 159.00 | 120.10 |
| 24300 | 103.20 | 67.05 | 189.00 | 145.20 |
| 24350 | 74.75 | 50.50 | 222.35 | 173.55 |
| 24400 | 56.40 | 37.30 | 259.40 | 205.10 |
| 24450 | 45.55 | 27.00 | 297.95 | 240.50 |
| 24500 | 30.10 | 19.45 | 340.60 | 279.20 |
| 24550 | 23.85 | 13.90 | 383.45 | 318.40 |

Applying the rule to this table: a CE trade at Top (24250) would compare against **Top's own PE Low = 120.10**; a PE trade at Top against **Top's own CE High = 121.50**; a CE trade at Bottom (24200) against **Bottom's own PE High = 131.60**; a PE trade at Bottom against **Bottom's own CE Low = 110.30**. This is the confirmed 13-level ladder `ReferenceBuilder` already builds — no new data-capture logic needed if this rule is accepted, only a new comparison.

**Open questions this statement does not yet resolve** (do not guess at these — ask the Product Owner directly):

1. ~~**Entry trigger order**~~ — **answered by the Entry/Target/SL/TSL Clarification section below** (2026-08-01): Winner Detection ("the winner guessing generator") *is* the entry trigger, gated by an underlying-trend pre-check, confirmed by the dual crossover. Still open: the ladder of levels checked is wider than what `WinnerEngine` currently implements (see that section's cross-check).
2. ~~**"These levels act as Entry, Target, SL, Support, Resistance"**~~ — **answered by the 2026-08-01 clarification**: Entry = a marked level (S), Target = S+1 (next marked level up), Competitor Exit = touch of S-1, SL = S-1, TSL = min. 3 points, continuously trailing. SL and Competitor Exit appear to sit at the *same* level (S-1) but trigger off different conditions — flagged, not yet confirmed as intentional.
3. ~~**No dated worked example yet**~~ — **now supplied**, see Worked Example 1 below (22 July, corrected to 4 sequential trades). Still need 2 more independent dated examples per `evidence_acceptance_checklist.md`.
4. ~~**Competitor identity conflict** (same-strike vs adjacent-strike 24050/24000)~~ — **resolved by the 2026-08-01 clarification**: the competitor is *any* of the 13 marked levels, whichever is crossed first in the trend-confirmed direction — not fixed to one strike. 24050/24000 were simply the levels that happened to be crossed on 22-July's specific trades, not a separate competing rule.

---

## Entry Trigger Rule (Product Owner, supplied in chat, 2026-07-31, second message)

**Status: a real, executable entry condition — the strongest evidence recorded in this document so far.** Recorded verbatim (Tamil original), with an English paraphrase for clarity (paraphrase is NOT the evidence of record — the Tamil original is).

**Verbatim (Tamil):**

> Entry Rule: உங்கள் excel-ல இருந்து. PE Buy Condition: PE Premium crosses 24050 CE High AND CE Premium crosses 24050 PE Low. இரண்டும் ஒரே நேரத்தில். இதுதான் மிகவும் powerful condition. இதுதான் false breakout filter.
>
> CE Buy Condition: CE crosses 24000 PE Low AND PE crosses 24000 CE High. இரண்டும் confirmation.
>
> Workflow: 9:20 → Fetch ATM → Generate 4 ITM, 4 OTM → Get CE High → Get CE Low → Get PE High → Get PE Low → Draw Lines → Wait → Premium Cross → Competitor Cross → BUY → Trail → Exit.

**English paraphrase (not the evidence of record):** At 9:20, fetch the ATM strike, generate a 9-strike ladder (ATM ± 4 ITM/OTM), capture each strike's first-5-minute CE/PE High/Low, draw those as lines. From then on, watch for a **simultaneous dual crossover**: for a PE Buy at a given strike, its own PE premium must cross that strike's CE High *at the same time* its own CE premium crosses that strike's PE Low. Source: "from your Excel" — i.e. the Product Owner's own trade log, not a fresh invention. Described explicitly as "the most powerful condition" and "a false breakout filter" — the dual, same-instant requirement is the point, not incidental.

**Cross-check against existing confirmed evidence:**

| Statement | Cross-check result |
|---|---|
| Same-strike CE+PE dual touch, same candle, as the entry trigger | **Structurally similar to already-implemented `WinnerEngine`** (Rule 3, CONFIRMED: "If CE touches any of its reference levels AND PE touches any of its reference levels during the SAME candle... Winner immediately generates Entry Signal"). **Not yet confirmed identical** — `WinnerEngine` checks touch against *any* of a strike's own CE/PE High/Low band; this statement specifies a more precise cross pattern (PE crosses CE High specifically, CE crosses PE Low specifically) and ties it explicitly to "false breakout filter" framing that `WinnerEngine`'s existing docstring does not mention. **Open question, do not assume equivalence without asking:** is this the same event as Winner Detection under a different name, or a stricter refinement of it? |
| ATM ± 4 ITM/OTM = 9 strikes | **Possible structural difference from the earlier General Rule Statement** (Top/Bottom, "6 ITM and OTM" = 13 strikes total across two anchors). **Open question, do not guess:** is ATM here the same concept as Top/Bottom Strike, or a third, distinct anchor point? Ask the Product Owner directly before assuming either way. |

---

## Entry/Target/SL/TSL Clarification (Product Owner, supplied in chat, 2026-08-01)

**Status: resolves the competitor-identity conflict flagged above, and is the first real evidence for Session 3 (Stop Loss) and Session 4 (Trailing Stop).** Recorded verbatim (original wording), with an English restatement clearly marked as not the evidence of record.

**Verbatim:**

> Entry can happen at any level not the top and bottom strike. On 22nd the top strike is 24150, so we have to mark the 24150 +- 6 levels first 5mins High to 24150PE and Low to 24150CE. So now 24150 is ATM (Real ATM is different and its change time to time). The above should happen after 9.20AM. After 9.20AM the winner guessing generator starts and check who is going to win (CE/PE). First we have get the current market trend bullish/bearish (underlying), based on that we have to check the 24150CE and PE crossing any marked level - if the market seems bullish the 24150CE cross up any marked level same time the 24150PE cross down any marked level, this is the confirmation of CE entry trade and vice versa.
>
> Target/EXIT: Once enter the trade, the exit should be trade value (marked level S) and the target is s+1 (next up marked level), another exit based on the competitor touch the S-1 marked level. SL is trade taken mark -1 marked level. TSL is minimum 3 points from trade taken and keeps on travel.

**English restatement (not the evidence of record):**
- "24150" for 22-July is the **Top Strike**, but is here relabeled "ATM" for that session's purposes — explicitly **not** the real, continuously-moving ATM strike ("Real ATM is different and its changes time to time"). This resolves the earlier open question about whether "ATM ± 4/4" and "Top/Bottom" are the same concept: **they are** — "ATM" in the Entry Trigger Rule section above was this session's Top (or Bottom) Strike, fixed for the day, not the live ATM.
- The 13-level ladder (anchor ± 6) is built exactly as the General Rule Statement described: each level's CE High is drawn on the anchor's own PE chart, each level's PE Low is drawn on the anchor's own CE chart (matches the screenshots in `daily_data_2026-07-31.md` exactly — e.g. "24050CE ITM3 | High: 238" drawn on a PE chart).
- **Underlying trend is checked first** (bullish/bearish), before any crossover is evaluated — a pre-filter not previously recorded anywhere in this project's evidence.
- The dual crossover is then checked **against any of the marked levels**, not one fixed strike — whichever level is crossed first, in the direction the trend already implied, confirms entry. **This directly resolves the competitor-identity conflict** noted in Worked Example 1: 24050 CE / 24000 CE were simply whichever marked levels got crossed on those specific 22-July trades, not a separate, fixed rule contradicting the same-strike Top/Bottom statement.
- **Target = S+1**, the next marked level up from entry (S) — confirms, does not contradict, the correction already made to Worked Example 1 (single-step target per trade, not a multi-rung ladder within one trade).
- **Competitor Exit = touch of S-1** — matches the shape of already-confirmed Rule 2's Competitor Exit concept, generalized here to "the marked-level ladder" rather than strictly "the adjacent strike."
- **Stop Loss = S-1**, the same marked level as the Competitor Exit trigger above. **Not yet confirmed whether this is intentional** (SL and Competitor Exit sitting at the identical price, triggered by different conditions) or a simplification in this description — flagged, not assumed either way.
- **Trailing Stop = minimum 3 points from entry, "keeps on travelling"** — confirms the already-known +3 net premium points rule (Session 4), and confirms, rather than merely infers, the pattern already noticed in the 22-July table (each new sequential trade's SL sitting at the previous trade's entry price) — this is a continuously-updating trail, not a one-time move.

**Cross-check against already-implemented code:**

| Statement | Cross-check result |
|---|---|
| Checking crossover against *any* of the 13 marked levels (not just the entry strike's own CE/PE High/Low band) | **Materially different from the currently-implemented `WinnerEngine`**, which only checks a single strike's own reference band. If accepted, `WinnerEngine`/`QualificationEngine` would need to check against the full ladder, not just one strike's levels — this is a real scope difference, not just a naming question. **Product Owner response (2026-08-01): "Need example"** — i.e. this question needs a worked example to answer properly rather than a one-line confirmation. Still open; the next dated worked example (28-July/27-July, or any other) should specifically capture which strike's own band vs. the wider ladder actually got crossed, so this can be settled from real data rather than asked abstractly again. |
| Target = S+1, Competitor Exit = S-1 (marked-level ladder, generalized) | **Consistent in shape with already-confirmed Rule 2** (`CE(S+1)`/`PE(S-1)` for Target, competitor mapping for Exit) — the generalization from strikes to marked levels is new, but the S+1/S-1 structure itself is not contradicted. |
| Stop Loss = S-1 | **First-ever evidence for Stop Loss** (Session 3, previously zero evidence beyond "named as an exit condition"). **Analysis added 2026-08-01, see `stop_loss_session3_intake_2026-07-31.md`**: Rule 2 distinguishes Support (`CE(S-1)`/`PE(S+1)`, same side) from Competitor Exit (`PE(S-1)`/`CE(S+1)`, opposite side) — an SL naturally expressed on the trader's own position most consistently reads as **SL = Support**, not Competitor Exit, which remains a genuinely distinct level. Still a strong inference, not a Product-Owner-confirmed fact — needs explicit confirmation or a worked example demonstrating the two prices match. |
| TSL minimum 3 points, continuously trailing | **Confirms the already-accepted +3 net premium points rule** (Session 4). Activation trigger and step size are still not fully specified — "keeps on travelling" describes continuous behavior but not the exact increment. |

---

## Worked Example 1

**Date:** 22 July (year not stated — context suggests 2026, consistent with everything else fetched this session; **please confirm the exact year before this is treated as fully specified**).
**Strike(s) involved:** 24150 (Top or Bottom not restated here — the same strike used throughout Trades 1, 2, 4; Trade 3 uses 24000).

**CORRECTION to this document's earlier recording of this day:** originally recorded as one PE trade with two sequential Targets (206.35 → 238.75 → 269.95). The Product Owner's full trade-log table (below) shows this was **four separate, sequential trades**, each re-entering at the level the previous one exited — not one trade with a multi-rung ladder target. Rule 2's single-fixed-Target design is **not contradicted** by this data; each individual trade still has exactly one Target.

**Full trade-log table, recorded verbatim as tab-separated by the Product Owner (column headers as given — see alignment note below):**

```
22-July-2026  Entry time  Price   Target  SL      TSL          CE/PE  Entry Premium  Competitor Strike  Competitor Price  Exit time  Exit price  Captured points  Total  Entry reason                                              Exit Reason
24150         9.25        206.35  238.75  176.85  You can fix  PE     24050CE High   24050PE Low        114               9.45       238.75      32.4              2106   PE crossed 24050CE high and same time CE crosses 24050PE low  Target hit as well as Competitor Support line hit
              10.2        238.75  269.95  206.35  You can fix  PE     24000CE High   24000PE Low        94.4              10.25      269.95      31.2              2028   PE crossed 24000CE high and same time CE crosses 24000PE low  Target hit first and Competitor line not hit
              10.5        94.4    114     78.2                 CE     24000PE Low    24000CE High       238.75            11.3       101.6       7.2               468    CE crossed 24000PE Low and same time PE crosses 24000CE High  CE Resistance hit first
              12          238.75  269.95  206.35  You can fix  PE     24000CE High   24000PE Low        94.4              12.2       269.95      31.2              2028   PE crossed 24000CE high and same time CE crosses 24000PE low  Target hit first and Competitor line hit
```

**Column-alignment note — UNCONFIRMED, do not treat as settled:** the header names "Entry Premium" / "Competitor Strike" / "Competitor Price" do not cleanly match their column's values (e.g. row 1's "Entry Premium" cell holds the text `24050CE High`, a level *label*, not a premium number). My best-guess reading, **not confirmed by the Product Owner:** the two label cells (`24050CE High`, `24050PE Low`) together identify the dual-crossover reference pair from the Entry Trigger Rule above (matching the Entry reason text exactly), and the adjacent numeric cell (114, 94.4, 238.75, 94.4) is the Competitor Price at entry. Please confirm this reading rather than let it stand as assumed.

1. **Why was this trade qualified?**
   Per the Entry Trigger Rule (Entry reason column, verbatim): Trade 1 — "PE crossed 24050CE high and same time CE crosses 24050PE low." Trade 3 (the CE trade) — "CE crossed 24000PE Low and same time PE crosses 24000CE High." Both match the simultaneous dual-crossover condition already recorded above.

2. **Which competitor was compared?**
   Trades 1/2/4 (PE side): 24050 CE and 24000 CE respectively — **not 24150 CE (same strike)** as the General Rule Statement's Top/Bottom framing would suggest. This is the **adjacent-strike-style reference** (24050, 24000 — both below the 24150 entry strike, moving further away as each successive trade re-enters), closer in shape to Rule 2's adjacent-strike pattern than to the "same strike opposite side" pattern from the General Rule Statement. **This is a real, material inconsistency between two parts of this document's own evidence, recorded here rather than resolved by guessing.**

3. **Why this competitor?**
   Not stated independently of the crossover condition itself — **UNKNOWN** whether 24050/24000 were chosen because they were "the next rung down" mechanically, or for some other stated reason.

4. **Would another competitor have changed the result?**
   **UNKNOWN — not asked.**

**Raw supporting data:** the full table above. Additional internally-consistent finding: **`Total` = `Captured points` × 65, exactly, on all four rows** (32.4×65=2106, 31.2×65=2028, 7.2×65=468, 31.2×65=2028) — a real, self-verifying number pulled from the data itself, not an assumption. Possibly the lot size in use, not yet confirmed as such by the Product Owner.

**Candidate Trailing-Stop/SL mechanism observed (Session 3/4 relevant, inference only, not confirmed):** Trade 2's SL (206.35) exactly equals Trade 1's own Entry price, and Trade 4's SL (206.35) matches the same value. This looks like "the stop trails up to lock in the previous trade's entry level as each successive trade opens" — a real candidate answer to Session 4's open trail-mechanics question, but this is read out of the numbers, not stated outright by the Product Owner, and should be confirmed directly rather than assumed.

**A third exit type found, beyond Target/SL/Competitor:** Trade 3 exited via "CE Resistance hit first" at 101.6 — between its SL (78.2) and Target (114), not equal to either. This is consistent with the R1/R2 resistance labels seen drawn directly on the TradingView screenshots in `research/incoming/daily_data_2026-07-31.md`, and suggests the real exit-condition set may be larger than the four conditions (Target/Competitor/SL/Trailing Stop) currently coded into `ExitEngine`.

**Product Owner answer (2026-08-01), verbatim:** "Standard pivot points (Implement this later)." Identifies R1/R2/S1/S2/Resistance as the well-known, publicly-documented Classic Pivot Point formula (`PP = (High+Low+Close)/3`, `R1 = 2×PP - Low`, `S1 = 2×PP - High`, etc.) rather than a bespoke rule specific to this project — but **explicitly deferred**. Per the Product Owner's own instruction, do not pursue implementing this now; recorded here for traceability only. Also worth noting: since this is a named, standard formula rather than an unstated one, it does not carry the same "must not guess" risk as the other blocked engines if it's picked up later — but confirm the exact pivot-point variant and the period it's computed over (prior day? session open?) before implementing, since "standard pivot points" has more than one common variant.

**Counter Example for this day, if any** (a moment the same day where the pattern did *not* hold, or UNKNOWN):

---

## Worked Example 2 — 29-July-2026

**Correction to earlier finding:** this table's Bottom (24150) trade uses **Entry = 165.8** and **SL = 137.3** — both values from the discrepancy flagged in `daily_data_2026-07-31.md` (table said 165.8, a screenshot said 137.3). **This strongly suggests the discrepancy was never a data error** — 165.8 (the docx table's "PE High") and 137.3 (the screenshot's label) are simply two *different* marked levels in the same ladder: 165.8 is the level used as this trade's Entry (S), 137.3 is the next marked level down, used as SL (S-1) — exactly matching the already-confirmed `SL = S-1` rule. **Candidate resolution, not yet the Product Owner's own confirmation** (they said "will confirm" to the original question) — recorded here because the internal arithmetic support is strong, not as a final answer.

**Full trade-log table, verbatim:**

```
29-July-2026  Anchor       Entry time  Price   Target   SL       TSL          CE/PE  Ref Label 1     Ref Label 2      Competitor Price  Exit time  Exit price  Captured  Total     Entry reason                                                    Exit Reason
              24200-TOP    11.05       152.05  179.7    128      You can fix  CE     24250PE Low     24250CE High    117.62            15.25      146.5       -5.55     -360.75   CE crossed 24250PE Low and same time PE crosses 24250CE High  market closed (No level touched)
              24150-BOTTOM 9.2         165.8   189.6    137.3    You can fix  CE     24200PE High    24200CE Low     116               12.05      189.6       23.8      1547      CE crossed 24200PE high and same time PE crosses 24200CE low  Target hit first and Competitor line not hit
                           13.05       189.6   221.35   165.8    You can fix  CE     24250PE High    24250CE Low     92.5              15.25      177.55      -12.05    -783.25   CE crossed 24250PE high and same time PE crosses 24250CE low  market closed (No level touched)
```

**Arithmetic check (all 3 rows): `Total = Captured points × 65`, exact** — (-5.55×65=-360.75), (23.8×65=1547), (-12.05×65=-783.25). Further corroborates the lot-size-65 finding from 22-July.

**New exit type found: "market closed (No level touched)"** — a trade still open at market close, forced closed at whatever the current price is, with no Target/SL/Competitor/TSL condition having fired. This is a **fifth exit condition**, beyond the four (Target/Competitor/SL/Trailing Stop) currently coded into `ExitEngine` — none of which currently model an end-of-day forced close.

**Sequential re-entry pattern reconfirmed**: row 3's Entry (189.6) = row 2's Exit; row 3's SL (165.8) = row 2's own Entry price — same "SL trails to the previous trade's entry" pattern already noted for 22-July.

**Competitor identity reconfirmed as "any marked level," not fixed**: 24200-TOP's trade competitor is 24250 (an adjacent strike above); 24150-BOTTOM's two trades use competitors 24200 then 24250 (moving further away each re-entry) — consistent with the 2026-08-01 clarification, not the same-strike-only reading.

---

## Worked Example 3 — 30-July-2026

**Full trade-log table, verbatim (6 trades across both anchors):**

```
30-July-2026  Anchor       Entry time  Price   Target   SL      TSL          CE/PE  Ref Label 1     Ref Label 2      Competitor Price  Exit time  Exit price  Captured  Total     Entry reason                                                    Exit Reason
              24250-TOP    9.2         120.1   145.2    98.3    You can fix  CE     24250PE Low     24250CE High    121.5             10.25      98.3        -21.8     -1417     CE crossed 24250PE Low and same time PE crosses 24250CE High  SL Hit
                           10.4        98.3    120.1    80      You can fix  CE     24200PE Low     24250CE High    121.5             11.25      120.1       21.8      1417      CE crossed 24200PE Low and same time PE crosses 24250CE High  Target Hit first
                           13.1        103.2   121.5    74.75   You can fix  PE     24300CE High    24250PE Low     120.1             14.3       121.5       18.3      1189.5    PE crossed 24300CE high and same time CE crosses 24250PE low  Target Hit first
                           14.45       120.1   145.2    98.3    You can fix  CE     24250PE Low     24300CE High    103.2             15.25      134         13.9      903.5     CE crossed 24250PE Low and same time PE crosses 24300CE High  market closed (No level touched)
              24150-BOTTOM 10.4        159     189      131.6   You can fix  CE     24250PE High    24250CE Low     87                12.3       189         30        1950      CE crossed 24250PE high and same time PE crosses 24250CE low  Target hit first
                           13.1        67.05   87       50.5    You can fix  PE     24300CE Low     24300PE High    189               14.2       74.35       7.3       474.5     PE crossed 24300CE low and same time CE crosses 24300PE high  24300PE High competitor level touched first
```

**Arithmetic check (all 6 rows): `Total = Captured points × 65`, exact on every row.**

**First SL-hit-then-immediate-re-entry example**: row 1 stopped out at 98.3 (SL Hit); row 2 re-enters at exactly 98.3 (the same price), not just after a Target hit — shows the sequential re-entry pattern applies after SL exits too, not only Target exits.

**Explicit "competitor level touched" exit reason** (row 6): "24300PE High competitor level touched first" — directly confirms the Competitor Exit condition by name, with the exact level identified.

---

## Worked Example 4 — 31-July-2026

**Important correction to this project's own prior finding**: this trade log proves NIFTY options traded normally on 31-July-2026. The earlier attempt to backtest this date via the Upstox connector returned zero rows for every strike tried, which was tentatively attributed to "possibly a market holiday" — **that guess was wrong**. The real cause was a data-availability gap specific to the Upstox historical API for that date, not an actual market closure. Corrected here rather than left standing.

**Full trade-log table, verbatim:**

```
31-July-2026  Anchor       Entry time  Price   Target   SL      TSL          CE/PE  Ref Label 1     Ref Label 2      Competitor Price  Exit time  Exit price  Captured  Total     Entry reason                                                    Exit Reason
              24400-TOP    9.3         145     180      86.85   You can fix  PE     24350CE High    24300PE Low     64.75             12.25      83.35       -61.65    -4007.25  PE crossed 24300CE high and same time CE crosses 24300PE low  24350PE low competitor level touched first
              24300-BOTTOM 9.3         92.75   121      71.15   You can fix  PE     24350CE Low     24300PE High    123               10.35      71.15       -21.6     -1404     PE crossed 24350CE low and same time CE crosses 24300PE high  SL hit
                           10.4        123     139.95   98.7    You can fix  CE     24350PE High    24400CE Low     71.15             12.1       139.95      16.95     1101.75   CE crossed 24350PE high and same time PE crosses 24400CE low  target hit first
```

**Arithmetic check (all 3 rows): `Total = Captured points × 65`, exact.**

**Minor inconsistency in the source text itself, recorded not silently corrected**: row 1's Entry reason says "PE crossed 24300CE high and same time CE crosses 24300PE low," but the Ref Label columns for that same row say "24350CE High"/"24300PE Low" — a strike mismatch (24300 vs 24350) between the prose and the labeled columns. Similarly its Exit Reason names "24350PE low," a level not identified anywhere else in that row. Likely a transcription slip in the original data, not a business-rule contradiction — flagged for the Product Owner to clarify if it matters, not treated as evidence of a different rule.

**Top Strike 24400 / Bottom Strike 24300 for this day** — notably different range than 22/29/30-July (24150-24250), consistent with real underlying price movement across the week, not a data anomaly.

---

## Worked Example 5 (optional — strongly recommended for a Counter Example)

**Status: no longer strictly required** — with Worked Examples 1-4 (22/29/30/31-July) now supplying 4 independent dated examples, this document already exceeds `evidence_acceptance_checklist.md`'s "minimum three worked examples" bar for the core Entry/Target/SL/Competitor mechanics. Still valuable if a clean Counter Example (a day where the pattern visibly breaks) exists — otherwise this slot can stay blank.

**Date:** _______________
**Strike(s) involved:** _______________

1. **Why was this trade qualified?**

2. **Which competitor was compared?**

3. **Why this competitor?**

4. **Would another competitor have changed the result?**

**Raw supporting data:**

**Counter Example for this day, if any:**

---

## Worked Example 6 (optional)

**Date:** _______________
**Strike(s) involved:** _______________

1. **Why was this trade qualified?**

2. **Which competitor was compared?**

3. **Why this competitor?**

4. **Would another competitor have changed the result?**

**Raw supporting data:**

**Counter Example for this day, if any:**

---

## Cross-cutting questions (answer once, after all examples above are filled in)

- **Does the competitor change during replay** (i.e., within a single session, does which strike/level counts as "the competitor" ever shift), or is it fixed for the day? _______________
- **Is there more than one competitor** — do TP High and TP Low use the same competitor, or different ones? _______________
- **How is the competitor selected**, in the Product Owner's own words, as a general rule (not tied to one day)? _______________
- **Is the competitor any of**: Weekly Future / Top Strike / Bottom Strike / Reference Level / Premium / ORB / the Exit-stage Rule 2 mapping (`PE(S-1)`/`CE(S+1)`) / something else entirely? **Per the General Rule Statement above: the same strike's own opposite side** — Top's PE Low (for CE)/CE High (for PE), Bottom's PE High (for CE)/CE Low (for PE). Distinct from the Exit-stage Rule 2 mapping. Still needs a dated Worked Example to move from "stated" to "Confirmed."

## Expected Result

(Once the above is filled in, state in one paragraph what a correct `QualificationEngine` implementation should now be able to do, independent of any single worked example above — this becomes the regression-test target per `evidence_traceability_standard.md`.)

## Confidence

(Product Owner's own honest rating for the full session: High / Medium / Low — how sure are they this captures a real, consistent rule rather than day-specific judgment calls.)

---

## After this session

1. This filled-in file gets a **Rule ID** assigned (reuse `QUAL-007` — it already exists in `docs/RULE_INDEX.md`) and stays in `research/incoming/` under its current filename.
2. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` (Extraction → Verification → Cross-check → Classification).
3. Score the result against `research/specifications/evidence_acceptance_checklist.md`.
4. Log the outcome as a new row in `research/evidence_log.md` (Evidence Complete → Implement / Evidence Partial → Research / Evidence Missing → Freeze, per `research/specifications/product_owner_evidence_process.md`'s Decision Matrix).
5. Only on an **Implement** outcome does Sprint 10 (Qualification Engine) become eligible to start.

**Status as of 2026-08-01, updated:** 4 independent dated worked examples now exist (22/29/30/31-July-2026), each internally arithmetic-consistent (`Total = Captured × 65` exact on every one of ~16 trade rows), each showing the same Entry/Target(S+1)/Competitor(S-1)/SL(S-1) structure and the "any marked level, trend-confirmed" competitor rule holding without exception. This clears the raw "≥3 worked examples, consistent outputs" bar. **Not yet a full Evidence Complete / Implement outcome** — remaining before a formal scoring pass: PE-side SL confirmation, the WinnerEngine full-ladder-vs-single-band scope question, and a decision on how to handle the newly-found fifth exit type ("market closed, no level touched") that `ExitEngine` doesn't currently model at all.

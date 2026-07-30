# Incoming Evidence — Weekly Future Formula (raw data)

**Received:** 2026-07-30, pasted directly in chat by the Product Owner/domain expert (User).
**Format:** tabular worked examples, 3 trading dates, 6 data points (High + Low per date).

Per `research/EVIDENCE_INTAKE_PROCESS.md`, this file is the raw intake record — see `research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` for the derived, verified specification and `research/evidence_log.md` for this source's logged disposition.

## Raw data, verbatim

```
29-07-2026
Strike Price(Today open Approx)  CE High(1st 5min)  PE Low(1st 5min)  FUT High  SP
24200                            143.45              128               24215.45  24200   1st 5min High

Strike Price(Today open Approx)  PE High(1st 5min)  CE Low(1st 5min)  FUT Low   SP
24200                            165.8               116               24150.2   24150   1st 5min Low

28-07-2026
Strike Price(Today open Approx)  CE High(1st 5min)  PE Low(1st 5min)  FUT High  SP
24000                            218                 107.75            24110.25  24100   1st 5min High

Strike Price(Today open Approx)  PE High(1st 5min)  CE Low(1st 5min)  FUT Low   SP
24000                            136.65              180.95            24044.3   24050   1st 5min Low

27-07-2026
Strike Price(Today open Approx)  CE High(1st 5min)  PE Low(1st 5min)  FUT High  SP
23950                            212.75              177.05            23985.7   24000   1st 5min High

Strike Price(Today open Approx)  PE High(1st 5min)  CE Low(1st 5min)  FUT Low   SP
23950                            201.3               176.2             23924.9   23900   1st 5min Low
```

## Clarification obtained (same session, in chat)

**Q:** What role does "SP" (the nearest-50 rounded value) play?
**A (Product Owner):** SP from FUT High = Top Strike; SP from FUT Low = Bottom Strike.

## Verification performed

Every row's `FUT High`/`FUT Low` was recomputed independently and matched exactly (see `research/specifications/WEEKLY_FUTURE_CALCULATION_EXAMPLES.md` for the full step-by-step arithmetic). Every `SP` value was independently recomputed as `round(FUT / 50) * 50` and matched exactly. Zero contradictions across all 6 data points, spanning 3 independent trading dates.

## Disposition

**ACCEPTED** — meets `WEEKLY_FUTURE_BLOCKER_REPORT.md` §5's fallback evidence bar (≥3 independently consistent worked examples) for the Weekly Future High/Low formula, and additionally resolves Top/Bottom Strike selection (previously a separate, Critical gap). See `research/specifications/WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` for what remains unresolved (Entry/Exit rules, exceptions, instrument/expiry scope).

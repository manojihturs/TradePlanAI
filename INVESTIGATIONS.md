# Strategy Engine Investigation Log

Documentation-only record of investigations into discrepancies between the
manual trading journal and the strategy engine (`strategy/` package,
Modules 1-9). No investigation on this page authorizes or implies a code
change by itself - any resulting change is made and committed separately,
with its own rationale.

---

## Investigation #1 — Manual 10:20 trade, 22-July-2026

**Status: CLOSED**

### Subject

The manual trading journal for 22-July-2026 records a PE trade at 10:20
(strike 24000, entry premium 238.75). The strategy engine's replay of that
session does not produce this trade.

### Scope of the investigation

1. Mapping validation — checked every mapped level (TOP and BOTTOM anchor,
   all four fields: CE-High, CE-Low, PE-High, PE-Low) across all 13
   captured strikes for an exact numeric match to the manually logged
   entry price.
2. Historical feed validation — pulled the complete 1-minute and 5-minute
   OHLC series for strikes 24000, 24050, and 24100 (both CE and PE) and
   compared session highs/lows against the manual journal and against
   available chart-screenshot values.
3. Reverse trade reconstruction — replayed the exact entry rule (both
   TOP and BOTTOM anchors, all fields, fresh-cross logic) across every
   captured strike for the 09:15-15:25 session, searching specifically
   for any qualifying signal within an hour of 10:20 in either direction.

### Conclusion

**The manual 10:20 trade on 22-July-2026 cannot be reproduced from the
available historical replay dataset using the current, fully specified
strategy.**

The investigation verified:

- Opening-range capture is correct.
- Mapping rules are correct.
- TOP/BOTTOM anchor selection is correct.
- Fresh-cross logic is functioning as specified.
- No qualifying signal exists on any captured strike or anchor near 10:20.

Therefore the discrepancy remains unresolved and is classified as an
**external data discrepancy**, not a confirmed strategy-engine defect. The
most likely explanations, in order of plausibility given the data checked
(see historical feed validation report): a live-tick/broker-screen price
that the 1-minute historical feed does not reflect, or a manual
transcription error at the time the journal was recorded. Neither could be
confirmed or ruled out without the original timestamped screenshot or
tick-level data for that specific trade, which was not available.

### Disposition

Marked **CLOSED**. No strategy code was modified as a result of this
investigation, and none should be, based on this investigation alone.

Reopen only if new evidence becomes available - specifically, an original
timestamped screenshot of the 10:20 entry, or tick-level (sub-1-minute)
price data for PE(24000) covering that morning.

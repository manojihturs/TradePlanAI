# Weekly Future Calculation — Verified Examples

Companion to `WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` v1.0. Every example below was independently recomputed (Python, exact decimal arithmetic) against the Product Owner-supplied values and matched exactly — see the verification note at the end of each block.

---

## Example 1 — 2026-07-29, High

**Inputs:** Strike = 24200, CE High(1st 5-min) = 143.45, PE Low(1st 5-min) = 128

**Calculation:**
```
Weekly Future High = Strike + (CE High − PE Low)
                    = 24200 + (143.45 − 128)
                    = 24200 + 15.45
                    = 24215.45
```
**Top Strike** = round(24215.45 / 50) × 50 = **24200**

**Verification:** computed 24215.45 == supplied 24215.45 ✓; computed Top Strike 24200 == supplied SP 24200 ✓

---

## Example 2 — 2026-07-29, Low

**Inputs:** Strike = 24200, PE High(1st 5-min) = 165.8, CE Low(1st 5-min) = 116

**Calculation:**
```
Weekly Future Low = Strike − (PE High − CE Low)
                   = 24200 − (165.8 − 116)
                   = 24200 − 49.8
                   = 24150.2
```
**Bottom Strike** = round(24150.2 / 50) × 50 = **24150**

**Verification:** computed 24150.2 == supplied 24150.2 ✓; computed Bottom Strike 24150 == supplied SP 24150 ✓

---

## Example 3 — 2026-07-28, High

**Inputs:** Strike = 24000, CE High(1st 5-min) = 218, PE Low(1st 5-min) = 107.75

**Calculation:**
```
Weekly Future High = 24000 + (218 − 107.75) = 24000 + 110.25 = 24110.25
```
**Top Strike** = round(24110.25 / 50) × 50 = **24100**

**Verification:** computed 24110.25 == supplied 24110.25 ✓; computed Top Strike 24100 == supplied SP 24100 ✓

---

## Example 4 — 2026-07-28, Low

**Inputs:** Strike = 24000, PE High(1st 5-min) = 136.65, CE Low(1st 5-min) = 180.95

**Calculation:**
```
Weekly Future Low = 24000 − (136.65 − 180.95) = 24000 − (−44.3) = 24044.3
```
**Bottom Strike** = round(24044.3 / 50) × 50 = **24050**

**Note — the sign-flip case:** here `PE High (136.65) < CE Low (180.95)`, so `(PE High − CE Low)` is negative and the subtraction becomes an addition automatically. This is the exact scenario that made `TR-001.md`'s narration confusing (it required a spoken "double-negative becomes a plus" explanation); this formula requires no special case at all — it is the same formula as every other row.

**Verification:** computed 24044.3 == supplied 24044.3 ✓; computed Bottom Strike 24050 == supplied SP 24050 ✓

---

## Example 5 — 2026-07-27, High

**Inputs:** Strike = 23950, CE High(1st 5-min) = 212.75, PE Low(1st 5-min) = 177.05

**Calculation:**
```
Weekly Future High = 23950 + (212.75 − 177.05) = 23950 + 35.7 = 23985.7
```
**Top Strike** = round(23985.7 / 50) × 50 = **24000**

**Verification:** computed 23985.7 == supplied 23985.7 ✓; computed Top Strike 24000 == supplied SP 24000 ✓

---

## Example 6 — 2026-07-27, Low

**Inputs:** Strike = 23950, PE High(1st 5-min) = 201.3, CE Low(1st 5-min) = 176.2

**Calculation:**
```
Weekly Future Low = 23950 − (201.3 − 176.2) = 23950 − 25.1 = 23924.9
```
**Bottom Strike** = round(23924.9 / 50) × 50 = **23900**

**Verification:** computed 23924.9 == supplied 23924.9 ✓; computed Bottom Strike 23900 == supplied SP 23900 ✓

---

## Summary

**6 of 6 computations verified exactly, across 3 independent trading dates.** Zero contradictions. This is the evidence basis for `WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` v1.0 being marked authoritative.

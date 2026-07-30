# TradePlanAI Business Engine Prompt

Reserved for the six blocked engines only — `WeeklyFutureCalculator`, `StrikeSelector`, `TPEngine`, `QualificationEngine`, `StopLossEngine`, `TrailingStopEngine`. Run `SPRINT_GATE_READINESS_REVIEW_TEMPLATE.md` (`research/`) first to get a GO/GO WITH LIMITATIONS/NO GO decision; only use this prompt once that's GO.

```text
Switch to FULL REVIEW MODE.

This task implements business logic.

Perform:

1. Requirement Review
2. Architecture Review
3. Evidence Review
4. Implementation
5. Tests
6. Verification

Never invent trading rules.

Unknown behaviour must remain:

UNRESOLVED – Awaiting Evidence.

If evidence is insufficient:

STOP.

Do not implement assumptions.
```

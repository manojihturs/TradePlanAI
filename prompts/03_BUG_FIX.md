# TradePlanAI Bug Fix Prompt

For production defect fixes. Stays in compact mode — a bug fix is not an architecture event unless the root cause turns out to be architectural (in which case, stop and switch to `02_BUSINESS_ENGINE_IMPLEMENTATION.md`'s Full Review Mode pattern instead).

```text
Use COMPACT DEVELOPMENT MODE.

Fix only the reported bug.

Do not refactor unrelated code.

Maintain backward compatibility.

Run the full verification gate.

Return only:

- Files Changed
- Root Cause
- Fix Applied
- Tests Added
- Verification Summary
```

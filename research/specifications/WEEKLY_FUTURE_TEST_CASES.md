# Weekly Future — Test Cases

Executable-ready input/output pairs, derived from `WEEKLY_FUTURE_CALCULATION_EXAMPLES.md`. Each case gives exact `Decimal` inputs and expected outputs, ready to drive `WeeklyFutureCalculator`/`StrikeSelector` unit tests.

| Case | Strike | CE High | CE Low | PE High | PE Low | Expected Weekly Future High | Expected Weekly Future Low | Expected Top Strike | Expected Bottom Strike |
|---|---|---|---|---|---|---|---|---|---|
| TC-1 (2026-07-29) | 24200 | 143.45 | 116 | 165.8 | 128 | 24215.45 | 24150.2 | 24200 | 24150 |
| TC-2 (2026-07-28) | 24000 | 218 | 180.95 | 136.65 | 107.75 | 24110.25 | 24044.3 | 24100 | 24050 |
| TC-3 (2026-07-27) | 23950 | 212.75 | 176.2 | 201.3 | 177.05 | 23985.7 | 23924.9 | 24000 | 23900 |

**Edge cases to additionally test (not from evidence — structural/engineering edge cases only, no invented business values):**

| Case | Purpose | Notes |
|---|---|---|
| TC-EDGE-1 | `CE High == PE Low` | Weekly Future High == Strike exactly (difference is zero) — pure arithmetic edge case, not a business assumption |
| TC-EDGE-2 | `PE High == CE Low` | Weekly Future Low == Strike exactly, same rationale |
| TC-EDGE-3 | Rounding exactly at the midpoint between two multiples of 50 (e.g. a computed value ending in `.00` exactly 25 away from both neighbors) | **UNRESOLVED – Awaiting Strategy Evidence** — no worked example demonstrates this tie-break; test should assert whatever Python's `round()`/banker's-rounding default produces and flag it as an assumption pending confirmation, not a confirmed rule |
| TC-EDGE-4 | Non-candle-mode (tick) input to the underlying `MarketSnapshot` | Should raise `core.exceptions.ValidationError`, matching every other engine's existing candle-mode requirement (e.g. `ExitEngine`) |

**Explicitly out of scope for these test cases** (per `WEEKLY_FUTURE_FORMULA_SPECIFICATION.md` §6–§8, still UNRESOLVED): Entry rules, Exit rules (Stop Loss/Time Exit), Exceptions (Holiday/Gap Up/Gap Down/Invalid Data). No test case here should be written to cover these — doing so would require inventing behavior this evidence does not supply.

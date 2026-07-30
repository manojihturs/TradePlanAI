# Sprint 5+ Engine Implementation — Reusable Prompt Template

**Do not use this until you have new, authoritative evidence for the engine in question.** The framework is frozen at `v0.6.0-business-orchestration`; this template is the trigger for the *only* two kinds of future work agreed on — an evidence-backed business engine, or a bug fix. See `WEEKLY_FUTURE_BLOCKER_REPORT.md` / `PHASE1_CLOSEOUT.md` for why nothing has been implemented yet.

## How to use this

1. Obtain evidence for one engine (video/transcript/worked examples/screenshots/domain-owner confirmation).
2. Run it through `research/EVIDENCE_INTAKE_PROCESS.md` first — classify it, cross-reference it, get it to ACCEPTED before implementation.
3. Copy the prompt below, fill in the bracketed placeholders for the target engine, and send it as-is.
4. Repeat once per engine, in this order (per `BUSINESS_RULE_INTEGRATION_GUIDE.md` §3): `WeeklyFutureCalculator` → `StrikeSelector` → `TPEngine` → `QualificationEngine` → `StopLossEngine`/`TrailingStopEngine` (the last two are independent of 1–4 and each other; either order, or in parallel with earlier steps, once their own evidence arrives).

---

## Prompt template

```text
You are a Principal Software Engineer working on TradePlanAI.

=========================================================
CURRENT PROJECT STATE
=========================================================

Framework Status:

✓ Core Infrastructure
✓ Event System
✓ Trade Lifecycle
✓ Business Orchestration
✓ Business Architecture
✓ Business Workflow
✓ Requirements Traceability
✓ Business Acceptance Specification

Current Version:

v0.6.0-business-orchestration (or later, if a prior engine in this
sequence has already shipped — check `git tag` first)

=========================================================
IMPORTANT
=========================================================

New authoritative strategy evidence has been provided for:

[NAME THE ENGINE — e.g. WeeklyFutureCalculator]

The evidence consists of:

- [video/transcript/worked examples/screenshots/updated evidence
  documents — list what was actually supplied]

Use ONLY this evidence.

If the evidence is contradictory,
STOP and explain why.

Do NOT guess.

Do NOT repair arithmetic.

Do NOT infer missing rules.

=========================================================
OBJECTIVE
=========================================================

Implement ONLY:

[ENGINE NAME]

Nothing else.

=========================================================
IMPLEMENTATION RULES
=========================================================

The implementation MUST satisfy:

1. BUSINESS_ARCHITECTURE.md
2. BUSINESS_WORKFLOW_SPECIFICATION.md
3. BUSINESS_ACCEPTANCE_SPECIFICATION.md
4. REQUIREMENTS_TRACEABILITY_MATRIX.md

=========================================================
IMPLEMENT
=========================================================

Create only:

src/[engine_package]/

tests/[engine_package]/

Implement:

[EngineName]

Associated dataclasses

Validation

Unit tests

Replay tests

Nothing outside this module.

=========================================================
TEST REQUIREMENTS
=========================================================

Every worked example supplied in the evidence becomes a test case.

Every contradiction becomes a failing validation test.

Every unknown remains:

UNRESOLVED – Awaiting Strategy Evidence

=========================================================
QUALITY
=========================================================

Python 3.12+

mypy --strict

ruff

black

100% tests

No circular dependencies

=========================================================
DO NOT
=========================================================

Do NOT implement any engine other than [ENGINE NAME] in this pass.

The remaining blocked engines stay blocked until their own evidence
arrives.

=========================================================
OUTPUT
=========================================================

Only production code and tests.

No markdown.

No documentation.

No speculative behaviour.
```

---

## Reminders for whoever fills this in

- Re-read the target Protocol directly from `src/interfaces/` before starting — it is the authoritative signature, not this template or any prior document (per `BUSINESS_RULE_INTEGRATION_GUIDE.md`'s own note on this).
- `StopLossEngine`/`TrailingStopEngine` are already constructor-injected into `ExitEngine` — implementing either is a pure drop-in, no other file should need to change.
- After the engine ships: update `REQUIREMENTS_TRACEABILITY_MATRIX.md`'s status for that capability, tag a new version, and — per standing project rule — never auto-commit or push; wait for explicit review and confirmation at each step.

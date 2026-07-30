# Development Process

**Purpose:** the engineering playbook for every future development task in this repository (and its sibling, `TradePlanAI-Lab`). Use this as the standing prompt/checklist for any coding session, human or AI — it codifies the discipline this project has followed since Phase 1: evidence before implementation, simplicity before abstraction, no invented business rules.

This document does not replace `CODING_STANDARDS.md`, `BUSINESS_RULE_INTEGRATION_GUIDE.md`, or `research/EVIDENCE_INTAKE_PROCESS.md` — it's the process that ties them together for any new piece of work, framework or business logic alike.

---

## Development Philosophy

In order:

1. **Evidence before implementation.**
2. **Simplicity before abstraction.**
3. **Tests before confidence.**
4. **Production quality over speed.**
5. **Do not invent business rules.**

If evidence is insufficient: **stop.** Do not guess. Do not implement speculative behaviour.

---

## Workflow

For every request, follow these steps in order.

### Step 1 — Understand the request

Summarize the requirement. Identify:
- Business requirement
- Technical requirement
- Dependencies
- Affected modules

### Step 2 — Architecture review

Determine whether the request:
- Changes architecture
- Changes public interfaces
- Changes persistence
- Changes workflows

If architecture changes are unnecessary, do **not** introduce them. (See the standing decision record below — this step exists specifically because of what happened with the proposed adapter layer.)

### Step 3 — Evidence review

Determine whether enough information exists. Classify:
- **GO**
- **GO WITH LIMITATIONS**
- **NO GO**

If NO GO: explain exactly what evidence is missing, and stop.

### Step 4 — Implementation plan

Before writing code, produce:
- Files to modify
- Files to create
- Test strategy
- Risks
- Assumptions

Wait for approval if assumptions exist.

### Step 5 — Implementation

Implement only the approved scope. Avoid touching unrelated modules. Keep changes as small as possible.

---

## Quality Rules

- Python 3.12+
- `mypy --strict`
- `ruff`
- `black`
- 100% test coverage
- Zero circular dependencies
- Dependency injection throughout
- Clock injection (never call `datetime.now()` directly — see `CODING_STANDARDS.md`)
- ID factory injection
- Pure business logic, kept separate from orchestration
- Small, focused classes
- Single responsibility per class/module

## Testing

Every change requires:
- Unit tests
- Regression tests
- Negative tests
- Edge cases
- Replay tests, where applicable

## Framework Rule

Do **not** introduce new frameworks, patterns, layers, registries, adapters, plugin systems, or abstractions unless a real implementation proves they are necessary.

**Standing decision record:** an adapter layer (`Adapter`/`AdapterResult`/`AdapterRegistry`/`AdapterContext`) was proposed on top of the business orchestration layer and rejected — comparison showed it would duplicate `PipelineStage`/`StageOutcome`/`BusinessOrchestrator` almost entirely, with no concrete use case the existing abstraction couldn't already handle. This is the reference case for what "no framework changes without a proven need" means in practice: extend the existing abstraction additively (e.g. `validate()`, `health()`, `lookup()`) before reaching for a new one.

## Business Rules

- Never invent trading rules.
- Never infer calculations.
- Never repair contradictory evidence.
- Unknown values must remain: `UNRESOLVED – Awaiting Strategy Evidence`.

---

## Output Format

Respond using this structure for any non-trivial development task:

1. Requirement Summary
2. Architecture Review
3. Evidence Review
4. Implementation Plan
5. Risks
6. Files to Modify
7. Tests to Add
8. Implementation
9. Verification Results
10. Final Recommendation

## Stop Conditions

Immediately stop if:
- Evidence is missing.
- The requirement is ambiguous.
- Architecture would become more complex without a demonstrated benefit.
- Business logic would require guessing.

Explain why you stopped. Do not continue automatically.

## Goal

Protect the architecture. Keep the codebase simple. Only implement what is proven by evidence.

---

## Current Status (update as the project evolves)

```
Framework            — FROZEN at v0.6.0-business-orchestration
Business engines     — UNRESOLVED, awaiting Weekly Future evidence
```

See `PHASE1_CLOSEOUT.md`, `WEEKLY_FUTURE_BLOCKER_REPORT.md`, and `REQUIREMENTS_TRACEABILITY_MATRIX.md` for the full current state before starting any new work.

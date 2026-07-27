# Python Implementation Guide

Companion to `SOLUTION_STRUCTURE.md`, `DOMAIN_ARCHITECTURE.md`,
`RULE_ENGINE_ARCHITECTURE.md`, `PROJECT_STRUCTURE.md`, and
`IMPLEMENTATION_ROADMAP.md`. This document records the concrete
Python packaging, dependency, and tooling decisions introduced by the
Milestone 4.0R technology pivot. It does not change any business rule,
Rule ID, Entity ID, Evidence ID, domain responsibility, Rule Engine
architecture, State Machine, or Evidence Model — those remain exactly
as approved. No Python code is written in this milestone; this is a
tooling/standards decision record only.

---

## 1. Recommended Python version

**Python 3.12+.**

Rationale: 3.12 has mature, stable support for the language features
this architecture leans on structurally (dataclasses, `typing.Protocol`,
`enum`, `abc`) and is the current baseline for the libraries listed in
Section 11. The existing `strategy/` package elsewhere in this
repository already assumes a comparably modern interpreter (per its
own `.venv`), so this does not introduce a new minimum-version
constraint the repository didn't already have in practice.

---

## 2. Project structure

See `docs/architecture/PROJECT_STRUCTURE.md` for the full package tree.
Summary: a single top-level package, `trading_engine/`, placed at the
repository root as a sibling to the existing `strategy/`, `docs/`, and
`research/` directories — not nested inside any of them, to avoid
collision with the existing reconstruction documentation or the
separate Version 1.0/1.1 implementation.

---

## 3. Packaging strategy

**A single `pyproject.toml`-based package** (`trading_engine`), using
the `src`-layout convention is *not* mandated here — `PROJECT_STRUCTURE.md`
shows `trading_engine/` as a flat top-level package (no intermediate
`src/`) to match the folder-per-layer structure already designed
(`domain/`, `rules/`, `engine/`, etc. as direct subpackages). This is a
deliberate simplicity choice for a project still in Domain-only
implementation (Milestone 4.1) — revisit if/when the package is
published or needs stricter import isolation from its own tests.

Build backend: `setuptools` (via `pyproject.toml`'s
`[build-system]` table) is recommended as the least-surprising choice
absent any evidence this project needs a more specialized backend
(e.g. a compiled-extension build tool) — nothing in the confirmed
architecture requires anything beyond pure Python.

---

## 4. Dependency management

**`pyproject.toml` as the single source of dependency truth**, using
its standard `[project.dependencies]` / `[project.optional-dependencies]`
tables (e.g. a `dev` extra for the Section 6–9 tooling). Lockfile
tooling (e.g. `pip-tools`, `uv`, or `poetry`) is left as an open
choice for whoever begins Milestone 4.1 implementation — no confirmed
requirement in the reviewed architecture docs favors one over another,
so naming one here would be an unevidenced preference, not an
architectural decision.

**No dependency belongs in `domain/`.** Per `SOLUTION_STRUCTURE.md`,
`domain` depends only on `shared`; in Python terms this means
`domain/` and `shared/` should have **zero third-party imports** —
standard library only (`dataclasses`, `typing`, `enum`, `abc`, `uuid`,
`datetime`). This is the Python-level enforcement of the architecture's
"Domain layer must remain stable" requirement, since Python has no
compile-time project-reference boundary to enforce it otherwise.

---

## 5. Coding standards

- Every domain object is an **immutable `dataclass`**
  (`@dataclass(frozen=True)`), matching the "immutable domain models"
  expectation carried over from the original Milestone 4.1 instruction
  — a frozen dataclass is the direct Python equivalent of the
  C# `sealed record` pattern originally planned.
- **Validation lives in `__post_init__`**, raising a dedicated
  exception type (e.g. a `DomainValidationError` in `shared/`) rather
  than a bare `ValueError`/`AssertionError` — mirroring the
  `DomainValidationException` concept from the original C# plan, so
  domain-rule violations are distinguishable from generic Python
  errors.
- **Enums, not magic strings**, for every closed set of values already
  fixed in documentation (`RuleCategory`, `RuleStatus`,
  `ConfidenceLevel`, `EvidenceLevel`, the five `SessionStateType`
  values) — using `enum.Enum` (or `enum.StrEnum` on 3.12+ where a
  string representation is convenient for logging/serialization).
- **No mutation of "changing" values** (e.g. a TrendPoint's value
  changing over time per TREND-002): represented by producing a new
  frozen-dataclass instance, using `dataclasses.replace(...)`, not by
  mutating an existing instance — preserving the immutability
  requirement while still modeling values that are documented as
  changing over time.
- **Type hints on every public function/attribute** — this is not
  optional style guidance here; it is what makes the static type
  checker (Section 7) meaningful.

---

## 6. Testing framework

**`pytest`.** Chosen for being the de facto standard, and for direct
consistency with the existing `strategy/` package's own test suite
elsewhere in this repository (113 passing tests using Python's
built-in `unittest`, per `CHANGELOG.md`/`SPECIFICATION.md` history) —
`pytest` can run `unittest`-style tests too, so this does not conflict
with that precedent, it extends it with better fixture/parametrization
ergonomics for the new package.

Test layout: `trading_engine/tests/domain/` and
`trading_engine/tests/rules_engine/`, matching `PROJECT_STRUCTURE.md`.

---

## 7. Type checking

**`mypy`, run in strict mode for `domain/` and `rules/`/`engine/`**
(the two layers this milestone and the near-term roadmap actually
touch). Strict mode is recommended specifically for these layers
because they are the ones `SOLUTION_STRUCTURE.md` designates as
needing to "remain stable" — a strict type checker is the closest
Python equivalent to the compile-time safety a statically-typed
language would have given this architecture for free, and this
project explicitly traded that away by pivoting off C#/.NET (per the
Milestone 4.0R background: "rapid iteration is more important than
static typing" was stated as a reason for the *rules' mathematics*,
not as a reason to skip typing the structural code around them).

---

## 8. Linting

**`ruff`.** Chosen for speed and because it subsumes what would
otherwise require several separate tools (import-order checking,
common bug patterns, etc.) in one fast, actively-maintained tool —
minimizing tooling surface area for a project that does not yet have
established local conventions of its own.

---

## 9. Formatting

**`black`** (or `ruff format`, which is Black-compatible) — the point
is a single, non-configurable formatter so code review never spends
time on formatting bikeshedding, consistent with this whole
reconstruction effort's emphasis on evidence over opinion.

---

## 10. Documentation standards

**Google-style or NumPy-style docstrings** (either is acceptable; pick
one and apply it consistently — not decided here, since no evidence in
the reviewed architecture favors one over the other) on every public
module, class, and function, with the same traceability discipline
already used throughout `/docs`: every docstring for a domain object
must cite its Entity ID/Rule ID, and every `TODO` marking an extension
point must cite the Rule ID it is blocked on (e.g. `# TODO (TREND-002):
...`), exactly as the original C# XML-documentation plan specified —
this requirement did not change with the language.

---

## 11. Recommended libraries

Grouped by concern, per the milestone's own example structure. None of
these are installed or imported by this milestone — this is a
recommendation for when implementation begins (Milestone 4.1 onward),
scoped to what each future milestone will actually need.

### Core (Milestone 4.1+)
- `dataclasses` (standard library) — domain object implementation
- `typing` (standard library) — type hints, `Protocol` for rule interfaces (Milestone 4.3)
- `enum` (standard library) — closed value sets (Section 5)
- `abc` (standard library) — alternative to `Protocol` for rule interfaces, if nominal typing is preferred over structural typing once Milestone 4.3 is reached

### Data (Milestone 4.5+ — Replay/Backtest)
- `pandas` — candle/tick series handling for replay
- `numpy` — numeric operations underlying `pandas`

### Backtesting (Milestone 4.7 — optional, evaluate when reached)
- `vectorbt` *(optional)* — only relevant once real rule mathematics
  exist; evaluate against actual rule shapes at that time rather than
  committing now
- `backtesting.py` *(optional)* — same caveat

### API (future, beyond this roadmap's current milestones)
- `FastAPI` — noted for completeness per the milestone's own example
  list; nothing in the current architecture or roadmap (through
  Milestone 4.9) calls for an HTTP API, so this is explicitly
  speculative and not scheduled

### Testing (Milestone 4.6)
- `pytest` (Section 6)
- `pytest-cov` — coverage reporting, natural pairing with `pytest`

### Quality (all milestones)
- `ruff` (Section 8)
- `black` (Section 9)
- `mypy` (Section 7)

### Configuration (Milestone 4.9 — Broker Integration, when reached)
- `pydantic-settings` — structured config for broker credentials/endpoints
- `python-dotenv` — local `.env` support, consistent with the existing
  `strategy/` package's own `.env` convention (`orb_common.py` already
  uses `python-dotenv` in this repository, so this choice is also
  precedented, not novel)

### Logging (Milestone 4.4+ — Rule Engine, for evaluation tracing)
- `structlog` *(preferred)* — structured logging pairs naturally with
  this architecture's traceability requirement (every log line about a
  rule evaluation can carry the Rule ID/Evidence ID as structured
  fields, not just interpolated into a message string)
- standard `logging` *(acceptable fallback)* if `structlog` proves to
  be more than the project needs at Milestone 4.1–4.4's stage

---

## What this document deliberately does not specify

- Any actual dependency version pin (no `pyproject.toml` is written
  here)
- Which lockfile tool to use (Section 4)
- Which docstring style, Google vs. NumPy (Section 10)
- Any rule mathematics, domain behaviour, or business logic — those
  remain governed entirely by `docs/DOMAIN_ARCHITECTURE.md` and
  `docs/RULE_ENGINE_ARCHITECTURE.md`, unchanged by this pivot

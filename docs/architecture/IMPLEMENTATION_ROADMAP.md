# Implementation Roadmap

> **Milestone 4.0R note:** Implementation technology pivoted from
> C#/.NET to Python — see `docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md`.
> Every milestone's scope, exit criteria, and blocking dependency below
> are unchanged; only package/project names and language-specific terms
> (e.g. "interface" → "Protocol/ABC") were updated.

Milestones for implementing the architecture described in this
document set. This roadmap sequences *work*, not logic — no milestone
below authorizes inventing rule mathematics; several are explicitly
scoped to stop short of that until more evidence exists.

## Milestone 4.1 — Domain Models

**Scope:** Implement the confirmed and Candidate domain objects from
`DOMAIN_ARCHITECTURE.md` as data structures only — attributes and
relationships exactly as documented, no calculation methods, no rule
logic. In Python, these are expected to be implemented as immutable
`dataclasses` (see `PYTHON_IMPLEMENTATION_GUIDE.md`), not as
behaviour-bearing classes.

**In scope:** Strike, FirstCandle, TrendPoint, Opponent (with
OpponentHigh/Low as unpopulated attribute slots), MarketStructure
(as an abstract signal type), Reversal, Premium, Edge (as a
condition-evaluation shape, not a stored entity), MarketSession
(container only). The five Candidates, modeled but never imported by
anything outside `domain/candidates/`.

**Out of scope:** Any function that computes a value (strike selection,
TrendPoint updates, Edge threshold, defeat conditions) — these stay as
extension points per `DOMAIN_ARCHITECTURE.md`, not stub functions with
guessed bodies.

**Exit criteria:** The `domain` package imports cleanly, has no
dependency on `rules`/`engine`/`infrastructure`/`backtest`, and every
type maps 1:1 to a heading in `DOMAIN_ARCHITECTURE.md`.

---

## Milestone 4.2 — Session Objects

**Scope:** Implement MarketContext and SessionState per
`RULE_ENGINE_ARCHITECTURE.md`, including the five `STATE_MACHINE.md`
states as a representable-but-not-self-transitioning value (Session
State records which state applies; it does not decide transitions).

**Exit criteria:** SessionState can hold a current state value and the
current TrendPoint(s) for a session; no transition function exists that
wasn't evidenced in `STATE_MACHINE.md`.

---

## Milestone 4.3 — Rule Interfaces

**Scope:** Define the shape a "rule" must have to be registered (what
a rule implementation looks like structurally: it accepts Market
Context + Session State, and can produce a Rule Result) — a
`typing.Protocol` (or `abc.ABC`, per `PYTHON_IMPLEMENTATION_GUIDE.md`'s
recommendation) only, no concrete rule implements it yet.

**Exit criteria:** The Protocol/ABC is defined and is provably
satisfiable by *some* type (even a no-op/test double), without any of
the 6 confirmed rules being implemented against it yet.

---

## Milestone 4.4 — Rule Engine

**Scope:** Implement Rule Registry and Rule Evaluation Pipeline per
`RULE_ENGINE_ARCHITECTURE.md`: registration by Rule ID, dependency-order
evaluation per `RULE_INDEX.md`'s `Depends On` graph, Rule Result and
Decision Object aggregation.

**Explicitly deferred:** The 6 confirmed rules' actual internal logic.
This milestone builds the engine that *would* run them, populated at
this stage with placeholder/no-op registrations only (or none at all)
— consistent with "Do NOT create Rule logic" for Milestone 4.0's
successor work. Implementing real rule bodies requires new evidence
(a further transcript analysis milestone, e.g. a Phase 3.x cycle)
before it can happen without guessing.

**Exit criteria:** The Pipeline can register and evaluate a rule that
satisfies the Milestone 4.3 Protocol/ABC, produce a Rule Result carrying
Rule ID + Evidence ID, and respect the dependency order — provable
with test-double rules, not real ones.

---

## Milestone 4.5 — Replay Engine

**Scope:** `trading_engine.replay` — feed historical candle/tick data
through the Rule Evaluation Pipeline one step at a time, in
chronological order, without any live broker connection.

**Dependency:** Requires Milestone 4.4's Pipeline to exist, but does
not require real rule logic to be meaningful for backtesting yet — it
can be validated end-to-end using the same test-double rules.

---

## Milestone 4.6 — Unit Tests

**Scope:** `tests/` coverage for `domain` (object shape, invariants
explicitly stated in `DOMAIN_ARCHITECTURE.md` — e.g. "TrendPoint
belongs to exactly one Strike") and `rules`/`engine` (Registry lookup,
Pipeline ordering, Decision Object aggregation), using `pytest` per
`PYTHON_IMPLEMENTATION_GUIDE.md`.

**Note on placement:** Listed here per the milestone numbering
requested, but in practice test coverage should accompany each of
4.1–4.5 as they land, not be deferred as one large effort — this
milestone represents closing any coverage gaps, not the first tests
written.

---

## Milestone 4.7 — Backtest

**Scope:** Run the Replay Engine (4.5) against real historical data
end-to-end via `trading_engine.backtest`, producing Decision Objects
across a full session/dataset, and validate the output is
inspectable/traceable back to Rule IDs — mirroring the kind of
validation already done manually for the documentation layer in
`M3_3_REPOSITORY_VALIDATION.md`.

**Blocked on:** Real rule implementations existing (i.e., a future
milestone that evidences and implements at least one rule's actual
mathematics) — without that, a backtest run produces no meaningful
trading-relevant output, only proof that the pipeline mechanics work.

---

## Milestone 4.8 — Paper Trading

**Scope:** Run the same Pipeline against a live (or simulated-live)
data feed instead of historical replay, with no real order placement —
mirrors the existing Python system's Module 11 precedent
(`strategy/live_paper_trading.py`) at an architectural level only; no
code or logic is carried over from that module, even though both now
share the same implementation language.

**Blocked on:** Milestone 4.7 and real rule implementations, same as
above.

---

## Milestone 4.9 — Broker Integration

**Scope:** `trading_engine.infrastructure` — connect a real broker's
market-data and (eventually, separately, and outside this roadmap's
current scope) order-placement APIs, isolated behind the
infrastructure seam defined in `SOLUTION_STRUCTURE.md`.

**Explicitly out of scope for this roadmap entry:** Which broker,
authentication mechanism, or order-placement capability — none of that
is evidenced or decided here; this entry only confirms *where* that
work will live when it happens.

---

## Cross-cutting note on sequencing

Milestones 4.1–4.4 can proceed immediately on the current evidence
(they build structure, not logic). Milestones 4.5–4.6 can proceed on
scaffolding alone (test-double rules). Milestones 4.7–4.9 are
**functionally blocked**, not just sequenced, on new evidence: none of
them produce a meaningful trading outcome until at least one rule's
mathematics moves from `Unknown`/`Partially Known` to `Known` through
further transcript analysis (Phase 3's process, applied again).

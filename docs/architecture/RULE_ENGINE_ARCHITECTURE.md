# Rule Engine Architecture

> **Milestone 4.0R note:** Implementation technology pivoted from
> C#/.NET to Python — see `docs/architecture/PYTHON_IMPLEMENTATION_GUIDE.md`.
> The Rule Engine's responsibilities, boundaries, and traceability
> requirements below are unchanged; only project/language references
> were updated.

Describes the shape of the Rule Engine living in the `rules`/`engine`
packages (see `SOLUTION_STRUCTURE.md`). Architecture only — no rule
mathematics, no implementation code. The design goal this document
serves directly: rule traceability and "rules evolve without changing
unrelated code" (Milestone 4.0 objective).

## Guiding constraint

Every one of the 6 confirmed rules currently has `Mathematical
Definition: Unknown` or `Partially Known` (`TRADINGVIEW_STRATEGY_BIBLE.md`).
This architecture must therefore be able to **register and evaluate
rules whose internal logic doesn't exist yet**, and let that logic be
filled in independently, per rule, as evidence arrives — without the
Rule Engine itself changing shape each time.

---

## Rule Registry

**Responsibility:** A lookup from Rule ID (exactly the IDs in
`RULE_INDEX.md` — `STRIKE-001`, `TREND-001`, `TREND-002`, `TREND-003`,
`OPPONENT-001`, `REVERSAL-001`, plus the two Awaiting-Evidence
placeholders `OPPONENT-002`/`OPPONENT-003`) to a registered rule
implementation.

**Why a registry, not a fixed list:** `RULE_INDEX.md` is explicitly a
living document — new rules arrive per transcript (Milestone 3.1/3.2's
process). A registry keyed by Rule ID means a new rule is added by
registering it, not by modifying the engine's own code — directly
satisfying "rules evolve without changing unrelated code."

**Traceability requirement:** Every registry entry must carry, at
minimum, the same identifying fields `RULE_INDEX.md` already tracks
per rule (Category, Status, Confidence, Evidence Count, Depends
On/Referenced By) so the registry can be validated against the
documentation source it mirrors — the same kind of cross-document
consistency check performed manually in
`research/reviews/M3_3_REPOSITORY_VALIDATION.md` should eventually be
automatable against this registry.

**Placeholder rules:** `OPPONENT-002`/`OPPONENT-003` (Awaiting
Evidence, Evidence Count 0) are represented in the registry as
*registered but inactive* entries — present for traceability
completeness, never invoked by the Evaluation Pipeline, consistent
with `DOMAIN_ARCHITECTURE.md`'s Opponent High/Low treatment (attribute
slots only, no computation).

---

## Market Context

**Responsibility:** The read-only snapshot of market data a rule
evaluation runs against for one moment in time — analogous to a single
candle/tick being fed to the engine.

**Composition (from confirmed Domain objects only):** references the
current MarketSession, the Strike(s) under analysis, and whatever raw
price/premium data a rule needs to read (Premium, per
`DOMAIN_ARCHITECTURE.md`'s thin Premium object). Market Context does
not itself compute anything — it is data, assembled once per
evaluation step and handed to every rule that runs against it.

**Instrument-agnostic:** Per `SOLUTION_STRUCTURE.md`'s multi-instrument
goal, Market Context is not designed around a specific instrument
(NIFTY or otherwise) — nothing in the confirmed evidence ties any rule
to a specific instrument.

---

## Session State

**Responsibility:** The mutable, accumulating state that persists
*across* evaluation steps within one MarketSession — as opposed to
Market Context, which is the input for a single step.

**What it holds (from confirmed evidence only):** the current
TrendPoint value(s) per Strike (since TREND-001/002 describe TrendPoint
as something read *and later updated*), and the current position in
`STATE_MACHINE.md`'s state set (`STRIKE_SELECTED`, `TREND_TRACKING`,
`OPPONENT_ENGAGEMENT`, `OPPONENT_DEFEATED`, `REVERSAL_IDENTIFIED`) —
each state carried exactly as `STATE_MACHINE.md` defines it, including
that most transition conditions remain `UNKNOWN`.

**Explicit non-design:** Session State does **not** encode any
transition logic between those five states — `STATE_MACHINE.md`
itself states 4 of 5 states have `UNKNOWN` entry/exit conditions and
the one populated transition (`OPPONENT_ENGAGEMENT` →
`OPPONENT_DEFEATED`) is marked hypothesised, not confirmed. Session
State is a place to *record* which state applies, not a state machine
implementation that *decides* transitions — that would mean inventing
the missing logic.

---

## Rule Evaluation Pipeline

**Responsibility:** The ordered process that takes a Market Context +
Session State, runs the currently-registered, currently-active rules
against them, and produces Rule Results.

**Shape (architecture-level, not implementation):**

1. Assemble Market Context for the current evaluation step.
2. Look up all active (non-placeholder) rules from the Rule Registry.
3. For each rule, evaluate it against (Market Context, Session State) —
   producing zero or one Rule Result per rule per step.
4. Collect Rule Results into a Decision Object.
5. Apply any resulting Session State updates.

**Ordering:** `RULE_INDEX.md`'s `Depends On`/`Referenced By` columns
already express a dependency graph among the 6 confirmed rules (e.g.
`TREND-002` depends on `TREND-001`; `TREND-003` depends on `TREND-001`
and `OPPONENT-001`). The Pipeline's evaluation order is derived from
this existing graph, not a new ordering invented here — a rule is
never evaluated before a rule it depends on.

**No cross-rule logic invented:** The Pipeline sequences and collects;
it does not decide what a rule concludes. Nothing here encodes, e.g.,
how a `TREND-003` (Edge) result should influence a `REVERSAL-001`
evaluation — no such interaction is evidenced.

---

## Rule Results

**Responsibility:** The outcome of one rule's evaluation at one Market
Context, carrying:
- The Rule ID it came from (traceability back to `RULE_INDEX.md`)
- The Evidence ID(s) backing that rule (traceability back to
  `TRACEABILITY_MATRIX.md`'s `EVID-NNN` entries)
- An outcome value — deliberately left generic in this architecture
  (not typed as boolean/numeric/etc.) since different rules' outcomes
  are not yet evidenced to share a shape (e.g. STRIKE-001 "produces a
  strike," TREND-003 "evaluates a condition" — these are not
  interchangeable result types by current evidence)

**Why results carry Evidence IDs, not just Rule IDs:** a Rule Result
produced while its rule's Confidence is `Medium` (Evidence Count 2)
should be distinguishable, at the result level, from one produced once
that rule reaches `High`/`Confirmed` — carrying the Evidence ID(s) lets
downstream consumers (backtesting, later paper trading) weight or
filter results by evidentiary strength without the Rule Engine itself
making that judgment call.

---

## Decision Objects

**Responsibility:** The aggregate of Rule Results from one evaluation
step, representing "what the engine currently believes," without
itself constituting a trading decision (no entry/exit logic exists in
confirmed evidence — `docs/TRADINGVIEW_STRATEGY_BIBLE.md`'s `ENTRY`
and `EXIT` categories are both empty).

**Explicit scope limit:** Decision Objects are named for what they
will eventually support (a future trading decision), but at this
milestone they are purely a structured collection of Rule Results plus
the Session State they were produced against — no synthesis logic
(e.g. "if TREND-003 Edge holds AND REVERSAL-001 fires, then...") is
designed, because no such combination rule is evidenced anywhere in
the reviewed documents.

---

## Rule Traceability (cross-cutting)

Every architectural element above that touches a rule — Registry
entries, Rule Results, Decision Objects — carries the Rule ID and
Evidence ID(s) verbatim from `RULE_INDEX.md`/`TRACEABILITY_MATRIX.md`.
This is a deliberate design constraint, not an incidental feature: it
means a future automated consistency check (the natural next step
after `research/reviews/M3_3_REPOSITORY_VALIDATION.md`'s manual review)
can compare the running system's registered rules against the
documentation and flag drift the same way that review flagged
documentation-to-documentation drift.

**Candidates are not wired into the Pipeline.** The five Candidate
entities (`ENT-010`–`014`) and the Unknown Concept (`UNK-001`, IVL
Level) have no corresponding Rule ID in `RULE_INDEX.md` and therefore
have no Registry entry, no evaluation step, and produce no Rule
Results — consistent with `docs/DOMAIN_ARCHITECTURE.md`'s "reserved,
inactive" treatment of them.

---

## What this document deliberately does not specify

- The internal algorithm of any rule (all remain `Unknown`/`Partially
  Known` per the Bible)
- The exact data type of a Rule Result's outcome value
- Transition logic between `STATE_MACHINE.md`'s five states
- Any synthesis/combination logic across multiple Rule Results
- Any backtest-specific or broker-specific concern (those belong to
  the `backtest`/`infrastructure` packages per `SOLUTION_STRUCTURE.md`,
  and are out of scope for Milestone 4.0)

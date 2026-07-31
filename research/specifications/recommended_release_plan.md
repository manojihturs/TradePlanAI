# Recommended Release Plan

**Status:** Documentation only. Recommendations based solely on evidence-backed work identified in `business_engine_portfolio.md`, `implementation_priority_matrix.md`, and `dependency_graph.md`. No engine is scheduled ahead of its evidence being resolved.

---

## Version 0.2 — Already Achieved

Everything in this release is already implemented and verified (100% test coverage, per this session's own standard gate):

- Replay Framework
- Weekly Future
- Strike Selection
- ORB (Opening Range Breakout)
- Strategy Timeline / Strategy Inspector / Replay Session Explorer / Replay Comparison
- Winner Detection
- Entry Engine
- Target computation (Rule 2, inside PositionManager)
- Exit Engine — Target/Competitor legs

This is effectively the current state of the codebase as of this audit — no new engineering work is required to call this milestone complete; it is a naming/tagging exercise, not a build task.

## Version 0.3 — Contingent on Priority 2 Research

Ships only if the research sprint recommended in `implementation_priority_matrix.md` succeeds:

- Stop Loss Engine (contingent on Product-Owner evidence: SL price, basis, placement rule)
- Trailing Stop Engine (contingent on Product-Owner evidence: activation trigger, step/distance, brokerage/exchange/tax figures)
- Exit Engine — full 4-condition evaluation, including precedence ordering (contingent on both of the above, plus a stated precedence rule for Section 20 item 11)

**If this research does not succeed:** Version 0.3 ships as a no-op — Exit Engine remains at its current partial (Target/Competitor-only) capability, and the project moves directly to considering Version 1.0 scope without these three items.

## Version 0.4 — Not Currently Plannable

No engine in this audit has a credible, evidence-backed path to this release. Premium Calculator's only path forward (REVERSAL-001, Draft/Medium confidence, 2 evidence points) is too thin to schedule against a version number; it would need to be re-evaluated only if new Product-Owner evidence arrives, at which point it could be considered for whatever version is then in progress.

## Version 1.0 — Ships Without Frozen Engines, Per Existing Decision Rule

Per this project's own decision tree ("If multiple engines are frozen → Accept that Version 1.0 will ship without them unless new Product Owner evidence becomes available"), the following remain frozen and out of scope for 1.0 unless new evidence arrives:

- Qualification Engine (QUAL-007)
- Market State Engine (same root cause as Qualification Engine)
- Target Engine — pre-Winner TP Engine half (same root cause)
- Premium Calculator
- Greeks Engine
- Risk Engine

This is not a gap in the release — it reflects that this project's evidence-first discipline has been applied consistently across the entire engine portfolio, not just the engines convenient to build.

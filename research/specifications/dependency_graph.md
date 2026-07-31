# Business Engine Dependency Graph

**Status:** Documentation only. Every edge below is sourced from `business_engine_portfolio.md`; no dependency is inferred beyond what the evidence states.

---

## Confirmed dependency edges

```
Winner Detection (implemented)
        |
        v  publishes WinnerDetectedEvent, consumed by
Entry Engine (implemented)
        |
        v  calls PositionManager.open_position
Target/Competitor computation — Rule 2 (implemented, inside PositionManager)
        |
        v  reused directly by (no duplication, per source instruction)
Exit Engine — Target/Competitor legs (implemented)
        |
        +---> Stop Loss Engine (frozen/research) ---> gates Exit Engine's 3rd exit condition
        |
        +---> Trailing Stop Engine (partial/research) ---> gates Exit Engine's 4th exit condition
        |
        v
Exit Engine — full 4-condition evaluation (PARTIAL: blocked until SL + Trailing Stop resolved)
        |
        v  precedence among simultaneous conditions
Exit Engine — precedence ordering (frozen: Section 20 item 11, MISSING INFORMATION)
```

```
Qualification Engine (frozen: QUAL-007)
        |
        +--- same root blocker as ---> Market State Engine (not a separate engine)
        |
        +--- same root blocker as ---> Target Engine, pre-Winner TP Engine half
```

```
Premium Calculator (frozen: no primary-side evidence)
        |
        v  only speculative link (not confirmed anywhere)
REVERSAL-001 (Draft, Medium confidence, 2 evidence points)
```

## Isolated (no dependency edges found)

- **Greeks Engine** — no evidence of any inputs, outputs, or connections to any other engine.
- **Risk Engine** — no evidence of any inputs, outputs, or connections to any other engine.

---

## Reading the graph

- The **only live, working chain** today is Winner Detection → Entry Engine → Target/Competitor (Rule 2) → Exit Engine's Target/Competitor legs. This chain is fully implemented and requires no further evidence.
- **Exit Engine is the single integration point** where two Priority-2 research items (Stop Loss, Trailing Stop) would plug in without requiring any change to the already-implemented chain above — closing those two gaps is additive, not a rework.
- **Qualification Engine's freeze radiates** to two other items in the original 10-engine list (Market State Engine, pre-Winner TP Engine) — they are not independent blockers requiring separate research; resolving QUAL-007 resolves all three at once.
- **Premium Calculator and Greeks/Risk Engines are dependency dead-ends** — nothing in the currently-implemented chain depends on them, and they depend on nothing already resolved. Freezing them has zero impact on any other engine's progress.

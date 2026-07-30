# Service Sequence

The runtime call sequence given in the milestone brief and reproduced
in `research/specification/REALTIME_TRADING_SPECIFICATION.md` Section
1's workflow table and Section 1's Mermaid architecture diagram:
09:15 Market Open -> 09:20 First Candle Complete -> Strike Engine ->
Premium Snapshot -> Level Engine -> Trend Engine -> Competitor Engine
-> Winner Engine -> Trade Engine -> Exit Engine -> Paper Trade.

Sequence only — which service calls which, in what order. No
algorithm inside any step. Cross-referenced against
`REALTIME_TRADING_SPECIFICATION.md` Section 1's existing Mermaid
diagram rather than re-derived from scratch.

---

## Sequence description

1. **09:15 Market Open.** A clock event, not a calculation (FSD
   Section 1, workflow step 1). Triggers `SessionState`'s initial
   state; no engine call yet.
2. **09:20 First Candle Complete.** A clock event (workflow step 2,
   FSD Section 1). The exact 09:20 timing itself is user-supplied for
   this milestone only, not repository-evidenced (FSD Section 1 row
   2). Triggers the Weekly Future arithmetic step next, per the
   Mermaid diagram's `B --> WF` edge.
3. **Weekly Future arithmetic (WeeklyFutureCalculator).** Called with
   Call/Put option first-candle High/Low and ATM strike. Its output
   feeds Strike Engine next, per the diagram's `WF --> SE` edge. This
   step's own internals are NOT READY (`WEEKLY_FUTURE_VERIFICATION.md`)
   — the sequence position is describable even though the content is
   not.
4. **Strike Engine (StrikeEngine).** Called with the Weekly Future
   High/Low output. Produces Top Strike and Bottom Strike (diagram's
   `SE --> TS`, `SE --> BS` edges), corresponding to workflow steps
   3-4. Rule shape PARTIALLY READY; overall NOT READY (see
   CLASS_DIAGRAM.md §3).
5. **Option Range Engine (OptionRangeEngine).** Per the diagram, both
   Top Strike and Bottom Strike feed into this step (`TS --> ORE`,
   `BS --> ORE`) before Premium Snapshot is reached. Entirely UNKNOWN
   internals (FSD Section 4) — its sequence position (after Strike
   selection, before Premium Snapshot) is the only describable part,
   per the diagram's own edges.
6. **Premium Snapshot (PremiumSnapshotEngine).** Called next in the
   diagram (`ORE --> PSE`), corresponding to workflow step 5, "Capture
   Premium Levels." Output is a Premium value holder
   (id/value/timestamp only).
7. **Level Engine (LevelEngine).** Called with the Premium Snapshot
   output (`PSE --> LE`). Entirely UNKNOWN scope beyond this position
   in the sequence (FSD Section 5).
8. **Competitor Engine (CompetitorEngine).** Called next (`LE --> CE`),
   corresponding to workflow step 6, "Monitor Competitor." The diagram
   also shows a separate, parallel edge from Trend Engine into
   Competitor Engine (`TE --> CE`) — i.e. Trend Engine's own output is
   itself an input to this step, not purely sequential-after. Rule
   shape referenced (OPPONENT-001, Evidence Count 2); "defeat"
   condition itself UNKNOWN.
9. **Trend Engine (TrendEngine).** Per the diagram, Trend Engine feeds
   both Competitor Engine (`TE --> CE`) and Winner Engine (`TE --> WE`)
   directly — it is not placed strictly between Competitor Engine and
   Winner Engine in the diagram's own edges, but rather runs alongside
   Competitor Engine and supplies both Competitor Engine and Winner
   Engine. This blueprint preserves that diagram structure rather than
   forcing a purely linear Competitor-Engine-then-Trend-Engine
   ordering that the workflow's prose list alone might imply.
10. **Winner Engine (WinnerEngine).** Called with Competitor Engine's
    output and Trend Engine's output (`CE --> WE`, `TE --> WE`),
    corresponding to workflow step 7, "Determine Winner." Entirely
    UNKNOWN internals (FSD Section 8) — no rule ID or entity
    corresponds to this concept at all.
11. **Entry Engine / Trade Engine (TradeEngine).** Called with Winner
    Engine's output (`WE --> EE`), corresponding to workflow step 8,
    "Entry." Documented non-rule (FSD Section 9) — entry framed as a
    "logical" judgment, not a fixed formula.
12. **Trade Management / Risk Engine (RiskEngine).** Called next
    (`EE --> TME`), corresponding to workflow step 9, "Trade
    Management." Documented non-rule (FSD Section 11).
13. **Exit Engine (ExitEngine).** Called last in the primary chain
    (`TME --> XE`), corresponding to workflow step 10, "Exit."
    Documented non-rule (FSD Section 10). The diagram additionally
    shows Reversal (`RE -.feeds.-> XE`, `RE -.feeds.-> TME`) as a
    dashed (i.e. weakly-evidenced/architectural, not a firm sequential
    call) feed into both Exit Engine and Trade Management — REVERSAL-001
    is "the worst-evidenced rule in the project" (FSD Section 10), so
    this feed's own timing/trigger mechanism is UNKNOWN even though
    its position in the diagram is stated.
14. **Paper Trade (PaperTradeEngine).** Not present in the FSD's own
    Mermaid diagram (the diagram ends at Exit Engine); its position at
    the end of the sequence comes from the milestone brief's own
    workflow list and from
    `research/analysis/IMPLEMENTATION_UNLOCK_SEQUENCE.md`'s roadmap
    statement that "Paper trading (Milestone 4.8) follows Backtest in
    the roadmap's sequence." Entirely UNKNOWN internals; consumes
    TradeEngine/ExitEngine/RiskEngine outputs, by workflow-list
    position only, not by any evidenced data contract.

---

## Cross-reference to the FSD's own Mermaid diagram

The above sequence reuses `REALTIME_TRADING_SPECIFICATION.md` Section
1's diagram edges directly (`A --> B --> WF --> SE --> {TS, BS} -->
ORE --> PSE --> LE --> CE`, with `TE --> CE` and `TE --> WE` as
parallel feeds, `CE --> WE --> EE --> TME --> XE`, and `RE -.feeds.->
{XE, TME}` as dashed architectural feeds) rather than re-deriving
dependency order from the workflow's prose list alone, per this
document's own instruction to cross-reference that diagram as the
authority.

## Where the sequence's internals are entirely UNKNOWN

Per FSD Section 17's Unknown Knowledge Register, the following steps'
sequence *position* is describable (per the diagram above) while their
internal content is entirely or almost entirely UNKNOWN: Option Range
Engine (step 5), Level Engine (step 7), Winner Engine (step 10), Entry
Engine (step 11, documented non-rule), Trade Management/Risk Engine
(step 12, documented non-rule), Exit Engine (step 13, documented
non-rule), Paper Trade (step 14). Steps 3 (Weekly Future), 4 (Strike
Engine), 8 (Competitor Engine), and 9 (Trend Engine) have PARTIAL
rule-shape evidence (their existence and rough inputs/outputs are
stated) even though their computations remain NOT READY.

---

Sources: `research/specification/REALTIME_TRADING_SPECIFICATION.md`
Section 1 (workflow table + Mermaid diagram), Sections 2-11, Section
17; `research/analysis/IMPLEMENTATION_UNLOCK_SEQUENCE.md` (Paper
Trading roadmap sequencing).

# TradingView Hidden Rules

Living document. Recovers undocumented business logic from manual
chart analysis and the original TradingView strategy - treated here as
source of truth, independent of and prior to any comparison against
the current Python implementation (`strategy/` Modules 1-11, "Version
1.0", frozen). No code is modified as a result of this document; no
rule here is proposed for implementation until you decide it's ready.

## Purpose

The original TradingView strategy reportedly achieved ~90% success
during manual backtesting. The written specification that Modules 1-11
implement, and the Python Premium Mapping itself, are NOT assumed to
be a complete or correct account of that strategy - per current
instruction, they are demoted to "one interpretation" pending
reconstruction of the original logic from firsthand evidence (chart
review, manual backtesting notes, the YouTube strategy source).

This document is deliberately separate from `TRADINGVIEW_REQUIREMENTS_RECOVERY.md`
(RTV-N entries), which compares evidence against the current Python
code. Entries here (`HR-N`) focus purely on documenting what the
original strategy did, without reference to what Modules 1-11
currently implement - that comparison happens later, as its own step.

## Rules of this document

1. **Evidence-driven only.** An entry is added only in response to a
   concrete example you walk through - a chart, a video segment you
   describe, a manual backtest note. Nothing is added speculatively or
   inferred from the Python code.
2. **No fabrication.** I have no ability to watch, transcribe, or
   infer the contents of a YouTube video or any other source I have
   not been shown directly in this conversation. If a source hasn't
   been shared with me, it does not appear here, however plausible a
   rule might seem.
3. **No comparison to the current implementation in this document.**
   That happens later, as an explicit separate step, once enough of
   the original logic has been recovered.
4. **No optimisation, no thresholds, no new rules proposed here.**
   Pure documentation of observed behaviour only.

## Per-example documentation fields

For every TradingView example reviewed:

- **Entry reason** - what triggered the trade, as shown/described.
- **Exit reason** - what triggered the exit, as shown/described.
- **Competitor behaviour** - what the opposite-side contract was doing
  at entry and exit, if shown.
- **Own premium behaviour** - the traded contract's own price action
  around entry and exit.
- **Market structure** - spot price context, support/resistance,
  pivot levels, or other structural context visible on the chart.
- **Hidden confirmation** - anything used as a condition that is not
  currently documented anywhere in `SPECIFICATION.md` or the Modules
  1-11 build history.

---

## Examples

*(No examples reviewed yet. Entries are appended below in the order
they are provided, each numbered `HR-1`, `HR-2`, etc. - "HR" = Hidden
Rule.)*

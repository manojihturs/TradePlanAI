# Knowledge Sources

The single source of truth for all research materials feeding the
TradingView strategy reconstruction effort (see `/docs` at the repo
root for the reconstruction documentation itself). This document
defines what each type of source is for, how much confidence it
carries, and the rule governing when evidence is sufficient to add a
business rule to the Strategy Bible.

## Folder structure

```
/research
    /transcripts   - Raw YouTube transcript text, one file per video
    /videos        - Video metadata/references (URLs, titles, dates) -
                     not the video files themselves
    /notes         - User-provided manual notes, observations, and
                     annotations not tied to a specific transcript or
                     screenshot
    /analysis      - Derived analysis documents that synthesise raw
                     sources (e.g. cross-referencing two transcripts) -
                     distinct from the raw sources themselves
```

Raw source material (transcripts, screenshots, notes) is never edited
in place once added - corrections or reinterpretations go in
`/analysis` as a new, separately-dated document, so the original
evidence trail stays intact.

## Source types and their purpose

### YouTube transcript
The author's own recorded explanation of the methodology, in their own
words. This is the closest available material to the original source
of the strategy. Stored verbatim in `/research/transcripts`, one file
per video, with the video's title/URL/date recorded alongside it.

### Manual observation
A description, in the user's own words, of a specific trade or chart
pattern observed while manually trading or reviewing charts (not tied
to a specific TradingView screenshot artifact). Stored in
`/research/notes`.

### Existing Python implementation
The `strategy/` package (Version 1.0/1.1) and its supporting
documentation (`SPECIFICATION.md`, `CHANGELOG.md`, `INVESTIGATIONS.md`
at the repo root). Represents one prior interpretation of the strategy,
already built and tested against historical data - useful as a
comparison point, not as a source of what the original strategy
actually specified.

### TradingView screenshots
Chart images showing the live strategy in use, with entry/exit
markers, price levels, and mapped-value labels visible. Stored as
image files (or references to where they're stored, if handled outside
this repo) with accompanying description in `/research/notes` or
`/research/analysis` of what the screenshot shows.

### Excel backtest
Spreadsheet exports of historical trade data - either the user's own
manual trade journal, or exports from the existing Python engine's
backtest runs (`backtest_summary.xlsx`, `trade_journal.xlsx`, etc. at
the repo root). Used to check whether a hypothesised rule is consistent
with actual historical outcomes.

### User notes
Free-form clarification, correction, or context provided directly by
the user in conversation - not tied to a specific transcript,
screenshot, or spreadsheet. Stored in `/research/notes`.

## Evidence levels

| Level | Source type | Confidence |
|---|---|---|
| **LEVEL 1** | Original YouTube transcript | Highest - the author's own direct explanation |
| **LEVEL 2** | User manual observations (including TradingView screenshots and manual trade logs) | High - firsthand account of real behaviour, but filtered through interpretation/recollection |
| **LEVEL 3** | Existing implementation | Reference only - a prior interpretation, not original source material |
| **LEVEL 4** | Hypothesis | Lowest - a pattern noticed or inferred, not yet confirmed against any direct source |

Higher-numbered levels do not override lower-numbered ones. A LEVEL 3
(existing code) observation never establishes what the original
strategy did; it only describes what one implementation attempt did. A
LEVEL 1 transcript statement takes precedence over a LEVEL 2
observation if they conflict, and any conflict between levels is
recorded as a contradiction, not silently resolved.

## Governing rule

**No business rule may be added to `TRADINGVIEW_STRATEGY_BIBLE.md`
unless it references one or more evidence sources**, each identified by
its file/location in `/research` and its evidence level. A rule with
no traceable source is not recorded as a rule - at most it is recorded
as an open question (see `RULE_INDEX.md`'s `INSUFFICIENT_EVIDENCE`
status and each rule's "Unknown Questions" field).

## Status

Structure created. No sources have been added yet - `/research`'s
subfolders are currently empty (holding only placeholder files to
preserve the directory structure in git). No trading rules have been
extracted from any source at this stage.
